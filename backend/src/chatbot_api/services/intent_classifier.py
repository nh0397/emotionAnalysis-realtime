import re
import json
import requests
from typing import Tuple, Optional, List, Dict
from chatbot_api.config import (
    OLLAMA_BASE_URL, 
    OLLAMA_MODEL, 
    OLLAMA_TIMEOUT,
    OLLAMA_TEMP_CLASSIFICATION
)

def classify_intent_smart(
    question: str, 
    has_screenshot: bool,
    current_page: Optional[str] = None,
    previous_queries: List[Dict] = None
) -> Tuple[str, dict]:
    """
    LLM-first intent classification with minimal hardcoded rules.
    
    Returns: (intent, context)
    intent: 'smalltalk', 'data_query', 'rag_query'
    context: additional routing information
    """
    
    if previous_queries is None:
        previous_queries = []
    
    q_lower = question.lower().strip()
    
    # ==== FAST PATH: OBVIOUS PATTERNS (avoid LLM call) ====
    
    # 1. Greetings and acknowledgments
    greetings = [
        'hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening',
        'thanks', 'thank you', 'bye', 'goodbye', 'ok', 'okay', 'cool', 
        'nice', 'great', 'awesome', 'perfect', 'yes', 'no', 'yep', 'nope'
    ]
    
    for greeting in greetings:
        if q_lower == greeting or q_lower.startswith(greeting + ' ') or q_lower.startswith(greeting + ','):
            print(f"[intent_classifier.py:41] Fast path: '{question}' matched greeting '{greeting}' → smalltalk")
            return 'smalltalk', {'reason': 'greeting_detected', 'matched': greeting}
    
    if len(q_lower.split()) <= 2 and q_lower in ['sure', 'k']:
        return 'smalltalk', {'reason': 'short_acknowledgment'}
    
    # 2. UI/Help questions - these should NEVER go to data_query
    ui_patterns = [
        'what is this page',
        'what am i looking at',
        'what does this page',
        'what is this',
        'explain this page',
        'what page is this',
        'what am i seeing',
        'what does this show',
        'how do i use this',
        'how does this work',
        'what can i do here',
        'what is the history page',
        'what is the live stream',
        'what is the analytics',
        'what is the emotion map'
    ]
    
    for pattern in ui_patterns:
        if pattern in q_lower:
            print(f"[intent_classifier.py:56] Fast path: '{question}' matched UI pattern '{pattern}' → rag_query")
            return 'rag_query', {'reason': 'ui_pattern_match', 'matched': pattern}
    
    # 3. Contextual UI questions (require conversation history)
    contextual_ui_patterns = [
        'and this one',
        'what about this',
        'and this page',
        'this one',
        'and here',
        'what about here'
    ]
    
    # Check if it's a contextual question AND we have recent UI questions in history
    if any(pattern in q_lower for pattern in contextual_ui_patterns):
        # Look for recent UI-related questions in history
        if previous_queries:
            recent_intents = [q.get('intent') for q in previous_queries[-3:]]
            if 'rag_query' in recent_intents or any('page' in q.get('question', '').lower() for q in previous_queries[-2:]):
                print(f"[intent_classifier.py:78] Fast path: '{question}' is contextual UI question → rag_query")
                return 'rag_query', {'reason': 'contextual_ui_question', 'previous_context': True}
    
    # ==== LLM CLASSIFICATION (PRIMARY) ====
    intent, confidence = classify_with_llm(question, current_page, previous_queries)
    
    return intent, {
        'reason': 'llm_classification',
        'confidence': confidence
    }


def classify_with_llm(
    question: str, 
    current_page: Optional[str],
    previous_queries: List[Dict]
) -> Tuple[str, float]:
    """
    Use Ollama to classify intent with rich context.
    Returns: (intent, confidence)
    """
    
    # Build context
    context_parts = []
    
    if current_page:
        page_descriptions = {
            '/': 'Live Stream page (real-time tweets)',
            '/live': 'Live Stream page (real-time tweets)',
            '/history': 'Historical Tweets page',
            '/metrics': 'Analytics/Metrics page',
            '/visualization': 'Emotion Map visualization page (dot plot with states)'
        }
        page_desc = page_descriptions.get(current_page, f"'{current_page}' page")
        context_parts.append(f"User is currently viewing: {page_desc}")
    
    if previous_queries and len(previous_queries) > 0:
        recent = previous_queries[-3:]  # Last 3 queries
        recent_qs = [f"Q: {q.get('question', '')}" for q in recent]
        context_parts.append(f"Recent conversation:\n" + "\n".join(recent_qs))
    
    context = "\n".join(context_parts) if context_parts else "No additional context"
    
    prompt = f"""You are an intent classifier for TecViz, an emotion analytics platform.

TecViz shows emotion data (anger, joy, fear, sadness, surprise, anticipation, trust, disgust) across US states.
Users can query data by state, emotion, time period, or ask for help with the interface.

CONTEXT:
{context}

USER QUESTION: "{question}"

CLASSIFY INTO ONE CATEGORY:

1. **data_query** - User wants to query/analyze data
   - Asking about states (California, TX, New York, etc.)
   - Asking about emotions (anger, joy, fear, etc.)
   - Asking for trends, comparisons, statistics
   - Questions like: "What's happening in X?", "Show me Y", "Compare A and B", "Highest Z"
   
2. **rag_query** - User needs help with the UI or platform
   - Asking about the interface ("what is this page?", "what am I looking at?")
   - Questions like "explain this", "what does this show?", "how do I use this?"
   - Confused about what they're seeing on the current page
   - Asking for guidance or explanations of the visualization
   
3. **smalltalk** - Casual conversation
   - Greetings, thanks, acknowledgments
   - General chitchat

THINK STEP-BY-STEP:
1. Is the user asking for DATA/ANALYTICS or HELP/EXPLANATION?
2. Are they asking about specific emotions, states, or trends? → data_query
3. Are they asking "what is this?" or "how do I use...?" → rag_query
4. Just being casual? → smalltalk
5. CONTEXTUAL: Are they saying "and this one", "this one" after asking about pages? → rag_query

IMPORTANT: 
- Questions about "what is this page", "what am I looking at", "explain this" → rag_query
- Contextual questions like "and this one?", "what about this?" → rag_query
- Questions with specific states/emotions/data requests → data_query
- Use conversation history to understand context
- Be precise - don't default everything to data_query

Respond with ONLY valid JSON (no markdown, no extra text):
{{"intent": "data_query", "confidence": 0.90, "reasoning": "User asking about specific state data"}}"""
    
    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": OLLAMA_TEMP_CLASSIFICATION,
                    "top_p": 0.9,
                    "num_predict": 150
                }
            },
            timeout=OLLAMA_TIMEOUT
        )
        
        if response.status_code != 200:
            print(f"[intent_classifier.py:143] Ollama API error: {response.status_code}")
            return 'data_query', 0.5  # Default to data_query on error
        
        result_text = response.json().get("response", "").strip()
        
        # Clean up markdown code blocks if present
        result_text = result_text.replace("```json", "").replace("```", "").strip()
        
        # Try to parse JSON
        result = json.loads(result_text)
        intent = result.get('intent', 'data_query')
        confidence = result.get('confidence', 0.5)
        reasoning = result.get('reasoning', '')
        
        # Validate intent
        if intent not in ['data_query', 'rag_query', 'smalltalk']:
            print(f"[intent_classifier.py:159] Invalid intent from LLM: {intent}, defaulting to data_query")
            intent = 'data_query'
            confidence = 0.5
        
        print(f"[intent_classifier.py:163] LLM Classification: {intent} (confidence: {confidence}) - {reasoning}")
        return intent, float(confidence)
        
    except json.JSONDecodeError as e:
        print(f"[intent_classifier.py:167] JSON parse error: {e}, response: {result_text[:200]}")
        # Try fallback text parsing
        if 'response' in locals():
            response_lower = str(result_text).lower()
            if 'data_query' in response_lower or 'data' in response_lower:
                return 'data_query', 0.6
            elif 'rag_query' in response_lower or 'rag' in response_lower or 'help' in response_lower:
                return 'rag_query', 0.6
            elif 'smalltalk' in response_lower:
                return 'smalltalk', 0.6
        
        # Default to data_query (most common)
        return 'data_query', 0.5
        
    except requests.exceptions.RequestException as e:
        print(f"[intent_classifier.py:182] Ollama connection error: {e}")
        return 'data_query', 0.5
        
    except Exception as e:
        print(f"[intent_classifier.py:186] Unexpected error in LLM classification: {e}")
        return 'data_query', 0.5

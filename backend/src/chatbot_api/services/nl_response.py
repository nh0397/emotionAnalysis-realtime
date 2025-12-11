"""
Natural Language Response Generator
Converts SQL query results into human-readable English responses using LLM
"""

import requests
from typing import List, Dict, Optional
from ..config import GEMINI_API_KEY, GEMINI_MODEL_NL2SQL



def generate_nl_response(question: str, sql: str, rows: List[Dict], chart_hint: Optional[str] = None, current_page: Optional[str] = None) -> str:
    """
    Generate a natural language response from SQL results using LLM
    
    Args:
        question: User's original question
        sql: SQL query that was executed
        rows: Query results (list of dicts)
        chart_hint: Suggested visualization type
    
    Returns:
        Natural language response string
    """
    # If no results, provide a clear message
    if not rows or len(rows) == 0:
        return "I found no results matching your query."
    
    # Prepare data summary for the LLM
    data_summary = prepare_data_summary(rows, max_rows=5)
    
    # Use Gemini for fast, natural response
    try:
        # Use gemini-1.5-flash as it is most stable for v1beta API
        model_name = "gemini-1.5-flash" 
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
        
        prompt = f"""You are a helpful data analyst. Explain these query results in 1-2 natural English sentences.
        
        User Question: "{question}"
        
        Data (top 5 rows):
        {data_summary}
        
        Rules:
        - Be concise and direct.
        - Mention key numbers/trends.
        - No technical jargon.
        - No "Here is the data" intros.
        """
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        
        print(f"[nl_response] Calling Gemini ({model_name})...")
        response = requests.post(url, json=payload, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            candidates = data.get("candidates", [])
            if candidates:
                nl_response = candidates[0].get("content", {}).get("parts", [])[0].get("text", "").strip()
                if chart_hint:
                     nl_response += f"\n\n(Visualized as {chart_hint.replace('_', ' ')})"
                return nl_response
        
        print(f"[nl_response] Gemini API failed: {response.status_code} - {response.text}")
        return fallback_response(rows, question)

    except Exception as e:
        print(f"[nl_response] Gemini CRASH: {e}")
        return fallback_response(rows, question)
    
    # Build the prompt
    page_context = {
        'live': 'real-time tweet stream',
        'history': 'historical tweet data',
        'metrics': 'analytics dashboard',
        'visualization': 'emotion map visualization'
    }.get(current_page, 'the platform')
    
    system_prompt = f"""You are a helpful data analyst assistant. Your job is to explain query results in clear, conversational English.

Context: User is currently viewing the {page_context}.

Guidelines:
- Answer in 1-3 sentences
- Be specific with numbers and values
- Use natural language, not technical jargon
- If there are multiple rows, summarize trends or patterns
- Don't mention SQL, tables, or technical details
- Focus on answering the user's question directly
- Tailor your response to the current page context"""

    user_prompt = f"""User asked: "{question}"

Query returned {len(rows)} result(s).

Sample data (first {min(len(rows), 5)} rows):
{data_summary}

Please provide a natural, conversational response in English that answers the user's question based on this data."""

    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json={
                "model": OLLAMA_MODEL_NL_RESPONSE,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "stream": False,
                "options": {
                    "temperature": OLLAMA_TEMP_SMALLTALK  # Use creative temperature for natural responses
                }
            },
            timeout=OLLAMA_TIMEOUT
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"[nl_response.py:79] Ollama response structure: {list(result.keys())}")
            # Ollama /api/chat returns: {"message": {"content": "..."}}
            nl_response = result.get("message", {}).get("content", "").strip()
            # Fallback if structure is different
            if not nl_response:
                nl_response = result.get("response", "").strip()
            
            print(f"[nl_response.py:85] Extracted response length: {len(nl_response) if nl_response else 0}")
            
            # Add chart hint if available (no emojis)
            if chart_hint and nl_response:
                nl_response += f"\n\nThis data would work well as a {chart_hint}."
            
            return nl_response if nl_response else fallback_response(rows, question)
        else:
            print(f"[nl_response.py:93] Ollama error: {response.status_code} - {response.text[:200]}")
            return fallback_response(rows, question)
    
    except Exception as e:
        print(f"[nl_response.py:97] Error generating response: {e}")
        return fallback_response(rows, question)


def prepare_data_summary(rows: List[Dict], max_rows: int = 5) -> str:
    """
    Prepare a readable summary of the data for the LLM
    
    Args:
        rows: Query results
        max_rows: Maximum number of rows to include
    
    Returns:
        Formatted string representation of the data
    """
    if not rows:
        return "No data"
    
    # Get column names
    columns = list(rows[0].keys())
    
    # Build a readable text representation
    summary_lines = []
    for i, row in enumerate(rows[:max_rows]):
        row_parts = []
        for col, val in row.items():
            # Format values nicely
            if isinstance(val, float):
                formatted_val = f"{val:.3f}"
            elif val is None:
                formatted_val = "null"
            else:
                formatted_val = str(val)
            
            row_parts.append(f"{col}: {formatted_val}")
        
        summary_lines.append(f"Row {i+1}: {', '.join(row_parts)}")
    
    if len(rows) > max_rows:
        summary_lines.append(f"... ({len(rows) - max_rows} more rows)")
    
    return "\n".join(summary_lines)


def fallback_response(rows: List[Dict], question: str) -> str:
    """
    Generate a simple fallback response if LLM fails
    """
    if not rows:
        return "I couldn't find any data matching that request."
        
    row_count = len(rows)
    first_row = rows[0]
    
    # Try to construct a natural sentence from the first row
    try:
        # Find numeric and text columns
        numeric_cols = [k for k, v in first_row.items() if isinstance(v, (int, float))]
        text_cols = [k for k, v in first_row.items() if isinstance(v, str) and k not in ['created_at', 'timestamp', 'date']]
        
        # If it's a comparison or list (multiple rows)
        if row_count > 1:
            if 'state_code' in first_row and numeric_cols:
                # Comparison: "California has 0.25 anger, Texas has 0.12 anger..."
                metric = numeric_cols[0]
                summary = []
                for r in rows[:3]:
                    state = r.get('state_name', r.get('state_code', 'Unknown'))
                    val = r.get(metric, 0)
                    summary.append(f"{state} ({val:.2f})")
                
                return f"Here is the data for {', '.join(summary)}. See the chart for the full comparison."
            
            return f"I found {row_count} records. The top result is {list(first_row.values())[0]}."

        # Single row result
        if row_count == 1:
            # "The average anger in California is 0.25"
            parts = []
            for k, v in first_row.items():
                if isinstance(v, float):
                    parts.append(f"{k} is {v:.3f}")
                else:
                    parts.append(f"{k}: {v}")
            return f"Here is the answer: {', '.join(parts)}."
            
    except Exception:
        pass
        
    # Ultimate fallback
    return "I've retrieved the data you asked for. Please check the table and chart below."


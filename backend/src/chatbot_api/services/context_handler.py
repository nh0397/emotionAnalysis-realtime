"""
Context Handler for Conversation Continuity
Detects contextual follow-ups and manages query context
"""

import re
from typing import List, Dict, Optional, Tuple


def detect_contextual_followup(question: str, previous_queries: List[Dict]) -> Optional[Dict]:
    """
    Detect if the current question is a follow-up to a previous data query.
    Works with both LangChain memory format and legacy conversation_history format.
    
    Returns:
        Dict with previous query context if detected, None otherwise
    """
    if not previous_queries:
        return None
    
    q_lower = question.lower().strip()
    
    # Patterns that indicate user wants to work with previous query results
    # More flexible patterns to catch various phrasings
    contextual_patterns = [
        r'(get|show|give|fetch|display|plot|visualize|chart|graph)\s+(me\s+)?(the\s+)?(complete|full|all|entire|detailed|raw|actual)\s+(data|results?|query|information)',
        r'(plot|chart|graph|visualize)\s+(it|this|that|the\s+data|on\s+a\s+chart)',
        r'(help\s+me\s+)?(plot|chart|graph|visualize)\s+(this|it|that|the\s+data|on\s+a\s+chart)',
        r'(show|get|give)\s+(me\s+)?(all|complete|full|the\s+data)',
        r'(let\'?s|let\s+us)\s+(plot|chart|visualize|see)',
        r'(can\s+you|please|help\s+me)\s+(show|get|give|plot|chart)\s+(me\s+)?(the\s+)?(complete|full|all|data|results?|this|it)',
        r'(what\s+about|how\s+about)\s+(the\s+)?(complete|full|all|data|results?)',
        r'(expand|extend|get\s+more|show\s+more)\s+(of\s+)?(the\s+)?(data|results?|query)',
        r'(remove|take\s+off|drop)\s+(the\s+)?(limit|restriction)',
        r'(previous|last|earlier|that)\s+(query|data|results?|question)',
        r'(plot|chart|visualize|graph)\s+(this|it|that)\s+(on\s+a\s+)?(chart|graph|plot)',
        r'(show|display)\s+(me\s+)?(a\s+)?(chart|graph|plot|visualization)\s+(for|of|this|it|that)',
    ]
    
    # Check if question matches contextual patterns
    for pattern in contextual_patterns:
        if re.search(pattern, q_lower):
            # Try LangChain memory format first (role-based chat history)
            for msg in reversed(previous_queries):
                # LangChain format: {role: 'user'/'assistant', content: str, metadata: {sql, chart_hint, ...}}
                if msg.get('role') == 'assistant' and msg.get('metadata'):
                    metadata = msg.get('metadata', {})
                    if metadata.get('sql') and metadata.get('rows') is not None:
                        print(f"[context_handler.py] Detected contextual follow-up (LangChain format): '{question}'")
                        return {
                            'previous_question': previous_queries[-2].get('content', '') if len(previous_queries) >= 2 else '',
                            'previous_sql': metadata.get('sql'),
                            'previous_rows': metadata.get('rows'),
                            'previous_chart_hint': metadata.get('chart_hint'),
                            'follow_up_type': _classify_followup_type(q_lower)
                        }
                
                # Legacy format: {intent: 'data_query', result: {sql, rows, ...}}
                if msg.get('intent') == 'data_query' and msg.get('result'):
                    result = msg.get('result', {})
                    if result.get('sql') and result.get('rows') is not None:
                        print(f"[context_handler.py] Detected contextual follow-up (legacy format): '{question}'")
                        return {
                            'previous_question': msg.get('question', ''),
                            'previous_sql': result.get('sql'),
                            'previous_rows': result.get('rows'),
                            'previous_chart_hint': result.get('chart_hint'),
                            'follow_up_type': _classify_followup_type(q_lower)
                        }
            
            # Also check last_query_context from AnalyticsMemory
            # This will be handled in run_analytics_pipeline if memory has last_query_context
    
    return None


def _classify_followup_type(question_lower: str) -> str:
    """Classify the type of follow-up request"""
    if any(word in question_lower for word in ['plot', 'chart', 'graph', 'visualize']):
        return 'visualize'
    elif any(word in question_lower for word in ['complete', 'full', 'all', 'entire', 'remove limit']):
        return 'expand_data'
    elif any(word in question_lower for word in ['more', 'details', 'detailed']):
        return 'more_details'
    else:
        return 'general_followup'


def inject_context_into_prompt(question: str, context: Optional[Dict]) -> str:
    """
    Enhance the user question with previous query context for NL2SQL.
    """
    if not context:
        return question
    
    previous_question = context.get('previous_question', '')
    previous_sql = context.get('previous_sql', '')
    
    # Build enhanced prompt
    enhanced = f"""Previous query: "{previous_question}"

Previous SQL (for reference):
{previous_sql}

Current request: "{question}"

Note: The user is asking about the SAME data from the previous query. 
"""
    
    # Add specific instructions based on follow-up type
    followup_type = context.get('follow_up_type', 'general_followup')
    if followup_type == 'expand_data':
        enhanced += "\nThe user wants to see MORE data (remove or increase LIMIT, show all results)."
    elif followup_type == 'visualize':
        enhanced += "\nThe user wants to visualize the previous query results."
    elif followup_type == 'more_details':
        enhanced += "\nThe user wants more detailed information from the previous query."
    
    enhanced += f"\n\nGenerate SQL for: {question}"
    
    return enhanced


def should_return_previous_results(question: str, context: Optional[Dict]) -> bool:
    """
    Determine if we should return previous results directly (without new SQL).
    """
    if not context:
        return False
    
    q_lower = question.lower().strip()
    
    # If user just wants to plot/visualize previous results, return them directly
    # More flexible patterns to catch various phrasings
    visualization_patterns = [
        r'plot\s+(it|this|that|the\s+data|on\s+a\s+chart)',
        r'visualize\s+(it|this|that|the\s+data|on\s+a\s+chart)',
        r'chart\s+(it|this|that|the\s+data)',
        r'graph\s+(it|this|that|the\s+data)',
        r'(help\s+me\s+)?(plot|chart|visualize|graph)\s+(this|it|that|the\s+data|on\s+a\s+chart)',
        r'show\s+(me\s+)?(a\s+)?(chart|graph|plot|visualization)\s*(for|of|this|it|that)?',
        r'let\'?s\s+(plot|chart|visualize|see)',
        r'(can\s+you|please)\s+(plot|chart|visualize|show\s+a\s+chart)\s+(this|it|that|for\s+me)?',
    ]
    
    for pattern in visualization_patterns:
        if re.match(pattern, q_lower):
            return True
    
    return False


def expand_previous_query(context: Dict) -> Optional[str]:
    """
    Modify previous SQL to expand results (remove/increase LIMIT).
    Returns modified SQL or None if not applicable.
    """
    if not context:
        return None
    
    previous_sql = context.get('previous_sql', '')
    if not previous_sql:
        return None
    
    # Remove LIMIT clause or increase it significantly
    sql_upper = previous_sql.upper()
    
    # If LIMIT exists, remove it or increase to 5000
    if 'LIMIT' in sql_upper:
        # Remove LIMIT clause
        # Match LIMIT with optional number
        pattern = r'\s+LIMIT\s+\d+(\s*;)?'
        modified_sql = re.sub(pattern, '', previous_sql, flags=re.IGNORECASE)
        # Add back semicolon if it was there
        if previous_sql.strip().endswith(';') and not modified_sql.strip().endswith(';'):
            modified_sql += ';'
        return modified_sql.strip()
    
    return None

"""
Natural Language Response Generator
Converts SQL query results into human-readable English responses using LLM
"""

import requests
from typing import List, Dict, Optional
from ..config import OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT, OLLAMA_TEMP_SMALLTALK


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
                "model": OLLAMA_MODEL,
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
            nl_response = result.get("message", {}).get("content", "").strip()
            
            # Add chart hint if available
            if chart_hint and nl_response:
                nl_response += f"\n\n💡 This data would work well as a {chart_hint}."
            
            return nl_response if nl_response else fallback_response(rows, question)
        else:
            print(f"[nl_response.py:88] Ollama error: {response.status_code}")
            return fallback_response(rows, question)
    
    except Exception as e:
        print(f"[nl_response.py:92] Error generating response: {e}")
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
    
    Args:
        rows: Query results
        question: Original question
    
    Returns:
        Simple summary string
    """
    row_count = len(rows)
    
    if row_count == 1:
        # Single result - show key-value pairs
        row = rows[0]
        parts = []
        for key, val in row.items():
            if isinstance(val, float):
                parts.append(f"{key}: {val:.3f}")
            else:
                parts.append(f"{key}: {val}")
        return f"Found one result: {', '.join(parts)}"
    
    else:
        # Multiple results - show count and first few
        return f"Found {row_count} results matching your query. Check the table below for details."


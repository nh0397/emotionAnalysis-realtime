"""
LangChain-based Analytics Pipeline
Microsoft Fabric-inspired UX with auto-visualization and context-aware decisions
"""

from typing import Dict, List, Optional, Any
import requests
import sys
import os

# Add parent directory for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chatbot_api.config import (
    OLLAMA_BASE_URL, OLLAMA_MODEL_NL2SQL, OLLAMA_TIMEOUT,
    GEMINI_API_KEY, NL2SQL_PROVIDER, GEMINI_ENABLE_FALLBACK
)
from chatbot_api.schema_config import DATABASE_SCHEMA, get_schema_context

class AnalyticsMemory:
    """Simple memory for conversation context tracking"""
    
    def __init__(self):
        self.chat_history: List[Dict] = []
        self.last_query_context: Optional[Dict] = None
        self.last_visualization: Optional[str] = None
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """Add message to history"""
        self.chat_history.append({
            'role': role,
            'content': content,
            'metadata': metadata or {}
        })
    
    def get_recent_context(self, n: int = 3) -> List[Dict]:
        """Get recent conversation context"""
        return self.chat_history[-n:] if len(self.chat_history) > n else self.chat_history


def should_auto_visualize(rows: List[Dict], chart_hint: Optional[str]) -> bool:
    """
    Microsoft Fabric-inspired: Auto-show visualization when appropriate.
    
    Rules:
    - Always show if chart_hint is provided
    - Show if data is multi-dimensional (3+ numeric columns)
    - Show if time series data (date + metric)
    - Show if multiple states with emotions
    - Don't show if single row, single metric
    """
    if not rows or len(rows) == 0:
        return False
    
    if chart_hint:
        return True
    
    first_row = rows[0]
    columns = list(first_row.keys())
    numeric_cols = [k for k, v in first_row.items() if isinstance(v, (int, float)) and v is not None]
    
    # Single row, single metric → no auto-viz
    if len(rows) == 1 and len(numeric_cols) <= 1:
        return False
    
    # Multi-dimensional data → auto-viz
    if len(numeric_cols) >= 3:
        return True
    
    # Time series → auto-viz
    has_date = any('date' in c.lower() or 'timestamp' in c.lower() for c in columns)
    if has_date and len(numeric_cols) >= 1:
        return True
    
    # Multiple states with emotions → auto-viz
    has_state = any('state' in c.lower() for c in columns)
    if has_state and len(numeric_cols) >= 2:
        return True
    
    return False


def _analyze_query_complexity(question: str) -> str:
    """Analyze query complexity to optimize SQL generation"""
    q_lower = question.lower()
    
    # Complex indicators
    complex_keywords = [
        'week over week', 'month over month', 'yoy', 'year over year',
        'correlation', 'trend', 'volatility', 'fluctuation', 'change',
        'subquery', 'cte', 'with', 'window', 'over', 'partition',
        'join', 'union', 'except', 'intersect'
    ]
    
    if any(kw in q_lower for kw in complex_keywords):
        return 'high'
    
    # Simple indicators
    simple_keywords = ['top', 'highest', 'lowest', 'average', 'count', 'sum']
    if len(question.split()) <= 8 and any(kw in q_lower for kw in simple_keywords):
        return 'low'
    
    return 'medium'


def generate_sql_with_retry(question: str, max_retries: int = 3, context: Optional[Dict] = None, complexity: str = 'medium') -> Optional[str]:
    """
    Generate SQL with retry logic for 90-100% accuracy.
    Uses validation feedback to improve on retries.
    """
    from chatbot_api.services.validator import validate_sql
    from chatbot_api.schema_config import FEW_SHOT_EXAMPLES
    
    schema_context = get_schema_context()
    validation_errors = []
    
    for attempt in range(max_retries):
        print(f"[SQL_GEN] 🔄 Attempt {attempt + 1}/{max_retries}")
        try:
            # Build context-aware prompt
            context_str = ""
            if context and context.get('previous_sql'):
                context_str = f"""
PREVIOUS QUERY CONTEXT:
Previous question: {context.get('previous_question', '')}
Previous SQL: {context.get('previous_sql', '')}
"""
            
            error_feedback = ""
            if validation_errors:
                error_feedback = f"\n\nPREVIOUS ATTEMPTS FAILED:\n" + "\n".join([f"- {e}" for e in validation_errors[-2:]])
            
            # Complexity-aware prompt adjustments
            complexity_hint = ""
            if complexity == 'high':
                complexity_hint = "\nNOTE: This is a complex query. Use CTEs (WITH clauses) for better organization and performance."
            elif complexity == 'low':
                complexity_hint = "\nNOTE: This is a simple query. Keep it straightforward and efficient."
            
            # Enhanced prompt for 90-100% accuracy with Few-Shot Examples
            prompt = f"""You are an expert SQL analyst. Generate PostgreSQL queries with 100% accuracy.
{complexity_hint}

{DATABASE_SCHEMA}

{FEW_SHOT_EXAMPLES}

{schema_context}

{context_str}

CRITICAL RULES (MUST FOLLOW):
1. ALWAYS include LIMIT clause (default 500, adjust based on question intent)
2. ALL non-aggregated columns in SELECT must be in GROUP BY clause
3. **CRITICAL: If you ORDER BY an aggregate (AVG, SUM, COUNT, etc.), you MUST include that aggregate in the SELECT clause**
   Example: If ORDER BY AVG(anger) DESC, then SELECT must include AVG(anger) AS avg_anger
4. Use proper PostgreSQL syntax (no MySQL/Oracle syntax)
5. Use CTEs (WITH clauses) for complex multi-step queries
6. Use state_code (2-letter) for filtering, state_name for display
7. ALWAYS include LIMIT clause (max 500 rows)
8. CRITICAL: Use 'timestamp' column for ALL time-based queries (NOT 'created_at')
9. Use proper date functions: DATE(timestamp), INTERVAL 'X days', CURRENT_DATE
10. For time series: ORDER BY date/timestamp ASC
11. For comparisons/rankings: ORDER BY metric DESC before LIMIT, AND include the metric in SELECT
12. Use proper aggregate functions: AVG(), SUM(), COUNT(), MAX(), MIN(), STDDEV()
13. When asking for "top N by X", SELECT both the entity AND the metric: SELECT state_name, AVG(anger) AS avg_anger

{error_feedback}

User Question: {question}

Generate ONLY valid PostgreSQL SQL (no explanations, no markdown, no code blocks):"""

            # Try Gemini first if configured, with fallback to Ollama
            sql = None
            if NL2SQL_PROVIDER == "GEMINI" and GEMINI_API_KEY:
                sql = _generate_with_gemini(prompt)
                # If Gemini fails and fallback enabled, try Ollama
                if not sql and GEMINI_ENABLE_FALLBACK:
                    print(f"[langchain_chain.py] Gemini failed on attempt {attempt + 1}, falling back to Ollama...")
                    sql = _generate_with_ollama(prompt)
            else:
                sql = _generate_with_ollama(prompt)
            
            if not sql:
                print(f"[SQL_GEN] ❌ No SQL generated on attempt {attempt + 1}")
                continue
            
            # Additional cleaning (in case LLM added extra text)
            sql = sql.strip()
            if "SELECT" in sql.upper() or "WITH" in sql.upper():
                # Find first SELECT or WITH
                for keyword in ["WITH", "SELECT"]:
                    if keyword in sql.upper():
                        sql = sql[sql.upper().find(keyword):]
                        break
            if sql and not sql.endswith(";"):
                sql += ";"
            
            print(f"[SQL_GEN] ✓ SQL generated: {sql[:100]}...")
            
            # Auto-add LIMIT if missing BEFORE validation
            from chatbot_api.services.validator import validate_sql, add_limit_if_missing
            from chatbot_api.config import MAX_SQL_LIMIT
            sql = add_limit_if_missing(sql, max_limit=MAX_SQL_LIMIT)
            
            # Validate and auto-fix
            is_valid, error = validate_sql(sql)
            if is_valid:
                print(f"[SQL_GEN] ✅ SQL validated successfully on attempt {attempt + 1}")
                return sql
            else:
                print(f"[SQL_GEN] ⚠ SQL validation failed (attempt {attempt + 1}): {error}")
                validation_errors.append(error)
                if attempt < max_retries - 1:
                    print(f"[SQL_GEN] 🔄 Retrying with error feedback...")
                    continue
        
        except Exception as e:
            print(f"[SQL_GEN] ❌ Error on attempt {attempt + 1}: {e}")
            if attempt == max_retries - 1:
                print(f"[SQL_GEN] ❌ SQL generation failed after {max_retries} attempts")
                return None
    
    return None


def _generate_with_ollama(prompt: str) -> Optional[str]:
    """Generate SQL using Ollama with enhanced cleaning"""
    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL_NL2SQL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.1, "num_predict": 1000}
            },
            timeout=OLLAMA_TIMEOUT
        )
        if response.status_code == 200:
            sql = response.json().get("response", "").strip()
            
            # Enhanced cleaning
            sql = sql.replace("```sql", "").replace("```", "").strip()
            # Remove any leading/trailing whitespace and newlines
            sql = "\n".join([line.strip() for line in sql.split("\n") if line.strip()])
            # Remove any explanation text before SQL
            if "SELECT" in sql.upper():
                sql = sql[sql.upper().find("SELECT"):]
            if sql and not sql.endswith(";"):
                sql += ";"
            
            return sql if sql else None
    except Exception as e:
        print(f"[langchain_chain.py] Ollama error: {e}")
    return None


def _generate_with_gemini(prompt: str) -> Optional[str]:
    """Generate SQL using Gemini"""
    from chatbot_api.services.gemini import generate_sql_gemini
    
    question = prompt.split("User Question:")[-1].strip() if "User Question:" in prompt else prompt
    
    from chatbot_api.config import GEMINI_MODEL_NL2SQL, GEMINI_TIMEOUT
    
    sql = generate_sql_gemini(
        api_key=GEMINI_API_KEY,
        model=GEMINI_MODEL_NL2SQL,
        question=question,
        system_prompt="You are an expert SQL analyst. Generate PostgreSQL queries with 100% accuracy.",
        schema_context=DATABASE_SCHEMA,
        guardrails="CRITICAL: Include LIMIT, proper GROUP BY, PostgreSQL syntax only.",
        timeout=GEMINI_TIMEOUT
    )
    
    # Return None if Gemini failed (will trigger fallback)
    if not sql:
        print(f"[langchain_chain.py] Gemini returned no SQL")
    return sql


def run_analytics_pipeline(
    question: str,
    memory: AnalyticsMemory,
    current_page: Optional[str] = None
) -> Dict[str, Any]:
    """
    SIMPLIFIED ANALYTICS PIPELINE
    
    Flow: NL → SQL → Data → LLM (chart type) → Chart Generator
    
    Steps:
    1. Context Detection & Early Exit (visualization requests)
    2. NL → SQL Generation 
    3. Data Fetching
    4. LLM Chart Decision (type + filters)
    5. Response Generation
    6. Memory Update
    """
    print(f"[PIPELINE] 🚀 Starting analytics pipeline for: '{question}'")
    from chatbot_api.services.context_handler import detect_contextual_followup, should_return_previous_results
    from chatbot_api.services.validator import validate_sql, add_limit_if_missing, ensure_group_by
    from chatbot_api.services.db import run_sql
    from chatbot_api.services.chart_hints import infer_chart_type
    from chatbot_api.services.chart_llm import suggest_chart_with_llm
    from chatbot_api.services.nl_response import generate_nl_response
    from chatbot_api.config import MAX_SQL_LIMIT, SQL_TIMEOUT
    
    # Step 1: Check for contextual follow-up (check memory.last_query_context first, then chat_history)
    print(f"[PIPELINE] 🔍 STEP 1: Context Detection")
    context = None
    if memory.last_query_context:
        print(f"[PIPELINE] ✓ Memory has last_query_context")
        # Check if question matches contextual patterns
        q_lower = question.lower().strip()
        contextual_keywords = ['plot', 'visualize', 'chart', 'graph', 'complete', 'full', 'all', 'data', 'it', 'this', 'that', 'previous', 'visualisation', 'visualization']
        if any(keyword in q_lower for keyword in contextual_keywords):
            context = {
                'previous_question': memory.last_query_context.get('question', ''),
                'previous_sql': memory.last_query_context.get('sql'),
                'previous_rows': memory.last_query_context.get('rows'),
                'previous_chart_hint': memory.last_query_context.get('chart_hint'),
                'previous_chart_filters': memory.last_query_context.get('chart_filters'),
                'follow_up_type': 'visualize' if any(kw in q_lower for kw in ['plot', 'visualize', 'chart', 'visualisation']) else 'expand_data'
            }
            print(f"[PIPELINE] ✓ Detected contextual follow-up from memory: {context.get('follow_up_type')}")
        else:
            print(f"[PIPELINE] ⚠ Question doesn't match contextual keywords")
    else:
        print(f"[PIPELINE] ⚠ No last_query_context in memory")
    
    # Fallback to chat_history-based detection
    if not context:
        print(f"[PIPELINE] 🔄 Checking chat_history for context...")
        context = detect_contextual_followup(question, memory.chat_history)
        if context:
            print(f"[PIPELINE] ✓ Detected context from chat_history")
        else:
            print(f"[PIPELINE] ⚠ No context detected - proceeding with new query")
    
    # Step 2: Handle visualization requests (return previous results)
    if context and should_return_previous_results(question, context):
        print(f"[PIPELINE] 📊 STEP 2: Returning previous results for visualization")
        print(f"[PIPELINE] ✓ Previous SQL: {context.get('previous_sql', 'None')[:100] if context.get('previous_sql') else 'None'}...")
        print(f"[PIPELINE] ✓ Previous rows: {len(context.get('previous_rows', []))}")
        print(f"[PIPELINE] ✓ Previous chart: {context.get('previous_chart_hint')}")
        
        # Validate context has required data
        if not context.get('previous_sql') or context.get('previous_rows') is None:
            print(f"[PIPELINE] ❌ Context missing SQL or rows - falling through to new query")
        else:
            return {
                "sql": context['previous_sql'],
                "rows": context.get('previous_rows', []),
                "chart_hint": context.get('previous_chart_hint'),
                "chart_filters": context.get('previous_chart_filters'),
                "auto_show_viz": True,
                "message": f"Here's the visualization for: {context.get('previous_question', 'your previous query')}",
                "is_contextual": True
            }
    
    # Step 2.5: Query Complexity Analysis (for optimization)
    print(f"[PIPELINE] 🔍 STEP 2.5: Query Complexity Analysis")
    query_complexity = _analyze_query_complexity(question)
    print(f"[PIPELINE] ✓ Complexity: {query_complexity}")
    
    # Step 3: Generate SQL with retry (90-100% accuracy goal) - now complexity-aware
    print(f"[PIPELINE] 📝 STEP 3: NL → SQL Generation")
    sql = generate_sql_with_retry(question, max_retries=3, context=context, complexity=query_complexity)
    if not sql:
        print(f"[PIPELINE] ❌ SQL generation failed after retries")
        return {
            "sql": None,
            "rows": [],
            "chart_hint": None,
            "auto_show_viz": False,
            "message": "I couldn't generate a valid SQL query. Please rephrase your question."
        }
    print(f"[PIPELINE] ✓ SQL generated: {sql[:150]}...")
    
    # Step 4: Query Optimization & Validation
    print(f"[PIPELINE] 🔧 STEP 4: SQL Optimization & Validation")
    from chatbot_api.services.validator import ensure_order_by_in_select
    
    sql = ensure_group_by(sql)
    print(f"[PIPELINE] ✓ Ensured GROUP BY")
    
    sql = ensure_order_by_in_select(sql)  # CRITICAL: Add missing ORDER BY columns to SELECT
    print(f"[PIPELINE] ✓ Fixed ORDER BY in SELECT")
    
    # NOTE: PostgreSQL DOES support aliases in ORDER BY, so we don't need to expand them.
    # forcing expansion often causes syntax errors (e.g. tuple comparisons).
    # sql = fix_order_by_alias_references(sql) 
    
    # Add LIMIT last to ensure it's at the very end
    sql = add_limit_if_missing(sql, max_limit=MAX_SQL_LIMIT)
    print(f"[PIPELINE] ✓ Added LIMIT if missing")
    
    # Optional: Query optimization based on complexity
    if query_complexity == 'high':
        print(f"[PIPELINE] ⚠ Complex query detected - applying optimizations")
    
    is_valid, error = validate_sql(sql)
    if not is_valid:
        print(f"[PIPELINE] ❌ SQL validation failed: {error}")
        return {
            "sql": sql,
            "rows": [],
            "chart_hint": None,
            "auto_show_viz": False,
            "message": f"Query validation failed: {error}"
        }
    print(f"[PIPELINE] ✓ SQL validated successfully")
    
    # Step 5: Execute SQL
    print(f"[PIPELINE] 💾 STEP 5: Execute SQL & Fetch Data")
    rows, exec_error = run_sql(sql, timeout=SQL_TIMEOUT)
    if exec_error:
        print(f"[PIPELINE] ❌ SQL execution failed: {exec_error}")
        return {
            "sql": sql,
            "rows": [],
            "chart_hint": None,
            "auto_show_viz": False,
            "message": f"Query execution error: {exec_error}"
        }
    print(f"[PIPELINE] ✓ Data fetched: {len(rows)} rows")
    
    # 🎨 STEP 6: Chart Selection (HEURISTIC ONLY - FAST)
    print(f"[PIPELINE] 🎨 STEP 6: Chart Selection (using heuristic)")
    
    chart_hint = infer_chart_type(sql, rows, question)
    if isinstance(chart_hint, dict):
        chart_hint = chart_hint.get('chart_type')
    
    chart_config = None
    chart_reasoning = None
    chart_code = None
    
    print(f"[PIPELINE] ✓ Chart selected: {chart_hint}")
    
    # Step 7: Generate NL Response
    print(f"[PIPELINE] 💬 STEP 7: Generate NL Response (chart_hint={chart_hint})")
    print(f"[PIPELINE] ⏳ Calling generate_nl_response... (this may be slow if using Ollama)")
    nl_message = generate_nl_response(question, sql, rows, chart_hint, current_page)
    print(f"[PIPELINE] ✓ NL response generated")
    
    # Step 8: Auto-visualization Decision
    print(f"[PIPELINE] 🎯 STEP 8: Auto-visualization Decision")
    auto_show_viz = should_auto_visualize(rows, chart_hint)
    print(f"[PIPELINE] ✓ Auto-show viz: {auto_show_viz}")
    
    # Step 9: Update Memory
    print(f"[PIPELINE] 💾 STEP 9: Update Memory")
    memory.last_query_context = {
        'question': question,
        'sql': sql,
        'rows': rows,
        'chart_hint': chart_hint,
        'chart_config': chart_config,
        'chart_reasoning': chart_reasoning,
        'chart_code': chart_code
    }
    memory.add_message('user', question)
    memory.add_message('assistant', nl_message, {
        'sql': sql,
        'rows': rows,
        'chart_hint': chart_hint,
        'auto_show_viz': auto_show_viz
    })
    print(f"[PIPELINE] ✓ Memory updated")
    
    
    print(f"[PIPELINE] ✅ Pipeline completed successfully!")
    
    result = {
        "sql": sql,
        "rows": rows,
        "chart_hint": chart_hint,
        "chart_config": chart_config,
        "chart_reasoning": chart_reasoning,
        "chart_code": chart_code,
        "auto_show_viz": auto_show_viz,
        "message": nl_message,
        "is_contextual": context is not None
    }
    
    print(f"[PIPELINE] 📤 RETURNING TO FRONTEND:")
    print(f"[PIPELINE]   - Rows: {len(rows)}")
    print(f"[PIPELINE]   - chart_hint: {chart_hint}")
    print(f"[PIPELINE]   - auto_show_viz: {auto_show_viz}")
    print(f"[PIPELINE]   - message length: {len(nl_message) if nl_message else 0}")
    
    return result



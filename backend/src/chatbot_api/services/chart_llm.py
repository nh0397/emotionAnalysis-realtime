"""
LLM-based Chart Type Selection
Uses LLM to intelligently suggest the best chart type based on query, data structure, and context
"""

import requests
import json
import re
from typing import List, Dict, Optional
from ..config import (
    OLLAMA_BASE_URL, OLLAMA_MODEL_CHART, OLLAMA_TIMEOUT, OLLAMA_TEMP_CHART,
    CHART_PROVIDER, GEMINI_API_KEY, GEMINI_MODEL_CHART, GEMINI_TIMEOUT, GEMINI_ENABLE_FALLBACK,
    CHART_GENERATION_MODE
)
from .gemini import generate_chart_gemini


def suggest_chart_with_llm(sql: str, rows: List[Dict], question: Optional[str] = None) -> Optional[Dict]:
    """
    Use LLM to suggest the best chart type, configuration, and generate React code.
    
    Returns:
        Dict with:
        - chart_type: str
        - chart_config: Dict (title, axes, colors, etc.)
        - reasoning: str (why this chart?)
        - chart_code: str (React component code)
    """
    if not rows or len(rows) == 0:
        return None
    
    # If single row, single metric → no chart needed (unless specifically asked)
    if len(rows) == 1 and len([k for k, v in rows[0].items() if isinstance(v, (int, float))]) <= 1:
        # Check if user explicitly asked for a chart
        if question and not any(kw in question.lower() for kw in ['chart', 'plot', 'graph', 'visualize']):
            return None
    
    columns = list(rows[0].keys()) if rows else []
    first_row = rows[0] if rows else {}
    
    # Analyze data structure
    numeric_cols = [k for k, v in first_row.items() if isinstance(v, (int, float)) and v is not None]
    has_date = any('date' in c.lower() or 'timestamp' in c.lower() for c in columns)
    has_state = any('state' in c.lower() for c in columns)
    
    # Data stats for LLM
    row_count = len(rows)
    unique_states = len(set(row.get('state_name', row.get('state_code', '')) for row in rows if 'state' in str(row))) if has_state else 0
    
    # Sample data (first 3 rows)
    sample_str = json.dumps(rows[:3], default=str)
    
    prompt = f"""You are an expert Data Visualization Engineer and React Developer.
Your task is to analyze the data and user question to design the PERFECT visualization.

USER QUESTION: {question or "Not provided"}

DATA STATISTICS:
- Row Count: {row_count}
- Columns: {', '.join(columns)}
- Numeric Columns: {', '.join(numeric_cols)}
- Has Date/Time: {has_date}
- Has State/Location: {has_state} ({unique_states} unique locations)

SAMPLE DATA:
{sample_str}

TASK:
1. Choose the best Recharts component (LineChart, BarChart, AreaChart, PieChart, RadarChart, ScatterChart, etc.).
2. Design the configuration (colors, axes, tooltips, legend).
3. Write the React code using 'recharts'.
4. Explain your reasoning.

GUIDELINES:
- For Time Series: Use AreaChart (beautiful gradients) or LineChart.
- For Comparisons: Use BarChart (vertical or horizontal).
- For Composition: Use PieChart or Stacked BarChart.
- For Multi-dimensional: Use RadarChart.
- For Large Datasets: Use ScatterChart or aggregated BarChart.
- THEME: Dark Mode (background #1a1a1a, text #e0e0e0). Use vibrant colors: ['#4ea1ff', '#ff6b6b', '#51cf66', '#ffd43b', '#845ef7'].

CRITICAL AXIS SELECTION RULES:
1. **NEVER use a column with CONSTANT values as the X-axis or Y-axis.**
   - Example: If 'state_name' is 'Texas' for ALL rows, do NOT use it as an axis.
   - Instead, use the categorical column that VARIES (e.g., 'emotion', 'category', 'date').
2. Identify which column is the "Category" (varies across rows) and which is the "Metric" (numeric).
   - X-Axis: Usually the Category (e.g., 'emotion').
   - Y-Axis: Usually the Metric (e.g., 'avg_score').
3. If multiple columns seem like categories, pick the one with the most unique values (but < 20).

WHEN NOT TO RECOMMEND CHARTS (BE SPECIFIC):
- If data has only 1 row: Say "Cannot create visualization - only 1 data point. Need at least 2 points for meaningful visualization."
- If data is purely textual (no numeric columns): Say "Cannot create visualization - data contains only text fields. Charts require numeric values to visualize."
- If question asks for raw data/list: Say "Visualization not recommended - user requested raw data/list format which is better displayed as a table."
- If data is too sparse/incomplete: Say "Visualization not recommended - data is too sparse with many null values. Table view is more appropriate."

RESPONSE FORMAT (JSON ONLY):
{{
  "chart_type": "area_chart" OR "none",
  "reasoning": "Since the user asked for a trend over time, an AreaChart is best to show the magnitude of change..." OR "Cannot create visualization - only 1 data point. Need at least 2 points for meaningful visualization.",
  "chart_config": {{
    "title": "Anger Trend over Time",
    "xAxis": "date",
    "yAxis": "anger_avg",
    "colors": ["#4ea1ff"]
  }} OR null,
  "code": "..." OR null // The complete React component code wrapping <ResponsiveContainer>
}}

CODE REQUIREMENTS:
- Return ONLY the JSX inside <ResponsiveContainer>...</ResponsiveContainer>.
- Do NOT include imports or 'export default'.
- Use 'data' prop which will be passed to your component.
- Example:
<ResponsiveContainer width="100%" height={{400}}>
  <AreaChart data={{data}}>
    <defs>
      <linearGradient id="colorVal" x1="0" y1="0" x2="0" y2="1">
        <stop offset="5%" stopColor="#4ea1ff" stopOpacity={{0.8}}/>
        <stop offset="95%" stopColor="#4ea1ff" stopOpacity={{0}}/>
      </linearGradient>
    </defs>
    <CartesianGrid strokeDasharray="3 3" stroke="#333" />
    <XAxis dataKey="date" stroke="#bbb" />
    <YAxis stroke="#bbb" />
    <Tooltip contentStyle={{{{backgroundColor: '#333', border: 'none'}}}} />
    <Area type="monotone" dataKey="value" stroke="#4ea1ff" fillOpacity={{1}} fill="url(#colorVal)" />
  </AreaChart>
</ResponsiveContainer>
"""

    # Try Gemini first if configured
    if CHART_PROVIDER == "GEMINI":
        result = generate_chart_gemini(
            api_key=GEMINI_API_KEY,
            model=GEMINI_MODEL_CHART,
            prompt=prompt,
            timeout=GEMINI_TIMEOUT,
            generate_code=False # We handle JSON parsing here
        )
        if result and isinstance(result, dict):
             # Ensure code is present
            if 'code' not in result:
                 # Fallback to simple generation if code missing
                 pass
            else:
                return result

    # Use Ollama
    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL_CHART,
                "prompt": prompt,
                "stream": False,
                "format": "json", # Force JSON mode
                "options": {
                    "temperature": 0.2,
                    "num_predict": 1500 # Need more tokens for code
                }
            },
            timeout=OLLAMA_TIMEOUT
        )
        
        if response.status_code == 200:
            result = response.json()
            raw_response = result.get("response", "").strip()
            
            try:
                # Parse JSON
                chart_data = json.loads(raw_response)
                
                # Validate fields
                if 'chart_type' in chart_data:
                    return {
                        'chart_type': chart_data.get('chart_type'),
                        'chart_config': chart_data.get('chart_config', {}),
                        'reasoning': chart_data.get('reasoning', 'AI suggested this chart.'),
                        'code': chart_data.get('code', '')
                    }
            except json.JSONDecodeError:
                print(f"[chart_llm.py] JSON parse failed: {raw_response[:100]}...")
                
    except Exception as e:
        print(f"[chart_llm.py] Error: {e}")

    return None


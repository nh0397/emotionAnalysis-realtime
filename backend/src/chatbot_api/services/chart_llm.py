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
from .ollama_service import generate_chart_ollama
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

RESPONSE FORMAT - CRITICAL:
You MUST respond with ONLY valid JSON. NO markdown, NO code blocks, NO backticks, NO explanation outside JSON.

CORRECT FORMAT (copy this structure EXACTLY):
{{"chart_type": "area_chart", "reasoning": "User asked for trend so area chart is best"}}

WRONG (do NOT do this):
```json
{{chart_type: area_chart}}
```

Valid chart_type values: line_chart, multi_line_chart, area_chart, bar_chart, grouped_bar_chart, stacked_bar_chart, horizontal_bar_chart, radar_chart, pie_chart, heatmap, none

Respond with ONLY the JSON object, nothing else:

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
        print(f"[chart_llm] Calling Gemini ({GEMINI_MODEL_CHART})...")
        result = generate_chart_gemini(
            api_key=GEMINI_API_KEY,
            model=GEMINI_MODEL_CHART,
            prompt=prompt,
            timeout=GEMINI_TIMEOUT,
            generate_code=False
        )
        if result:
            return result

    # Use Ollama via Service
    print(f"[chart_llm] Calling Ollama service (Model: {OLLAMA_MODEL_CHART})...")
    result = generate_chart_ollama(
        base_url=OLLAMA_BASE_URL,
        model=OLLAMA_MODEL_CHART,
        prompt=prompt,
        timeout=120
    )
    
    if result:
        print(f"[chart_llm] Received result: {result.keys()}")
        return {
            'chart_type': result.get('chart_type'),
            'chart_config': result.get('chart_config', {}),
            'reasoning': result.get('reasoning', f"Ollama suggested {result.get('chart_type')}"),
            'code': result.get('code', '')
        }
        
    print(f"[chart_llm] No valid result from Ollama")
    return None


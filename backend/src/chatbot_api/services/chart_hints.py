from typing import List, Dict, Optional

def infer_chart_type(sql: str, rows: List[Dict]) -> Optional[str]:
    """
    Infer the best chart type based on SQL pattern and result shape.
    Returns a chart type hint for the frontend.
    """
    if not rows or len(rows) == 0:
        return None
    
    sql_lower = sql.lower()
    columns = list(rows[0].keys()) if rows else []
    
    # Time series: has 'date' column + one or more metrics
    if 'date' in columns:
        metric_cols = [c for c in columns if c not in ['date', 'state_code', 'state_name']]
        if len(metric_cols) == 1:
            return "line_chart"
        elif len(metric_cols) > 1:
            return "multi_line_chart"
    
    # State comparison: has 'state_code' + metric
    if 'state_code' in columns:
        metric_cols = [c for c in columns if c not in ['state_code', 'state_name', 'date']]
        if 'date' in columns:
            return "multi_line_chart"  # Time series per state
        elif len(metric_cols) >= 1:
            return "bar_chart"  # State comparison
    
    # Sentiment split: has positive/negative/neutral columns
    sentiment_cols = {'positive', 'negative', 'neutral'}
    if sentiment_cols.issubset(set(columns)):
        return "stacked_bar_chart"
    
    # Emotion breakdown: multiple emotion columns
    emotion_cols = {'anger', 'fear', 'sadness', 'joy', 'surprise', 'anticipation', 'trust', 'disgust'}
    matching_emotions = emotion_cols.intersection(set(columns))
    if len(matching_emotions) >= 3:
        return "radar_chart"
    
    # Top N rankings
    if 'limit' in sql_lower and any(k in sql_lower for k in ['top', 'order by']):
        if len(rows) <= 10:
            return "horizontal_bar_chart"
    
    # Default: table view
    return "table"


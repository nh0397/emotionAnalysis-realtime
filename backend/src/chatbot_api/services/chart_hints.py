from typing import List, Dict, Optional, Tuple

def infer_chart_type(sql: str, rows: List[Dict]) -> Optional[str]:
    """
    Infer the best chart type based on SQL pattern and result shape.
    Returns a chart type hint for the frontend with metadata.
    
    Chart types:
    - radar_chart: Multi-dimensional data (3+ numeric dimensions per row)
    - heatmap: Two categorical dimensions + one numeric (e.g., states x emotions)
    - line_chart: Time series with single metric
    - multi_line_chart: Time series with multiple metrics
    - bar_chart: Single dimension comparison (states vs one metric)
    - grouped_bar_chart: States vs multiple metrics (2-4 metrics)
    - horizontal_bar_chart: Top N rankings
    - stacked_bar_chart: Sentiment breakdown
    """
    if not rows or len(rows) == 0:
        return None
    
    sql_lower = sql.lower()
    columns = list(rows[0].keys()) if rows else []
    first = rows[0]
    
    # Identify column types
    numeric_cols = [k for k, v in first.items() if isinstance(v, (int, float)) and v is not None]
    categorical_cols = [k for k in columns if k not in numeric_cols]
    
    # Key identifiers
    has_date = any('date' in c.lower() or 'timestamp' in c.lower() for c in columns)
    has_state = any('state' in c.lower() for c in columns)
    emotion_cols = {'anger', 'fear', 'sadness', 'joy', 'surprise', 'anticipation', 'trust', 'disgust'}
    matching_emotions = emotion_cols.intersection({c.lower() for c in columns})
    
    # If it's a single-row, single-metric response → no viz (text/table only)
    if len(rows) == 1 and len(numeric_cols) <= 1:
        return None

    # Time series detection
    if has_date:
        metric_cols = [c for c in numeric_cols if c not in ['state_code', 'state_name']]
        if len(metric_cols) == 1:
            return "line_chart"
        elif len(metric_cols) > 1:
            return "multi_line_chart"
    
    # Multi-dimensional emotion data (the user's case)
    # Multiple emotion columns + categorical dimension (state_name)
    if len(matching_emotions) >= 3 and has_state and len(rows) > 1:
        # If we have many states and many emotions, use heatmap
        if len(rows) >= 5 and len(matching_emotions) >= 5:
            return "heatmap"
        # Otherwise radar chart (one per state or grouped)
        return "radar_chart"
    
    # Multi-dimensional data in general (3+ numeric cols per row)
    if len(numeric_cols) >= 3 and has_state and len(rows) > 1:
        # Check if it's a comparison scenario (states vs metrics)
        if len(rows) <= 15:  # Reasonable number for grouped bars
            if len(numeric_cols) <= 4:
                return "grouped_bar_chart"
            else:
                # Too many metrics for grouped bars, use heatmap
                return "heatmap"
        else:
            # Too many rows, heatmap is better
            return "heatmap"
    
    # Single metric comparison (states vs one metric)
    if has_state and len(numeric_cols) == 1:
        if len(rows) <= 10:
            return "horizontal_bar_chart"
        else:
            return "bar_chart"
    
    # Two metrics comparison
    if has_state and len(numeric_cols) == 2:
        return "grouped_bar_chart"
    
    # Sentiment breakdown
    sentiment_cols = {'positive', 'negative', 'neutral'}
    if sentiment_cols.issubset({c.lower() for c in columns}):
        return "stacked_bar_chart"
    
    # Top N rankings (single metric, no grouping)
    if 'limit' in sql_lower and any(k in sql_lower for k in ['top', 'order by']):
        if len(rows) <= 10 and len(numeric_cols) == 1:
            return "horizontal_bar_chart"
    
    # Default: table view only
    return None


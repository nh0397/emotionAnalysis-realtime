import requests
import json
from typing import Optional
from chatbot_api.config import (
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    OLLAMA_TIMEOUT,
    OLLAMA_TEMP_SQL_GENERATION
)

def load_system_prompt() -> str:
    """Load system prompt with schema and few-shot examples"""
    return """You are a SQL expert. Convert English questions to a single PostgreSQL SELECT query.

STRICT RULES:
- Only SELECT statements allowed (no INSERT/UPDATE/DELETE/DROP)
- Always add LIMIT 500
- Only use table: tweets
- Use DATE(timestamp) for daily aggregations
- Return ONLY the SQL query, no explanation

SCHEMA:
tweets(
  id, tweet_id, username, raw_text, timestamp,
  state_code, state_name, context,
  likes, retweets, replies, views,
  sentiment (positive/negative/neutral),
  sentiment_confidence,
  anger, fear, sadness, surprise, joy, anticipation, trust, disgust (all FLOAT 0-1),
  dominant_emotion, emotion_confidence, compound
)

FEW-SHOT EXAMPLES:

Q: Show daily average anger in CA for last 30 days
SQL: SELECT DATE(timestamp) AS date, AVG(anger) AS anger
FROM tweets
WHERE state_code='CA' AND timestamp >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(timestamp)
ORDER BY date
LIMIT 500;

Q: Which state has the highest joy this week?
SQL: SELECT state_code, AVG(joy) AS avg_joy
FROM tweets
WHERE timestamp >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY state_code
ORDER BY avg_joy DESC
LIMIT 1;

Q: Sentiment split in TX last week
SQL: SELECT DATE(timestamp) AS date,
       SUM(CASE WHEN sentiment='positive' THEN 1 ELSE 0 END) AS positive,
       SUM(CASE WHEN sentiment='negative' THEN 1 ELSE 0 END) AS negative,
       SUM(CASE WHEN sentiment='neutral' THEN 1 ELSE 0 END) AS neutral
FROM tweets
WHERE state_code='TX' AND timestamp >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY DATE(timestamp)
ORDER BY date
LIMIT 500;

Q: Top 5 states by fear this month
SQL: SELECT state_code, state_name, AVG(fear) AS avg_fear
FROM tweets
WHERE timestamp >= DATE_TRUNC('month', CURRENT_DATE)
GROUP BY state_code, state_name
ORDER BY avg_fear DESC
LIMIT 5;

Q: Compare anger between CA and TX last 14 days
SQL: SELECT state_code, DATE(timestamp) AS date, AVG(anger) AS avg_anger
FROM tweets
WHERE state_code IN ('CA', 'TX')
  AND timestamp >= CURRENT_DATE - INTERVAL '14 days'
GROUP BY state_code, DATE(timestamp)
ORDER BY state_code, date
LIMIT 500;

Now convert this question to SQL:
"""

def generate_sql(question: str, model: str = None) -> Optional[str]:
    """Generate SQL from natural language using Ollama"""
    if model is None:
        model = OLLAMA_MODEL
    
    try:
        system_prompt = load_system_prompt()
        full_prompt = f"{system_prompt}\nQ: {question}\nSQL:"
        
        payload = {
            "model": model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": OLLAMA_TEMP_SQL_GENERATION,
                "top_p": 0.9,
                "stop": [";", "\n\n"]
            }
        }
        
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=payload,
            timeout=OLLAMA_TIMEOUT
        )
        
        if response.status_code != 200:
            print(f"[nl2sql.py:109] Ollama error: {response.status_code} - {response.text}")
            return None
        
        result = response.json()
        sql = result.get("response", "").strip()
        
        # Clean up the SQL
        sql = sql.replace("```sql", "").replace("```", "").strip()
        
        # Ensure it ends with semicolon
        if sql and not sql.endswith(";"):
            sql += ";"
        
        return sql if sql else None
        
    except requests.exceptions.RequestException as e:
        print(f"[nl2sql.py:125] Ollama connection error: {e}")
        return None
    except Exception as e:
        print(f"[nl2sql.py:128] NL→SQL generation error: {e}")
        return None

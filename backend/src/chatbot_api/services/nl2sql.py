import requests
import json
from typing import Optional
from chatbot_api.config import (
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    OLLAMA_MODEL_NL2SQL,
    OLLAMA_TIMEOUT,
    OLLAMA_TEMP_SQL_GENERATION,
    NL2SQL_PROVIDER,
    GEMINI_API_KEY,
    GEMINI_MODEL_NL2SQL,
    GEMINI_TIMEOUT,
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

Now convert this question to SQL:
"""

# Import schema from config
from ..schema_config import get_schema_context
from .gemini import generate_sql_gemini

def generate_sql(question: str, model: str = None) -> Optional[str]:
    """Generate SQL from natural language using Ollama with schema context"""
    if model is None:
        model = OLLAMA_MODEL_NL2SQL if 'OLLAMA_MODEL_NL2SQL' in globals() else OLLAMA_MODEL
    
    try:
        system_prompt = load_system_prompt()
        schema_context = get_schema_context()
        guardrails = (
            "Return ONE Postgres SQL only. No prose. "
            "Balance parentheses. Prefer CTEs for thresholds. "
            "Do not use emotion_aggregates inside HAVING against tweet-level groups; "
            "if you need a threshold, compute it from tweets in a CTE named threshold."
        )
        full_prompt = f"{system_prompt}\n{schema_context}\nRULES: {guardrails}\nQ: {question}\nSQL:"
        
        # Debug selection
        try:
            print(f"[nl2sql] provider={NL2SQL_PROVIDER} model={model}")
        except Exception:
            pass

        if NL2SQL_PROVIDER == "GEMINI":
            sql = generate_sql_gemini(
                api_key=GEMINI_API_KEY,
                model=GEMINI_MODEL_NL2SQL,
                question=question,
                system_prompt=system_prompt,
                schema_context=schema_context,
                guardrails=guardrails,
                timeout=GEMINI_TIMEOUT,
            )
            if not sql:
                print("[nl2sql] Gemini returned no SQL; falling back to Ollama")
                NL2SQL_provider_fallback = True
            else:
                NL2SQL_provider_fallback = False
        else:
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

        # If Gemini path failed, optionally try Ollama fallback
        if NL2SQL_PROVIDER == "GEMINI" and (not sql):
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
                print(f"[nl2sql.py:fallback] Ollama error: {response.status_code} - {response.text}")
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

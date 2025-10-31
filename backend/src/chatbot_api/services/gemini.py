import requests
from typing import Optional


def generate_sql_gemini(
    *,
    api_key: str,
    model: str,
    question: str,
    system_prompt: str,
    schema_context: str,
    guardrails: str,
    timeout: int = 60,
) -> Optional[str]:
    """Call Gemini to generate a single PostgreSQL SQL statement.

    Returns SQL string or None on failure.
    """
    if not api_key:
        return None

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    prompt = f"{system_prompt}\n{schema_context}\nRULES: {guardrails}\nQ: {question}\nSQL:"

    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ]
    }

    try:
        resp = requests.post(url, json=payload, timeout=timeout)
        if resp.status_code != 200:
            print(f"[gemini] HTTP {resp.status_code}: {resp.text[:200]}")
            return None
        data = resp.json()
        # Extract text
        candidates = data.get("candidates", [])
        if not candidates:
            return None
        parts = candidates[0].get("content", {}).get("parts", [])
        text = "".join(p.get("text", "") for p in parts)
        sql = text.replace("```sql", "").replace("```", "").strip()
        if sql and not sql.endswith(";"):
            sql += ";"
        return sql or None
    except requests.exceptions.RequestException as e:
        print(f"[gemini] request error: {e}")
        return None
    except Exception as e:
        print(f"[gemini] parse error: {e}")
        return None



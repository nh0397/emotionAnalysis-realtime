import requests
import json
import re
from typing import Optional, Dict


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
            if resp.status_code == 429:
                print("[gemini] rate limited (429)")
                return None
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


def generate_chart_gemini(
    *,
    api_key: str,
    model: str,
    prompt: str,
    timeout: int = 60,
    generate_code: bool = False,
) -> Optional[Dict]:
    """Call Gemini to generate chart type suggestion or code.
    
    Args:
        generate_code: If True, returns JSX code; if False, returns JSON with chart_type
    Returns dict with chart_type/suggest_filters/filter_types OR chart_code/generation_mode, or None on failure.
    """
    if not api_key:
        return None
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    
    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 8192  # Max for Flash
        }
    }
    
    try:
        resp = requests.post(url, json=payload, timeout=timeout)
        if resp.status_code != 200:
            if resp.status_code == 429:
                print("[gemini] rate limited (429)")
                return None
            print(f"[gemini] HTTP {resp.status_code}: {resp.text[:200]}")
            return None
        
        data = resp.json()
        candidates = data.get("candidates", [])
        if not candidates:
            print(f"[gemini] No candidates returned: {data}")
            return None
        
        parts = candidates[0].get("content", {}).get("parts", [])
        raw_response = "".join(p.get("text", "") for p in parts).strip()
        
        # Code generation mode: return code directly
        if generate_code:
            cleaned = raw_response.replace("```jsx", "").replace("```js", "").replace("```", "").strip()
            print(f"[gemini] ✅ Code generation mode: returning JSX code")
            return {
                'chart_code': cleaned,
                'generation_mode': 'code'
            }
        
        # JSON mode: Parse JSON response
        try:
            cleaned = raw_response.replace("```json", "").replace("```", "").strip()
            # Find first { and last }
            start_idx = cleaned.find('{')
            end_idx = cleaned.rfind('}')
            
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                json_str = cleaned[start_idx:end_idx+1]
                chart_data = json.loads(json_str)
                
                chart_type = chart_data.get('chart_type', '').lower()
                suggest_filters = chart_data.get('suggest_filters', False)
                filter_types = chart_data.get('filter_types', [])
                
                valid_types = ['line_chart', 'multi_line_chart', 'radar_chart', 'heatmap', 
                              'grouped_bar_chart', 'bar_chart', 'horizontal_bar_chart', 'stacked_bar_chart', 'none']
                
                if chart_type in valid_types:
                    if chart_type == 'none':
                        print(f"[gemini] Determined no chart needed")
                        return None
                    
                    print(f"[gemini] ✅ Chart parsed: chart_type={chart_type}, filters={filter_types}")
                    return {
                        'chart_type': chart_type,
                        'suggest_filters': suggest_filters,
                        'filter_types': filter_types if suggest_filters else []
                    }
        except (json.JSONDecodeError, AttributeError) as e:
            print(f"[gemini] JSON parse failed: {e}")
        
        # Fallback text extraction
        chart_type = raw_response.lower()
        chart_type = chart_type.replace('"', '').replace("'", '').replace('\n', ' ').strip()
        
        valid_types = ['line_chart', 'multi_line_chart', 'radar_chart', 'heatmap', 
                      'grouped_bar_chart', 'bar_chart', 'horizontal_bar_chart', 'stacked_bar_chart']
        
        for valid_type in valid_types:
            if valid_type in chart_type:
                print(f"[gemini] ✅ Chart substring match: {valid_type}")
                return valid_type
        
        print(f"[gemini] ❌ Could not parse chart response: '{chart_type[:100]}'")
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"[gemini] request error: {e}")
        return None
    except Exception as e:
        print(f"[gemini] parse error: {e}")
        return None



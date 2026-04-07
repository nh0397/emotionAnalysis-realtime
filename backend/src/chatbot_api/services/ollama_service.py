
import requests
import json
import re
from typing import Optional, Dict

def generate_sql_ollama(
    *,
    base_url: str,
    model: str,
    question: str,
    system_prompt: str,
    schema_context: str,
    guardrails: str,
    timeout: int = 120,
) -> Optional[str]:
    """Call Ollama to generate a single PostgreSQL SQL statement."""
    print(f"[OLLAMA] Generating SQL with model: {model}")
    print(f"[OLLAMA] Question: {question}")
    
    full_prompt = f"{system_prompt}\n\nSchema:\n{schema_context}\n\nStrict Rules:\n{guardrails}\n\nQuestion: {question}\n\nSQL Query:"
    
    url = f"{base_url}/api/generate"
    payload = {
        "model": model,
        "prompt": full_prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,  # Low temperature for precise SQL
            "num_predict": 1024
        }
    }
    
    try:
        print(f"[OLLAMA] Sending request to {url}...")
        resp = requests.post(url, json=payload, timeout=timeout)
        
        if resp.status_code != 200:
            print(f"[OLLAMA] Error {resp.status_code}: {resp.text[:200]}")
            return None
            
        result = resp.json()
        raw_text = result.get("response", "").strip()
        print(f"[OLLAMA] Raw output length: {len(raw_text)}")
        
        # Clean SQL
        sql = raw_text.replace("```sql", "").replace("```", "").strip()
        # Remove any leading conversational text (common in smaller models)
        if "select" in sql.lower():
            # Find the first SELECT
            idx = sql.lower().find("select")
            sql = sql[idx:]
        
        if sql and not sql.endswith(";"):
            sql += ";"
            
        print(f"[OLLAMA] Generated SQL: {sql}")
        return sql
        
    except Exception as e:
        print(f"[OLLAMA] Exception in generate_sql_ollama: {e}")
        return None


def generate_chart_ollama(
    *,
    base_url: str,
    model: str,
    prompt: str,
    timeout: int = 120,
    generate_code: bool = False,
) -> Optional[Dict]:
    """Call Ollama to generate chart hints."""
    print(f"[OLLAMA] Generating Chart Hint with model: {model}")
    print(f"[OLLAMA] Generate Code: {generate_code}")
    
    url = f"{base_url}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_predict": 2048
        }
    }
    
    try:
        print(f"[OLLAMA] Sending request to {url}...")
        resp = requests.post(url, json=payload, timeout=timeout)
        
        if resp.status_code != 200:
            print(f"[OLLAMA] Error {resp.status_code}: {resp.text[:200]}")
            return None
            
        result = resp.json()
        raw_response = result.get("response", "").strip()
        print(f"[OLLAMA] Raw output length: {len(raw_response)}")
        
        if generate_code:
            # Code mode
            cleaned = raw_response.replace("```jsx", "").replace("```js", "").replace("```", "").strip()
            print(f"[OLLAMA] Returning chart code (Snippet: {cleaned[:50]}...)")
            return {
                'chart_code': cleaned,
                'generation_mode': 'code'
            }
        
        # JSON mode
        # Extract JSON-like structures
        json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group(0))
                if 'chart_type' in data:
                    print(f"[OLLAMA] Parsed JSON chart type: {data['chart_type']}")
                    return data
            except:
                pass
        
        # Fallback Regex extraction
        valid_types = ['line_chart', 'multi_line_chart', 'radar_chart', 'heatmap', 
                      'grouped_bar_chart', 'bar_chart', 'horizontal_bar_chart', 
                      'stacked_bar_chart', 'area_chart', 'pie_chart', 'none']
                      
        for vt in valid_types:
            if vt in raw_response.lower():
                print(f"[OLLAMA] Found chart type via substring: {vt}")
                return {'chart_type': vt, 'suggest_filters': False, 'filter_types': []}
                
        print(f"[OLLAMA] No valid chart type found.")
        return None
        
    except Exception as e:
        print(f"[OLLAMA] Exception in generate_chart_ollama: {e}")
        return None

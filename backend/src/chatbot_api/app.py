from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chatbot_api.services.nl2sql import generate_sql
from chatbot_api.services.validator import validate_sql, add_limit_if_missing
from chatbot_api.services.db import run_sql, check_explain_cost
from chatbot_api.services.chart_hints import infer_chart_type

app = FastAPI(title="TecVis 2.0 Chatbot API")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Question(BaseModel):
    question: str

class VisionQuestion(BaseModel):
    question: str
    screenshot: Optional[str] = None

@app.get("/health")
def health():
    """Health check endpoint"""
    return {"status": "ok", "service": "TecVis 2.0 Chatbot API"}

@app.post("/chat")
def chat(q: Question):
    """
    NL→SQL pipeline: question → SQL → validate → execute → results + chart hint
    """
    if not q.question or not q.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    # Step 1: Generate SQL from natural language
    sql = generate_sql(q.question)
    if not sql:
        return {
            "sql": None,
            "rows": [],
            "chart_hint": None,
            "message": "I couldn't generate a valid SQL query. Try rephrasing your question."
        }
    
    # Step 2: Ensure LIMIT is present
    sql = add_limit_if_missing(sql, max_limit=500)
    
    # Step 3: Validate SQL for safety
    is_valid, error = validate_sql(sql)
    if not is_valid:
        return {
            "sql": sql,
            "rows": [],
            "chart_hint": None,
            "message": f"Query validation failed: {error}"
        }
    
    # Step 4: Check query cost with EXPLAIN
    is_safe, cost_error = check_explain_cost(sql, max_cost=10000.0)
    if not is_safe:
        return {
            "sql": sql,
            "rows": [],
            "chart_hint": None,
            "message": f"Query rejected: {cost_error}. Try adding more filters or reducing the date range."
        }
    
    # Step 5: Execute SQL
    rows, exec_error = run_sql(sql, timeout=10)
    if exec_error:
        return {
            "sql": sql,
            "rows": [],
            "chart_hint": None,
            "message": f"Execution error: {exec_error}"
        }
    
    # Step 6: Infer chart type
    chart_hint = infer_chart_type(sql, rows)
    
    # Step 7: Return results
    return {
        "sql": sql,
        "rows": rows,
        "chart_hint": chart_hint,
        "message": f"Found {len(rows)} result(s)" if rows else "No results found"
    }

@app.post("/chat/vision")
def chat_vision(q: VisionQuestion):
    """
    Vision-based chat: screenshot + question → LLM (LLaVA or GPT-4V) → answer
    (Placeholder for now - will implement vision model integration later)
    """
    if not q.question or not q.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    # TODO: Implement vision model (LLaVA via Ollama or GPT-4V)
    # For now, return a placeholder
    return {
        "sql": None,
        "rows": [],
        "chart_hint": None,
        "message": "Vision-based chat coming soon! For now, try asking data questions without screenshots."
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9001, log_level="info")

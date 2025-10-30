from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Question(BaseModel):
    question: str

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/chat")
def chat(q: Question):
    return {
        "sql": None,
        "rows": [],
        "chart_hint": None,
        "message": "NL→SQL not wired yet"
    }

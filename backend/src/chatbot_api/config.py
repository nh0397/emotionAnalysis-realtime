"""
Centralized configuration for TecVis 2.0 Chatbot API
"""

import os
from pathlib import Path
try:
    # Load .env from project root automatically
    from dotenv import load_dotenv  # type: ignore
    _root_env = Path(__file__).resolve().parents[3] / ".env"
    load_dotenv(dotenv_path=str(_root_env), override=False)
except Exception:
    pass

# Ollama Configuration
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_TIMEOUT = None  # No timeout for local development

# Task-specific LLM Models (each node can use different models)
OLLAMA_MODEL_INTENT = os.getenv("OLLAMA_MODEL_INTENT", "llama3.2:3b")  # Intent classification (fast, small)
OLLAMA_MODEL_NL2SQL = os.getenv("OLLAMA_MODEL_NL2SQL", "sqlcoder:7b")  # NL→SQL generation (accurate)
OLLAMA_MODEL_CHART = os.getenv("OLLAMA_MODEL_CHART", "gpt-oss:20b")  # Chart selection (understanding) - supports gpt-oss:20b, mistral:7b, etc.
OLLAMA_MODEL_NL_RESPONSE = os.getenv("OLLAMA_MODEL_NL_RESPONSE", "llama3.2:3b")  # Natural language response (conversational)
OLLAMA_MODEL = OLLAMA_MODEL_INTENT  # Default fallback

# Temperature settings for different tasks
OLLAMA_TEMP_CLASSIFICATION = 0.1  # Low for consistency in intent classification
OLLAMA_TEMP_SQL_GENERATION = 0.1  # Low for accurate SQL
OLLAMA_TEMP_CHART = 0.2  # Moderate for chart selection
OLLAMA_TEMP_SMALLTALK = 0.7      # Higher for natural conversation

# NL→SQL Provider ("OLLAMA" or "GEMINI")
NL2SQL_PROVIDER = os.getenv("NL2SQL_PROVIDER", "OLLAMA").upper()

# Chart Selection Provider ("OLLAMA" or "GEMINI")
CHART_PROVIDER = os.getenv("CHART_PROVIDER", "OLLAMA").upper()

# Chart Generation Mode ("json" or "code")
# - "json": Returns chart_type, suggest_filters, filter_types (default, safe)
# - "code": Returns full React/Recharts component code (experimental, can be reverted)
CHART_GENERATION_MODE = os.getenv("CHART_GENERATION_MODE", "json").lower()  # Default to JSON for backward compatibility

# Gemini configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL_NL2SQL = os.getenv("GEMINI_MODEL_NL2SQL", "gemini-2.5-flash")  # Try latest version
GEMINI_MODEL_CHART = os.getenv("GEMINI_MODEL_CHART", "gemini-2.5-flash")  # Chart selection
GEMINI_TIMEOUT = 60  # seconds
GEMINI_ENABLE_FALLBACK = os.getenv("GEMINI_ENABLE_FALLBACK", "true").lower() == "true"  # Fallback to Ollama on failure

# Database Configuration
DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "tweetdb"
DB_USER = "tweetuser"
DB_PASSWORD = "tweetpass"

# Query Limits
MAX_SQL_LIMIT = 500
SQL_TIMEOUT = None  # No timeout for local development
MAX_QUERY_COST = None  # No cost limit for local development

# Conversation Settings
MAX_CONVERSATION_HISTORY = 10  # Keep last N queries per session


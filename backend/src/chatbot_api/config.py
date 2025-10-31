"""
Centralized configuration for TecViz Chatbot API
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
OLLAMA_MODEL = "llama3.2:3b"  # Default for smalltalk/classification
OLLAMA_MODEL_NL2SQL = "sqlcoder:7b"  # Dedicated model for NL→SQL
OLLAMA_TIMEOUT = None  # No timeout for local development

# Temperature settings for different tasks
OLLAMA_TEMP_CLASSIFICATION = 0.1  # Low for consistency in intent classification
OLLAMA_TEMP_SQL_GENERATION = 0.1  # Low for accurate SQL
OLLAMA_TEMP_SMALLTALK = 0.7      # Higher for natural conversation

# NL→SQL Provider ("OLLAMA" or "GEMINI")
NL2SQL_PROVIDER = os.getenv("NL2SQL_PROVIDER", "OLLAMA").upper()

# Gemini configuration (used when NL2SQL_PROVIDER == "GEMINI")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL_NL2SQL = os.getenv("GEMINI_MODEL_NL2SQL", "gemini-1.5-flash")
GEMINI_TIMEOUT = 60  # seconds

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


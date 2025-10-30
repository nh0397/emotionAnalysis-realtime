"""
Centralized configuration for TecViz Chatbot API
"""

# Ollama Configuration
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2:3b"  # Change model here for all services
OLLAMA_TIMEOUT = None  # No timeout for local development

# Temperature settings for different tasks
OLLAMA_TEMP_CLASSIFICATION = 0.1  # Low for consistency in intent classification
OLLAMA_TEMP_SQL_GENERATION = 0.1  # Low for accurate SQL
OLLAMA_TEMP_SMALLTALK = 0.7      # Higher for natural conversation

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


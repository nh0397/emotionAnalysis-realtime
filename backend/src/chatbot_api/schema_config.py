"""
Database Schema Configuration for NL→SQL Generation
Update this file when your database schema changes
"""

# Database schema description for LLM context
DATABASE_SCHEMA = """
DATABASE SCHEMA:
Table: tweets
- tweet_id (text): Unique identifier for each tweet
- username (text): Twitter username of the author
- raw_text (text): Original tweet content/message
- timestamp (timestamp): When the tweet was originally posted
- state_code (text): US state abbreviation (CA, TX, NY, FL, etc.)
- state_name (text): Full US state name (California, Texas, New York, etc.)
- context (text): Topic/keyword context or category
- likes (integer): Number of likes/hearts on the tweet
- retweets (integer): Number of retweets/shares
- replies (integer): Number of replies to the tweet
- views (integer): Number of times the tweet was viewed
- created_at (timestamp): When this record was inserted into our database

EMOTION ANALYSIS COLUMNS (all float values between 0.0 and 1.0):
- anger: Intensity of anger emotion (0.0 = no anger, 1.0 = maximum anger)
- joy: Intensity of joy/happiness emotion
- fear: Intensity of fear/anxiety emotion  
- sadness: Intensity of sadness/depression emotion
- surprise: Intensity of surprise/shock emotion
- anticipation: Intensity of anticipation/expectation emotion
- trust: Intensity of trust/confidence emotion
- disgust: Intensity of disgust/revulsion emotion

SENTIMENT ANALYSIS COLUMN:
- sentiment (text): Overall sentiment classification
  Values: 'positive', 'negative', 'neutral'

QUERY PATTERNS & EXAMPLES:
- Filter by state: WHERE state_code = 'CA' OR WHERE state_name = 'California'
- Emotion averages: SELECT AVG(anger), AVG(joy) FROM tweets
- Top emotions: ORDER BY emotion_name DESC LIMIT 10
- Time filtering: WHERE timestamp >= '2025-01-01' AND timestamp < '2025-02-01'
- Sentiment filtering: WHERE sentiment = 'positive'
- State grouping: GROUP BY state_code, state_name
- Always include LIMIT clause for large result sets (recommended: LIMIT 500)

COMMON QUERY TEMPLATES:
- State emotion summary: SELECT state_name, AVG(emotion) FROM tweets WHERE state_code = 'XX' GROUP BY state_name
- Top states by emotion: SELECT state_name, AVG(emotion) as avg_emotion FROM tweets GROUP BY state_name ORDER BY avg_emotion DESC LIMIT 10
- Emotion comparison: SELECT emotion1, emotion2 FROM tweets WHERE state_code = 'XX'
- Time series: SELECT DATE(timestamp), AVG(emotion) FROM tweets GROUP BY DATE(timestamp) ORDER BY DATE(timestamp)
"""

# Table and column mappings for validation
VALID_TABLES = ['tweets']

VALID_COLUMNS = {
    'tweets': [
        'tweet_id', 'username', 'raw_text', 'timestamp', 'state_code', 'state_name',
        'context', 'likes', 'retweets', 'replies', 'views', 'created_at',
        'anger', 'joy', 'fear', 'sadness', 'surprise', 'anticipation', 'trust', 'disgust',
        'sentiment'
    ]
}

# Emotion columns for specific validation
EMOTION_COLUMNS = [
    'anger', 'joy', 'fear', 'sadness', 'surprise', 'anticipation', 'trust', 'disgust'
]

# Valid sentiment values
SENTIMENT_VALUES = ['positive', 'negative', 'neutral']

# US state mappings for better query generation
STATE_MAPPINGS = {
    'california': 'CA', 'texas': 'TX', 'new york': 'NY', 'florida': 'FL',
    'illinois': 'IL', 'pennsylvania': 'PA', 'ohio': 'OH', 'georgia': 'GA',
    'north carolina': 'NC', 'michigan': 'MI', 'new jersey': 'NJ', 'virginia': 'VA',
    'washington': 'WA', 'arizona': 'AZ', 'massachusetts': 'MA', 'tennessee': 'TN',
    'indiana': 'IN', 'maryland': 'MD', 'missouri': 'MO', 'wisconsin': 'WI',
    'colorado': 'CO', 'minnesota': 'MN', 'south carolina': 'SC', 'alabama': 'AL',
    'louisiana': 'LA', 'kentucky': 'KY', 'oregon': 'OR', 'oklahoma': 'OK',
    'connecticut': 'CT', 'utah': 'UT', 'iowa': 'IA', 'nevada': 'NV',
    'arkansas': 'AR', 'mississippi': 'MS', 'kansas': 'KS', 'new mexico': 'NM',
    'nebraska': 'NE', 'west virginia': 'WV', 'idaho': 'ID', 'hawaii': 'HI',
    'new hampshire': 'NH', 'maine': 'ME', 'montana': 'MT', 'rhode island': 'RI',
    'delaware': 'DE', 'south dakota': 'SD', 'north dakota': 'ND', 'alaska': 'AK',
    'vermont': 'VT', 'wyoming': 'WY'
}

def get_schema_context() -> str:
    """
    Get the database schema context for NL→SQL generation.
    This is loaded from the config, making it easy to update when schema changes.
    """
    return DATABASE_SCHEMA

def validate_column_name(column: str) -> bool:
    """Check if a column name is valid for the tweets table"""
    return column.lower() in [col.lower() for col in VALID_COLUMNS['tweets']]

def is_emotion_column(column: str) -> bool:
    """Check if a column is an emotion column"""
    return column.lower() in [col.lower() for col in EMOTION_COLUMNS]

def get_state_code(state_name: str) -> str:
    """Convert state name to state code"""
    return STATE_MAPPINGS.get(state_name.lower(), state_name.upper())

"""
Database Schema Configuration for NL→SQL Generation
Update this file when your database schema changes
"""

# Database schema description for LLM context
DATABASE_SCHEMA = """
DATABASE SCHEMA:

=== IMPORTANT: DATA GRANULARITY ===
• tweets table: INDIVIDUAL TWEET LEVEL - each row is one tweet with its emotion scores
• emotion_aggregates table: STATE LEVEL - pre-calculated averages and counts per state

=== PRIMARY TABLE: tweets (Individual Tweet Data) ===
GRANULARITY: One row per tweet (detailed, individual-level data)
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
- anger: Intensity of anger emotion for THIS SPECIFIC TWEET
- joy: Intensity of joy/happiness emotion for THIS SPECIFIC TWEET
- fear: Intensity of fear/anxiety emotion for THIS SPECIFIC TWEET
- sadness: Intensity of sadness/depression emotion for THIS SPECIFIC TWEET
- surprise: Intensity of surprise/shock emotion for THIS SPECIFIC TWEET
- anticipation: Intensity of anticipation/expectation emotion for THIS SPECIFIC TWEET
- trust: Intensity of trust/confidence emotion for THIS SPECIFIC TWEET
- disgust: Intensity of disgust/revulsion emotion for THIS SPECIFIC TWEET

SENTIMENT ANALYSIS COLUMN:
- sentiment (text): Overall sentiment classification for THIS SPECIFIC TWEET
  Values: 'positive', 'negative', 'neutral'

=== AGGREGATED TABLE: emotion_aggregates (Pre-calculated State Summaries) ===
GRANULARITY: One row per state (aggregated, summary-level data)
- state_code (text): US state abbreviation
- state_name (text): Full US state name
- tweet_count (integer): Total number of tweets from this state

PRE-CALCULATED EMOTION AVERAGES (float 0.0-1.0):
- anger_avg: Average anger across all tweets from this state
- joy_avg: Average joy across all tweets from this state
- fear_avg: Average fear across all tweets from this state
- sadness_avg: Average sadness across all tweets from this state
- surprise_avg: Average surprise across all tweets from this state
- anticipation_avg: Average anticipation across all tweets from this state
- trust_avg: Average trust across all tweets from this state
- disgust_avg: Average disgust across all tweets from this state

PRE-CALCULATED SENTIMENT COUNTS:
- sentiment_positive_count: Number of positive tweets from this state
- sentiment_negative_count: Number of negative tweets from this state
- sentiment_neutral_count: Number of neutral tweets from this state

METADATA:
- last_updated (timestamp): When aggregates were last calculated

=== WHEN TO USE WHICH TABLE ===
• Use 'tweets' for: Individual tweet analysis, detailed queries, time series, specific tweet searches
• Use 'emotion_aggregates' for: Quick state comparisons, overview dashboards, pre-calculated summaries

QUERY PATTERNS & EXAMPLES:
- Individual tweets: SELECT * FROM tweets WHERE state_code = 'CA' LIMIT 100
- Tweet-level averages: SELECT state_name, AVG(anger) FROM tweets GROUP BY state_name
- Pre-calculated averages: SELECT state_name, anger_avg FROM emotion_aggregates
- Filter by state: WHERE state_code = 'CA' OR WHERE state_name = 'California'
- Time filtering: WHERE timestamp >= '2025-01-01' (only works on tweets table)
- Sentiment filtering: WHERE sentiment = 'positive' (tweets) OR sentiment_positive_count > 100 (aggregates)
- Always include LIMIT clause for large result sets (recommended: LIMIT 500)

COMMON QUERY TEMPLATES:
- Individual tweet emotions: SELECT raw_text, anger, joy FROM tweets WHERE state_code = 'CA' LIMIT 10
- Calculate state averages: SELECT state_name, AVG(anger) FROM tweets GROUP BY state_name ORDER BY AVG(anger) DESC
- Use pre-calculated averages: SELECT state_name, anger_avg FROM emotion_aggregates ORDER BY anger_avg DESC
- Time series (tweets only): SELECT DATE(timestamp), AVG(anger) FROM tweets GROUP BY DATE(timestamp) ORDER BY DATE(timestamp)
- State comparison: SELECT state_name, anger_avg, joy_avg FROM emotion_aggregates WHERE state_code IN ('CA', 'TX')
"""

# Table and column mappings for validation
VALID_TABLES = ['tweets', 'emotion_aggregates']

VALID_COLUMNS = {
    'tweets': [
        'tweet_id', 'username', 'raw_text', 'timestamp', 'state_code', 'state_name',
        'context', 'likes', 'retweets', 'replies', 'views', 'created_at',
        'anger', 'joy', 'fear', 'sadness', 'surprise', 'anticipation', 'trust', 'disgust',
        'sentiment'
    ],
    'emotion_aggregates': [
        'state_code', 'state_name', 'tweet_count', 'last_updated',
        'anger_avg', 'joy_avg', 'fear_avg', 'sadness_avg', 'surprise_avg', 
        'anticipation_avg', 'trust_avg', 'disgust_avg',
        'sentiment_positive_count', 'sentiment_negative_count', 'sentiment_neutral_count'
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

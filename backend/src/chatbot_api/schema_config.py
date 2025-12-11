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

Table "public.tweets"
Columns:
- id                   | integer (PK) | not null | default nextval('tweets_id_seq')
- tweet_id             | bigint       | not null
- username             | varchar(255) | not null
- raw_text             | text         | not null
- timestamp            | timestamp    | not null
- created_at           | timestamp    |          | default CURRENT_TIMESTAMP
- state_code           | char(2)      | not null
- state_name           | varchar(255) | not null
- context              | varchar(255) | not null
- likes                | integer      |          | default 0
- retweets             | integer      |          | default 0
- replies              | integer      |          | default 0
- views                | integer      |          | default 0
- sentiment            | varchar(10)  | not null
- sentiment_confidence | double       | not null
- anger                | double       |          | default 0.0
- fear                 | double       |          | default 0.0
- sadness              | double       |          | default 0.0
- surprise             | double       |          | default 0.0
- joy                  | double       |          | default 0.0
- anticipation         | double       |          | default 0.0
- trust                | double       |          | default 0.0
- disgust              | double       |          | default 0.0
- dominant_emotion     | varchar(50)  |          |
- emotion_confidence   | double       |          | default 0.0
- compound             | double       |          | default 0.0

Indexes:
- tweets_pkey PRIMARY KEY (id)
- idx_tweets_context (context)
- idx_tweets_created_at (created_at)

=== AGGREGATED TABLE: emotion_aggregates (Pre-calculated State Summaries) ===
GRANULARITY: One row per state (aggregated, summary-level data)

Table "public.emotion_aggregates"
Columns:
- id                       | integer (PK) | not null | default nextval('emotion_aggregates_id_seq')
- state_code               | char(2)      | not null
- state_name               | varchar(255) | not null
- sentiment_positive_count | integer      |          | default 0
- sentiment_negative_count | integer      |          | default 0
- sentiment_neutral_count  | integer      |          | default 0
- sentiment_positive_avg   | double       |          | default 0.0
- sentiment_negative_avg   | double       |          | default 0.0
- sentiment_neutral_avg    | double       |          | default 0.0
- anger_avg                | double       |          | default 0.0
- fear_avg                 | double       |          | default 0.0
- sadness_avg              | double       |          | default 0.0
- surprise_avg             | double       |          | default 0.0
- joy_avg                  | double       |          | default 0.0
- anticipation_avg         | double       |          | default 0.0
- trust_avg                | double       |          | default 0.0
- disgust_avg              | double       |          | default 0.0
- tweet_count              | integer      |          | default 0
- last_updated             | timestamp    |          | default CURRENT_TIMESTAMP

Indexes:
- emotion_aggregates_pkey PRIMARY KEY (id)
- emotion_aggregates_state_code_key UNIQUE (state_code)

=== WHEN TO USE WHICH TABLE ===
• Use 'tweets' for: Individual tweet analysis, detailed queries, time series, specific tweet searches
• Use 'emotion_aggregates' for: Quick state comparisons, overview dashboards, pre-calculated summaries

=== CRITICAL: TIME COLUMN USAGE ===
• ALWAYS use 'timestamp' column for time-based queries and time series analysis
• 'created_at' is for internal database tracking only - DO NOT USE in queries
• For time filtering: WHERE timestamp >= '2025-01-01'
• For time series: SELECT DATE(timestamp), AVG(emotion) FROM tweets GROUP BY DATE(timestamp) ORDER BY DATE(timestamp)

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
 
=== QUERY RULES (PostgreSQL) ===
• Return ONE valid SQL statement only; no explanations.
• Keep parentheses balanced; avoid trailing or extra closing parentheses.
• When using HAVING with a threshold, compute the threshold from the SAME table/filters using a CTE or scalar subquery, e.g.:
  WITH threshold AS (
    SELECT AVG(anger) AS avg_anger_threshold
    FROM tweets
    WHERE timestamp >= CURRENT_DATE - INTERVAL '7 days'
      AND state_code IN ('CA','TX')
  )
  SELECT state_name
  FROM tweets
  WHERE timestamp >= CURRENT_DATE - INTERVAL '7 days'
  GROUP BY state_name
  HAVING AVG(anger) > (SELECT avg_anger_threshold FROM threshold)
  LIMIT 500;
• Do NOT compare aggregates from tweets to values from emotion_aggregates in HAVING unless you explicitly JOIN on state_code; prefer computing thresholds from tweets directly.
• Use emotion_aggregates for direct state-level summaries (e.g., select anger_avg) without mixing into tweet-level HAVING.
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

def get_state_code(state_name: str) -> str:
    """Get 2-letter state code from full name"""
    return STATE_MAPPINGS.get(state_name.lower(), state_name.upper())

def get_schema_context() -> str:
    """
    Get the database schema context for NL→SQL generation.
    This is loaded from the config, making it easy to update when schema changes.
    """
    # Add state mappings to context to help LLM with state names
    mapping_str = "STATE NAME MAPPINGS (Use these codes):\n" + ", ".join([f"{k.title()}='{v}'" for k, v in STATE_MAPPINGS.items()])
    return f"{DATABASE_SCHEMA}\n\n{mapping_str}"

def validate_column_name(column: str) -> bool:
    """Check if a column name is valid for the tweets table"""
    return column.lower() in [col.lower() for col in VALID_COLUMNS['tweets']]

def is_emotion_column(column: str) -> bool:
    """Check if a column is an emotion column"""
    return column.lower() in [col.lower() for col in EMOTION_COLUMNS]

# Few-shot examples for complex queries
FEW_SHOT_EXAMPLES = """
EXAMPLE 1: Time Series Analysis
Question: "Show me the trend of anger in California over the last 7 days"
SQL:
SELECT DATE(timestamp) as date, AVG(anger) as anger_avg 
FROM tweets 
WHERE state_code = 'CA' 
  AND timestamp >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY DATE(timestamp) 
ORDER BY DATE(timestamp) ASC;

EXAMPLE 2: State Comparison
Question: "Compare the joy levels between Texas and New York"
SQL:
SELECT state_name, AVG(joy) as joy_avg 
FROM emotion_aggregates 
WHERE state_code IN ('TX', 'NY')
ORDER BY joy_avg DESC;

EXAMPLE 3: Top N Ranking
Question: "Which 5 states are the happiest?"
SQL:
SELECT state_name, joy_avg 
FROM emotion_aggregates 
ORDER BY joy_avg DESC 
LIMIT 5;

EXAMPLE 4: Composition/Breakdown
Question: "What is the sentiment breakdown for Florida?"
SQL:
SELECT 
  sentiment_positive_count, 
  sentiment_negative_count, 
  sentiment_neutral_count 
FROM emotion_aggregates 
WHERE state_code = 'FL';

EXAMPLE 5: Complex Multi-Metric
Question: "Show me anger vs fear for the top 10 states by tweet count"
SQL:
SELECT state_name, anger_avg, fear_avg, tweet_count
FROM emotion_aggregates
ORDER BY tweet_count DESC
LIMIT 10;

EXAMPLE 6: Top Emotions for a Single State (Unpivoting)
Question: "What are the top emotions in Texas?"
SQL:
SELECT
    L.emotion_name,
    L.emotion_value
FROM emotion_aggregates
CROSS JOIN LATERAL (
    VALUES 
        ('anger', anger_avg),
        ('joy', joy_avg),
        ('fear', fear_avg),
        ('sadness', sadness_avg),
        ('surprise', surprise_avg),
        ('anticipation', anticipation_avg),
        ('trust', trust_avg),
        ('disgust', disgust_avg)
) AS L(emotion_name, emotion_value)
WHERE state_code = 'TX'
ORDER BY emotion_value DESC
LIMIT 5;
"""

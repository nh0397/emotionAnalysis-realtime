#!/usr/bin/env python3
"""
Database Migration Script
Fixes the schema to properly separate sentiment from emotions
"""

import psycopg2
import sys
from datetime import datetime

# Database configuration
DB_PARAMS = {
    'host': 'localhost',
    'port': 5432,
    'database': 'tweetdb',
    'user': 'tweetuser',
    'password': 'tweetpass'
}

def get_db_connection():
    """Get database connection"""
    try:
        return psycopg2.connect(**DB_PARAMS)
    except Exception as e:
        print(f"Database connection failed: {e}")
        return None

def create_new_schema():
    """Create the new, properly designed schema"""
    
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    try:
        print("Creating new tweets table with proper sentiment/emotion separation...")
        
        # Drop existing table (WARNING: This will delete all data!)
        cursor.execute("DROP TABLE IF EXISTS tweets CASCADE")
        cursor.execute("DROP TABLE IF EXISTS emotion_aggregates CASCADE")
        
        # Create new tweets table with proper schema
        cursor.execute('''
            CREATE TABLE tweets (
                -- Primary key and metadata
                id SERIAL PRIMARY KEY,
                tweet_id BIGINT NOT NULL,
                username VARCHAR(255) NOT NULL,
                raw_text TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Location data
                state_code CHAR(2) NOT NULL,
                state_name VARCHAR(255) NOT NULL,
                context VARCHAR(255) NOT NULL,
                
                -- Social metrics
                likes INTEGER DEFAULT 0,
                retweets INTEGER DEFAULT 0,
                replies INTEGER DEFAULT 0,
                views INTEGER DEFAULT 0,
                
                -- SENTIMENT (3-way classification)
                sentiment VARCHAR(10) NOT NULL,  -- 'positive', 'negative', 'neutral'
                sentiment_confidence FLOAT NOT NULL,
                
                -- EMOTIONS (8-way classification)
                anger FLOAT DEFAULT 0.0,
                fear FLOAT DEFAULT 0.0,
                sadness FLOAT DEFAULT 0.0,
                surprise FLOAT DEFAULT 0.0,
                joy FLOAT DEFAULT 0.0,
                anticipation FLOAT DEFAULT 0.0,
                trust FLOAT DEFAULT 0.0,
                disgust FLOAT DEFAULT 0.0,
                
                -- Overall emotion analysis
                dominant_emotion VARCHAR(50),  -- from the 8 emotions above
                emotion_confidence FLOAT DEFAULT 0.0,
                
                -- VADER-style compound score (for compatibility)
                compound FLOAT DEFAULT 0.0,
                
                -- Indexes for performance
                CONSTRAINT valid_sentiment CHECK (sentiment IN ('positive', 'negative', 'neutral')),
                CONSTRAINT valid_emotion_scores CHECK (
                    anger >= 0 AND anger <= 1 AND
                    fear >= 0 AND fear <= 1 AND
                    sadness >= 0 AND sadness <= 1 AND
                    surprise >= 0 AND surprise <= 1 AND
                    joy >= 0 AND joy <= 1 AND
                    anticipation >= 0 AND anticipation <= 1 AND
                    trust >= 0 AND trust <= 1 AND
                    disgust >= 0 AND disgust <= 1
                )
            )
        ''')
        
        # Create indexes for performance
        cursor.execute('CREATE INDEX idx_tweets_timestamp ON tweets(timestamp)')
        cursor.execute('CREATE INDEX idx_tweets_state ON tweets(state_code)')
        cursor.execute('CREATE INDEX idx_tweets_sentiment ON tweets(sentiment)')
        cursor.execute('CREATE INDEX idx_tweets_dominant_emotion ON tweets(dominant_emotion)')
        cursor.execute('CREATE INDEX idx_tweets_created_at ON tweets(created_at)')
        
        # Create emotion aggregates table (updated schema)
        cursor.execute('''
            CREATE TABLE emotion_aggregates (
                id SERIAL PRIMARY KEY,
                state_code CHAR(2) NOT NULL,
                state_name VARCHAR(255) NOT NULL,
                
                -- Sentiment aggregates
                sentiment_positive_count INTEGER DEFAULT 0,
                sentiment_negative_count INTEGER DEFAULT 0,
                sentiment_neutral_count INTEGER DEFAULT 0,
                sentiment_positive_avg FLOAT DEFAULT 0.0,
                sentiment_negative_avg FLOAT DEFAULT 0.0,
                sentiment_neutral_avg FLOAT DEFAULT 0.0,
                
                -- Emotion aggregates (averages)
                anger_avg FLOAT DEFAULT 0.0,
                fear_avg FLOAT DEFAULT 0.0,
                sadness_avg FLOAT DEFAULT 0.0,
                surprise_avg FLOAT DEFAULT 0.0,
                joy_avg FLOAT DEFAULT 0.0,
                anticipation_avg FLOAT DEFAULT 0.0,
                trust_avg FLOAT DEFAULT 0.0,
                disgust_avg FLOAT DEFAULT 0.0,
                
                -- Counts
                tweet_count INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                UNIQUE(state_code)
            )
        ''')
        
        # Create aggregate update function
        cursor.execute('''
            CREATE OR REPLACE FUNCTION update_emotion_aggregates()
            RETURNS TRIGGER AS $$
            BEGIN
                INSERT INTO emotion_aggregates (
                    state_code, state_name,
                    sentiment_positive_count, sentiment_negative_count, sentiment_neutral_count,
                    sentiment_positive_avg, sentiment_negative_avg, sentiment_neutral_avg,
                    anger_avg, fear_avg, sadness_avg, surprise_avg, joy_avg, 
                    anticipation_avg, trust_avg, disgust_avg, tweet_count, last_updated
                )
                SELECT 
                    state_code,
                    state_name,
                    COUNT(CASE WHEN sentiment = 'positive' THEN 1 END),
                    COUNT(CASE WHEN sentiment = 'negative' THEN 1 END),
                    COUNT(CASE WHEN sentiment = 'neutral' THEN 1 END),
                    AVG(CASE WHEN sentiment = 'positive' THEN sentiment_confidence END),
                    AVG(CASE WHEN sentiment = 'negative' THEN sentiment_confidence END),
                    AVG(CASE WHEN sentiment = 'neutral' THEN sentiment_confidence END),
                    AVG(anger), AVG(fear), AVG(sadness), AVG(surprise), AVG(joy),
                    AVG(anticipation), AVG(trust), AVG(disgust),
                    COUNT(*), CURRENT_TIMESTAMP
                FROM tweets 
                WHERE state_code = NEW.state_code
                GROUP BY state_code, state_name
                ON CONFLICT (state_code) DO UPDATE SET
                    sentiment_positive_count = EXCLUDED.sentiment_positive_count,
                    sentiment_negative_count = EXCLUDED.sentiment_negative_count,
                    sentiment_neutral_count = EXCLUDED.sentiment_neutral_count,
                    sentiment_positive_avg = EXCLUDED.sentiment_positive_avg,
                    sentiment_negative_avg = EXCLUDED.sentiment_negative_avg,
                    sentiment_neutral_avg = EXCLUDED.sentiment_neutral_avg,
                    anger_avg = EXCLUDED.anger_avg,
                    fear_avg = EXCLUDED.fear_avg,
                    sadness_avg = EXCLUDED.sadness_avg,
                    surprise_avg = EXCLUDED.surprise_avg,
                    joy_avg = EXCLUDED.joy_avg,
                    anticipation_avg = EXCLUDED.anticipation_avg,
                    trust_avg = EXCLUDED.trust_avg,
                    disgust_avg = EXCLUDED.disgust_avg,
                    tweet_count = EXCLUDED.tweet_count,
                    last_updated = EXCLUDED.last_updated;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        ''')
        
        # Create trigger
        cursor.execute('''
            CREATE TRIGGER trigger_update_emotion_aggregates
            AFTER INSERT OR UPDATE OR DELETE ON tweets
            FOR EACH ROW EXECUTE FUNCTION update_emotion_aggregates();
        ''')
        
        conn.commit()
        print("✅ New schema created successfully!")
        print("✅ Indexes created for performance")
        print("✅ Aggregation functions and triggers created")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating schema: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def generate_schema_diagram():
    """Generate Mermaid diagram code for the database schema"""
    
    mermaid_code = '''
graph TD
    subgraph "Tweet Analysis Database Schema"
        TWEETS["`**tweets**
        ---
        **Primary Data**
        • id (SERIAL PK)
        • tweet_id (BIGINT)
        • username (VARCHAR)
        • raw_text (TEXT)
        • timestamp (TIMESTAMP)
        • created_at (TIMESTAMP)
        
        **Location**
        • state_code (CHAR(2))
        • state_name (VARCHAR)
        • context (VARCHAR)
        
        **Social Metrics**
        • likes (INTEGER)
        • retweets (INTEGER)
        • replies (INTEGER)
        • views (INTEGER)
        
        **Sentiment (3-way)**
        • sentiment (VARCHAR)
        • sentiment_confidence (FLOAT)
        
        **Emotions (8-way)**
        • anger (FLOAT)
        • fear (FLOAT)
        • sadness (FLOAT)
        • surprise (FLOAT)
        • joy (FLOAT)
        • anticipation (FLOAT)
        • trust (FLOAT)
        • disgust (FLOAT)
        
        **Analysis Results**
        • dominant_emotion (VARCHAR)
        • emotion_confidence (FLOAT)
        • compound (FLOAT)`"]
        
        AGGREGATES["`**emotion_aggregates**
        ---
        **State-level Aggregates**
        • state_code (CHAR(2))
        • state_name (VARCHAR)
        
        **Sentiment Counts**
        • sentiment_positive_count
        • sentiment_negative_count
        • sentiment_neutral_count
        
        **Sentiment Averages**
        • sentiment_positive_avg
        • sentiment_negative_avg
        • sentiment_neutral_avg
        
        **Emotion Averages**
        • anger_avg
        • fear_avg
        • sadness_avg
        • surprise_avg
        • joy_avg
        • anticipation_avg
        • trust_avg
        • disgust_avg
        
        **Metadata**
        • tweet_count (INTEGER)
        • last_updated (TIMESTAMP)`"]
        
        TWEETS -->|"Aggregates by state"| AGGREGATES
        
        subgraph "Data Flow"
            KAFKA["`**Kafka Stream**
            Raw tweets`"]
            NLP["`**NLP Pipeline**
            DistilRoBERTa-Emotion
            • Sentiment: pos/neg/neu
            • Emotions: 8 categories`"]
            DB["`**PostgreSQL**
            Real-time storage`"]
            
            KAFKA --> NLP
            NLP --> DB
        end
        
        subgraph "API Endpoints"
            API1["`**/emotionData**
            State aggregates`"]
            API2["`**/timeSeriesData**
            Historical trends`"]
            API3["`**/timeSeriesData/compare**
            State comparisons`"]
        end
        
        AGGREGATES --> API1
        TWEETS --> API2
        TWEETS --> API3
    end
    
    classDef primaryTable fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef aggregateTable fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef processBox fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px
    classDef apiBox fill:#fff3e0,stroke:#ef6c00,stroke-width:2px
    
    class TWEETS primaryTable
    class AGGREGATES aggregateTable
    class KAFKA,NLP,DB processBox
    class API1,API2,API3 apiBox
    '''
    
    return mermaid_code

def save_schema_diagram():
    """Save the schema diagram to a file"""
    mermaid_code = generate_schema_diagram()
    
    with open('database_schema_diagram.md', 'w') as f:
        f.write(f"""# Database Schema Diagram

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Mermaid Diagram

Copy this code into [Mermaid Live Editor](https://mermaid.live/) or any Mermaid-compatible tool:

```mermaid
{mermaid_code}
```

## Schema Design Principles

### Sentiment vs Emotions
- **Sentiment**: 3-way classification (positive, negative, neutral)
- **Emotions**: 8-way classification (anger, fear, sadness, surprise, joy, anticipation, trust, disgust)

### Data Flow
1. **Kafka Stream**: Raw tweets from Twitter API
2. **NLP Pipeline**: DistilRoBERTa-Emotion analysis
3. **PostgreSQL**: Real-time storage with proper separation
4. **API Endpoints**: Serve aggregated and time-series data

### Performance Optimizations
- Indexes on timestamp, state_code, sentiment, dominant_emotion
- Automatic aggregation triggers
- Efficient query patterns for real-time dashboards

## Migration Notes
- Old schema mixed sentiment and emotions
- New schema properly separates concerns
- All existing APIs will need updates to use new column names
""")
    
    print("✅ Schema diagram saved to: database_schema_diagram.md")
    print("📊 Copy the Mermaid code to https://mermaid.live/ to view the diagram")

def main():
    """Run the database migration"""
    print("🗄️  Database Schema Migration")
    print("=" * 50)
    print("⚠️  WARNING: This will DROP existing tables and DELETE all data!")
    
    # Check if running in non-interactive mode
    if len(sys.argv) > 1 and sys.argv[1] == '--yes':
        response = 'yes'
    else:
        try:
            response = input("Continue? (yes/no): ").lower().strip()
        except EOFError:
            print("Non-interactive mode detected. Use --yes flag to proceed.")
            return
    
    if response != 'yes':
        print("Migration cancelled.")
        return
    
    print("\n1. Creating new schema...")
    if create_new_schema():
        print("\n2. Generating schema diagram...")
        save_schema_diagram()
        print("\n✅ Migration completed successfully!")
        print("\nNext steps:")
        print("1. Update your NLP pipeline to use new column names")
        print("2. Update API endpoints to use new schema")
        print("3. Test with sample data")
    else:
        print("\n❌ Migration failed!")

if __name__ == "__main__":
    main()

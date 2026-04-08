#!/usr/bin/env python3
"""
Database Consumer
Consumes tweets from Kafka and stores them in PostgreSQL database
"""

import json
import psycopg2
import psycopg2.errors
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable
from datetime import datetime
import sys
import signal
import time
from typing import Dict, Any
from unified_logger import logger

class DatabaseConsumer:
    def __init__(
        self, 
        kafka_bootstrap_servers=['localhost:9092'],
        db_host='localhost',
        db_port=5432,
        db_name='tweetdb',
        db_user='tweetuser',
        db_password='tweetpass'
    ):
        # Initialize database connection
        self.db_params = {
            'host': db_host,
            'port': db_port,
            'database': db_name,
            'user': db_user,
            'password': db_password
        }
        
        # Store Kafka settings
        self.kafka_bootstrap_servers = kafka_bootstrap_servers
        self.consumer = None
        
        # Initialize database
        self.init_database()
        
        # Initialize Kafka consumer with retries
        self.connect_kafka()
        
        logger.system_event("DB_CONSUMER_STARTED")

    def connect_kafka(self, max_retries=30, retry_interval=2):
        """Connect to Kafka with retries"""
        retries = 0
        while retries < max_retries:
            try:
                self.consumer = KafkaConsumer(
                    'tweets',  # FIXED: Correct topic name
                    bootstrap_servers=self.kafka_bootstrap_servers,
                    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                    auto_offset_reset='earliest',
                    group_id='db-consumer-group',
                    enable_auto_commit=True,
                    api_version_auto_timeout_ms=30000
                )
                return True
            except Exception as e:
                retries += 1
                time.sleep(retry_interval)

        return False

    def wait_for_postgres(self, max_retries=30, delay=1):
        """Wait for PostgreSQL to be ready"""
        retries = 0
        while retries < max_retries:
            try:
                conn = psycopg2.connect(**self.db_params)
                conn.close()
                return True
            except psycopg2.OperationalError:
                retries += 1
                time.sleep(delay)
        
        return False

    def init_database(self):
        """Initialize PostgreSQL database with full schema (tweets, aggregates, triggers)"""
        if not self.wait_for_postgres():
            logger.error("DB_CONSUMER", "PostgreSQL not ready, exiting.")
            sys.exit(1)

        try:
            conn = psycopg2.connect(**self.db_params)
            cursor = conn.cursor()
            
            # 1. Create tweets table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tweets (
                    id SERIAL PRIMARY KEY,
                    tweet_id BIGINT NOT NULL,
                    username VARCHAR(255) NOT NULL,
                    raw_text TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    state_code CHAR(2) NOT NULL,
                    state_name VARCHAR(255) NOT NULL,
                    context VARCHAR(255) NOT NULL,
                    likes INTEGER DEFAULT 0,
                    retweets INTEGER DEFAULT 0,
                    replies INTEGER DEFAULT 0,
                    views INTEGER DEFAULT 0,
                    sentiment VARCHAR(10) DEFAULT 'neutral',
                    sentiment_confidence FLOAT DEFAULT 0.0,
                    anger FLOAT DEFAULT 0.0,
                    fear FLOAT DEFAULT 0.0,
                    sadness FLOAT DEFAULT 0.0,
                    surprise FLOAT DEFAULT 0.0,
                    joy FLOAT DEFAULT 0.0,
                    anticipation FLOAT DEFAULT 0.0,
                    trust FLOAT DEFAULT 0.0,
                    negative FLOAT DEFAULT 0.0,
                    disgust FLOAT DEFAULT 0.0,
                    compound FLOAT DEFAULT 0.0,
                    dominant_emotion VARCHAR(50),
                    emotion_confidence FLOAT DEFAULT 0.0
                )
            ''')
            
            # 2. Create aggregates table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS emotion_aggregates (
                    id SERIAL PRIMARY KEY,
                    state_code CHAR(2) NOT NULL,
                    state_name VARCHAR(255) NOT NULL,
                    sentiment_positive_count INTEGER DEFAULT 0,
                    sentiment_negative_count INTEGER DEFAULT 0,
                    sentiment_neutral_count INTEGER DEFAULT 0,
                    sentiment_positive_avg FLOAT DEFAULT 0.0,
                    sentiment_negative_avg FLOAT DEFAULT 0.0,
                    sentiment_neutral_avg FLOAT DEFAULT 0.0,
                    anger_avg FLOAT DEFAULT 0.0,
                    fear_avg FLOAT DEFAULT 0.0,
                    sadness_avg FLOAT DEFAULT 0.0,
                    surprise_avg FLOAT DEFAULT 0.0,
                    joy_avg FLOAT DEFAULT 0.0,
                    anticipation_avg FLOAT DEFAULT 0.0,
                    trust_avg FLOAT DEFAULT 0.0,
                    disgust_avg FLOAT DEFAULT 0.0,
                    tweet_count INTEGER DEFAULT 0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(state_code)
                )
            ''')
            
            # 3. Create aggregate update function
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
            
            # 4. Create trigger (drop first if exists to avoid errors)
            cursor.execute('DROP TRIGGER IF EXISTS trigger_update_emotion_aggregates ON tweets')
            cursor.execute('''
                CREATE TRIGGER trigger_update_emotion_aggregates
                AFTER INSERT OR UPDATE OR DELETE ON tweets
                FOR EACH ROW EXECUTE FUNCTION update_emotion_aggregates();
            ''')
            
            # 5. Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tweets_timestamp ON tweets(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tweets_state_code ON tweets(state_code)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tweets_context ON tweets(context)')
            
            conn.commit()
            conn.close()
            logger.system_event("DB_SCHEMA_INITIALIZED")
            
        except Exception as e:
            logger.error("DB_CONSUMER", f"Database initialization failed: {e}")
            sys.exit(1)

    def store_tweet(self, tweet: Dict[str, Any]):
        """Store tweet in database with new sentiment/emotion schema"""
        try:
            # Convert and validate data types EXPLICITLY
            tweet_id = int(tweet['id'])
            username = str(tweet['username'])
            raw_text = str(tweet['raw_text'])
            timestamp = str(tweet['timestamp'])
            state_code = str(tweet['state_code'])
            state_name = str(tweet['state_name'])
            context = str(tweet['context'])
            
            # Convert engagement metrics to integers
            likes = int(tweet.get('likes', 0))
            retweets = int(tweet.get('retweets', 0))
            replies = int(tweet.get('replies', 0))
            views = int(tweet.get('views', 0))
            
            # Extract sentiment (3-way classification)
            sentiment = str(tweet.get('sentiment', 'neutral'))
            sentiment_confidence = float(tweet.get('sentiment_confidence', 0.0))
            
            # Extract emotion scores (8-way classification)
            anger = float(tweet.get('anger', 0.0))
            fear = float(tweet.get('fear', 0.0))
            sadness = float(tweet.get('sadness', 0.0))
            surprise = float(tweet.get('surprise', 0.0))
            joy = float(tweet.get('joy', 0.0))
            anticipation = float(tweet.get('anticipation', 0.0))
            trust = float(tweet.get('trust', 0.0))
            disgust = float(tweet.get('disgust', 0.0))
            
            # Analysis results
            dominant_emotion = str(tweet.get('dominant_emotion', 'joy'))
            emotion_confidence = float(tweet.get('emotion_confidence', 0.0))
            compound = float(tweet.get('compound', 0.0))
            
            # CREATE THE ACTUAL SQL STRING to see exactly what we're executing
            sql_query = f"""
                INSERT INTO tweets (
                    tweet_id, username, raw_text, timestamp, 
                    state_code, state_name, context,
                    likes, retweets, replies, views,
                    sentiment, sentiment_confidence,
                    anger, fear, sadness, surprise, joy, 
                    anticipation, trust, disgust,
                    dominant_emotion, emotion_confidence, compound
                ) VALUES (
                    {tweet_id}, '{username}', '{raw_text.replace("'", "''")}', '{timestamp}', 
                    '{state_code}', '{state_name}', '{context}',
                    {likes}, {retweets}, {replies}, {views},
                    '{sentiment}', {sentiment_confidence},
                    {anger}, {fear}, {sadness}, {surprise}, {joy}, 
                    {anticipation}, {trust}, {disgust}, 
                    '{dominant_emotion}', {emotion_confidence}, {compound}
                )
            """
            
            # Log the EXACT SQL being executed
            logger.system_event("SQL_DEBUG", f"Executing SQL: {sql_query}")
            
            # Log specific emotion values for debugging
            logger.system_event("EMOTION_VALUES_DEBUG", 
                f"Tweet {tweet_id}: sentiment={sentiment}, anger={anger}, joy={joy}, dominant={dominant_emotion}")
            
            # Connect and execute
            conn = psycopg2.connect(**self.db_params)
            cursor = conn.cursor()
            
            # Execute the SQL string directly
            cursor.execute(sql_query)
            
            # Database triggers will automatically update emotion_aggregates
            # No manual aggregation needed!
            
            conn.commit()
            conn.close()
            logger.db_stored(tweet_id, state_code, dominant_emotion)
            
        except Exception as e:
            logger.error("DB_CONSUMER", f"Failed to store tweet {tweet.get('id', 'unknown')}: {e}")
            logger.error("DB_CONSUMER", f"Tweet data: {tweet}")

    # Old aggregation methods removed - using database triggers now!

    def start_consuming(self):
        """Start consuming tweets and storing in database"""
        
        while True:
            try:
                if not self.consumer:
                    if not self.connect_kafka():
                        time.sleep(5)
                        continue

                for message in self.consumer:
                    tweet = message.value
                    logger.kafka_received(tweet['id'], tweet['state_code'])
                    self.store_tweet(tweet)
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.consumer = None
                time.sleep(5)

    def close(self):
        """Close Kafka consumer"""
        if self.consumer:
            self.consumer.close()

def signal_handler(signum, frame):
    sys.exit(0)

if __name__ == "__main__":
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start consumer
    consumer = DatabaseConsumer()
    try:
        consumer.start_consuming()
    finally:
        consumer.close()

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
        """Initialize PostgreSQL database with tweets table"""
        if not self.wait_for_postgres():
            sys.exit(1)

        try:
            conn = psycopg2.connect(**self.db_params)
            cursor = conn.cursor()
            
            # Create tweets table with ALL emotion columns
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tweets (
                    id SERIAL PRIMARY KEY,
                    tweet_id INTEGER NOT NULL,
                    username VARCHAR(255) NOT NULL,
                    raw_text TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    state_code CHAR(2) NOT NULL,
                    state_name VARCHAR(255) NOT NULL,
                    context VARCHAR(255) NOT NULL,
                    likes INTEGER DEFAULT 0,
                    retweets INTEGER DEFAULT 0,
                    replies INTEGER DEFAULT 0,
                    views INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    anger FLOAT DEFAULT 0.0,
                    fear FLOAT DEFAULT 0.0,
                    positive FLOAT DEFAULT 0.0,
                    sadness FLOAT DEFAULT 0.0,
                    surprise FLOAT DEFAULT 0.0,
                    joy FLOAT DEFAULT 0.0,
                    anticipation FLOAT DEFAULT 0.0,
                    trust FLOAT DEFAULT 0.0,
                    negative FLOAT DEFAULT 0.0,
                    disgust FLOAT DEFAULT 0.0,
                    compound FLOAT DEFAULT 0.0,
                    dominant_emotion VARCHAR(50),
                    confidence FLOAT DEFAULT 0.0
                )
            ''')
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tweets_timestamp ON tweets(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tweets_state_code ON tweets(state_code)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tweets_context ON tweets(context)')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            sys.exit(1)

    def store_tweet(self, tweet: Dict[str, Any]):
        """Store tweet in database with emotion data"""
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
            
            # Convert emotion scores to floats (CRITICAL!)
            anger = float(tweet.get('anger', 0.0))
            fear = float(tweet.get('fear', 0.0))
            positive = float(tweet.get('positive', 0.0))
            sadness = float(tweet.get('sadness', 0.0))
            surprise = float(tweet.get('surprise', 0.0))
            joy = float(tweet.get('joy', 0.0))
            anticipation = float(tweet.get('anticipation', 0.0))
            trust = float(tweet.get('trust', 0.0))
            negative = float(tweet.get('negative', 0.0))
            disgust = float(tweet.get('disgust', 0.0))
            compound = float(tweet.get('compound', 0.0))
            confidence = float(tweet.get('confidence', 0.0))
            
            dominant_emotion = str(tweet.get('dominant_emotion', 'neutral'))
            
            # CREATE THE ACTUAL SQL STRING to see exactly what we're executing
            sql_query = f"""
                INSERT INTO tweets (
                    tweet_id, username, raw_text, timestamp, 
                    state_code, state_name, context,
                    likes, retweets, replies, views,
                    anger, fear, positive, sadness, surprise, joy, 
                    anticipation, trust, negative, disgust, 
                    compound, dominant_emotion, confidence
                ) VALUES (
                    {tweet_id}, '{username}', '{raw_text.replace("'", "''")}', '{timestamp}', 
                    '{state_code}', '{state_name}', '{context}',
                    {likes}, {retweets}, {replies}, {views},
                    {anger}, {fear}, {positive}, {sadness}, {surprise}, {joy}, 
                    {anticipation}, {trust}, {negative}, {disgust}, 
                    {compound}, '{dominant_emotion}', {confidence}
                )
            """
            
            # Log the EXACT SQL being executed
            logger.system_event("SQL_DEBUG", f"Executing SQL: {sql_query}")
            
            # Log specific emotion values for debugging
            logger.system_event("EMOTION_VALUES_DEBUG", 
                f"Tweet {tweet_id}: anger={anger}({type(anger)}), joy={joy}({type(joy)}), positive={positive}({type(positive)}), dominant={dominant_emotion}")
            
            # Connect and execute
            conn = psycopg2.connect(**self.db_params)
            cursor = conn.cursor()
            
            # Execute the SQL string directly
            cursor.execute(sql_query)
            
            conn.commit()
            conn.close()
            logger.db_stored(tweet_id, state_code, dominant_emotion)
            
        except Exception as e:
            logger.error("DB_CONSUMER", f"Failed to store tweet {tweet.get('id', 'unknown')}: {e}")
            logger.error("DB_CONSUMER", f"Tweet data: {tweet}")

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

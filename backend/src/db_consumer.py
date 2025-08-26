#!/usr/bin/env python3
"""
Database Consumer
Consumes tweets from Kafka and stores them in PostgreSQL database
"""

import json
import psycopg2
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable
from datetime import datetime
import sys
import signal
import time
from typing import Dict, Any

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

    def connect_kafka(self, max_retries=30, retry_interval=2):
        """Connect to Kafka with retries"""
        retries = 0
        while retries < max_retries:
            try:
                self.consumer = KafkaConsumer(
                    'raw_tweets',
                    bootstrap_servers=self.kafka_bootstrap_servers,
                    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                    auto_offset_reset='earliest',
                    group_id='db-consumer-group',
                    enable_auto_commit=True,
                    api_version_auto_timeout_ms=30000
                )
                print(f"Connected to Kafka at {self.kafka_bootstrap_servers}")
                return True
            except NoBrokersAvailable:
                retries += 1
                print(f"Waiting for Kafka to be ready... Attempt {retries}/{max_retries}")
                time.sleep(retry_interval)
            except Exception as e:
                print(f"Failed to connect to Kafka: {e}")
                time.sleep(retry_interval)
                retries += 1

        print("Failed to connect to Kafka after maximum retries")
        return False

    def wait_for_postgres(self, max_retries=30, delay=1):
        """Wait for PostgreSQL to be ready"""
        retries = 0
        while retries < max_retries:
            try:
                conn = psycopg2.connect(**self.db_params)
                conn.close()
                print("Successfully connected to PostgreSQL")
                return True
            except psycopg2.OperationalError:
                retries += 1
                print(f"Waiting for PostgreSQL... ({retries}/{max_retries})")
                time.sleep(delay)
        
        print("Failed to connect to PostgreSQL after maximum retries")
        return False

    def init_database(self):
        """Initialize PostgreSQL database with tweets table"""
        if not self.wait_for_postgres():
            sys.exit(1)

        try:
            conn = psycopg2.connect(**self.db_params)
            cursor = conn.cursor()
            
            # Create tweets table
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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tweets_timestamp ON tweets(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tweets_state_code ON tweets(state_code)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tweets_context ON tweets(context)')
            
            conn.commit()
            conn.close()
            print("Database initialized with tables and indexes")
            
        except Exception as e:
            print(f"Failed to initialize database: {e}")
            sys.exit(1)

    def store_tweet(self, tweet: Dict[str, Any]):
        """Store tweet in database"""
        try:
            conn = psycopg2.connect(**self.db_params)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO tweets (
                    tweet_id, username, raw_text, timestamp, 
                    state_code, state_name, context,
                    likes, retweets, replies, views
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                tweet['id'],
                tweet['username'],
                tweet['raw_text'],
                tweet['timestamp'],
                tweet['state_code'],
                tweet['state_name'],
                tweet['context'],
                tweet.get('likes', 0),
                tweet.get('retweets', 0),
                tweet.get('replies', 0),
                tweet.get('views', 0)
            ))
            
            conn.commit()
            conn.close()
            print(f"Stored tweet in database: {tweet['state_code']} - {tweet['raw_text']}")
            
        except Exception as e:
            print(f"Failed to store tweet in database: {e}")

    def start_consuming(self):
        """Start consuming tweets and storing in database"""
        print("Database consumer started")
        
        while True:
            try:
                if not self.consumer:
                    if not self.connect_kafka():
                        time.sleep(5)
                        continue

                for message in self.consumer:
                    tweet = message.value
                    self.store_tweet(tweet)
                    
            except KeyboardInterrupt:
                print("\nDatabase consumer stopped")
                break
            except Exception as e:
                print(f"Error in database consumer: {e}")
                self.consumer = None  # Reset consumer to trigger reconnection
                time.sleep(5)

    def close(self):
        """Close Kafka consumer"""
        if self.consumer:
            self.consumer.close()
            print("Kafka consumer closed")

def signal_handler(signum, frame):
    print("\nReceived signal to stop")
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
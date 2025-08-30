#!/usr/bin/env python3
"""
Database Writer - Consumes from Kafka and stores tweets in PostgreSQL
"""

import json
import logging
import psycopg2
from kafka import KafkaConsumer
from kafka.errors import KafkaError
import signal
import sys
import os
from datetime import datetime

from system_logger import db_logger as logger

class DatabaseWriter:
    def __init__(self):
        self.running = True
        self.db_params = {
            'host': 'localhost',
            'port': 5432,
            'database': 'tweetdb',
            'user': 'tweetuser',
            'password': 'tweetpass'
        }
        
        # Initialize database
        self.init_database()
        
        # Initialize Kafka consumer
        self.consumer = KafkaConsumer(
            'tweets',
            bootstrap_servers=['localhost:9092'],
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest',
            group_id='db-writer-group'
        )
        logger.system_event("DB_WRITER_INITIALIZED")

    def init_database(self):
        """Initialize PostgreSQL database with tweets table"""
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
            logger.system_event("DATABASE_INITIALIZED")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize database: {e}")
            sys.exit(1)

    def store_tweet(self, tweet):
        """Store tweet in database"""
        try:
            conn = psycopg2.connect(**self.db_params)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO tweets (
                    tweet_id, username, raw_text, timestamp, 
                    state_code, state_name, context, likes, retweets, replies, views
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                tweet['id'],
                tweet['username'],
                tweet['raw_text'],
                tweet['timestamp'],
                tweet.get('state_code'),
                tweet.get('state_name'),
                tweet.get('context'),
                tweet.get('likes', 0),
                tweet.get('retweets', 0),
                tweet.get('replies', 0),
                tweet.get('views', 0)
            ))
            
            conn.commit()
            conn.close()
            logger.db_stored(tweet['id'])
            
        except Exception as e:
            logger.db_failed(tweet.get('id', 'unknown'), str(e))

    def start_consuming(self):
        """Start consuming tweets and storing in database"""
        logger.system_event("DB_WRITER_STARTING")
        
        try:
            for message in self.consumer:
                if not self.running:
                    break
                    
                try:
                    tweet = message.value
                    self.store_tweet(tweet)
                except Exception as e:
                    logger.error(f"❌ Error processing tweet: {e}")
                    
        except KafkaError as e:
            logger.error(f"❌ Kafka error: {e}")
        finally:
            self.close()

    def stop(self):
        self.running = False

    def close(self):
        if self.consumer:
            self.consumer.close()
            logger.system_event("DB_WRITER_CLOSED")

def signal_handler(signum, frame):
    logger.system_event("SHUTDOWN_SIGNAL_RECEIVED")
    writer.stop()

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    writer = DatabaseWriter()
    try:
        writer.start_consuming()
    except KeyboardInterrupt:
        logger.system_event("DB_WRITER_STOPPING")
    finally:
        writer.close()

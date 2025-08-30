#!/usr/bin/env python3
"""
Tweet Consumer
Receives tweets from Kafka and logs them
"""

import json
import logging
from kafka import KafkaConsumer
from kafka.errors import KafkaError
import signal
import sys
import os

# Set up logging - using the logs directory in the same folder as this script
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [CONSUMER] %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'tweet_consumer.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TweetConsumer:
    def __init__(self, bootstrap_servers=['localhost:9092'], topic='tweets'):
        """Initialize consumer"""
        self.topic = topic
        self.running = True
        
        try:
            self.consumer = KafkaConsumer(
                self.topic,
                bootstrap_servers=bootstrap_servers,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='latest',
                group_id='tweet-consumer-group'
            )
            logger.info(f"✅ Connected to Kafka at {bootstrap_servers}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Kafka: {e}")
            raise

    def start_consuming(self):
        """Start consuming tweets"""
        logger.info(f"👂 Listening for tweets on topic: {self.topic}")
        
        try:
            for message in self.consumer:
                if not self.running:
                    break
                    
                try:
                    tweet = message.value
                    logger.info("\n📥 Received Tweet:")
                    logger.info("=" * 50)
                    logger.info(f"From: {tweet['username']} in {tweet['location']}")
                    logger.info(f"Keyword: {tweet['keyword']}")
                    logger.info(f"Tweet: {tweet['raw_text']}")
                    logger.info(f"Engagement: ❤️ {tweet['likes']} | 🔄 {tweet['retweets']} | 💬 {tweet['replies']}")
                    logger.info(f"Kafka - Partition: {message.partition}, Offset: {message.offset}")
                    logger.info("=" * 50)
                    
                except Exception as e:
                    logger.error(f"❌ Error processing tweet: {e}")
                    
        except KafkaError as e:
            logger.error(f"❌ Kafka error: {e}")
        finally:
            self.close()

    def stop(self):
        """Stop consuming"""
        self.running = False

    def close(self):
        """Close consumer"""
        if self.consumer:
            self.consumer.close()
            logger.info("👋 Consumer closed")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info("🛑 Received signal to stop")
    consumer.stop()

if __name__ == "__main__":
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and start consumer
    consumer = TweetConsumer()
    try:
        consumer.start_consuming()
    except KeyboardInterrupt:
        logger.info("👋 Stopping consumer")
    finally:
        consumer.close()

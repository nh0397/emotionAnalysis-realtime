#!/usr/bin/env python3
"""
Unified Logger - Single logging system for the entire tweet pipeline
"""

import logging
import os
from datetime import datetime

class UnifiedLogger:
    def __init__(self, log_file="logs/system.log"):
        self.log_file = log_file
        
        # Ensure logs directory exists
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s | %(message)s',
            datefmt='%H:%M:%S',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()  # Also print to console
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def tweet_generated(self, tweet_id, keyword, state, text_preview):
        """Log when a tweet is generated"""
        self.logger.info(f"GENERATED | ID:{tweet_id} | {keyword} | {state} | {text_preview}")
    
    def kafka_sent(self, tweet_id, topic):
        """Log when tweet is sent to Kafka"""
        self.logger.info(f"KAFKA_SENT | ID:{tweet_id} | Topic:{topic}")
    
    def kafka_received(self, tweet_id, state):
        """Log when tweet is received from Kafka"""
        self.logger.info(f"KAFKA_RECV | ID:{tweet_id} | {state}")
    
    def db_stored(self, tweet_id, state, emotion):
        """Log when tweet is stored in database"""
        self.logger.info(f"DB_STORED | ID:{tweet_id} | {state} | Emotion:{emotion}")
    
    def error(self, component, error_msg):
        """Log errors"""
        self.logger.error(f"ERROR | {component} | {error_msg}")
    
    def system_event(self, event, details=""):
        """Log system events"""
        self.logger.info(f"SYSTEM | {event} | {details}")

# Global logger instance
logger = UnifiedLogger()

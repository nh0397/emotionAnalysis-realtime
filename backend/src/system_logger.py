#!/usr/bin/env python3
"""
Centralized System Logger
Clean, structured logging for the entire tweet system
"""

import logging
import os
from datetime import datetime
import json

class SystemLogger:
    def __init__(self, component_name):
        self.component = component_name
        
        # Create logs directory
        log_dir = os.path.join(os.path.dirname(__file__), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Set up logger
        self.logger = logging.getLogger(component_name)
        self.logger.setLevel(logging.INFO)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # File handler
        file_handler = logging.FileHandler(
            os.path.join(log_dir, f'{component_name}.log')
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        
        # Simple, clean format
        formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
            datefmt='%H:%M:%S'
        )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def tweet_generated(self, tweet_id, keyword, state_code, tweet_text):
        """Log tweet generation"""
        self.logger.info(f"GENERATED | ID:{tweet_id} | {keyword} | {state_code} | {tweet_text[:50]}...")
    
    def kafka_sent(self, tweet_id, topic, partition, offset):
        """Log Kafka send success"""
        self.logger.info(f"KAFKA_SENT | ID:{tweet_id} | Topic:{topic} | Partition:{partition} | Offset:{offset}")
    
    def kafka_failed(self, tweet_id, error):
        """Log Kafka send failure"""
        self.logger.error(f"KAFKA_FAILED | ID:{tweet_id} | Error:{error}")
    
    def db_stored(self, tweet_id):
        """Log database storage success"""
        self.logger.info(f"DB_STORED | ID:{tweet_id}")
    
    def db_failed(self, tweet_id, error):
        """Log database storage failure"""
        self.logger.error(f"DB_FAILED | ID:{tweet_id} | Error:{error}")
    
    def ui_streamed(self, tweet_id):
        """Log UI streaming"""
        self.logger.info(f"UI_STREAMED | ID:{tweet_id}")
    
    def system_event(self, event, details=""):
        """Log general system events"""
        self.logger.info(f"SYSTEM | {event} | {details}")
    
    def error(self, message):
        """Log errors"""
        self.logger.error(f"ERROR | {message}")
    
    def debug(self, message):
        """Log debug info"""
        self.logger.debug(f"DEBUG | {message}")
    
    def info(self, message):
        """Log info messages"""
        self.logger.info(f"INFO | {message}")
    
    def warning(self, message):
        """Log warnings"""
        self.logger.warning(f"WARNING | {message}")

# Create loggers for each component
tweet_logger = SystemLogger("tweet_generator")
kafka_logger = SystemLogger("kafka_handler") 
db_logger = SystemLogger("database")
ui_logger = SystemLogger("ui_streamer")

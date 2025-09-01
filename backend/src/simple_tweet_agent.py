#!/usr/bin/env python3
"""
Tweet Generator with Kafka Integration
Generates tweets and sends them directly to Kafka
"""

import json
import random
import time
import logging
from datetime import datetime
from typing import Dict, Any
from ollama import chat, ChatResponse
from kafka import KafkaProducer
from kafka.errors import KafkaError
from system_logger import tweet_logger as logger
from nlp_pipeline import CustomEmotionAnalyzer


class TweetGenerator:
    def __init__(self, bootstrap_servers=['localhost:9092'], topic='tweets'):
        self.tweet_id_counter = 1
        self.topic = topic
        
        # Initialize NLP Pipeline
        logger.system_event("INITIALIZING_NLP_PIPELINE")
        start_time = time.time()
        try:
            self.emotion_analyzer = CustomEmotionAnalyzer()
            nlp_load_time = time.time() - start_time
            logger.system_event("NLP_PIPELINE_LOADED", f"Load time: {nlp_load_time:.2f}s")
        except Exception as e:
            logger.error(f"Failed to initialize NLP pipeline: {e}")
            raise
        
        # Initialize Kafka producer
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            logger.system_event("KAFKA_CONNECTED", f"Bootstrap: {bootstrap_servers}")
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            raise
        
        # Test keywords (these would come from UI later)
        self.keywords = [
            "AI ethics",
            "remote work culture",
            "tech layoffs",
            "startup funding",
            "ChatGPT updates",
            "coding practices",
            "tech interviews",
            "developer burnout"
        ]
        
        # US State abbreviations and names
        self.states = {
            'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas',
            'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware',
            'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho',
            'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas',
            'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
            'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi',
            'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada',
            'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York',
            'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma',
            'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
            'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah',
            'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia',
            'WI': 'Wisconsin', 'WY': 'Wyoming'
        }

    def generate_tweet_content(self, keyword: str, state: str) -> str:
        """Generate tweet content using Ollama"""
        prompt = f"""Generate a tweet about {keyword}.
        - Be as expressive and raw as possible
        - Max 280 characters
        - Include hashtags
        - Be authentic and tech-focused
        - End with ({state})
        """
        
        try:
            response: ChatResponse = chat(
                model='llama3.2:3b',
                messages=[{
                    'role': 'user',
                    'content': prompt
                }]
            )
            
            tweet_text = response["message"]["content"].strip()
            
            # Ensure state tag is included
            if f"({state})" not in tweet_text:
                tweet_text = tweet_text.rstrip() + f" ({state})"
                
            return tweet_text
                
        except Exception as e:
            logger.error(f"Error generating tweet: {e}")
            return f"Thoughts on {keyword}... 🤔 ({state})"

    def generate_and_send_tweet(self, keyword: str = None) -> bool:
        """Generate a tweet and send it to Kafka with NLP processing"""
        if keyword is None:
            keyword = random.choice(self.keywords)
            
        state_code = random.choice(list(self.states.keys()))
        state_name = self.states[state_code]
        
        # Start timing the entire process
        total_start_time = time.time()
        
        # Generate tweet content
        generation_start = time.time()
        tweet_text = self.generate_tweet_content(keyword, state_code)
        generation_time = time.time() - generation_start
        
        # Process through NLP pipeline
        nlp_start_time = time.time()
        try:
            emotion_results = self.emotion_analyzer.analyze_emotion(tweet_text)
            nlp_time = time.time() - nlp_start_time
            
            # Log NLP processing time
            logger.system_event("NLP_PROCESSED", f"Tweet {self.tweet_id_counter}: {nlp_time:.3f}s")
            
        except Exception as e:
            nlp_time = time.time() - nlp_start_time
            logger.error(f"NLP processing failed for tweet {self.tweet_id_counter}: {e}")
            # Fallback emotion values
            emotion_results = {
                'anger': 0.0, 'fear': 0.0, 'positive': 0.5, 'sadness': 0.0,
                'surprise': 0.0, 'joy': 0.5, 'anticipation': 0.0, 'trust': 0.0,
                'negative': 0.0, 'disgust': 0.0, 'dominant_emotion': 'positive',
                'confidence': 0.5, 'compound': 0.0
            }
        
        # Create tweet object with NLP results
        tweet = {
            "id": self.tweet_id_counter,
            "username": f"tech_{random.randint(1000, 9999)}",
            "raw_text": tweet_text,
            "timestamp": datetime.now().isoformat(),
            "state_code": state_code,
            "state_name": state_name,
            "context": f"{keyword}",
            "likes": random.randint(0, 1000),
            "retweets": random.randint(0, 200),
            "replies": random.randint(0, 50),
            "views": random.randint(500, 5000),
            # Add emotion analysis results
            **emotion_results,
            # Add performance metrics
            "processing_times": {
                "generation_ms": round(generation_time * 1000, 1),
                "nlp_ms": round(nlp_time * 1000, 1),
                "total_ms": round((time.time() - total_start_time) * 1000, 1)
            }
        }
        
        # Log tweet generation with timing
        total_time = time.time() - total_start_time
        logger.tweet_generated(
            tweet['id'], 
            tweet['context'], 
            tweet['state_code'], 
            f"{tweet['raw_text'][:50]}... | Gen: {generation_time:.2f}s, NLP: {nlp_time:.3f}s, Total: {total_time:.3f}s"
        )
        
        # Send to Kafka
        try:
            future = self.producer.send(self.topic, value=tweet)
            record_metadata = future.get(timeout=10)
            logger.kafka_sent(tweet['id'], self.topic, record_metadata.partition, record_metadata.offset)
            self.tweet_id_counter += 1
            return True
        except KafkaError as e:
            logger.kafka_failed(tweet['id'], str(e))
            return False

    def close(self):
        """Close Kafka producer"""
        if self.producer:
            self.producer.close()
            logger.system_event("KAFKA_PRODUCER_CLOSED")

def main():
    generator = TweetGenerator()
    logger.system_event("TWEET_GENERATOR_STARTED", f"Keywords: {len(generator.keywords)}")
    
    try:
        while True:
            generator.generate_and_send_tweet()
            time.sleep(10)
            
    except KeyboardInterrupt:
        logger.system_event("TWEET_GENERATOR_STOPPED")
    finally:
        generator.close()

if __name__ == "__main__":
    main()
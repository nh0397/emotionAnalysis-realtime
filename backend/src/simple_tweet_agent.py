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
from unified_logger import logger
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
            
            # DEBUG: Log the actual emotion values being generated
            logger.system_event("NLP_EMOTION_DEBUG", 
                f"Tweet {self.tweet_id_counter}: anger={emotion_results.get('anger', 0)}, joy={emotion_results.get('joy', 0)}, positive={emotion_results.get('positive', 0)}, dominant={emotion_results.get('dominant_emotion', 'unknown')}")
            
            # Log NLP processing time
            logger.system_event("NLP_PROCESSED", f"Tweet {self.tweet_id_counter}: {nlp_time:.3f}s")
            
        except Exception as e:
            nlp_time = time.time() - nlp_start_time
            logger.error("TWEET_GENERATOR", f"NLP processing failed for tweet {self.tweet_id_counter}: {e}")
            # Fallback emotion values
            emotion_results = {
                'anger': 0.1, 'fear': 0.1, 'positive': 0.5, 'sadness': 0.1,
                'surprise': 0.1, 'joy': 0.3, 'anticipation': 0.1, 'trust': 0.2,
                'negative': 0.1, 'disgust': 0.05, 'dominant_emotion': 'positive',
                'confidence': 0.5, 'compound': 0.2
            }
            logger.system_event("NLP_FALLBACK_DEBUG", f"Tweet {self.tweet_id_counter}: Using fallback emotions")
        
        
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
            **emotion_results
        }
        
        # Log tweet generation
        logger.tweet_generated(tweet['id'], tweet['context'], tweet['state_code'], tweet['raw_text'][:50])
        
        # Send to Kafka
        try:
            future = self.producer.send(self.topic, value=tweet)
            record_metadata = future.get(timeout=10)
            logger.kafka_sent(tweet['id'], self.topic)
            self.tweet_id_counter += 1
            return True
        except KafkaError as e:
            logger.error("TWEET_GENERATOR", f"Kafka failed for tweet {tweet['id']}: {e}")
            return False

    def close(self):
        """Close Kafka producer"""
        if self.producer:
            self.producer.close()
            logger.system_event("KAFKA_PRODUCER_CLOSED")

def console_demo():
    """Console demo mode - shows NLP results without Kafka"""
    print("🚀 TecVis 2.0 Tweet Generator with NLP Pipeline")
    print("📊 Console Demo Mode - No Kafka/DB")
    print("=" * 60)
    
    # Initialize just the NLP components (no Kafka)
    print("🧠 Loading NLP models...")
    start_time = time.time()
    
    try:
        emotion_analyzer = CustomEmotionAnalyzer()
        load_time = time.time() - start_time
        print(f"✅ NLP models loaded in {load_time:.2f}s")
    except Exception as e:
        print(f"❌ Failed to load NLP models: {e}")
        return
    
    # Tweet generation components
    keywords = [
        "AI ethics", "remote work culture", "tech layoffs", "startup funding",
        "ChatGPT updates", "coding practices", "tech interviews", "developer burnout"
    ]
    
    states = {
        'CA': 'California', 'NY': 'New York', 'TX': 'Texas', 'FL': 'Florida',
        'WA': 'Washington', 'MA': 'Massachusetts', 'IL': 'Illinois', 'PA': 'Pennsylvania'
    }
    
    tweet_counter = 1
    
    print(f"\n🎯 Starting tweet generation (Ctrl+C to stop)")
    print("-" * 60)
    
    try:
        while True:
            # Pick random keyword and state
            keyword = random.choice(keywords)
            state_code = random.choice(list(states.keys()))
            state_name = states[state_code]
            
            print(f"\n📝 Tweet #{tweet_counter}")
            print(f"🏷️  Keyword: {keyword}")
            print(f"📍 Location: {state_name} ({state_code})")
            
            # Generate tweet text
            gen_start = time.time()
            try:
                prompt = f"""Generate a tweet about {keyword}.
                - Be expressive and authentic
                - Max 280 characters
                - Include hashtags
                - Be tech-focused
                - End with ({state_code})
                """
                
                response: ChatResponse = chat(
                    model='llama3.2:3b',
                    messages=[{'role': 'user', 'content': prompt}]
                )
                
                tweet_text = response["message"]["content"].strip()
                if f"({state_code})" not in tweet_text:
                    tweet_text = tweet_text.rstrip() + f" ({state_code})"
                    
            except Exception as e:
                tweet_text = f"Thoughts on {keyword}... 🤔 ({state_code})"
                print(f"⚠️  Ollama error: {e}")
                
            gen_time = time.time() - gen_start
            
            print(f"📄 Generated Text: {tweet_text}")
            print(f"⏱️  Generation Time: {gen_time:.2f}s")
            
            # Analyze emotions
            nlp_start = time.time()
            try:
                emotions = emotion_analyzer.analyze_emotion(tweet_text)
                nlp_time = time.time() - nlp_start
                
                print(f"🧠 NLP Analysis Time: {nlp_time:.3f}s")
                print(f"🎭 Dominant Emotion: {emotions['dominant_emotion']} (confidence: {emotions['confidence']:.3f})")
                
                # Display all emotions with visual bars
                print("📊 All Emotion Scores:")
                emotion_names = ['anger', 'fear', 'positive', 'sadness', 'surprise', 
                               'joy', 'anticipation', 'trust', 'negative', 'disgust']
                
                for emotion in emotion_names:
                    score = emotions.get(emotion, 0.0)
                    bar = "█" * int(score * 20)  # Visual bar
                    print(f"   {emotion:12}: {score:.3f} {bar}")
                
                # Sentiment summary
                compound = emotions.get('compound', 0.0)
                if compound >= 0.05:
                    sentiment = "Positive 😊"
                elif compound <= -0.05:
                    sentiment = "Negative 😔"
                else:
                    sentiment = "Neutral 😐"
                    
                print(f"💭 Overall Sentiment: {sentiment} ({compound:.3f})")
                
            except Exception as e:
                nlp_time = time.time() - nlp_start
                print(f"❌ NLP analysis failed: {e}")
            
            total_time = gen_time + nlp_time
            print(f"⚡ Total Processing: {total_time:.3f}s")
            print("-" * 60)
            
            tweet_counter += 1
            
            # Wait before next tweet
            print(f"⏳ Waiting 10 seconds for next tweet...\n")
            time.sleep(10)
            
    except KeyboardInterrupt:
        print(f"\n🛑 Demo stopped by user")
        print(f"📈 Generated {tweet_counter - 1} tweets with full NLP analysis")

def main():
    """Main function with mode selection"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        console_demo()
    else:
        # Original Kafka mode
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
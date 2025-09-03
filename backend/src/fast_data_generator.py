#!/usr/bin/env python3
"""
Fast Data Generator - Generate millions of diverse tweet records (2019-2025)
Optimized for high-performance bulk insertion
"""

import psycopg2
import psycopg2.extras
import random
import json
from datetime import datetime, timedelta
import multiprocessing as mp
import numpy as np
from tqdm import tqdm
import time
from ollama import chat, ChatResponse
from nlp_pipeline import CustomEmotionAnalyzer

# Database configuration
DB_PARAMS = {
    'host': 'localhost',
    'port': 5432,
    'database': 'tweetdb', 
    'user': 'tweetuser',
    'password': 'tweetpass'
}

# US State codes and full names
US_STATES = {
    'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas', 'CA': 'California',
    'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware', 'FL': 'Florida', 'GA': 'Georgia',
    'HI': 'Hawaii', 'ID': 'Idaho', 'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa',
    'KS': 'Kansas', 'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
    'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi', 'MO': 'Missouri',
    'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada', 'NH': 'New Hampshire', 'NJ': 'New Jersey',
    'NM': 'New Mexico', 'NY': 'New York', 'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio',
    'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
    'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah', 'VT': 'Vermont',
    'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia', 'WI': 'Wisconsin', 'WY': 'Wyoming'
}

# Tech-related contexts with realistic distributions
TECH_CONTEXTS = [
    'AI', 'blockchain', 'cybersecurity', 'cloud computing', 'data science',
    'machine learning', 'IoT', 'cryptocurrency', 'software development', 'mobile apps',
    'web development', 'DevOps', 'automation', 'robotics', 'VR/AR',
    'social media', 'e-commerce', 'fintech', 'healthtech', 'edtech',
    'gaming', 'streaming', 'electric vehicles', 'renewable energy', 'space tech'
]

# Realistic username patterns
USERNAME_PATTERNS = [
    'tech', 'dev', 'code', 'data', 'ai', 'cyber', 'cloud', 'mobile', 'web', 'app',
    'digital', 'smart', 'future', 'innovation', 'startup', 'geek', 'nerd', 'pro'
]

class FastDataGenerator:
    def __init__(self, batch_size=10000, use_nlp=True):
        self.batch_size = batch_size
        self.use_nlp = use_nlp
        
        # Initialize NLP pipeline if requested
        if self.use_nlp:
            print("🧠 Loading NLP models for realistic emotion analysis...")
            try:
                self.emotion_analyzer = CustomEmotionAnalyzer()
                print("✅ NLP models loaded successfully!")
            except Exception as e:
                print(f"❌ Failed to load NLP models: {e}")
                print("🔄 Falling back to realistic synthetic emotions...")
                self.use_nlp = False
                self.emotion_analyzer = None
        else:
            self.emotion_analyzer = None
    
    def generate_tweet_content_with_ollama(self, context, state_code):
        """Generate realistic tweet content using Ollama (like the working system)"""
        prompt = f"""Generate a tweet about {context}.
        - Be as expressive and raw as possible
        - Max 280 characters
        - Include hashtags
        - Be authentic and tech-focused
        - End with ({state_code})
        """
        
        try:
            response: ChatResponse = chat(
                model='llama3.2:3b',
                messages=[{
                    'role': 'user',
                    'content': prompt
                }],
                options={'temperature': 0.9}  # More creative/diverse
            )
            
            tweet_text = response["message"]["content"].strip()
            
            # Ensure state tag is included
            if f"({state_code})" not in tweet_text:
                tweet_text = tweet_text.rstrip() + f" ({state_code})"
                
            return tweet_text
                
        except Exception as e:
            # Fallback to template if Ollama fails
            templates = [
                f"Excited about the latest {context} developments! The future is here 🚀 ({state_code})",
                f"Working on a new {context} project. Technology is amazing! #tech ({state_code})",
                f"Just attended a {context} conference. Mind = blown 🤯 ({state_code})",
                f"The {context} industry is evolving so fast. Can't keep up! ({state_code})",
                f"New {context} tools are making development much easier ({state_code})",
                f"Concerns about {context} security issues. We need better standards ({state_code})",
                f"Amazing {context} breakthrough announced today! Game changer 💡 ({state_code})",
                f"Learning {context} has been challenging but rewarding ({state_code})"
            ]
            return random.choice(templates)
    
    def analyze_emotions_with_nlp(self, tweet_text):
        """Analyze emotions using the real NLP pipeline"""
        if not self.use_nlp or not self.emotion_analyzer:
            return None
            
        try:
            # Use the same emotion analysis as the working system
            emotion_results = self.emotion_analyzer.analyze_emotion(tweet_text)
            
            # Extract the 10 emotion scores
            emotions = {
                'anger': emotion_results.get('anger', 0.1),
                'fear': emotion_results.get('fear', 0.1),
                'sadness': emotion_results.get('sadness', 0.1),
                'surprise': emotion_results.get('surprise', 0.1),
                'joy': emotion_results.get('joy', 0.1),
                'anticipation': emotion_results.get('anticipation', 0.1),
                'trust': emotion_results.get('trust', 0.1),
                'disgust': emotion_results.get('disgust', 0.1),
                'positive': emotion_results.get('positive', 0.2),
                'negative': emotion_results.get('negative', 0.1)
            }
            
            return emotions
            
        except Exception as e:
            print(f"⚠️  NLP analysis failed: {e}")
            return None
        
    def generate_realistic_emotions(self, context, year, month):
        """Generate realistic emotion scores based on context and time trends"""
        base_emotions = {
            'anger': 0.1, 'fear': 0.15, 'sadness': 0.12, 'surprise': 0.08,
            'joy': 0.25, 'anticipation': 0.18, 'trust': 0.20, 'disgust': 0.08,
            'positive': 0.35, 'negative': 0.15
        }
        
        # Context-based modifiers
        context_modifiers = {
            'AI': {'anticipation': 0.1, 'fear': 0.05, 'positive': 0.08},
            'cybersecurity': {'fear': 0.15, 'anger': 0.08, 'trust': -0.05},
            'cryptocurrency': {'anticipation': 0.12, 'surprise': 0.10, 'fear': 0.08},
            'gaming': {'joy': 0.15, 'anticipation': 0.08, 'positive': 0.12},
            'social media': {'anger': 0.08, 'sadness': 0.05, 'negative': 0.10}
        }
        
        # Time-based trends (2019-2025)
        if year >= 2020 and year <= 2021:  # COVID impact
            base_emotions['fear'] += 0.10
            base_emotions['sadness'] += 0.08
            base_emotions['negative'] += 0.12
        elif year >= 2022:  # Recovery/optimism
            base_emotions['anticipation'] += 0.05
            base_emotions['positive'] += 0.08
            
        # Apply context modifiers
        if context in context_modifiers:
            for emotion, modifier in context_modifiers[context].items():
                base_emotions[emotion] = max(0, min(1, base_emotions[emotion] + modifier))
        
        # Add realistic noise
        emotions = {}
        for emotion, base_value in base_emotions.items():
            noise = np.random.normal(0, 0.05)  # Small random variation
            emotions[emotion] = max(0, min(1, base_value + noise))
            
        return emotions
    
    def generate_batch(self, start_date, end_date, batch_id):
        """Generate a batch of realistic tweets"""
        tweets = []
        current_date = start_date
        
        for i in range(self.batch_size):
            # Random timestamp within range
            days_diff = (end_date - start_date).days
            random_days = random.randint(0, days_diff)
            tweet_date = start_date + timedelta(days=random_days)
            tweet_time = tweet_date.replace(
                hour=random.randint(0, 23),
                minute=random.randint(0, 59),
                second=random.randint(0, 59)
            )
            
            # Select state (weighted toward populous states)
            state_weights = {
                'CA': 12, 'TX': 9, 'FL': 7, 'NY': 6, 'PA': 4, 'IL': 4, 'OH': 4,
                'GA': 3, 'NC': 3, 'MI': 3, 'NJ': 3, 'VA': 2, 'WA': 2, 'AZ': 2,
                'MA': 2, 'TN': 2, 'IN': 2, 'MO': 2, 'MD': 2, 'WI': 2, 'CO': 2,
                'MN': 2, 'SC': 2, 'AL': 2, 'LA': 2, 'KY': 1, 'OR': 1, 'OK': 1,
                'CT': 1, 'UT': 1, 'IA': 1, 'NV': 1, 'AR': 1, 'MS': 1, 'KS': 1,
                'NM': 1, 'NE': 1, 'WV': 1, 'ID': 1, 'HI': 1, 'NH': 1, 'ME': 1,
                'MT': 1, 'RI': 1, 'DE': 1, 'SD': 1, 'ND': 1, 'AK': 1, 'VT': 1, 'WY': 1
            }
            
            state_code = random.choices(
                list(state_weights.keys()),
                weights=list(state_weights.values())
            )[0]
            
            # Generate realistic username
            username_base = random.choice(USERNAME_PATTERNS)
            username = f"{username_base}_{random.choice(['user', 'guru', 'expert', 'fan', 'geek'])}_{random.randint(100, 9999)}"
            
            # Select context
            context = random.choice(TECH_CONTEXTS)
            
            # Generate realistic engagement metrics (log-normal distribution)
            likes = max(1, int(np.random.lognormal(3, 1.5)))
            retweets = max(0, int(likes * np.random.beta(2, 8)))
            replies = max(0, int(likes * np.random.beta(1.5, 10)))
            views = max(likes, int(likes * np.random.lognormal(2, 0.8)))
            
            # Generate realistic tweet text using NLP pipeline
            if self.use_nlp:
                # Use Ollama + NLP like the working system
                raw_text = self.generate_tweet_content_with_ollama(context, state_code)
                
                # Analyze emotions with real NLP pipeline
                nlp_emotions = self.analyze_emotions_with_nlp(raw_text)
                
                if nlp_emotions:
                    emotions = nlp_emotions
                    # Add a small indicator that this used real NLP
                    if i % 100 == 0:  # Log every 100th tweet
                        print(f"📊 Tweet {i}: Real NLP - {emotions.get('dominant_emotion', 'N/A')} emotion detected")
                else:
                    # Fallback to synthetic if NLP fails
                    emotions = self.generate_realistic_emotions(context, tweet_time.year, tweet_time.month)
            else:
                # Use template + synthetic emotions for speed
                templates = [
                    f"Excited about the latest {context} developments! The future is here 🚀 ({state_code})",
                    f"Working on a new {context} project. Technology is amazing! #tech ({state_code})",
                    f"Just attended a {context} conference. Mind = blown 🤯 ({state_code})",
                    f"The {context} industry is evolving so fast. Can't keep up! ({state_code})",
                    f"New {context} tools are making development much easier ({state_code})",
                    f"Concerns about {context} security issues. We need better standards ({state_code})",
                    f"Amazing {context} breakthrough announced today! Game changer 💡 ({state_code})",
                    f"Learning {context} has been challenging but rewarding ({state_code})"
                ]
                
                raw_text = random.choice(templates)
                emotions = self.generate_realistic_emotions(context, tweet_time.year, tweet_time.month)
            
            # Create tweet record
            tweet = {
                'id': f"{batch_id}_{i:06d}",
                'raw_text': raw_text,
                'username': username,
                'created_at': tweet_time,
                'likes': likes,
                'retweets': retweets,
                'replies': replies,
                'views': views,
                'state_code': state_code,
                'state_name': US_STATES[state_code],
                'context': context,
                **emotions
            }
            
            tweets.append(tweet)
            
        return tweets
    
    def insert_batch(self, tweets):
        """Insert a batch of tweets into database using COPY for speed"""
        try:
            conn = psycopg2.connect(**DB_PARAMS)
            cursor = conn.cursor()
            
            # Prepare data for COPY
            columns = [
                'id', 'raw_text', 'username', 'created_at', 'likes', 'retweets', 
                'replies', 'views', 'state_code', 'state_name', 'context',
                'anger', 'fear', 'sadness', 'surprise', 'joy', 'anticipation', 
                'trust', 'disgust', 'positive', 'negative'
            ]
            
            # Use COPY for maximum speed
            copy_data = []
            for tweet in tweets:
                row_data = [
                    tweet['id'], tweet['raw_text'], tweet['username'], 
                    tweet['created_at'], tweet['likes'], tweet['retweets'],
                    tweet['replies'], tweet['views'], tweet['state_code'], 
                    tweet['state_name'], tweet['context'],
                    tweet['anger'], tweet['fear'], tweet['sadness'], 
                    tweet['surprise'], tweet['joy'], tweet['anticipation'],
                    tweet['trust'], tweet['disgust'], tweet['positive'], tweet['negative']
                ]
                copy_data.append(row_data)
            
            # Execute bulk insert with COPY
            psycopg2.extras.execute_batch(
                cursor,
                """INSERT INTO tweets (id, raw_text, username, created_at, likes, retweets, 
                   replies, views, state_code, state_name, context, anger, fear, sadness, 
                   surprise, joy, anticipation, trust, disgust, positive, negative) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                copy_data,
                page_size=1000
            )
            
            conn.commit()
            conn.close()
            return len(tweets)
            
        except Exception as e:
            print(f"❌ Error inserting batch: {e}")
            return 0

def worker_process(args):
    """Worker process for parallel data generation"""
    worker_id, start_date, end_date, num_batches, batch_size, use_nlp = args
    
    generator = FastDataGenerator(batch_size, use_nlp)
    total_inserted = 0
    
    for batch_num in range(num_batches):
        batch_id = f"{worker_id}_{batch_num}"
        tweets = generator.generate_batch(start_date, end_date, batch_id)
        inserted = generator.insert_batch(tweets)
        total_inserted += inserted
        
        if batch_num % 10 == 0:
            print(f"Worker {worker_id}: Processed {batch_num}/{num_batches} batches ({total_inserted:,} records)")
    
    return total_inserted

def generate_massive_dataset(target_records=5_000_000, num_workers=8, batch_size=10000, use_nlp=False):
    """Generate millions of records using parallel processing"""
    
    print(f"🚀 FAST DATA GENERATOR - Target: {target_records:,} records")
    print(f"📊 Configuration: {num_workers} workers, {batch_size:,} records per batch")
    
    # Date range: 2019-2025
    start_date = datetime(2019, 1, 1)
    end_date = datetime(2025, 12, 31)
    
    # Calculate batches per worker
    total_batches = target_records // batch_size
    batches_per_worker = total_batches // num_workers
    
    print(f"📈 Total batches: {total_batches}, Per worker: {batches_per_worker}")
    
    # Prepare worker arguments
    worker_args = []
    for worker_id in range(num_workers):
        worker_args.append((worker_id, start_date, end_date, batches_per_worker, batch_size, use_nlp))
    
    # Start parallel processing
    start_time = time.time()
    
    print("🔥 Starting parallel data generation...")
    with mp.Pool(num_workers) as pool:
        results = pool.map(worker_process, worker_args)
    
    total_generated = sum(results)
    elapsed_time = time.time() - start_time
    
    print(f"\n✅ DATA GENERATION COMPLETE!")
    print(f"📊 Records generated: {total_generated:,}")
    print(f"⏱️  Time elapsed: {elapsed_time:.2f} seconds")
    print(f"🚀 Speed: {total_generated/elapsed_time:,.0f} records/second")
    
    # Update emotion aggregates
    print("\n🔄 Updating emotion aggregates...")
    update_emotion_aggregates()
    
    print("🎯 All done! Your database now has millions of diverse records from 2019-2025")

def update_emotion_aggregates():
    """Update the emotion_aggregates table with new data"""
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cursor = conn.cursor()
        
        # Recreate emotion_aggregates table
        cursor.execute("DROP TABLE IF EXISTS emotion_aggregates")
        cursor.execute("""
            CREATE TABLE emotion_aggregates AS
            SELECT 
                state_code,
                AVG(anger) as anger_avg,
                AVG(joy) as joy_avg,
                AVG(fear) as fear_avg,
                AVG(sadness) as sadness_avg,
                AVG(surprise) as surprise_avg,
                AVG(positive) as positive_avg,
                AVG(negative) as negative_avg,
                AVG(anticipation) as anticipation_avg,
                AVG(trust) as trust_avg,
                AVG(disgust) as disgust_avg,
                COUNT(*) as tweet_count,
                MAX(created_at) as last_updated
            FROM tweets 
            GROUP BY state_code
        """)
        
        conn.commit()
        conn.close()
        print("✅ Emotion aggregates updated!")
        
    except Exception as e:
        print(f"❌ Error updating aggregates: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate massive tweet dataset with real NLP')
    parser.add_argument('--records', type=int, default=5_000_000, help='Number of records to generate')
    parser.add_argument('--workers', type=int, default=8, help='Number of parallel workers')
    parser.add_argument('--batch-size', type=int, default=10000, help='Records per batch')
    parser.add_argument('--use-nlp', action='store_true', default=False, 
                       help='Use real NLP pipeline (Ollama + CustomEmotionAnalyzer) - slower but realistic')
    parser.add_argument('--fast-mode', action='store_true', default=False,
                       help='Use synthetic emotions only for maximum speed')
    
    args = parser.parse_args()
    
    # Determine NLP usage
    use_nlp = args.use_nlp and not args.fast_mode
    if use_nlp:
        print("🧠 NLP Mode: Using real Ollama + CustomEmotionAnalyzer (slower, realistic)")
        print("⚠️  Note: This mode requires Ollama to be running locally")
    else:
        print("⚡ Fast Mode: Using synthetic emotions (faster, less realistic)")
    
    generate_massive_dataset(args.records, args.workers, args.batch_size, use_nlp)

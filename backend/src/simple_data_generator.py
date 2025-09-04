#!/usr/bin/env python3
"""
Simple Data Generator
Generate 10 entries per state per day for the last year (Jan 1, 2025 to today)
Total: 50 states × 10 entries × 245 days = 122,500 records
Uses Ollama for tweet generation and BERT NLP pipeline for emotion analysis
"""

import psycopg2
import random
from datetime import datetime, timedelta
import time
import ollama
import sys
from nlp_pipeline import CustomEmotionAnalyzer

# Database configuration
DB_PARAMS = {
    'host': 'localhost',
    'port': 5432,
    'database': 'tweetdb', 
    'user': 'tweetuser',
    'password': 'tweetpass'
}

# US State codes and names
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

# Tech contexts
TECH_CONTEXTS = [
    'AI', 'blockchain', 'cybersecurity', 'cloud computing', 'data science',
    'machine learning', 'IoT', 'cryptocurrency', 'software development', 'mobile apps',
    'web development', 'DevOps', 'automation', 'robotics', 'VR/AR',
    'social media', 'e-commerce', 'fintech', 'healthtech', 'edtech',
    'gaming', 'streaming', 'electric vehicles', 'renewable energy', 'space tech'
]

class SimpleDataGenerator:
    def __init__(self):
        """Initialize the data generator with NLP components"""
        print("🔧 Initializing NLP components...")
        try:
            self.emotion_analyzer = CustomEmotionAnalyzer()
            print("✅ CustomEmotionAnalyzer initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize CustomEmotionAnalyzer: {e}")
            print("⚠️  Falling back to synthetic emotions")
            self.emotion_analyzer = None
    
    def cleanup_database(self):
        """Clean up database and reset sequences"""
        try:
            print("🗑️  Cleaning up database...")
            conn = psycopg2.connect(**DB_PARAMS)
            cursor = conn.cursor()
            
            # Truncate tables
            cursor.execute("TRUNCATE TABLE tweets RESTART IDENTITY CASCADE")
            cursor.execute("TRUNCATE TABLE emotion_aggregates RESTART IDENTITY CASCADE")
            
            conn.commit()
            conn.close()
            print("✅ Database cleaned successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Database cleanup failed: {e}")
            return False
    
    def generate_tweet_content_with_ollama(self, context, state_code):
        """Generate tweet content using Ollama"""
        try:
            prompt = f"Generate a short, natural tweet about {context} technology. Make it sound like a real person posting. Include the state code {state_code} at the end. Keep it under 280 characters."
            
            response = ollama.chat(
                model='llama3.2:3b',
                messages=[{'role': 'user', 'content': prompt}]
            )
            
            tweet_text = response['message']['content'].strip()
            
            # Clean up the response and ensure it ends with state code
            if not tweet_text.endswith(f"({state_code})"):
                tweet_text = f"{tweet_text} ({state_code})"
            
            # Truncate if too long
            if len(tweet_text) > 280:
                tweet_text = tweet_text[:277] + "..."
            
            return tweet_text
            
        except Exception as e:
            print(f"⚠️  Ollama failed for {context} in {state_code}: {e}")
            # Fallback to simple template
            fallback_templates = [
                f"Excited about {context} developments! The future is here 🚀 ({state_code})",
                f"Working on a {context} project and loving it! #tech #innovation ({state_code})",
                f"{context} is changing everything! Can't wait to see what's next ({state_code})"
            ]
            return random.choice(fallback_templates)
    
    def analyze_emotions_with_nlp(self, tweet_text):
        """Analyze emotions using the BERT NLP pipeline"""
        try:
            if self.emotion_analyzer:
                # Use the real NLP pipeline
                emotions = self.emotion_analyzer.analyze_emotion(tweet_text)
                return emotions
            else:
                # Fallback to synthetic emotions
                return self.generate_synthetic_emotions()
                
        except Exception as e:
            print(f"⚠️  NLP analysis failed: {e}")
            return self.generate_synthetic_emotions()
    
    def generate_synthetic_emotions(self):
        """Generate synthetic emotions as fallback"""
        emotions = {
            'anger': round(random.uniform(0.0, 0.8), 3),
            'fear': round(random.uniform(0.0, 0.7), 3),
            'positive': round(random.uniform(0.1, 0.9), 3),
            'sadness': round(random.uniform(0.0, 0.6), 3),
            'surprise': round(random.uniform(0.0, 0.8), 3),
            'joy': round(random.uniform(0.1, 0.9), 3),
            'anticipation': round(random.uniform(0.1, 0.9), 3),
            'trust': round(random.uniform(0.1, 0.8), 3),
            'negative': round(random.uniform(0.0, 0.7), 3),
            'disgust': round(random.uniform(0.0, 0.5), 3)
        }
        
        # Calculate compound and dominant emotion
        emotions['compound'] = round(emotions['positive'] - emotions['negative'], 3)
        
        # Find dominant emotion
        dominant_emotion = max(emotions.items(), key=lambda x: x[1] if x[0] not in ['compound', 'positive', 'negative'] else 0)
        emotions['dominant_emotion'] = dominant_emotion[0]
        emotions['confidence'] = round(dominant_emotion[1], 3)
        
        return emotions
    
    def insert_record(self, cursor, tweet_id, date, state_code, state_name, context):
        """Insert a single record into database"""
        # Generate tweet content using Ollama
        raw_text = self.generate_tweet_content_with_ollama(context, state_code)
        
        # Analyze emotions using NLP pipeline
        emotions = self.analyze_emotions_with_nlp(raw_text)
        
        # Generate engagement metrics
        likes = random.randint(0, 1000)
        retweets = random.randint(0, 500)
        replies = random.randint(0, 200)
        views = random.randint(100, 10000)
        
        # Create timestamp with random time during the day
        timestamp = date.replace(
            hour=random.randint(0, 23),
            minute=random.randint(0, 59),
            second=random.randint(0, 59)
        )
        
        # Insert record
        sql_query = f"""
            INSERT INTO tweets (
                tweet_id, username, raw_text, timestamp, state_code, state_name,
                context, likes, retweets, replies, views, anger, fear,
                positive, sadness, surprise, joy, anticipation, trust,
                negative, disgust, compound, dominant_emotion, confidence
            ) VALUES (
                {tweet_id}, 'tech_user_{random.randint(100, 999)}', '{raw_text.replace("'", "''")}', '{timestamp}', 
                '{state_code}', '{state_name}', '{context}',
                {likes}, {retweets}, {replies}, {views},
                {emotions['anger']}, {emotions['fear']}, {emotions['positive']}, {emotions['sadness']}, {emotions['surprise']}, {emotions['joy']}, 
                {emotions['anticipation']}, {emotions['trust']}, {emotions['negative']}, {emotions['disgust']}, 
                {emotions['compound']}, '{emotions['dominant_emotion']}', {emotions['confidence']}
            )
        """
        
        cursor.execute(sql_query)
    
    def generate_data(self):
        """Generate all the data"""
        print("🚀 Starting data generation...")
        print(f"📊 Target: {len(US_STATES)} states × 10 entries × 245 days = 122,500 records")
        
        # Calculate date range (Jan 1, 2025 to today)
        start_date = datetime(2025, 1, 1)
        end_date = datetime.now()
        total_days = (end_date - start_date).days + 1
        
        print(f"📅 Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')} ({total_days} days)")
        
        # Check if we should continue from existing data
        try:
            conn = psycopg2.connect(**DB_PARAMS)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM tweets")
            existing_count = cursor.fetchone()[0]
            conn.close()
            
            if existing_count > 0:
                print(f"📊 Found {existing_count:,} existing records - continuing from where we left off!")
                print("💡 To start fresh, run with --clean flag")
                return self.continue_generation(start_date, end_date, existing_count)
        except Exception as e:
            print(f"⚠️  Couldn't check existing data: {e}")
        
        # Clean up database first
        if not self.cleanup_database():
            return False
        
        try:
            conn = psycopg2.connect(**DB_PARAMS)
            cursor = conn.cursor()
            
            tweet_id = 1
            total_records = 0
            start_time = time.time()
            
            # Generate data for each day
            for day_offset in range(total_days):
                current_date = start_date + timedelta(days=day_offset)
                
                # Generate 10 entries for each state for this day
                for state_code, state_name in US_STATES.items():
                    for entry_num in range(10):
                        context = random.choice(TECH_CONTEXTS)
                        
                        # Insert record
                        self.insert_record(cursor, tweet_id, current_date, state_code, state_name, context)
                        
                        tweet_id += 1
                        total_records += 1
                        
                        # Progress update every 5 records
                        if total_records % 5 == 0:
                            elapsed = time.time() - start_time
                            rate = total_records / elapsed if elapsed > 0 else 0
                            print(f"📈 Record {total_records:,}: {state_code} - {context} ({rate:.0f} records/sec)")
                        
                        # Commit every 100 records for real-time visibility
                        if total_records % 100 == 0:
                            conn.commit()
                            print(f"💾 Committed {total_records:,} records to database")
                
                # Final commit for the day
                conn.commit()
                
                # Daily progress
                if day_offset % 30 == 0:
                    print(f"📅 Completed {day_offset + 1}/{total_days} days ({total_records:,} records)")
            
            conn.commit()
            conn.close()
            
            total_time = time.time() - start_time
            print(f"\n🎉 Data generation completed!")
            print(f"📊 Total records: {total_records:,}")
            print(f"⏱️  Total time: {total_time:.1f} seconds")
            print(f"⚡ Average rate: {total_records / total_time:.0f} records/second")
            
            return True
            
        except Exception as e:
            print(f"❌ Data generation failed: {e}")
            return False
    
    def continue_generation(self, start_date, end_date, existing_count):
        """Continue generation from where we left off"""
        print(f"🔄 Continuing generation from {existing_count:,} existing records...")
        
        try:
            conn = psycopg2.connect(**DB_PARAMS)
            cursor = conn.cursor()
            
            # Get the next tweet_id to use
            cursor.execute("SELECT MAX(tweet_id) FROM tweets")
            max_id_result = cursor.fetchone()
            tweet_id = (max_id_result[0] or 0) + 1
            
            total_records = existing_count
            start_time = time.time()
            
            # Calculate how many more records we need
            target_total = len(US_STATES) * 10 * ((end_date - start_date).days + 1)
            remaining_records = target_total - existing_count
            
            print(f"🎯 Need to generate {remaining_records:,} more records to reach {target_total:,}")
            
            # Generate remaining data
            for day_offset in range((end_date - start_date).days + 1):
                current_date = start_date + timedelta(days=day_offset)
                
                for state_code, state_name in US_STATES.items():
                    for entry_num in range(10):
                        # Check if we already have this state/day combination
                        cursor.execute("""
                            SELECT COUNT(*) FROM tweets 
                            WHERE state_code = %s AND DATE(timestamp) = %s
                        """, (state_code, current_date.date()))
                        
                        existing_for_state_day = cursor.fetchone()[0]
                        
                        if existing_for_state_day < 10:
                            # We need more records for this state/day
                            context = random.choice(TECH_CONTEXTS)
                            self.insert_record(cursor, tweet_id, current_date, state_code, state_name, context)
                            
                            tweet_id += 1
                            total_records += 1
                            
                            # Progress update every 50 records
                            if total_records % 50 == 0:
                                elapsed = time.time() - start_time
                                rate = (total_records - existing_count) / elapsed if elapsed > 0 else 0
                                print(f"📈 Record {total_records:,}: {state_code} - {context} ({rate:.0f} records/sec)")
                                conn.commit()
                                print(f"💾 Committed {total_records:,} records to database")
                        
                        if total_records >= target_total:
                            break
                    
                    if total_records >= target_total:
                        break
                
                if total_records >= target_total:
                    break
                
                # Commit every day
                conn.commit()
            
            conn.commit()
            conn.close()
            
            total_time = time.time() - start_time
            print(f"\n🎉 Generation completed!")
            print(f"📊 Total records: {total_records:,}")
            print(f"⏱️  Time for remaining records: {total_time:.1f} seconds")
            
            return True
            
        except Exception as e:
            print(f"❌ Continue generation failed: {e}")
            return False

def main():
    """Main execution function"""
    print("🚀 Simple Data Generator (with Ollama + NLP)")
    print("=============================================")
    print("")
    
    # Check for command line arguments
    force_clean = '--clean' in sys.argv
    
    if force_clean:
        print("🧹 Force clean mode - will clear all existing data")
        print("")
    
    # Confirm before proceeding
    print("⚠️  This will generate 122,500 records (10 per state per day for 1 year)")
    print("   - Starting from Jan 1, 2025")
    print("   - Uses Ollama for tweet generation")
    print("   - Uses BERT NLP pipeline for emotion analysis")
    if not force_clean:
        print("   - Will continue from existing data if found")
    else:
        print("   - All existing data will be cleared")
    print("")
    
    response = input("Continue? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("❌ Operation cancelled")
        return
    
    # Initialize generator and generate data
    generator = SimpleDataGenerator()
    
    if force_clean:
        # Force clean start
        if not generator.cleanup_database():
            return
        success = generator.generate_data()
    else:
        success = generator.generate_data()
    
    if success:
        print("\n✅ All done! Your database now has 122,500 diverse records.")
        print("🌍 Data spans all 50 US states with daily entries.")
        print("🤖 Generated using Ollama and analyzed with BERT NLP pipeline.")
    else:
        print("\n❌ Data generation failed!")

if __name__ == "__main__":
    main()

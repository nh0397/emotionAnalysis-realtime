#!/usr/bin/env python3
"""
Simple Dummy Data Generator
Creates fake emotion data spanning a year for testing purposes.
No Ollama or NLP pipeline required - just synthetic data.
"""

import psycopg2
import random
import time
import math
from datetime import datetime, timedelta
import argparse

class SimpleDummyGenerator:
    def __init__(self, db_config):
        self.db_config = db_config
        self.states = [
            'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
            'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
            'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
            'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
            'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
        ]
        
        self.contexts = [
            'AI', 'Machine Learning', 'Data Science', 'Cloud Computing',
            'Cybersecurity', 'Blockchain', 'IoT', '5G', 'Quantum Computing',
            'Robotics', 'VR/AR', 'Edge Computing', 'DevOps', 'Mobile Apps'
        ]
        
        self.usernames = [
            'tech_enthusiast', 'data_nerd', 'ai_fan', 'cloud_guru',
            'security_expert', 'blockchain_dev', 'iot_engineer', 'quantum_researcher',
            'robotics_geek', 'vr_creator', 'edge_developer', 'devops_master'
        ]

    def connect_db(self):
        """Connect to PostgreSQL database"""
        try:
            print(f"🔌 Attempting to connect to database: {self.db_config['database']} on {self.db_config['host']}:{self.db_config['port']}")
            conn = psycopg2.connect(**self.db_config)
            print("✅ Connected to database successfully")
            return conn
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            print(f"🔍 Connection details: {self.db_config}")
            return None

    def cleanup_database(self):
        """Truncate existing data and reset sequences"""
        conn = self.connect_db()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            print("🔍 Checking if tweets table exists...")
            cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'tweets')")
            tweets_exists = cursor.fetchone()[0]
            print(f"📊 Tweets table exists: {tweets_exists}")
            
            if not tweets_exists:
                print("❌ Tweets table does not exist! Please run db_consumer.py first to create the database schema.")
                return False
            
            print("🔍 Creating emotion_aggregates table if it doesn't exist...")
            # Create emotion_aggregates table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS emotion_aggregates (
                    state_code CHAR(2) PRIMARY KEY,
                    anger_avg FLOAT DEFAULT 0.0,
                    joy_avg FLOAT DEFAULT 0.0,
                    fear_avg FLOAT DEFAULT 0.0,
                    sadness_avg FLOAT DEFAULT 0.0,
                    surprise_avg FLOAT DEFAULT 0.0,
                    positive_avg FLOAT DEFAULT 0.0,
                    negative_avg FLOAT DEFAULT 0.0,
                    anticipation_avg FLOAT DEFAULT 0.0,
                    trust_avg FLOAT DEFAULT 0.0,
                    disgust_avg FLOAT DEFAULT 0.0,
                    tweet_count INTEGER DEFAULT 0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_processed_tweet_id INTEGER
                )
            """)
            
            print("🧹 Truncating existing data...")
            # Truncate tables
            cursor.execute("TRUNCATE TABLE tweets RESTART IDENTITY CASCADE")
            cursor.execute("TRUNCATE TABLE emotion_aggregates RESTART IDENTITY CASCADE")
            
            print("🔄 Resetting sequences...")
            # Reset sequences
            cursor.execute("ALTER SEQUENCE tweets_id_seq RESTART WITH 1")
            
            conn.commit()
            print("✅ Database cleaned successfully")
            return True
            
        except Exception as e:
            print(f"❌ Database cleanup failed: {e}")
            import traceback
            traceback.print_exc()
            conn.rollback()
            return False
        finally:
            conn.close()

    def generate_synthetic_emotions(self, state_code, context, date):
        """Generate realistic emotion scores with state-specific variations"""
        emotions = {}
        
        # Create a unique seed based on state, context, and date for consistent randomization
        seed_value = hash(f"{state_code}_{context}_{date.strftime('%Y-%m-%d')}") % (2**32)
        random.seed(seed_value)
        
        # Generate base emotions with state-specific characteristics
        # Some states are more "angry", others more "joyful", etc.
        state_modifiers = {
            'CA': {'joy': 0.2, 'positive': 0.15, 'anger': -0.1},      # California - generally positive
            'NY': {'anticipation': 0.2, 'trust': 0.1, 'fear': -0.1},   # New York - business-focused
            'TX': {'joy': 0.1, 'trust': 0.15, 'surprise': 0.1},        # Texas - friendly
            'FL': {'joy': 0.15, 'surprise': 0.2, 'fear': -0.1},        # Florida - exciting
            'WA': {'trust': 0.2, 'anticipation': 0.15, 'joy': 0.1},    # Washington - tech optimism
            'CO': {'joy': 0.25, 'positive': 0.2, 'fear': -0.15},       # Colorado - very positive
            'OR': {'trust': 0.15, 'joy': 0.1, 'anticipation': 0.1},    # Oregon - progressive
            'MA': {'anticipation': 0.2, 'trust': 0.15, 'joy': 0.1},    # Massachusetts - academic
            'IL': {'anticipation': 0.15, 'trust': 0.1, 'joy': 0.1},    # Illinois - business
            'PA': {'trust': 0.1, 'joy': 0.1, 'anticipation': 0.1},     # Pennsylvania - balanced
        }
        
        # Get state modifier or use default
        state_mod = state_modifiers.get(state_code, {})
        
        # Generate base emotions with full randomization (0 to 1 scale)
        base_emotions = {
            'anger': random.uniform(0.0, 1.0),
            'fear': random.uniform(0.0, 1.0),
            'sadness': random.uniform(0.0, 1.0),
            'surprise': random.uniform(0.0, 1.0),
            'joy': random.uniform(0.0, 1.0),
            'anticipation': random.uniform(0.0, 1.0),
            'trust': random.uniform(0.0, 1.0),
            'disgust': random.uniform(0.0, 1.0),
            'positive': random.uniform(0.0, 1.0),
            'negative': random.uniform(0.0, 1.0)
        }
        
        # Apply state modifiers
        for emotion, modifier in state_mod.items():
            if emotion in base_emotions:
                base_emotions[emotion] = min(1.0, max(0.0, base_emotions[emotion] + modifier))
        
        # Add some daily variation based on date
        day_of_year = date.timetuple().tm_yday
        
        # Seasonal patterns - different emotions peak at different times of year
        seasonal_patterns = {
            'joy': 0.15 * math.sin((day_of_year - 172) * 0.017) + 0.05,      # Peak in summer (June)
            'positive': 0.1 * math.sin((day_of_year - 172) * 0.017) + 0.05,   # Summer positivity
            'anticipation': 0.1 * math.sin((day_of_year - 1) * 0.017) + 0.05,  # New Year excitement
            'trust': 0.08 * math.sin((day_of_year - 80) * 0.017) + 0.04,      # Spring renewal
            'surprise': 0.1 * math.sin((day_of_year - 355) * 0.017) + 0.05,   # Holiday surprises
        }
        
        # Apply seasonal patterns
        for emotion, pattern in seasonal_patterns.items():
            if emotion in base_emotions:
                base_emotions[emotion] = min(1.0, max(0.0, base_emotions[emotion] + pattern))
        
        # General daily variation
        daily_variation = 0.05 * math.sin(day_of_year * 0.1)  # Smaller daily variation
        
        # Add context-specific variations
        context_modifiers = {
            'AI': {'anticipation': 0.2, 'trust': 0.1, 'joy': 0.1},           # AI - exciting future
            'Machine Learning': {'anticipation': 0.15, 'trust': 0.1, 'joy': 0.1}, # ML - innovative
            'Data Science': {'trust': 0.15, 'anticipation': 0.1, 'joy': 0.1},     # Data - analytical
            'Cloud Computing': {'trust': 0.2, 'anticipation': 0.1, 'joy': 0.1},   # Cloud - reliable
            'Cybersecurity': {'fear': 0.1, 'trust': 0.2, 'anticipation': 0.1},    # Security - cautious
            'Blockchain': {'anticipation': 0.2, 'trust': 0.1, 'surprise': 0.1},   # Blockchain - revolutionary
            'IoT': {'anticipation': 0.15, 'joy': 0.1, 'trust': 0.1},             # IoT - connected future
            '5G': {'anticipation': 0.2, 'joy': 0.1, 'surprise': 0.1},            # 5G - fast future
            'Quantum Computing': {'anticipation': 0.25, 'surprise': 0.2, 'joy': 0.1}, # Quantum - mind-blowing
            'Robotics': {'joy': 0.15, 'anticipation': 0.1, 'surprise': 0.1},     # Robotics - cool
            'VR/AR': {'joy': 0.2, 'surprise': 0.2, 'anticipation': 0.1},         # VR/AR - immersive
            'Edge Computing': {'trust': 0.15, 'anticipation': 0.1, 'joy': 0.1},   # Edge - efficient
            'DevOps': {'trust': 0.1, 'joy': 0.1, 'anticipation': 0.1},           # DevOps - practical
            'Mobile Apps': {'joy': 0.15, 'anticipation': 0.1, 'trust': 0.1}      # Mobile - accessible
        }
        
        # Get context modifier
        context_mod = context_modifiers.get(context, {})
        
        # Apply context modifiers
        for emotion, modifier in context_mod.items():
            if emotion in base_emotions:
                base_emotions[emotion] = min(1.0, max(0.0, base_emotions[emotion] + modifier))
        
        # Apply daily variation to all emotions
        for emotion in base_emotions:
            base_emotions[emotion] = min(1.0, max(0.0, base_emotions[emotion] + daily_variation))
        
        # Add small random noise to make each record unique
        for emotion in base_emotions:
            noise = random.uniform(-0.05, 0.05)  # Small random variation
            base_emotions[emotion] = min(1.0, max(0.0, base_emotions[emotion] + noise))
        
        # Round all values
        for emotion, value in base_emotions.items():
            emotions[emotion] = round(value, 3)
        
        # Calculate compound score
        compound = emotions['positive'] - emotions['negative']
        emotions['compound'] = round(max(-1, min(1, compound)), 3)
        
        # Determine dominant emotion
        emotion_scores = {k: v for k, v in emotions.items() 
                         if k not in ['compound', 'positive', 'negative']}
        dominant_emotion = max(emotion_scores, key=emotion_scores.get)
        emotions['dominant_emotion'] = dominant_emotion
        emotions['confidence'] = round(random.uniform(0.6, 0.95), 3)
        
        # Reset random seed to avoid affecting other random operations
        random.seed()
        
        return emotions

    def generate_tweet_content(self, context, state_code):
        """Generate synthetic tweet content"""
        templates = [
            f"Just discovered some amazing {context} trends! The future is here 🚀 #{context.replace(' ', '')} #{state_code}",
            f"Working on a new {context} project today. The possibilities are endless! 💻 #{context.replace(' ', '')} #{state_code}",
            f"Attended a great {context} workshop. Learning never stops! 📚 #{context.replace(' ', '')} #{state_code}",
            f"Excited about the latest {context} developments! Technology moves so fast ⚡ #{context.replace(' ', '')} #{state_code}",
            f"Building something cool with {context}. Innovation is key! 🔧 #{context.replace(' ', '')} #{state_code}",
            f"Just deployed my first {context} solution. Feeling accomplished! 🎉 #{context.replace(' ', '')} #{state_code}",
            f"Reading about {context} best practices. Knowledge is power! 📖 #{context.replace(' ', '')} #{state_code}",
            f"Collaborating with amazing {context} developers. Community is everything! 🤝 #{context.replace(' ', '')} #{state_code}",
            f"Exploring new {context} frameworks. Always learning! 🔍 #{context.replace(' ', '')} #{state_code}",
            f"Just finished a {context} certification. Skills upgraded! 🏆 #{context.replace(' ', '')} #{state_code}"
        ]
        
        return random.choice(templates)

    def insert_record(self, conn, tweet_data):
        """Insert a single tweet record"""
        try:
            cursor = conn.cursor()
            
            # Create the SQL string using f-string (same as db_consumer.py)
            sql_query = f"""
                INSERT INTO tweets (
                    tweet_id, username, raw_text, timestamp, 
                    state_code, state_name, context,
                    likes, retweets, replies, views,
                    anger, fear, positive, sadness, surprise, joy, 
                    anticipation, trust, negative, disgust, 
                    compound, dominant_emotion, confidence
                ) VALUES (
                    {tweet_data['tweet_id']}, '{tweet_data['username']}', '{tweet_data['raw_text'].replace("'", "''")}', '{tweet_data['timestamp']}', 
                    '{tweet_data['state_code']}', '{tweet_data['state_name']}', '{tweet_data['context']}',
                    {tweet_data['likes']}, {tweet_data['retweets']}, {tweet_data['replies']}, {tweet_data['views']},
                    {tweet_data['anger']}, {tweet_data['fear']}, {tweet_data['positive']}, {tweet_data['sadness']}, {tweet_data['surprise']}, {tweet_data['joy']}, 
                    {tweet_data['anticipation']}, {tweet_data['trust']}, {tweet_data['negative']}, {tweet_data['disgust']}, 
                    {tweet_data['compound']}, '{tweet_data['dominant_emotion']}', {tweet_data['confidence']}
                )
            """
            
            # Execute the SQL string directly (same as db_consumer.py)
            cursor.execute(sql_query)
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to insert record: {e}")
            return False

    def generate_data(self, start_date=None, end_date=None, records_per_state_per_day=5):
        """Generate data for the specified date range"""
        if not start_date:
            start_date = datetime(2025, 1, 1)  # Start from Jan 1, 2025
        if not end_date:
            end_date = datetime.now()  # End at today
        
        conn = self.connect_db()
        if not conn:
            return False
        
        try:
            total_records = 0
            start_time = time.time()
            
            # Calculate date range
            current_date = start_date
            date_range = []
            while current_date <= end_date:
                date_range.append(current_date)
                current_date += timedelta(days=1)
            
            print(f"📅 Generating data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
            print(f"📊 Target: {len(date_range)} days × {len(self.states)} states × {records_per_state_per_day} records = {len(date_range) * len(self.states) * records_per_state_per_day:,} total records")
            
            for date in date_range:
                for state_code in self.states:
                    for i in range(records_per_state_per_day):
                        # Generate tweet data
                        context = random.choice(self.contexts)
                        username = random.choice(self.usernames)
                        
                        # Generate emotions with state-specific variations
                        emotions = self.generate_synthetic_emotions(state_code, context, date)
                        
                        # Create tweet record
                        tweet_data = {
                            'tweet_id': total_records + 1,  # Integer ID as expected by schema
                            'username': username,
                            'raw_text': self.generate_tweet_content(context, state_code),
                            'timestamp': (date + timedelta(
                                hours=random.randint(0, 23),
                                minutes=random.randint(0, 59),
                                seconds=random.randint(0, 59)
                            )).strftime('%Y-%m-%d %H:%M:%S'),
                            'state_code': state_code,
                            'state_name': f"State {state_code}",
                            'context': context,
                            'likes': random.randint(0, 1000),
                            'retweets': random.randint(0, 500),
                            'replies': random.randint(0, 200),
                            'views': random.randint(100, 10000),
                            **emotions
                        }
                        
                        # Insert record
                        if self.insert_record(conn, tweet_data):
                            total_records += 1
                            
                            # Progress logging
                            if total_records % 50 == 0:
                                elapsed = time.time() - start_time
                                rate = total_records / elapsed if elapsed > 0 else 0
                                print(f"📈 Record {total_records:,}: {state_code} - {context} ({rate:.0f} records/sec)")
                        
                        # Commit every 200 records
                        if total_records % 200 == 0:
                            conn.commit()
                            print(f"💾 Committed {total_records:,} records to database")
            
            # Final commit
            conn.commit()
            elapsed = time.time() - start_time
            print(f"🎉 Data generation complete!")
            print(f"📊 Total records generated: {total_records:,}")
            print(f"⏱️  Total time: {elapsed:.1f} seconds")
            print(f"🚀 Average rate: {total_records / elapsed:.0f} records/sec")
            
            # Time series data will be generated on-demand from tweets table
            print("✅ Tweets ready! Time series data will be generated from tweets when needed.")
            
            return True
            
        except Exception as e:
            print(f"❌ Data generation failed: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def generate_time_series_data(self, start_date=None, end_date=None):
        """Generate time series data for the TimeSeriesChart component"""
        if not start_date:
            start_date = datetime(2024, 1, 1)
        if not end_date:
            end_date = datetime(2025, 1, 1)
        
        conn = self.connect_db()
        if not conn:
            return False
        
        try:
            print("🕒 Generating time series data...")
            
            # Calculate date range
            current_date = start_date
            date_range = []
            while current_date <= end_date:
                date_range.append(current_date)
                current_date += timedelta(days=1)
            
            print(f"📅 Generating {len(date_range)} days of time series data for {len(self.states)} states")
            
            # Create time series data table if it doesn't exist
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS time_series_data (
                    id SERIAL PRIMARY KEY,
                    date DATE NOT NULL,
                    state_code CHAR(2) NOT NULL,
                    anger FLOAT DEFAULT 0.0,
                    fear FLOAT DEFAULT 0.0,
                    sadness FLOAT DEFAULT 0.0,
                    surprise FLOAT DEFAULT 0.0,
                    joy FLOAT DEFAULT 0.0,
                    anticipation FLOAT DEFAULT 0.0,
                    trust FLOAT DEFAULT 0.0,
                    disgust FLOAT DEFAULT 0.0,
                    positive FLOAT DEFAULT 0.0,
                    negative FLOAT DEFAULT 0.0,
                    UNIQUE(date, state_code)
                )
            """)
            
            # Clear existing time series data
            cursor.execute("DELETE FROM time_series_data")
            
            total_records = 0
            
            for date in date_range:
                for state_code in self.states:
                    # Generate daily emotion averages for this state
                    daily_emotions = {}
                    
                    # Generate base emotions for this state/date combination
                    base_emotions = self.generate_synthetic_emotions(state_code, "Daily Average", date)
                    
                    # Add some daily trend variation (emotions change over time)
                    day_of_year = date.timetuple().tm_yday
                    
                    # Weekly patterns (weekends vs weekdays)
                    weekday = date.weekday()
                    if weekday >= 5:  # Weekend
                        base_emotions['joy'] = min(1.0, base_emotions['joy'] + 0.1)
                        base_emotions['positive'] = min(1.0, base_emotions['positive'] + 0.1)
                        base_emotions['anger'] = max(0.0, base_emotions['anger'] - 0.05)
                        base_emotions['fear'] = max(0.0, base_emotions['fear'] - 0.05)
                    
                    # Monthly patterns (beginning/end of month)
                    day_of_month = date.day
                    if day_of_month <= 5:  # Beginning of month
                        base_emotions['anticipation'] = min(1.0, base_emotions['anticipation'] + 0.1)
                        base_emotions['trust'] = min(1.0, base_emotions['trust'] + 0.05)
                    elif day_of_month >= 25:  # End of month
                        base_emotions['stress'] = min(1.0, base_emotions.get('stress', 0.0) + 0.1)
                        base_emotions['fear'] = min(1.0, base_emotions['fear'] + 0.05)
                    
                    # Insert time series record
                    insert_query = f"""
                        INSERT INTO time_series_data (
                            date, state_code, anger, fear, sadness, surprise, joy, 
                            anticipation, trust, disgust, positive, negative
                        ) VALUES (
                            '{date.strftime('%Y-%m-%d')}', '{state_code}', 
                            {base_emotions['anger']}, {base_emotions['fear']}, {base_emotions['sadness']}, 
                            {base_emotions['surprise']}, {base_emotions['joy']}, {base_emotions['anticipation']}, 
                            {base_emotions['trust']}, {base_emotions['disgust']}, 
                            {base_emotions['positive']}, {base_emotions['negative']}
                        )
                    """
                    
                    cursor.execute(insert_query)
                    total_records += 1
                    
                    if total_records % 100 == 0:
                        print(f"📊 Generated {total_records:,} time series records")
            
            conn.commit()
            print(f"✅ Time series data generation complete: {total_records:,} records")
            return True
            
        except Exception as e:
            print(f"❌ Time series data generation failed: {e}")
            import traceback
            traceback.print_exc()
            conn.rollback()
            return False
        finally:
            conn.close()

    def update_aggregates(self):
        """Update emotion aggregates table"""
        conn = self.connect_db()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            # Clear existing aggregates
            cursor.execute("DELETE FROM emotion_aggregates")
            
            # Insert new aggregates
            insert_query = """
            INSERT INTO emotion_aggregates (
                state_code, anger_avg, joy_avg, fear_avg, sadness_avg, surprise_avg,
                positive_avg, negative_avg, anticipation_avg, trust_avg, disgust_avg,
                tweet_count, last_updated, last_processed_tweet_id
            )
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
                NOW() as last_updated,
                MAX(id) as last_processed_tweet_id
            FROM tweets 
            GROUP BY state_code
            ORDER BY state_code
            """
            
            cursor.execute(insert_query)
            conn.commit()
            
            # Get count of updated aggregates
            cursor.execute("SELECT COUNT(*) FROM emotion_aggregates")
            count = cursor.fetchone()[0]
            
            print(f"✅ Updated emotion aggregates: {count} states")
            return True
            
        except Exception as e:
            print(f"❌ Failed to update aggregates: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

def main():
    parser = argparse.ArgumentParser(description='Generate dummy emotion data')
    parser.add_argument('--clean', action='store_true', help='Clean database before generating')
    parser.add_argument('--start-date', default='2025-01-01', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', default=None, help='End date (YYYY-MM-DD), defaults to today')
    parser.add_argument('--records-per-day', type=int, default=5, help='Records per state per day')
    
    args = parser.parse_args()
    
    # Database configuration
    db_config = {
        'host': 'localhost',
        'database': 'tweetdb',
        'user': 'tweetuser',
        'password': 'tweetpass',
        'port': 5432
    }
    
    generator = SimpleDummyGenerator(db_config)
    
    if args.clean:
        print("🧹 Cleaning database...")
        if not generator.cleanup_database():
            print("❌ Database cleanup failed. Exiting.")
            return
    
    # Parse dates
    start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
    if args.end_date:
        end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
    else:
        end_date = datetime.now()  # Default to today
    
    print("🚀 Starting dummy data generation...")
    print(f"📅 Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"📊 Records per state per day: {args.records_per_day}")
    
    if generator.generate_data(start_date, end_date, args.records_per_day):
        print("🔄 Updating emotion aggregates...")
        generator.update_aggregates()
        print("✅ All done! Ready for testing.")
    else:
        print("❌ Data generation failed.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()

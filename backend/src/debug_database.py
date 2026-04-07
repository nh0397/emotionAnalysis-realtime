#!/usr/bin/env python3
"""
Debug database connection and table structure
"""

import psycopg2
import sys

def debug_database():
    """Debug database connection and table structure"""
    print("🔍 DEBUGGING DATABASE CONNECTION...")
    
    try:
        # Database parameters
        db_params = {
            'host': 'localhost',
            'port': 5432,
            'database': 'tweetdb',
            'user': 'tweetuser',
            'password': 'tweetpass'
        }
        
        print(f"📡 Connecting to database: {db_params['host']}:{db_params['port']}/{db_params['database']}")
        
        # Test connection
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        
        print("✅ Database connection successful!")
        
        # Check if tweets table exists
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'tweets'
        """)
        
        if cursor.fetchone():
            print("✅ 'tweets' table exists")
        else:
            print("❌ 'tweets' table does NOT exist")
            conn.close()
            return
        
        # Get table structure
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'tweets' 
            ORDER BY ordinal_position
        """)
        
        print("\n📋 Table structure:")
        columns = cursor.fetchall()
        for col in columns:
            print(f"   {col[0]}: {col[1]} (nullable: {col[2]})")
        
        # Count existing tweets
        cursor.execute("SELECT COUNT(*) FROM tweets")
        count = cursor.fetchone()[0]
        print(f"\n📊 Total tweets in database: {count}")
        
        # Show recent tweets with emotion data
        cursor.execute("""
            SELECT tweet_id, state_code, anger, joy, positive, dominant_emotion 
            FROM tweets 
            ORDER BY id DESC 
            LIMIT 5
        """)
        
        recent_tweets = cursor.fetchall()
        if recent_tweets:
            print("\n🔥 Recent tweets with emotion data:")
            for tweet in recent_tweets:
                print(f"   ID {tweet[0]} ({tweet[1]}): anger={tweet[2]}, joy={tweet[3]}, positive={tweet[4]}, dominant={tweet[5]}")
        else:
            print("\n📭 No tweets found in database")
        
        # Test a simple insert
        print("\n🧪 Testing simple insert...")
        test_sql = """
            INSERT INTO tweets (
                tweet_id, username, raw_text, timestamp, 
                state_code, state_name, context,
                likes, retweets, replies, views,
                anger, fear, positive, sadness, surprise, joy, 
                anticipation, trust, negative, disgust, 
                compound, dominant_emotion, confidence
            ) VALUES (
                99999, 'debug_user', 'This is a debug test tweet', NOW(), 
                'CA', 'California', 'debug_test',
                10, 2, 1, 50,
                0.1, 0.05, 0.8, 0.02, 0.15, 0.75, 
                0.3, 0.4, 0.05, 0.01, 
                0.7, 'joy', 0.75
            )
        """
        
        print(f"📝 Test SQL: {test_sql}")
        
        # Execute test insert
        cursor.execute("DELETE FROM tweets WHERE tweet_id = 99999")  # Clean up first
        cursor.execute(test_sql)
        conn.commit()
        
        # Verify test insert
        cursor.execute("SELECT tweet_id, anger, joy, positive, dominant_emotion FROM tweets WHERE tweet_id = 99999")
        result = cursor.fetchone()
        
        if result:
            print(f"✅ Test insert successful: ID={result[0]}, anger={result[1]}, joy={result[2]}, positive={result[3]}, dominant={result[4]}")
            # Clean up
            cursor.execute("DELETE FROM tweets WHERE tweet_id = 99999")
            conn.commit()
        else:
            print("❌ Test insert failed")
        
        conn.close()
        print("\n🎯 Database debugging completed!")
        
    except Exception as e:
        print(f"❌ Database debug failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_database()

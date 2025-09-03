#!/usr/bin/env python3
"""
Quick test to verify database insertion with proper data types
"""

import psycopg2
import json
from datetime import datetime
from unified_logger import logger

# Test data with proper types
test_tweet = {
    'id': 999,
    'username': 'test_user_999',
    'raw_text': 'This is a test tweet to verify database insertion with proper emotion data!',
    'timestamp': datetime.now().isoformat(),
    'state_code': 'CA',
    'state_name': 'California',
    'context': 'database_test',
    'likes': 42,
    'retweets': 7,
    'replies': 3,
    'views': 156,
    # Emotion data with realistic values
    'anger': 0.0234,
    'fear': 0.0156,
    'positive': 0.8901,
    'sadness': 0.0123,
    'surprise': 0.1234,
    'joy': 0.7890,
    'anticipation': 0.2345,
    'trust': 0.3456,
    'negative': 0.0098,
    'disgust': 0.0067,
    'compound': 0.7654,
    'dominant_emotion': 'joy',
    'confidence': 0.7890
}

def test_database_insertion():
    """Test database insertion with proper type conversion"""
    print("🧪 Testing Database Insertion...")
    print(f"📊 Test tweet ID: {test_tweet['id']}")
    
    try:
        # Database parameters
        db_params = {
            'host': 'localhost',
            'port': 5432,
            'database': 'tweetdb',
            'user': 'tweetuser',
            'password': 'tweetpass'
        }
        
        # Convert data types explicitly
        tweet_id = int(test_tweet['id'])
        username = str(test_tweet['username'])
        raw_text = str(test_tweet['raw_text'])
        timestamp = str(test_tweet['timestamp'])
        state_code = str(test_tweet['state_code'])
        state_name = str(test_tweet['state_name'])
        context = str(test_tweet['context'])
        
        # Convert engagement metrics to integers
        likes = int(test_tweet.get('likes', 0))
        retweets = int(test_tweet.get('retweets', 0))
        replies = int(test_tweet.get('replies', 0))
        views = int(test_tweet.get('views', 0))
        
        # Convert emotion scores to floats
        anger = float(test_tweet.get('anger', 0.0))
        fear = float(test_tweet.get('fear', 0.0))
        positive = float(test_tweet.get('positive', 0.0))
        sadness = float(test_tweet.get('sadness', 0.0))
        surprise = float(test_tweet.get('surprise', 0.0))
        joy = float(test_tweet.get('joy', 0.0))
        anticipation = float(test_tweet.get('anticipation', 0.0))
        trust = float(test_tweet.get('trust', 0.0))
        negative = float(test_tweet.get('negative', 0.0))
        disgust = float(test_tweet.get('disgust', 0.0))
        compound = float(test_tweet.get('compound', 0.0))
        confidence = float(test_tweet.get('confidence', 0.0))
        
        dominant_emotion = str(test_tweet.get('dominant_emotion', 'neutral'))
        
        print("\n📋 Data being inserted:")
        print(f"   Tweet ID: {tweet_id} ({type(tweet_id).__name__})")
        print(f"   Username: {username}")
        print(f"   Text: {raw_text[:50]}...")
        print(f"   State: {state_code} - {state_name}")
        print(f"   Emotions:")
        print(f"     anger: {anger} ({type(anger).__name__})")
        print(f"     joy: {joy} ({type(joy).__name__})")
        print(f"     positive: {positive} ({type(positive).__name__})")
        print(f"     negative: {negative} ({type(negative).__name__})")
        print(f"     dominant: {dominant_emotion} ({type(dominant_emotion).__name__})")
        
        # Connect to database
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        
        # Insert the test tweet
        cursor.execute('''
            INSERT INTO tweets (
                tweet_id, username, raw_text, timestamp, 
                state_code, state_name, context,
                likes, retweets, replies, views,
                anger, fear, positive, sadness, surprise, joy, 
                anticipation, trust, negative, disgust, 
                compound, dominant_emotion, confidence
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            tweet_id, username, raw_text, timestamp, 
            state_code, state_name, context,
            likes, retweets, replies, views,
            anger, fear, positive, sadness, surprise, joy, 
            anticipation, trust, negative, disgust, 
            compound, dominant_emotion, confidence
        ))
        
        conn.commit()
        
        # Verify insertion by querying back
        cursor.execute("SELECT tweet_id, anger, joy, positive, dominant_emotion FROM tweets WHERE tweet_id = %s", (tweet_id,))
        result = cursor.fetchone()
        
        if result:
            print(f"\n✅ SUCCESS! Tweet inserted and verified:")
            print(f"   Retrieved ID: {result[0]}")
            print(f"   Retrieved anger: {result[1]}")
            print(f"   Retrieved joy: {result[2]}")
            print(f"   Retrieved positive: {result[3]}")
            print(f"   Retrieved dominant: {result[4]}")
        else:
            print("❌ ERROR: Tweet not found after insertion")
        
        conn.close()
        print("\n🎯 Database test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_database_insertion()

#!/usr/bin/env python3
"""
QUICK FIX: Generate realistic emotion data that actually works
"""

import psycopg2
import random
import warnings
from datetime import datetime, timedelta

# IGNORE ALL WARNINGS
warnings.filterwarnings('ignore')

def main():
    print("🚀 QUICK DATA GENERATION - NO BS!")
    
    # Connect (ignore warnings)
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='tweetdb',
        user='tweetuser',
        password='tweetpass'
    )
    
    cursor = conn.cursor()
    
    # Clear old data
    print("🗑️ Clearing...")
    cursor.execute("DELETE FROM tweets")
    conn.commit()
    
    # States with DRAMATIC emotion differences
    states_data = [
        # HIGH ANGER (0.7-0.9)
        ("TX", "Texas", {"anger": 0.85, "joy": 0.25, "fear": 0.15, "sadness": 0.35}),
        ("FL", "Florida", {"anger": 0.78, "joy": 0.45, "fear": 0.55, "sadness": 0.25}),
        ("AZ", "Arizona", {"anger": 0.82, "joy": 0.35, "fear": 0.25, "sadness": 0.15}),
        
        # HIGH JOY (0.8-0.9)
        ("CA", "California", {"anger": 0.25, "joy": 0.88, "fear": 0.15, "sadness": 0.25}),
        ("HI", "Hawaii", {"anger": 0.15, "joy": 0.92, "fear": 0.25, "sadness": 0.15}),
        ("CO", "Colorado", {"anger": 0.35, "joy": 0.82, "fear": 0.25, "sadness": 0.15}),
        
        # HIGH FEAR (0.7-0.8)
        ("NY", "New York", {"anger": 0.55, "joy": 0.35, "fear": 0.78, "sadness": 0.45}),
        ("IL", "Illinois", {"anger": 0.65, "joy": 0.25, "fear": 0.72, "sadness": 0.55}),
        ("NJ", "New Jersey", {"anger": 0.75, "joy": 0.15, "fear": 0.85, "sadness": 0.45}),
        
        # HIGH SADNESS (0.7-0.8)
        ("WV", "West Virginia", {"anger": 0.45, "joy": 0.15, "fear": 0.55, "sadness": 0.82}),
        ("MS", "Mississippi", {"anger": 0.55, "joy": 0.25, "fear": 0.45, "sadness": 0.78}),
        ("AL", "Alabama", {"anger": 0.65, "joy": 0.35, "fear": 0.35, "sadness": 0.75}),
        
        # BALANCED HIGH
        ("WA", "Washington", {"anger": 0.45, "joy": 0.68, "fear": 0.35, "sadness": 0.25}),
        ("OR", "Oregon", {"anger": 0.35, "joy": 0.75, "fear": 0.45, "sadness": 0.35}),
        
        # LOW EMOTIONS
        ("ND", "North Dakota", {"anger": 0.15, "joy": 0.35, "fear": 0.25, "sadness": 0.15}),
        ("SD", "South Dakota", {"anger": 0.25, "joy": 0.25, "fear": 0.15, "sadness": 0.25}),
        ("WY", "Wyoming", {"anger": 0.35, "joy": 0.15, "fear": 0.25, "sadness": 0.35}),
        
        # MEDIUM RANGE
        ("OH", "Ohio", {"anger": 0.45, "joy": 0.55, "fear": 0.35, "sadness": 0.45}),
        ("PA", "Pennsylvania", {"anger": 0.55, "joy": 0.45, "fear": 0.45, "sadness": 0.35}),
        ("MI", "Michigan", {"anger": 0.65, "joy": 0.35, "fear": 0.55, "sadness": 0.55}),
    ]
    
    tweet_id = 1000000
    total = 0
    
    for state_code, state_name, emotions in states_data:
        print(f"📊 {state_name}: anger={emotions['anger']}, joy={emotions['joy']}, fear={emotions['fear']}, sadness={emotions['sadness']}")
        
        # Generate 500 tweets per state
        for i in range(500):
            # Add small variation
            anger = max(0.0, min(1.0, emotions['anger'] + random.uniform(-0.05, 0.05)))
            joy = max(0.0, min(1.0, emotions['joy'] + random.uniform(-0.05, 0.05)))
            fear = max(0.0, min(1.0, emotions['fear'] + random.uniform(-0.05, 0.05)))
            sadness = max(0.0, min(1.0, emotions['sadness'] + random.uniform(-0.05, 0.05)))
            
            # Fill other emotions
            surprise = random.uniform(0.2, 0.6)
            anticipation = random.uniform(0.3, 0.7)
            trust = random.uniform(0.2, 0.8)
            disgust = random.uniform(0.1, 0.5)
            
            # Sentiment
            if joy > 0.6:
                sentiment = 'positive'
            elif anger > 0.6 or fear > 0.6 or sadness > 0.6:
                sentiment = 'negative'
            else:
                sentiment = 'neutral'
            
            # Random timestamp
            days_ago = random.randint(0, 180)
            timestamp = datetime.now() - timedelta(days=days_ago)
            
            cursor.execute("""
                INSERT INTO tweets (
                    tweet_id, username, raw_text, timestamp,
                    state_code, state_name, context,
                    likes, retweets, replies, views,
                    anger, fear, sadness, surprise, joy,
                    anticipation, trust, disgust,
                    sentiment, sentiment_confidence,
                    dominant_emotion, emotion_confidence, compound
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, (
                tweet_id, f'user_{i}', f'Tweet from {state_name}', timestamp,
                state_code, state_name, 'general',
                random.randint(0, 100), random.randint(0, 50), random.randint(0, 20), random.randint(100, 5000),
                round(anger, 3), round(fear, 3), round(sadness, 3), round(surprise, 3), round(joy, 3),
                round(anticipation, 3), round(trust, 3), round(disgust, 3),
                sentiment, 0.8, 'anger', max(anger, joy, fear, sadness), 0.0
            ))
            
            tweet_id += 1
            total += 1
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"✅ DONE! Generated {total:,} tweets with REAL SPREAD!")
    print("🎯 Texas: anger=0.85, California: joy=0.88, New York: fear=0.78")

if __name__ == "__main__":
    main()

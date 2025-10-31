#!/usr/bin/env python3
"""
Generate realistic emotion data with PROPER SPREAD across 0.1-0.9 range
"""

import psycopg2
import random
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

# US States
US_STATES = [
    ("AL", "Alabama"), ("AK", "Alaska"), ("AZ", "Arizona"), ("AR", "Arkansas"), ("CA", "California"),
    ("CO", "Colorado"), ("CT", "Connecticut"), ("DE", "Delaware"), ("FL", "Florida"), ("GA", "Georgia"),
    ("HI", "Hawaii"), ("ID", "Idaho"), ("IL", "Illinois"), ("IN", "Indiana"), ("IA", "Iowa"),
    ("KS", "Kansas"), ("KY", "Kentucky"), ("LA", "Louisiana"), ("ME", "Maine"), ("MD", "Maryland"),
    ("MA", "Massachusetts"), ("MI", "Michigan"), ("MN", "Minnesota"), ("MS", "Mississippi"), ("MO", "Missouri"),
    ("MT", "Montana"), ("NE", "Nebraska"), ("NV", "Nevada"), ("NH", "New Hampshire"), ("NJ", "New Jersey"),
    ("NM", "New Mexico"), ("NY", "New York"), ("NC", "North Carolina"), ("ND", "North Dakota"), ("OH", "Ohio"),
    ("OK", "Oklahoma"), ("OR", "Oregon"), ("PA", "Pennsylvania"), ("RI", "Rhode Island"), ("SC", "South Carolina"),
    ("SD", "South Dakota"), ("TN", "Tennessee"), ("TX", "Texas"), ("UT", "Utah"), ("VT", "Vermont"),
    ("VA", "Virginia"), ("WA", "Washington"), ("WV", "West Virginia"), ("WI", "Wisconsin"), ("WY", "Wyoming"),
    ("DC", "District of Columbia")
]

EMOTIONS = ["anger", "fear", "sadness", "surprise", "joy", "anticipation", "trust", "disgust"]

def connect_db():
    return psycopg2.connect(
        host='localhost',
        port=5432,
        database='tweetdb',
        user='tweetuser',
        password='tweetpass'
    )

def create_state_emotion_profile(state_code: str) -> Dict[str, float]:
    """Create REALISTIC emotion profiles with WIDE SPREAD"""
    
    # Define state personality types with DRAMATIC differences
    state_profiles = {
        # HIGH ANGER STATES (0.7-0.9 anger)
        'TX': {'anger': 0.85, 'fear': 0.15, 'sadness': 0.25, 'surprise': 0.35, 'joy': 0.45, 'anticipation': 0.55, 'trust': 0.25, 'disgust': 0.75},
        'FL': {'anger': 0.78, 'fear': 0.45, 'sadness': 0.35, 'surprise': 0.65, 'joy': 0.55, 'anticipation': 0.45, 'trust': 0.35, 'disgust': 0.65},
        'AZ': {'anger': 0.82, 'fear': 0.25, 'sadness': 0.15, 'surprise': 0.45, 'joy': 0.35, 'anticipation': 0.55, 'trust': 0.45, 'disgust': 0.75},
        
        # HIGH JOY STATES (0.7-0.9 joy)
        'CA': {'anger': 0.25, 'fear': 0.15, 'sadness': 0.25, 'surprise': 0.45, 'joy': 0.88, 'anticipation': 0.75, 'trust': 0.65, 'disgust': 0.15},
        'HI': {'anger': 0.15, 'fear': 0.25, 'sadness': 0.15, 'surprise': 0.35, 'joy': 0.92, 'anticipation': 0.85, 'trust': 0.88, 'disgust': 0.05},
        'CO': {'anger': 0.35, 'fear': 0.25, 'sadness': 0.15, 'surprise': 0.55, 'joy': 0.82, 'anticipation': 0.75, 'trust': 0.65, 'disgust': 0.25},
        
        # HIGH FEAR STATES (0.6-0.8 fear)
        'NY': {'anger': 0.55, 'fear': 0.78, 'sadness': 0.45, 'surprise': 0.65, 'joy': 0.35, 'anticipation': 0.45, 'trust': 0.25, 'disgust': 0.55},
        'IL': {'anger': 0.65, 'fear': 0.72, 'sadness': 0.55, 'surprise': 0.45, 'joy': 0.25, 'anticipation': 0.35, 'trust': 0.35, 'disgust': 0.65},
        'NJ': {'anger': 0.75, 'fear': 0.85, 'sadness': 0.45, 'surprise': 0.55, 'joy': 0.15, 'anticipation': 0.25, 'trust': 0.15, 'disgust': 0.75},
        
        # HIGH SADNESS STATES (0.6-0.8 sadness)
        'WV': {'anger': 0.45, 'fear': 0.55, 'sadness': 0.82, 'surprise': 0.25, 'joy': 0.15, 'anticipation': 0.25, 'trust': 0.35, 'disgust': 0.65},
        'MS': {'anger': 0.55, 'fear': 0.45, 'sadness': 0.78, 'surprise': 0.35, 'joy': 0.25, 'anticipation': 0.35, 'trust': 0.45, 'disgust': 0.55},
        'AL': {'anger': 0.65, 'fear': 0.35, 'sadness': 0.75, 'surprise': 0.25, 'joy': 0.35, 'anticipation': 0.45, 'trust': 0.55, 'disgust': 0.45},
        
        # HIGH TRUST STATES (0.7-0.9 trust)
        'VT': {'anger': 0.15, 'fear': 0.25, 'sadness': 0.25, 'surprise': 0.35, 'joy': 0.65, 'anticipation': 0.55, 'trust': 0.88, 'disgust': 0.15},
        'NH': {'anger': 0.25, 'fear': 0.35, 'sadness': 0.15, 'surprise': 0.45, 'joy': 0.75, 'anticipation': 0.65, 'trust': 0.82, 'disgust': 0.25},
        'ME': {'anger': 0.35, 'fear': 0.25, 'sadness': 0.35, 'surprise': 0.25, 'joy': 0.55, 'anticipation': 0.45, 'trust': 0.78, 'disgust': 0.35},
        
        # HIGH DISGUST STATES (0.7-0.9 disgust)
        'NV': {'anger': 0.75, 'fear': 0.45, 'sadness': 0.55, 'surprise': 0.35, 'joy': 0.25, 'anticipation': 0.35, 'trust': 0.15, 'disgust': 0.88},
        'LA': {'anger': 0.65, 'fear': 0.55, 'sadness': 0.65, 'surprise': 0.45, 'joy': 0.35, 'anticipation': 0.25, 'trust': 0.25, 'disgust': 0.82},
        
        # BALANCED HIGH STATES (multiple emotions 0.6+)
        'WA': {'anger': 0.45, 'fear': 0.35, 'sadness': 0.25, 'surprise': 0.75, 'joy': 0.68, 'anticipation': 0.82, 'trust': 0.72, 'disgust': 0.35},
        'OR': {'anger': 0.35, 'fear': 0.45, 'sadness': 0.35, 'surprise': 0.65, 'joy': 0.75, 'anticipation': 0.78, 'trust': 0.68, 'disgust': 0.25},
        
        # MODERATE STATES (0.3-0.6 range)
        'OH': {'anger': 0.45, 'fear': 0.35, 'sadness': 0.45, 'surprise': 0.35, 'joy': 0.55, 'anticipation': 0.45, 'trust': 0.55, 'disgust': 0.35},
        'PA': {'anger': 0.55, 'fear': 0.45, 'sadness': 0.35, 'surprise': 0.45, 'joy': 0.45, 'anticipation': 0.55, 'trust': 0.45, 'disgust': 0.45},
        'MI': {'anger': 0.65, 'fear': 0.55, 'sadness': 0.55, 'surprise': 0.35, 'joy': 0.35, 'anticipation': 0.45, 'trust': 0.35, 'disgust': 0.55},
        
        # LOW EMOTION STATES (0.1-0.3 range) - Calm states
        'ND': {'anger': 0.15, 'fear': 0.25, 'sadness': 0.15, 'surprise': 0.25, 'joy': 0.35, 'anticipation': 0.25, 'trust': 0.45, 'disgust': 0.15},
        'SD': {'anger': 0.25, 'fear': 0.15, 'sadness': 0.25, 'surprise': 0.15, 'joy': 0.25, 'anticipation': 0.35, 'trust': 0.35, 'disgust': 0.25},
        'WY': {'anger': 0.35, 'fear': 0.25, 'sadness': 0.35, 'surprise': 0.25, 'joy': 0.15, 'anticipation': 0.25, 'trust': 0.25, 'disgust': 0.35},
    }
    
    # If state has a predefined profile, use it
    if state_code in state_profiles:
        return state_profiles[state_code]
    
    # For remaining states, create random but realistic profiles
    random.seed(hash(state_code))
    
    # Pick a dominant emotion category
    categories = ['high_anger', 'high_joy', 'high_fear', 'high_sadness', 'balanced', 'low_emotion']
    category = random.choice(categories)
    
    if category == 'high_anger':
        return {
            'anger': round(random.uniform(0.7, 0.9), 2),
            'fear': round(random.uniform(0.1, 0.4), 2),
            'sadness': round(random.uniform(0.2, 0.5), 2),
            'surprise': round(random.uniform(0.3, 0.6), 2),
            'joy': round(random.uniform(0.1, 0.4), 2),
            'anticipation': round(random.uniform(0.3, 0.6), 2),
            'trust': round(random.uniform(0.1, 0.4), 2),
            'disgust': round(random.uniform(0.5, 0.8), 2)
        }
    elif category == 'high_joy':
        return {
            'anger': round(random.uniform(0.1, 0.3), 2),
            'fear': round(random.uniform(0.1, 0.3), 2),
            'sadness': round(random.uniform(0.1, 0.3), 2),
            'surprise': round(random.uniform(0.4, 0.7), 2),
            'joy': round(random.uniform(0.7, 0.9), 2),
            'anticipation': round(random.uniform(0.6, 0.8), 2),
            'trust': round(random.uniform(0.5, 0.8), 2),
            'disgust': round(random.uniform(0.1, 0.3), 2)
        }
    elif category == 'high_fear':
        return {
            'anger': round(random.uniform(0.4, 0.7), 2),
            'fear': round(random.uniform(0.7, 0.9), 2),
            'sadness': round(random.uniform(0.3, 0.6), 2),
            'surprise': round(random.uniform(0.5, 0.8), 2),
            'joy': round(random.uniform(0.1, 0.3), 2),
            'anticipation': round(random.uniform(0.2, 0.5), 2),
            'trust': round(random.uniform(0.1, 0.4), 2),
            'disgust': round(random.uniform(0.4, 0.7), 2)
        }
    elif category == 'balanced':
        return {
            'anger': round(random.uniform(0.3, 0.6), 2),
            'fear': round(random.uniform(0.3, 0.6), 2),
            'sadness': round(random.uniform(0.3, 0.6), 2),
            'surprise': round(random.uniform(0.4, 0.7), 2),
            'joy': round(random.uniform(0.4, 0.7), 2),
            'anticipation': round(random.uniform(0.4, 0.7), 2),
            'trust': round(random.uniform(0.4, 0.7), 2),
            'disgust': round(random.uniform(0.3, 0.6), 2)
        }
    else:  # low_emotion
        return {
            'anger': round(random.uniform(0.1, 0.3), 2),
            'fear': round(random.uniform(0.1, 0.3), 2),
            'sadness': round(random.uniform(0.1, 0.3), 2),
            'surprise': round(random.uniform(0.2, 0.4), 2),
            'joy': round(random.uniform(0.2, 0.4), 2),
            'anticipation': round(random.uniform(0.2, 0.4), 2),
            'trust': round(random.uniform(0.3, 0.5), 2),
            'disgust': round(random.uniform(0.1, 0.3), 2)
        }

def generate_tweets_for_state(state_code: str, state_name: str, num_tweets: int = 1000):
    """Generate tweets for a state with consistent emotion profile"""
    
    # Get the state's emotion profile
    emotion_profile = create_state_emotion_profile(state_code)
    
    tweets = []
    contexts = ["politics", "sports", "entertainment", "economy", "weather", "tech", "education", "social"]
    
    # Generate tweets over the last 6 months
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)
    
    for i in range(num_tweets):
        # Random timestamp in the last 6 months
        random_days = random.randint(0, 180)
        tweet_time = start_date + timedelta(days=random_days, 
                                          hours=random.randint(0, 23), 
                                          minutes=random.randint(0, 59))
        
        # Add some variation to emotions (±0.1) but keep the state character
        emotions = {}
        for emotion, base_value in emotion_profile.items():
            variation = random.uniform(-0.1, 0.1)
            emotions[emotion] = max(0.0, min(1.0, round(base_value + variation, 3)))
        
        # Determine sentiment from dominant emotion
        positive_emotions = {'joy', 'anticipation', 'trust'}
        negative_emotions = {'anger', 'fear', 'sadness', 'disgust'}
        
        pos_score = sum(emotions[e] for e in positive_emotions if e in emotions)
        neg_score = sum(emotions[e] for e in negative_emotions if e in emotions)
        
        if pos_score > neg_score + 0.2:
            sentiment = 'positive'
            sentiment_confidence = pos_score / 3.0
        elif neg_score > pos_score + 0.2:
            sentiment = 'negative'
            sentiment_confidence = neg_score / 4.0
        else:
            sentiment = 'neutral'
            sentiment_confidence = 0.5
        
        # Find dominant emotion
        dominant_emotion = max(emotions.items(), key=lambda x: x[1])[0]
        emotion_confidence = max(emotions.values())
        
        # Calculate compound score
        compound = max(-1.0, min(1.0, (pos_score - neg_score) / 4.0))
        
        tweet = {
            'tweet_id': 1000000 + len(tweets) + i,
            'username': f'user_{random.randint(1, 10000)}',
            'raw_text': f'Tweet about {random.choice(contexts)} from {state_name} - {tweet_time.strftime("%Y-%m-%d")}',
            'timestamp': tweet_time,
            'state_code': state_code,
            'state_name': state_name,
            'context': random.choice(contexts),
            'likes': random.randint(0, 1000),
            'retweets': random.randint(0, 500),
            'replies': random.randint(0, 200),
            'views': random.randint(100, 50000),
            'sentiment': sentiment,
            'sentiment_confidence': round(sentiment_confidence, 3),
            **emotions,
            'dominant_emotion': dominant_emotion,
            'emotion_confidence': round(emotion_confidence, 3),
            'compound': round(compound, 3)
        }
        tweets.append(tweet)
    
    return tweets

def insert_tweets(conn, tweets):
    """Insert tweets into database"""
    cursor = conn.cursor()
    
    for tweet in tweets:
        cursor.execute("""
            INSERT INTO tweets (
                tweet_id, username, raw_text, timestamp,
                state_code, state_name, context,
                likes, retweets, replies, views,
                sentiment, sentiment_confidence,
                anger, fear, sadness, surprise, joy,
                anticipation, trust, disgust,
                dominant_emotion, emotion_confidence, compound
            ) VALUES (
                %(tweet_id)s, %(username)s, %(raw_text)s, %(timestamp)s,
                %(state_code)s, %(state_name)s, %(context)s,
                %(likes)s, %(retweets)s, %(replies)s, %(views)s,
                %(sentiment)s, %(sentiment_confidence)s,
                %(anger)s, %(fear)s, %(sadness)s, %(surprise)s, %(joy)s,
                %(anticipation)s, %(trust)s, %(disgust)s,
                %(dominant_emotion)s, %(emotion_confidence)s, %(compound)s
            )
        """, tweet)
    
    conn.commit()
    cursor.close()

def main():
    print("🚀 Generating realistic emotion data with PROPER SPREAD...")
    
    # Connect to database
    conn = connect_db()
    
    # Clear existing data
    print("🗑️  Clearing old data...")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tweets")
    cursor.execute("DELETE FROM emotion_aggregates")
    conn.commit()
    cursor.close()
    
    total_tweets = 0
    
    # Generate data for each state
    for state_code, state_name in US_STATES:
        print(f"📊 Generating data for {state_name} ({state_code})...")
        
        # Generate 800-1200 tweets per state for good sample size
        num_tweets = random.randint(800, 1200)
        tweets = generate_tweets_for_state(state_code, state_name, num_tweets)
        
        # Insert tweets
        insert_tweets(conn, tweets)
        total_tweets += len(tweets)
        
        # Show emotion profile for this state
        if tweets:
            sample_tweet = tweets[0]
            emotions_str = ", ".join([f"{e}: {sample_tweet[e]}" for e in EMOTIONS])
            print(f"   Emotion profile: {emotions_str}")
    
    conn.close()
    
    print(f"✅ Generated {total_tweets:,} tweets with REALISTIC emotion spread!")
    print("🎯 Data now spans 0.1-0.9 range with dramatic state differences!")

if __name__ == "__main__":
    main()

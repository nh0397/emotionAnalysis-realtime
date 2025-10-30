#!/usr/bin/env python3
"""
Seed normalized synthetic tweet records for all US states across a recent time window.

Generates records compatible with the current tweets table schema used by db_consumer.py:
- sentiment (positive|negative|neutral) + sentiment_confidence
- emotions (anger, fear, sadness, surprise, joy, anticipation, trust, disgust)
- dominant_emotion, emotion_confidence, compound

Usage examples:
  python seed_fake_data.py --months 6 --per-day 8
  python seed_fake_data.py --days 90 --per-day 5 --dry-run
"""

import argparse
import math
import os
import random
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

import psycopg2


US_STATES: List[Tuple[str, str]] = [
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

EMOTIONS: List[str] = [
    "anger", "fear", "sadness", "surprise", "joy", "anticipation", "trust", "disgust"
]

# Map emotions to sentiment for synthetic sentiment attribution
POSITIVE_EMOTIONS = {"joy", "anticipation", "trust"}
NEGATIVE_EMOTIONS = {"anger", "fear", "sadness", "disgust"}


def connect_db():
    return psycopg2.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=int(os.getenv("PGPORT", "5432")),
        database=os.getenv("PGDATABASE", "tweetdb"),
        user=os.getenv("PGUSER", "tweetuser"),
        password=os.getenv("PGPASSWORD", "tweetpass"),
    )


def dirichlet_normalized(k: int, alpha: float = 1.5) -> List[float]:
    # Simple Dirichlet sampler using Gamma
    samples = [random.gammavariate(alpha, 1.0) for _ in range(k)]
    s = sum(samples)
    if s == 0:
        return [1.0 / k] * k
    return [x / s for x in samples]


def make_state_profile(seed: int) -> List[float]:
    random.seed(seed)
    # Bias vectors so different states lean differently
    base = dirichlet_normalized(len(EMOTIONS), alpha=random.uniform(1.2, 3.0))
    # Emphasize one or two emotions per state
    idx = random.sample(range(len(EMOTIONS)), k=2)
    for i in range(len(base)):
        if i in idx:
            base[i] *= random.uniform(1.5, 2.5)
        else:
            base[i] *= random.uniform(0.6, 1.1)
    # Renormalize
    s = sum(base)
    return [v / s for v in base]


STATE_BIASES: Dict[str, List[float]] = {code: make_state_profile(hash(code) & 0xFFFFFFFF) for code, _ in US_STATES}


def emotion_to_sentiment(emotion_values: Dict[str, float]) -> Tuple[str, float]:
    dominant = max(emotion_values.items(), key=lambda kv: kv[1])[0]
    if dominant in POSITIVE_EMOTIONS:
        return "positive", emotion_values[dominant]
    if dominant in NEGATIVE_EMOTIONS:
        return "negative", emotion_values[dominant]
    return "neutral", emotion_values[dominant]


def compute_compound(pos: float, neg: float) -> float:
    # Simple compound proxy in [-1,1]
    return max(min(pos - neg, 1.0), -1.0)


def generate_record(next_id: int, state_code: str, state_name: str, when: datetime) -> Dict[str, object]:
    # Random text/context scaffolding
    contexts = ["politics", "sports", "entertainment", "economy", "weather", "tech", "education"]
    context = random.choice(contexts)
    raw_text = f"Synthetic tweet about {context} in {state_name} at {when.date()}"

    # Each state gets consistent emotion values that don't change
    # Use state code as seed for consistent values per state
    random.seed(hash(state_code))
    
    # State-specific emotion intensity ranges
    state_hash = hash(state_code) % 100
    if state_hash < 30:  # 30% of states: low intensity (0.1-0.5 range)
        min_val, max_val = 0.1, 0.5
    elif state_hash < 60:  # 30% of states: high intensity (0.5-0.9 range)
        min_val, max_val = 0.5, 0.9
    else:  # 40% of states: full range (0.1-0.9 range)
        min_val, max_val = 0.1, 0.9
    
    # Generate consistent emotions for this state
    emotions = {}
    for name in EMOTIONS:
        # Fixed random value for this state (same for all entries)
        emotions[name] = round(random.uniform(min_val, max_val), 1)
    
    # Reset random seed to avoid affecting other states
    random.seed()

    # Sentiment from dominant emotion
    sentiment, sent_conf = emotion_to_sentiment(emotions)
    # Proxy positive/negative mass for compound
    pos_mass = sum(emotions[e] for e in POSITIVE_EMOTIONS)
    neg_mass = sum(emotions[e] for e in NEGATIVE_EMOTIONS)
    compound = round(compute_compound(pos_mass, neg_mass), 4)

    dominant_emotion = max(emotions.items(), key=lambda kv: kv[1])[0]
    emotion_conf = max(emotions.values())

    return {
        "tweet_id": next_id,
        "username": f"user_{next_id%1000}",
        "raw_text": raw_text,
        "timestamp": when.strftime("%Y-%m-%d %H:%M:%S"),
        "state_code": state_code,
        "state_name": state_name,
        "context": context,
        "likes": random.randint(0, 500),
        "retweets": random.randint(0, 200),
        "replies": random.randint(0, 100),
        "views": random.randint(10, 10_000),
        "sentiment": sentiment,
        "sentiment_confidence": round(sent_conf, 4),
        **emotions,
        "dominant_emotion": dominant_emotion,
        "emotion_confidence": round(emotion_conf, 4),
        "compound": compound,
    }


def insert_records(conn, records: List[Dict[str, object]]):
    cur = conn.cursor()
    for t in records:
        cur.execute(
            """
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
            """,
            t,
        )
    conn.commit()
    cur.close()


def main():
    parser = argparse.ArgumentParser(description="Seed normalized synthetic tweets")
    rng = parser.add_mutually_exclusive_group()
    rng.add_argument("--months", type=int, default=6, help="How many recent months to generate")
    rng.add_argument("--days", type=int, help="Override months with an exact day count")
    parser.add_argument("--per-day", type=int, default=6, help="Tweets per state per day")
    parser.add_argument("--dry-run", action="store_true", help="Do not insert, just print counts")
    args = parser.parse_args()

    days = args.days if args.days is not None else max(1, int(args.months * 30))
    end = datetime.now().date()
    start = end - timedelta(days=days - 1)

    # Create all timestamps at noon to simplify grouping; add jitter for variety
    all_dates = [start + timedelta(days=i) for i in range(days)]

    # Generate
    next_id = int(datetime.now().timestamp())  # monotonic-ish seed for tweet_id
    batch: List[Dict[str, object]] = []
    for day in all_dates:
        for code, name in US_STATES:
            for _ in range(args.per_day):
                when = datetime(day.year, day.month, day.day, 12, 0, 0) + timedelta(
                    minutes=random.randint(-300, 300)
                )
                batch.append(generate_record(next_id, code, name, when))
                next_id += 1

    if args.dry_run:
        print(f"Prepared {len(batch)} synthetic tweets for {len(US_STATES)} states across {days} days")
        return

    conn = connect_db()
    try:
        insert_records(conn, batch)
        print(f"Inserted {len(batch)} synthetic tweets spanning {days} days")
    finally:
        conn.close()


if __name__ == "__main__":
    main()



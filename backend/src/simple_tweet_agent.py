#!/usr/bin/env python3
"""
Simple Tweet Generator
Generates tweets based on keywords and prints them to console
"""

import json
import random
import time
from datetime import datetime
from typing import Dict, Any
from ollama import chat, ChatResponse

class SimpleTweetAgent:
    def __init__(self):
        self.tweet_id_counter = 1
        
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
        
        # US State abbreviations
        self.states = [
            'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
            'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
            'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
            'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
            'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
        ]

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
            print("Calling ollama")
            response: ChatResponse = chat(
                model='llama3.2:3b',
                messages=[{
                    'role': 'user',
                    'content': prompt
                }]
            )
            print("Ollama response: ", response)
            tweet_text = response.message.content.strip()
            
            # Ensure tweet fits Twitter's character limit
            if len(tweet_text) > 280:
                tweet_text = tweet_text[:277] + "..."
                
            # Ensure state tag is included
            if f"({state})" not in tweet_text:
                tweet_text = tweet_text.rstrip() + f" ({state})"
                
            return tweet_text
                
        except Exception as e:
            print(f"Error generating tweet: {e}")
            return f"Thoughts on {keyword}... 🤔 ({state})"

    def generate_tweet(self, keyword: str = None) -> Dict[str, Any]:
        """Generate a single tweet"""
        if keyword is None:
            keyword = random.choice(self.keywords)
            
        state = random.choice(self.states)
        tweet_text = self.generate_tweet_content(keyword, state)
        
        # Create tweet object (same format as would go to Kafka)
        tweet = {
            "id": self.tweet_id_counter,
            "username": f"tech_{random.randint(1000, 9999)}",
            "raw_text": tweet_text,
            "timestamp": datetime.now().isoformat(),
            "location": f"{state}",
            "keyword": keyword,
            "likes": random.randint(0, 1000),
            "retweets": random.randint(0, 200),
            "replies": random.randint(0, 50)
        }
        
        self.tweet_id_counter += 1
        return tweet

    def print_tweet(self, tweet: Dict[str, Any]):
        """Print tweet in a readable format"""
        print("\n📱 New Tweet Generated:")
        print("=" * 50)
        print(f"From: {tweet['username']} in {tweet['location']}")
        print(f"Keyword: {tweet['keyword']}")
        print(f"Tweet: {tweet['raw_text']}")
        print(f"Engagement: ❤️ {tweet['likes']} | 🔄 {tweet['retweets']} | 💬 {tweet['replies']}")
        print(f"Timestamp: {tweet['timestamp']}")
        print("\nKafka message format:")
        print(json.dumps(tweet, indent=2))
        print("=" * 50)

def main():
    agent = SimpleTweetAgent()
    print("\n🤖 Tweet Generator Started")
    print("Available keywords:", ", ".join(agent.keywords))
    print("\nGenerating tweets every 10 seconds... Press Ctrl+C to stop")
    
    try:
        while True:
            # Generate tweet from random keyword
            tweet = agent.generate_tweet()
            agent.print_tweet(tweet)
            
            # Wait 10 seconds before next tweet
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("\n\nTweet generator stopped")

if __name__ == "__main__":
    main()

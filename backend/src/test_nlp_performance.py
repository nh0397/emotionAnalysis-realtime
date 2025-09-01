#!/usr/bin/env python3
"""
Performance Test for NLP Pipeline
Tests both pure NLP performance and full system integration
"""

import time
import json
import random
from datetime import datetime
from ollama import chat, ChatResponse
from nlp_pipeline import CustomEmotionAnalyzer
from simple_tweet_agent import TweetGenerator
from system_logger import tweet_logger as logger

class LightweightTweetTester:
    def __init__(self):
        # Test keywords
        self.keywords = [
            "AI ethics",
            "remote work culture", 
            "tech layoffs",
            "startup funding",
            "ChatGPT updates",
            "coding practices",
            "tech interviews",
            "developer burnout",
            "machine learning",
            "blockchain technology"
        ]
        
        # US State abbreviations (subset for testing)
        self.states = ['CA', 'NY', 'TX', 'FL', 'WA', 'MA', 'IL', 'PA', 'OH', 'GA']
        
        # Initialize NLP Pipeline
        print("🧠 Loading NLP models...")
        nlp_start = time.time()
        self.emotion_analyzer = CustomEmotionAnalyzer()
        nlp_load_time = time.time() - nlp_start
        print(f"✅ NLP models loaded in {nlp_load_time:.2f}s")

    def generate_tweet_text(self, keyword: str, state: str) -> str:
        """Generate tweet content using Ollama"""
        prompt = f"""Generate a tweet about {keyword}.
        - Be expressive and authentic
        - Max 280 characters
        - Include hashtags
        - Be tech-focused
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
            print(f"❌ Ollama error: {e}")
            return f"Thoughts on {keyword}... 🤔 ({state})"

    def test_single_tweet(self, keyword: str = None) -> dict:
        """Generate and analyze a single tweet, return timing data"""
        if keyword is None:
            keyword = random.choice(self.keywords)
            
        state = random.choice(self.states)
        
        # Time the generation
        gen_start = time.time()
        tweet_text = self.generate_tweet_text(keyword, state)
        gen_time = time.time() - gen_start
        
        # Time the NLP processing
        nlp_start = time.time()
        try:
            emotion_results = self.emotion_analyzer.analyze_emotion(tweet_text)
            nlp_time = time.time() - nlp_start
            nlp_success = True
        except Exception as e:
            nlp_time = time.time() - nlp_start
            print(f"❌ NLP error: {e}")
            emotion_results = {"error": str(e)}
            nlp_success = False
        
        total_time = gen_time + nlp_time
        
        return {
            "keyword": keyword,
            "state": state,
            "text": tweet_text,
            "text_length": len(tweet_text),
            "emotion_results": emotion_results,
            "timing": {
                "generation_ms": round(gen_time * 1000, 1),
                "nlp_ms": round(nlp_time * 1000, 1),
                "total_ms": round(total_time * 1000, 1)
            },
            "success": nlp_success
        }

def run_pure_nlp_test(num_tweets=10):
    """Run pure NLP test without Kafka overhead"""
    print("🚀 Pure NLP Performance Test")
    print(f"📊 Testing {num_tweets} tweets (no Kafka overhead)")
    print("=" * 60)
    
    # Initialize tester
    setup_start = time.time()
    try:
        tester = LightweightTweetTester()
        setup_time = time.time() - setup_start
        print(f"✅ Setup completed in {setup_time:.2f}s")
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return
    
    print("-" * 60)
    
    # Performance tracking
    results = []
    generation_times = []
    nlp_times = []
    total_times = []
    successful = 0
    failed = 0
    
    # Run tests
    overall_start = time.time()
    
    for i in range(num_tweets):
        print(f"\n📝 Tweet {i+1}/{num_tweets}")
        
        try:
            result = tester.test_single_tweet()
            results.append(result)
            
            # Extract timings
            timing = result["timing"]
            generation_times.append(timing["generation_ms"])
            nlp_times.append(timing["nlp_ms"])
            total_times.append(timing["total_ms"])
            
            if result["success"]:
                successful += 1
                emotions = result["emotion_results"]
                dominant_emotion = emotions.get("dominant_emotion", "unknown")
                confidence = emotions.get("confidence", 0)
                
                print(f"   ✅ {timing['total_ms']}ms total")
                print(f"      📄 Text: {result['text'][:60]}...")
                print(f"      🎭 Dominant: {dominant_emotion} ({confidence:.3f})")
                print(f"      📊 All Emotions:")
                
                # Display all 10 emotions
                emotion_names = ['anger', 'fear', 'positive', 'sadness', 'surprise', 
                               'joy', 'anticipation', 'trust', 'negative', 'disgust']
                for emotion in emotion_names:
                    score = emotions.get(emotion, 0.0)
                    print(f"         {emotion}: {score:.3f}")
                    
                print(f"      ⏱️  Gen: {timing['generation_ms']}ms | NLP: {timing['nlp_ms']}ms")
            else:
                failed += 1
                print(f"   ❌ Failed in {timing['total_ms']}ms")
                
        except Exception as e:
            failed += 1
            print(f"   💥 Crashed: {e}")
    
    overall_time = time.time() - overall_start
    
    # Performance Analysis
    print("\n" + "=" * 60)
    print("📈 PURE NLP PERFORMANCE ANALYSIS")
    print("=" * 60)
    
    if successful > 0:
        # Calculate statistics
        avg_gen = sum(generation_times) / len(generation_times)
        avg_nlp = sum(nlp_times) / len(nlp_times)
        avg_total = sum(total_times) / len(total_times)
        
        min_nlp = min(nlp_times)
        max_nlp = max(nlp_times)
        
        print(f"🎯 Success Rate: {successful}/{num_tweets} ({(successful/num_tweets)*100:.1f}%)")
        print()
        print("⏱️  TIMING BREAKDOWN:")
        print(f"   🤖 Generation: {avg_gen:.1f}ms avg")
        print(f"   🧠 NLP Processing: {avg_nlp:.1f}ms avg (range: {min_nlp:.1f}-{max_nlp:.1f}ms)")
        print(f"   🎯 Total: {avg_total:.1f}ms avg")
        
        # Throughput calculations
        tweets_per_second = successful / overall_time
        tweets_per_minute = tweets_per_second * 60
        tweets_per_hour = tweets_per_minute * 60
        
        print(f"\n🚀 THROUGHPUT (without Kafka):")
        print(f"   Tweets/second: {tweets_per_second:.2f}")
        print(f"   Tweets/minute: {tweets_per_minute:.1f}")
        print(f"   Tweets/hour: {tweets_per_hour:.0f}")
        
        # NLP Performance rating
        if avg_nlp < 50:
            nlp_rating = "🟢 BLAZING FAST"
        elif avg_nlp < 100:
            nlp_rating = "🟢 EXCELLENT"
        elif avg_nlp < 200:
            nlp_rating = "🟡 GOOD"
        else:
            nlp_rating = "🟠 NEEDS OPTIMIZATION"
            
        print(f"\n🏆 NLP Performance: {nlp_rating}")
        
        # Emotion distribution summary
        print(f"\n🎭 EMOTION DISTRIBUTION SUMMARY:")
        emotion_names = ['anger', 'fear', 'positive', 'sadness', 'surprise', 
                        'joy', 'anticipation', 'trust', 'negative', 'disgust']
        emotion_totals = {emotion: 0.0 for emotion in emotion_names}
        
        # Calculate average emotion scores across all tweets
        for result in results:
            if result["success"]:
                for emotion in emotion_names:
                    emotion_totals[emotion] += result["emotion_results"].get(emotion, 0.0)
        
        # Display averages
        for emotion in emotion_names:
            avg_score = emotion_totals[emotion] / successful if successful > 0 else 0.0
            bar = "█" * int(avg_score * 20)  # Visual bar (20 chars max)
            print(f"   {emotion:12}: {avg_score:.3f} {bar}")
        
        # Dominant emotion frequency
        dominant_counts = {}
        for result in results:
            if result["success"]:
                dominant = result["emotion_results"].get("dominant_emotion", "unknown")
                dominant_counts[dominant] = dominant_counts.get(dominant, 0) + 1
        
        print(f"\n🏆 DOMINANT EMOTION FREQUENCY:")
        for emotion, count in sorted(dominant_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / successful) * 100 if successful > 0 else 0
            print(f"   {emotion}: {count}/{successful} ({percentage:.1f}%)")
        
    else:
        print("❌ No successful tweets generated")
    
    print(f"\n✅ Pure NLP test completed in {overall_time:.2f}s")

def run_full_system_test(num_tweets=5):
    """Run a performance test with specified number of tweets"""
    print("🚀 Starting NLP Performance Test...")
    print(f"📊 Testing with {num_tweets} tweets")
    print("-" * 60)
    
    # Initialize generator and measure setup time
    setup_start = time.time()
    try:
        generator = TweetGenerator()
        setup_time = time.time() - setup_start
        print(f"✅ Setup completed: {setup_time:.2f}s")
        print(f"   - NLP models loaded successfully")
        print(f"   - Kafka producer connected")
        print("-" * 60)
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return
    
    # Performance tracking
    times = {
        'generation': [],
        'nlp': [],
        'total': [],
        'kafka': []
    }
    
    successful_tweets = 0
    failed_tweets = 0
    
    # Generate test tweets
    test_keywords = [
        "artificial intelligence",
        "blockchain technology", 
        "remote work",
        "startup culture",
        "data science"
    ]
    
    print("🧪 Generating tweets with NLP analysis...")
    overall_start = time.time()
    
    for i in range(num_tweets):
        tweet_start = time.time()
        keyword = test_keywords[i % len(test_keywords)]
        
        print(f"\n📝 Tweet {i+1}/{num_tweets}: '{keyword}'")
        
        try:
            # Generate tweet (this includes NLP processing now)
            result = generator.generate_and_send_tweet(keyword)
            tweet_time = time.time() - tweet_start
            
            if result:
                successful_tweets += 1
                times['total'].append(tweet_time)
                print(f"   ✅ Success: {tweet_time:.3f}s")
            else:
                failed_tweets += 1
                print(f"   ❌ Failed: {tweet_time:.3f}s")
                
        except Exception as e:
            failed_tweets += 1
            tweet_time = time.time() - tweet_start
            print(f"   ❌ Error: {e} ({tweet_time:.3f}s)")
    
    overall_time = time.time() - overall_start
    
    # Print performance summary
    print("\n" + "=" * 60)
    print("📈 PERFORMANCE SUMMARY")
    print("=" * 60)
    
    if times['total']:
        avg_total = sum(times['total']) / len(times['total'])
        min_total = min(times['total'])
        max_total = max(times['total'])
        
        print(f"🎯 Success Rate: {successful_tweets}/{num_tweets} ({(successful_tweets/num_tweets)*100:.1f}%)")
        print(f"⏱️  Average Time per Tweet: {avg_total:.3f}s")
        print(f"🚀 Fastest Tweet: {min_total:.3f}s")
        print(f"🐌 Slowest Tweet: {max_total:.3f}s")
        print(f"📊 Total Test Time: {overall_time:.2f}s")
        print(f"🔄 Throughput: {successful_tweets/overall_time:.2f} tweets/second")
        
        # Estimate performance at scale
        tweets_per_hour = (successful_tweets / overall_time) * 3600
        tweets_per_day = tweets_per_hour * 24
        
        print(f"\n🔮 PROJECTED PERFORMANCE:")
        print(f"   📈 Tweets/hour: {tweets_per_hour:.0f}")
        print(f"   📈 Tweets/day: {tweets_per_day:.0f}")
        
        # Performance rating
        if avg_total < 2.0:
            rating = "🟢 EXCELLENT"
        elif avg_total < 5.0:
            rating = "🟡 GOOD"
        elif avg_total < 10.0:
            rating = "🟠 ACCEPTABLE"
        else:
            rating = "🔴 NEEDS OPTIMIZATION"
            
        print(f"\n🏆 Performance Rating: {rating}")
        
    else:
        print("❌ No successful tweets generated")
    
    # Cleanup
    generator.close()
    print(f"\n✅ Test completed. Check logs for detailed timing information.")

def main():
    """Main test function with menu"""
    print("🤖 TecViz NLP Performance Tester")
    print("Testing tweet generation with state-of-the-art emotion analysis")
    print()
    print("Choose test mode:")
    print("1. Pure NLP Test (fast, no Kafka overhead)")
    print("2. Full System Test (includes Kafka integration)")
    print("3. Both tests")
    print()
    
    try:
        choice = input("Enter your choice (1/2/3): ").strip()
        
        if choice == "1":
            run_pure_nlp_test(10)
        elif choice == "2":
            run_full_system_test(5)
        elif choice == "3":
            print("\n" + "="*60)
            print("RUNNING PURE NLP TEST FIRST")
            print("="*60)
            run_pure_nlp_test(10)
            
            print("\n\n" + "="*60)
            print("RUNNING FULL SYSTEM TEST")
            print("="*60)
            run_full_system_test(5)
        else:
            print("❌ Invalid choice. Running pure NLP test by default...")
            run_pure_nlp_test(10)
        
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

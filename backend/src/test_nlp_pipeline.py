#!/usr/bin/env python3
"""
Test NLP Pipeline with Sample Tweet Inputs
Tests the emotion analyzer with realistic tweet content to verify output format
"""

import sys
import time
from nlp_pipeline import CustomEmotionAnalyzer

def test_nlp_pipeline():
    """Test the NLP pipeline with sample tweet inputs"""
    print("🧠 Testing NLP Pipeline with Sample Inputs")
    print("=" * 60)
    
    # Sample tweets that the agent would generate
    sample_tweets = [
        "Just discovered some amazing AI trends! The future is here 🚀 #AI #CA",
        "Working on a new Machine Learning project today. The possibilities are endless! 💻 #ML #NY", 
        "Attended a great Data Science workshop. Learning never stops! 📚 #DataScience #TX",
        "Excited about the latest Cloud Computing developments! Technology moves so fast ⚡ #Cloud #FL",
        "Building something cool with Cybersecurity. Innovation is key! 🔧 #Security #WA",
        "Just deployed my first Blockchain solution. Feeling accomplished! 🎉 #Blockchain #MA",
        "Reading about IoT best practices. Knowledge is power! 📖 #IoT #IL",
        "Collaborating with amazing DevOps developers. Community is everything! 🤝 #DevOps #PA",
        "Exploring new Mobile Apps frameworks. Always learning! 🔍 #Mobile #OH",
        "Just finished a VR/AR certification. Skills upgraded! 🏆 #VR #AR #CO"
    ]
    
    print("🚀 Initializing NLP Pipeline...")
    start_time = time.time()
    
    try:
        analyzer = CustomEmotionAnalyzer()
        init_time = time.time() - start_time
        print(f"✅ NLP Pipeline initialized in {init_time:.2f}s")
        print()
    except Exception as e:
        print(f"❌ Failed to initialize NLP pipeline: {e}")
        return False
    
    print("🧪 Testing with sample tweets...")
    print("-" * 60)
    
    for i, tweet in enumerate(sample_tweets, 1):
        print(f"\n📝 Tweet {i}: {tweet}")
        
        # Analyze emotions
        analysis_start = time.time()
        try:
            result = analyzer.analyze_emotion(tweet)
            analysis_time = time.time() - analysis_start
            
            print(f"⏱️  Analysis time: {analysis_time:.3f}s")
            print(f"🎭 Dominant emotion: {result['dominant_emotion']} (confidence: {result['confidence']:.3f})")
            
            # Display emotion scores in a nice format
            print("📊 Emotion Scores:")
            emotions = ['anger', 'fear', 'sadness', 'surprise', 'joy', 
                       'anticipation', 'trust', 'disgust']
            
            for emotion in emotions:
                score = result.get(emotion, 0.0)
                bar = "█" * int(score * 20)  # Visual bar
                print(f"   {emotion:12}: {score:.4f} {bar}")
            
            # Sentiment display
            print("📊 Sentiment:")
            sentiment = result.get('sentiment', 'neutral')
            sentiment_conf = result.get('sentiment_confidence', 0.0)
            print(f"   sentiment     : {sentiment} (confidence: {sentiment_conf:.4f})")
            
            # Sentiment summary
            compound = result.get('compound', 0.0)
            pos = result.get('pos', 0.0)
            neg = result.get('neg', 0.0)
            neu = result.get('neu', 0.0)
            
            print(f"💭 Sentiment: pos={pos:.3f}, neg={neg:.3f}, neu={neu:.3f}, compound={compound:.3f}")
            
            # Show the exact format that would be sent to database (new schema)
            print("💾 Database Format:")
            db_format = {
                # Sentiment (3-way)
                'sentiment': result['sentiment'],
                'sentiment_confidence': result['sentiment_confidence'],
                
                # Emotions (8-way)
                'anger': result['anger'],
                'fear': result['fear'],
                'sadness': result['sadness'],
                'surprise': result['surprise'],
                'joy': result['joy'],
                'anticipation': result['anticipation'],
                'trust': result['trust'],
                'disgust': result['disgust'],
                
                # Analysis results
                'dominant_emotion': result['dominant_emotion'],
                'emotion_confidence': result['emotion_confidence'],
                'compound': result['compound']
            }
            print(f"   {db_format}")
            
        except Exception as e:
            analysis_time = time.time() - analysis_start
            print(f"❌ Analysis failed: {e}")
            print(f"⏱️  Failed after: {analysis_time:.3f}s")
        
        print("-" * 60)
    
    # Performance summary
    print(f"\n📈 Performance Summary:")
    stats = analyzer.get_performance_stats()
    for key, value in stats.items():
        print(f"   {key}: {value:.4f}")
    
    print("\n✅ NLP Pipeline test completed!")
    return True

if __name__ == "__main__":
    test_nlp_pipeline()

"""
Manual Test Script for Custom Emotion Pipeline
Interactive testing with user input before integration with tweet generator
"""

import sys
import os
import time
from pathlib import Path

# Add the src directory to Python path so we can import our modules
sys.path.append(str(Path(__file__).parent))

from nlp_pipeline import CustomEmotionAnalyzer


def print_banner():
    """Print a nice banner for the test script"""
    print("=" * 80)
    print("🧠 CUSTOM PYTORCH EMOTION PIPELINE TESTER")
    print("=" * 80)
    print("Testing state-of-the-art emotion analysis for tweet generation")
    print("Compatible with your existing 10-emotion visualization system")
    print("=" * 80)


def print_emotion_results(result, tweet_text):
    """Pretty print emotion analysis results"""
    print(f"\n📝 Analyzing: '{tweet_text}'")
    print("-" * 60)
    
    # Show processing info
    print(f"⚡ Processing Time: {result['processing_time']:.3f}s")
    print(f"🎯 Dominant Emotion: {result['dominant_emotion']} (confidence: {result['confidence']:.3f})")
    
    # Show all 10 emotions in a nice format
    print(f"\n📊 Complete Emotion Analysis:")
    emotions = ['anger', 'fear', 'positive', 'sadness', 'surprise', 
               'joy', 'anticipation', 'trust', 'negative', 'disgust']
    
    # Sort by score for better display
    emotion_scores = [(emotion, result[emotion]) for emotion in emotions]
    emotion_scores.sort(key=lambda x: x[1], reverse=True)
    
    for emotion, score in emotion_scores:
        bar_length = int(score * 50)  # Scale to 50 chars max
        bar = "█" * bar_length + "░" * (50 - bar_length)
        print(f"  {emotion:12} │{bar}│ {score:.4f}")
    
    # Show sentiment summary (VADER-compatible)
    print(f"\n💭 Sentiment Summary:")
    print(f"  Positive: {result['pos']:.3f}")
    print(f"  Negative: {result['neg']:.3f}")
    print(f"  Neutral:  {result['neu']:.3f}")
    print(f"  Compound: {result['compound']:+.3f}")


def test_predefined_examples(analyzer):
    """Test with predefined examples to validate the pipeline"""
    print("\n🧪 TESTING WITH PREDEFINED EXAMPLES")
    print("=" * 60)
    
    examples = [
        # Joy/Excitement
        ("I just got the job of my dreams! So excited!! 🎉", "joy"),
        ("This is absolutely AMAZING!!! Best day ever! 😍", "joy"),
        
        # Anger
        ("This is so frustrating!!! Why does this always happen to me?! 😡", "anger"),
        ("I can't believe they did this! Absolutely unacceptable! 🤬", "anger"),
        
        # Sadness
        ("Feeling really down today... nothing seems to go right 😢", "sadness"),
        ("Lost my best friend today. Heart is broken 💔", "sadness"),
        
        # Fear/Anxiety  
        ("Really worried about the upcoming presentation... 😰", "fear"),
        ("This is terrifying! I don't know what to do! 😨", "fear"),
        
        # Surprise
        ("OMG I can't believe this just happened! Totally unexpected! 😮", "surprise"),
        ("Plot twist! Did NOT see that coming! 🤯", "surprise"),
        
        # Tech/Positive (for your context)
        ("This new AI technology is revolutionary! Game changer! 🚀", "positive"),
        ("Machine learning is solving problems I never thought possible! 🤖", "positive"),
        
        # Mixed emotions
        ("Happy about the promotion but sad to leave my team... 😊😢", "mixed"),
        ("Excited for the future but nervous about changes ahead 🎢", "mixed")
    ]
    
    for i, (text, expected_category) in enumerate(examples, 1):
        print(f"\n📋 Example {i} (Expected: {expected_category})")
        result = analyzer.analyze_emotion(text)
        print_emotion_results(result, text)
        
        # Check if dominant emotion aligns with expectation
        dominant = result['dominant_emotion']
        if expected_category == "mixed":
            print(f"✅ Mixed emotion detected: {dominant}")
        elif expected_category in dominant or dominant in expected_category:
            print(f"✅ Correct emotion detected!")
        else:
            print(f"⚠️  Expected {expected_category}, got {dominant}")
        
        print("-" * 60)


def interactive_testing(analyzer):
    """Interactive testing with user input"""
    print("\n💬 INTERACTIVE TESTING MODE")
    print("=" * 60)
    print("Enter your own text to analyze emotions!")
    print("Type 'quit', 'exit', or 'q' to stop")
    print("Type 'examples' to see predefined test cases")
    print("Type 'stats' to see performance statistics")
    print("-" * 60)
    
    while True:
        try:
            user_input = input("\n🎤 Enter text to analyze: ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            elif user_input.lower() == 'examples':
                test_predefined_examples(analyzer)
                continue
            elif user_input.lower() == 'stats':
                stats = analyzer.get_performance_stats()
                print(f"\n📊 Performance Statistics:")
                for key, value in stats.items():
                    print(f"  {key}: {value:.4f}")
                continue
            
            # Analyze the user input
            start_time = time.time()
            result = analyzer.analyze_emotion(user_input)
            
            print_emotion_results(result, user_input)
            
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted by user. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error analyzing text: {e}")
            continue


def main():
    """Main function to run the emotion pipeline tester"""
    print_banner()
    
    print("\n🔄 Initializing Custom Emotion Analyzer...")
    print("This may take a moment to download models on first run...")
    
    try:
        # Initialize the analyzer
        analyzer = CustomEmotionAnalyzer()
        
        print(f"\n✅ Analyzer initialized successfully!")
        print(f"📱 Device: {analyzer.device}")
        print(f"🧠 Emotion Model: {analyzer.emotion_model_name}")
        print(f"💭 Sentiment Model: {analyzer.sentiment_model_name}")
        
        # Quick validation test
        print(f"\n🏃 Quick validation test...")
        test_result = analyzer.analyze_emotion("I love this new technology! 🚀")
        print(f"✅ Test completed in {test_result['processing_time']:.3f}s")
        
        # Choose testing mode
        print(f"\n🎮 Choose testing mode:")
        print(f"1. Interactive testing (enter your own text)")
        print(f"2. Predefined examples testing")
        print(f"3. Both")
        
        while True:
            choice = input("\nEnter choice (1/2/3): ").strip()
            
            if choice == '1':
                interactive_testing(analyzer)
                break
            elif choice == '2':
                test_predefined_examples(analyzer)
                break
            elif choice == '3':
                test_predefined_examples(analyzer)
                interactive_testing(analyzer)
                break
            else:
                print("❌ Invalid choice. Please enter 1, 2, or 3.")
        
        # Final performance stats
        print(f"\n📊 Final Performance Statistics:")
        stats = analyzer.get_performance_stats()
        for key, value in stats.items():
            print(f"  {key}: {value:.4f}")
        
        print(f"\n🎯 Pipeline testing completed!")
        print(f"Ready for integration with tweet generator! 🚀")
        
    except Exception as e:
        print(f"\n❌ Failed to initialize analyzer: {e}")
        print(f"💡 Make sure you have installed all dependencies:")
        print(f"   pip install torch transformers datasets accelerate scikit-learn")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

"""
Custom PyTorch Emotion Analyzer
High-performance emotion analysis pipeline using state-of-the-art transformer models
Drop-in replacement for VADER with 10-emotion compatibility
"""

import torch
import torch.nn.functional as F
from transformers import (
    AutoTokenizer, AutoModelForSequenceClassification,
    pipeline, logging
)
import numpy as np
from typing import List, Dict, Any, Optional, Union
import warnings
import time
from pathlib import Path

from .text_preprocessor import TextPreprocessor
from .emotion_mapper import EmotionMapper

# Suppress transformers warnings for cleaner output
logging.set_verbosity_error()
warnings.filterwarnings("ignore")


class CustomEmotionAnalyzer:
    """
    Custom PyTorch-based emotion analyzer optimized for real-time tweet processing
    """
    
    def __init__(self, 
                 emotion_model: str = "j-hartmann/emotion-english-distilroberta-base",
                 sentiment_model: str = "cardiffnlp/twitter-roberta-base-sentiment-latest",
                 device: Optional[str] = None,
                 cache_dir: Optional[str] = None):
        """
        Initialize the custom emotion analyzer
        
        Args:
            emotion_model: HuggingFace model for emotion detection
            sentiment_model: HuggingFace model for sentiment analysis
            device: Device to run models on ('cuda', 'cpu', or None for auto)
            cache_dir: Directory to cache downloaded models
        """
        print("🚀 Initializing Custom Emotion Analyzer...")
        
        # Setup device
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)
        
        print(f"📱 Using device: {self.device}")
        
        # Initialize components
        self.preprocessor = TextPreprocessor()
        self.emotion_mapper = EmotionMapper()
        
        # Cache directory for models
        self.cache_dir = cache_dir or str(Path.home() / ".cache" / "tweet_emotion_models")
        
        # Model configuration
        self.emotion_model_name = emotion_model
        self.sentiment_model_name = sentiment_model
        
        # Initialize models
        self._load_models()
        
        # Performance tracking
        self.inference_times = []
        
        print("✅ Custom Emotion Analyzer initialized successfully!")
    
    def _load_models(self):
        """Load and initialize all models"""
        print("📦 Loading emotion detection model...")
        start_time = time.time()
        
        try:
            # Emotion model (RoBERTa-based) - Use SafeTensors for security
            self.emotion_tokenizer = AutoTokenizer.from_pretrained(
                self.emotion_model_name,
                cache_dir=self.cache_dir
            )
            self.emotion_model = AutoModelForSequenceClassification.from_pretrained(
                self.emotion_model_name,
                cache_dir=self.cache_dir,
                use_safetensors=True  # Force SafeTensors usage
            ).to(self.device)
            
            # Set to evaluation mode for inference
            self.emotion_model.eval()
            
            print(f"✅ Emotion model loaded in {time.time() - start_time:.2f}s")
            
        except Exception as e:
            print(f"❌ Failed to load emotion model: {e}")
            # Fallback to pipeline approach
            self.emotion_pipeline = pipeline(
                "text-classification",
                model=self.emotion_model_name,
                device=0 if self.device.type == "cuda" else -1,
                return_all_scores=True
            )
            self.emotion_model = None
            print("🔄 Using pipeline fallback for emotion model")
        
        print("📦 Loading sentiment analysis model...")
        start_time = time.time()
        
        try:
            # Sentiment model - Use SafeTensors for security
            self.sentiment_tokenizer = AutoTokenizer.from_pretrained(
                self.sentiment_model_name,
                cache_dir=self.cache_dir
            )
            self.sentiment_model = AutoModelForSequenceClassification.from_pretrained(
                self.sentiment_model_name,
                cache_dir=self.cache_dir,
                use_safetensors=True  # Force SafeTensors usage
            ).to(self.device)
            
            # Set to evaluation mode
            self.sentiment_model.eval()
            
            print(f"✅ Sentiment model loaded in {time.time() - start_time:.2f}s")
            
        except Exception as e:
            print(f"❌ Failed to load sentiment model: {e}")
            # Fallback to pipeline
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model=self.sentiment_model_name,
                device=0 if self.device.type == "cuda" else -1
            )
            self.sentiment_model = None
            print("🔄 Using pipeline fallback for sentiment model")
    
    @torch.no_grad()
    def _predict_emotion_direct(self, text: str) -> List[Dict[str, Any]]:
        """
        Direct PyTorch inference for emotion detection (faster)
        
        Args:
            text: Preprocessed text
            
        Returns:
            List of emotion predictions with labels and scores
        """
        if self.emotion_model is None:
            # Fallback to pipeline
            return self.emotion_pipeline(text)
        
        # Tokenize
        inputs = self.emotion_tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=512
        ).to(self.device)
        
        # Forward pass
        outputs = self.emotion_model(**inputs)
        
        # Get probabilities
        probabilities = F.softmax(outputs.logits, dim=-1)
        
        # Convert to expected format
        predictions = []
        for i, prob in enumerate(probabilities[0]):
            label = self.emotion_model.config.id2label[i]
            predictions.append({
                'label': label,
                'score': prob.item()
            })
        
        return predictions
    
    @torch.no_grad()
    def _predict_sentiment_direct(self, text: str) -> Dict[str, Any]:
        """
        Direct PyTorch inference for sentiment analysis (faster)
        
        Args:
            text: Preprocessed text
            
        Returns:
            Sentiment prediction with label and score
        """
        if self.sentiment_model is None:
            # Fallback to pipeline
            result = self.sentiment_pipeline(text)[0]
            return result
        
        # Tokenize
        inputs = self.sentiment_tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=512
        ).to(self.device)
        
        # Forward pass
        outputs = self.sentiment_model(**inputs)
        
        # Get probabilities
        probabilities = F.softmax(outputs.logits, dim=-1)
        
        # Get best prediction
        best_class_idx = torch.argmax(probabilities, dim=-1).item()
        best_score = probabilities[0][best_class_idx].item()
        best_label = self.sentiment_model.config.id2label[best_class_idx]
        
        return {
            'label': best_label,
            'score': best_score
        }
    
    def analyze_emotion(self, text: str, return_raw: bool = False) -> Dict[str, Any]:
        """
        Main emotion analysis function - drop-in VADER replacement
        
        Args:
            text: Raw tweet text
            return_raw: Whether to return raw model outputs too
            
        Returns:
            Dictionary with 10-emotion scores compatible with visualization
        """
        start_time = time.time()
        
        # Preprocess text
        cleaned_text = self.preprocessor.preprocess_for_model(text)
        
        # Skip empty texts
        if not cleaned_text.strip():
            return self._get_neutral_emotions()
        
        try:
            # Get emotion predictions
            emotion_predictions = self._predict_emotion_direct(cleaned_text)
            
            # Get sentiment predictions
            sentiment_prediction = self._predict_sentiment_direct(cleaned_text)
            
            # Map to 10-emotion schema
            emotion_scores = self.emotion_mapper.map_roberta_emotions(emotion_predictions)
            sentiment_scores = self.emotion_mapper.map_sentiment_to_emotions(sentiment_prediction)
            
            # Combine emotion and sentiment
            combined_scores = self.emotion_mapper.combine_emotion_sources(
                emotion_scores, sentiment_scores
            )
            
            # Normalize scores
            normalized_scores = self.emotion_mapper.normalize_scores(combined_scores)
            
            # Format for visualization compatibility
            result = self.emotion_mapper.format_for_visualization(normalized_scores)
            
            # Add metadata
            result['processing_time'] = time.time() - start_time
            result['model_emotion'] = self.emotion_model_name
            result['model_sentiment'] = self.sentiment_model_name
            
            # Add raw outputs if requested (for debugging)
            if return_raw:
                result['raw_emotions'] = emotion_predictions
                result['raw_sentiment'] = sentiment_prediction
                result['preprocessed_text'] = cleaned_text
            
            # Track performance
            self.inference_times.append(result['processing_time'])
            
            return result
            
        except Exception as e:
            print(f"❌ Error in emotion analysis: {e}")
            return self._get_neutral_emotions()
    
    def batch_analyze(self, texts: List[str], batch_size: int = 8) -> List[Dict[str, Any]]:
        """
        Analyze multiple texts efficiently in batches
        
        Args:
            texts: List of raw tweet texts
            batch_size: Number of texts to process together
            
        Returns:
            List of emotion analysis results
        """
        results = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_results = [self.analyze_emotion(text) for text in batch]
            results.extend(batch_results)
        
        return results
    
    def _get_neutral_emotions(self) -> Dict[str, Any]:
        """
        Return neutral emotion scores for error cases
        
        Returns:
            Neutral emotion dictionary
        """
        return {
            'anger': 0.1,
            'fear': 0.1,
            'positive': 0.2,
            'sadness': 0.1,
            'surprise': 0.1,
            'joy': 0.1,
            'anticipation': 0.1,
            'trust': 0.1,
            'negative': 0.1,
            'disgust': 0.1,
            'dominant_emotion': 'positive',
            'confidence': 0.2,
            'compound': 0.1,
            'pos': 0.2,
            'neg': 0.1,
            'neu': 0.7,
            'processing_time': 0.001
        }
    
    def get_performance_stats(self) -> Dict[str, float]:
        """
        Get performance statistics
        
        Returns:
            Dictionary with performance metrics
        """
        if not self.inference_times:
            return {'avg_time': 0.0, 'min_time': 0.0, 'max_time': 0.0}
        
        return {
            'avg_time': np.mean(self.inference_times),
            'min_time': np.min(self.inference_times),
            'max_time': np.max(self.inference_times),
            'total_inferences': len(self.inference_times)
        }
    
    def clear_cache(self):
        """Clear GPU cache to free memory"""
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


# Example usage and testing
if __name__ == "__main__":
    print("=== Custom PyTorch Emotion Analyzer Test ===\n")
    
    # Initialize analyzer
    analyzer = CustomEmotionAnalyzer()
    
    # Test tweets
    test_tweets = [
        "I'm so excited about this new technology! 🚀",
        "This is absolutely terrible... I hate everything about it 😠",
        "Feeling a bit confused about what just happened 🤔",
        "Beautiful sunset today, feeling grateful 🌅",
        "OMG this is the BEST DAY EVER!!! 😍",
        "I'm really worried about the future... 😰",
        "Just had an amazing conversation with my team! 💪",
        "This traffic is making me so angry!!! 🚗😡",
        "Surprised by how well this worked out! 😮",
        "Feeling peaceful and content right now 😌"
    ]
    
    print("🧪 Testing individual emotion analysis...\n")
    
    for i, tweet in enumerate(test_tweets, 1):
        print(f"Tweet {i}: {tweet}")
        
        # Analyze emotions
        result = analyzer.analyze_emotion(tweet, return_raw=True)
        
        print(f"Dominant Emotion: {result['dominant_emotion']} ({result['confidence']:.3f})")
        print(f"Processing Time: {result['processing_time']:.3f}s")
        print(f"Top 3 Emotions:")
        
        # Show top 3 emotions
        emotions = {k: v for k, v in result.items() 
                   if k in analyzer.emotion_mapper.target_emotions}
        top_emotions = sorted(emotions.items(), key=lambda x: x[1], reverse=True)[:3]
        
        for emotion, score in top_emotions:
            print(f"  - {emotion}: {score:.3f}")
        
        print("-" * 50)
    
    # Test batch processing
    print("\n🔄 Testing batch processing...\n")
    batch_start = time.time()
    batch_results = analyzer.batch_analyze(test_tweets)
    batch_time = time.time() - batch_start
    
    print(f"Batch processed {len(test_tweets)} tweets in {batch_time:.3f}s")
    print(f"Average time per tweet: {batch_time/len(test_tweets):.3f}s")
    
    # Performance stats
    print("\n📊 Performance Statistics:")
    stats = analyzer.get_performance_stats()
    for key, value in stats.items():
        print(f"  {key}: {value:.4f}")
    
    print("\n✅ Testing completed!")

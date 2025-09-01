"""
Text Preprocessing Module for Tweet Analysis
Handles cleaning, normalization, and preparation of tweets for emotion analysis
"""

import re
import string
from typing import List, Dict, Any


class TextPreprocessor:
    def __init__(self):
        """Initialize the text preprocessor with patterns and mappings"""
        self.url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        self.mention_pattern = re.compile(r'@[\w]+')
        self.hashtag_pattern = re.compile(r'#[\w]+')
        self.emoji_pattern = re.compile(r'[^\w\s,]')
        
        # Common contractions and expansions
        self.contractions = {
            "ain't": "am not", "aren't": "are not", "can't": "cannot",
            "couldn't": "could not", "didn't": "did not", "doesn't": "does not",
            "don't": "do not", "hadn't": "had not", "hasn't": "has not",
            "haven't": "have not", "he'd": "he would", "he'll": "he will",
            "he's": "he is", "i'd": "i would", "i'll": "i will",
            "i'm": "i am", "i've": "i have", "isn't": "is not",
            "it'd": "it would", "it'll": "it will", "it's": "it is",
            "let's": "let us", "shouldn't": "should not", "that's": "that is",
            "there's": "there is", "they'd": "they would", "they'll": "they will",
            "they're": "they are", "they've": "they have", "we'd": "we would",
            "we're": "we are", "we've": "we have", "weren't": "were not",
            "what's": "what is", "where's": "where is", "who's": "who is",
            "won't": "will not", "wouldn't": "would not", "you'd": "you would",
            "you'll": "you will", "you're": "you are", "you've": "you have"
        }
    
    def clean_text(self, text: str, preserve_emotion_indicators: bool = True) -> str:
        """
        Clean and normalize text while preserving emotion-relevant content
        
        Args:
            text: Raw tweet text
            preserve_emotion_indicators: Whether to preserve caps, punctuation for emotion
            
        Returns:
            Cleaned text ready for emotion analysis
        """
        if not text:
            return ""
        
        # Convert to lowercase (but preserve original for emotion analysis if needed)
        original_text = text
        text = text.lower()
        
        # Remove URLs but keep a marker if they might indicate sharing behavior
        text = self.url_pattern.sub(' [URL] ' if preserve_emotion_indicators else ' ', text)
        
        # Handle mentions - keep them as they might indicate social interaction
        text = self.mention_pattern.sub(' [MENTION] ' if preserve_emotion_indicators else ' ', text)
        
        # Handle hashtags - keep them as they often contain emotional content
        if preserve_emotion_indicators:
            text = self.hashtag_pattern.sub(lambda m: f" {m.group()[1:]} ", text)  # Remove # but keep word
        else:
            text = self.hashtag_pattern.sub(' ', text)
        
        # Expand contractions
        for contraction, expansion in self.contractions.items():
            text = text.replace(contraction, expansion)
        
        # Handle repeated characters (looove -> love, but preserve some emphasis)
        if preserve_emotion_indicators:
            text = re.sub(r'(.)\1{2,}', r'\1\1', text)  # Max 2 repetitions
        else:
            text = re.sub(r'(.)\1+', r'\1', text)  # Remove all repetitions
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def extract_features(self, text: str) -> Dict[str, Any]:
        """
        Extract text features that might be useful for emotion analysis
        
        Args:
            text: Original tweet text
            
        Returns:
            Dictionary of extracted features
        """
        features = {}
        
        # Basic statistics
        features['length'] = len(text)
        features['word_count'] = len(text.split())
        
        # Capitalization features (might indicate emotion)
        features['caps_ratio'] = sum(1 for c in text if c.isupper()) / len(text) if text else 0
        features['has_caps_words'] = bool(re.search(r'\b[A-Z]{2,}\b', text))
        
        # Punctuation features (emotional indicators)
        features['exclamation_count'] = text.count('!')
        features['question_count'] = text.count('?')
        features['ellipsis_count'] = text.count('...')
        
        # Social features
        features['mention_count'] = len(self.mention_pattern.findall(text))
        features['hashtag_count'] = len(self.hashtag_pattern.findall(text))
        features['url_count'] = len(self.url_pattern.findall(text))
        
        # Repetition features (emotional emphasis)
        features['repeated_chars'] = len(re.findall(r'(.)\1{2,}', text))
        
        return features
    
    def preprocess_for_model(self, text: str) -> str:
        """
        Preprocess text specifically for transformer model input
        
        Args:
            text: Raw tweet text
            
        Returns:
            Text ready for model tokenization
        """
        # Clean text while preserving some emotional indicators
        cleaned = self.clean_text(text, preserve_emotion_indicators=True)
        
        # Additional model-specific cleaning
        # Remove excessive punctuation but keep some for emotion
        cleaned = re.sub(r'[!]{3,}', '!!', cleaned)  # Max 2 exclamations
        cleaned = re.sub(r'[?]{3,}', '??', cleaned)  # Max 2 questions
        
        # Ensure reasonable length for transformer models (most handle 512 tokens)
        words = cleaned.split()
        if len(words) > 100:  # Conservative limit for tweets
            cleaned = ' '.join(words[:100])
        
        return cleaned.strip()
    
    def batch_preprocess(self, texts: List[str]) -> List[str]:
        """
        Preprocess a batch of texts efficiently
        
        Args:
            texts: List of raw tweet texts
            
        Returns:
            List of preprocessed texts
        """
        return [self.preprocess_for_model(text) for text in texts]


# Example usage and testing
if __name__ == "__main__":
    preprocessor = TextPreprocessor()
    
    # Test cases
    test_tweets = [
        "OMG!!! This is AMAZING!!! 😍😍😍 #excited #happy @friend check this out: https://example.com",
        "I can't believe this happened... 😢 why me???",
        "Just loving this new AI technology! So cooool 🚀 #AI #tech",
        "Ugh, this is sooooo frustrating!!! I hate when this happens 😠",
        "Beautiful day today ☀️ feeling grateful 🙏 #blessed"
    ]
    
    print("=== Text Preprocessing Examples ===\n")
    
    for i, tweet in enumerate(test_tweets, 1):
        print(f"Tweet {i}: {tweet}")
        
        # Clean text
        cleaned = preprocessor.clean_text(tweet)
        print(f"Cleaned: {cleaned}")
        
        # Model-ready text
        model_text = preprocessor.preprocess_for_model(tweet)
        print(f"Model Ready: {model_text}")
        
        # Extract features
        features = preprocessor.extract_features(tweet)
        print(f"Features: {features}")
        print("-" * 50)

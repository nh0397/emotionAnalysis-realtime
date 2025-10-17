"""
Emotion Mapping Module
Maps transformer model outputs to the 10-emotion schema used by the visualization system
"""

import numpy as np
from typing import Dict, List, Any, Tuple


class EmotionMapper:
    def __init__(self):
        """Initialize emotion mapper with mappings for different models"""
        
        # Updated schema: separate sentiment from emotions
        self.sentiment_categories = ['positive', 'negative', 'neutral']
        self.emotion_categories = [
            'anger', 'fear', 'sadness', 'surprise', 'joy', 
            'anticipation', 'trust', 'disgust'
        ]
        # Legacy support for old schema
        self.target_emotions = [
            'anger', 'fear', 'positive', 'sadness', 'surprise',
            'joy', 'anticipation', 'trust', 'negative', 'disgust'
        ]
        
        # Common transformer emotion model outputs and their mappings
        self.emotion_mappings = {
            # RoBERTa emotion model (j-hartmann/emotion-english-distilroberta-base)
            'roberta_emotions': {
                'anger': 'anger',
                'disgust': 'disgust', 
                'fear': 'fear',
                'joy': 'joy',
                'neutral': None,  # Will be distributed
                'sadness': 'sadness',
                'surprise': 'surprise'
            },
            
            # GoEmotions model mapping (if used)
            'go_emotions': {
                'admiration': 'positive',
                'amusement': 'joy',
                'anger': 'anger',
                'annoyance': 'anger',
                'approval': 'positive',
                'caring': 'trust',
                'confusion': 'surprise',
                'curiosity': 'anticipation',
                'desire': 'anticipation',
                'disappointment': 'sadness',
                'disapproval': 'negative',
                'disgust': 'disgust',
                'embarrassment': 'negative',
                'excitement': 'joy',
                'fear': 'fear',
                'gratitude': 'positive',
                'grief': 'sadness',
                'joy': 'joy',
                'love': 'positive',
                'nervousness': 'fear',
                'optimism': 'positive',
                'pride': 'positive',
                'realization': 'surprise',
                'relief': 'positive',
                'remorse': 'sadness',
                'sadness': 'sadness',
                'surprise': 'surprise',
                'neutral': None
            }
        }
        
        # Sentiment to positive/negative mapping weights
        self.sentiment_weights = {
            'POSITIVE': {'positive': 0.8, 'joy': 0.2},
            'NEGATIVE': {'negative': 0.7, 'sadness': 0.3},
            'NEUTRAL': {}  # Distributed among other emotions
        }
    
    def map_roberta_emotions(self, roberta_output: List[Dict]) -> Dict[str, float]:
        """
        Map RoBERTa emotion model output to 10-emotion schema
        
        Args:
            roberta_output: List of dicts with 'label' and 'score' keys
            
        Returns:
            Dictionary with 10 emotions and their scores
        """
        # Initialize all emotions to 0
        emotion_scores = {emotion: 0.0 for emotion in self.target_emotions}
        
        # Map direct emotions
        total_mapped = 0.0
        neutral_score = 0.0
        
        for item in roberta_output:
            label = item['label'].lower()
            score = item['score']
            
            if label in self.emotion_mappings['roberta_emotions']:
                target_emotion = self.emotion_mappings['roberta_emotions'][label]
                if target_emotion:
                    emotion_scores[target_emotion] = score
                    total_mapped += score
                else:
                    neutral_score = score
        
        # Distribute neutral score among unmapped emotions
        unmapped_emotions = [e for e in self.target_emotions if emotion_scores[e] == 0.0]
        if unmapped_emotions and neutral_score > 0:
            # Distribute neutral proportionally among anticipation, trust (typically neutral-positive)
            if 'anticipation' in unmapped_emotions:
                emotion_scores['anticipation'] = neutral_score * 0.4
            if 'trust' in unmapped_emotions:
                emotion_scores['trust'] = neutral_score * 0.4
            
            # Distribute remaining to other unmapped emotions
            remaining = neutral_score * 0.2
            other_unmapped = [e for e in unmapped_emotions if e not in ['anticipation', 'trust']]
            if other_unmapped:
                per_emotion = remaining / len(other_unmapped)
                for emotion in other_unmapped:
                    emotion_scores[emotion] = per_emotion
        
        return emotion_scores
    
    def map_sentiment_to_emotions(self, sentiment_output: Dict) -> Dict[str, float]:
        """
        Map sentiment analysis output to positive/negative emotions
        
        Args:
            sentiment_output: Dict with 'label' and 'score' keys
            
        Returns:
            Dictionary with emotion scores
        """
        emotion_scores = {emotion: 0.0 for emotion in self.target_emotions}
        
        label = sentiment_output['label'].upper()
        score = sentiment_output['score']
        
        if label in self.sentiment_weights:
            weights = self.sentiment_weights[label]
            for emotion, weight in weights.items():
                emotion_scores[emotion] = score * weight
        
        return emotion_scores
    
    def combine_emotion_sources(self, 
                              emotion_scores: Dict[str, float],
                              sentiment_scores: Dict[str, float],
                              emotion_weight: float = 0.7,
                              sentiment_weight: float = 0.3) -> Dict[str, float]:
        """
        Combine emotion model and sentiment model outputs
        
        Args:
            emotion_scores: Scores from emotion model
            sentiment_scores: Scores from sentiment model  
            emotion_weight: Weight for emotion model (0-1)
            sentiment_weight: Weight for sentiment model (0-1)
            
        Returns:
            Combined emotion scores
        """
        combined_scores = {}
        
        for emotion in self.target_emotions:
            emotion_score = emotion_scores.get(emotion, 0.0)
            sentiment_score = sentiment_scores.get(emotion, 0.0)
            
            # Weighted combination
            combined_score = (emotion_score * emotion_weight + 
                            sentiment_score * sentiment_weight)
            combined_scores[emotion] = combined_score
        
        return combined_scores
    
    def normalize_scores(self, scores: Dict[str, float]) -> Dict[str, float]:
        """
        Normalize emotion scores to sum to 1.0
        
        Args:
            scores: Raw emotion scores
            
        Returns:
            Normalized emotion scores
        """
        total = sum(scores.values())
        if total == 0:
            # If no emotions detected, return uniform distribution
            uniform_score = 1.0 / len(self.target_emotions)
            return {emotion: uniform_score for emotion in self.target_emotions}
        
        return {emotion: score / total for emotion, score in scores.items()}
    
    def get_dominant_emotion(self, scores: Dict[str, float]) -> Tuple[str, float]:
        """
        Get the dominant emotion and its confidence
        
        Args:
            scores: Emotion scores
            
        Returns:
            Tuple of (dominant_emotion, confidence_score)
        """
        if not scores:
            return "neutral", 0.0
        
        dominant_emotion = max(scores, key=scores.get)
        confidence = scores[dominant_emotion]
        
        return dominant_emotion, confidence
    
    def format_for_visualization(self, scores: Dict[str, float]) -> Dict[str, Any]:
        """
        Format emotion scores for compatibility with existing visualization
        
        Args:
            scores: Normalized emotion scores
            
        Returns:
            Dictionary formatted for visualization system
        """
        # Get dominant emotion
        dominant_emotion, confidence = self.get_dominant_emotion(scores)
        
        # Format exactly like VADER output for drop-in compatibility
        formatted_output = {
            # Individual emotion scores (matching your visualization schema)
            'anger': round(scores.get('anger', 0.0), 4),
            'fear': round(scores.get('fear', 0.0), 4),
            'positive': round(scores.get('positive', 0.0), 4),
            'sadness': round(scores.get('sadness', 0.0), 4),
            'surprise': round(scores.get('surprise', 0.0), 4),
            'joy': round(scores.get('joy', 0.0), 4),
            'anticipation': round(scores.get('anticipation', 0.0), 4),
            'trust': round(scores.get('trust', 0.0), 4),
            'negative': round(scores.get('negative', 0.0), 4),
            'disgust': round(scores.get('disgust', 0.0), 4),
            
            # Meta information
            'dominant_emotion': dominant_emotion,
            'confidence': round(confidence, 4),
            
            # Aggregate scores for compatibility
            'compound': round(scores.get('positive', 0) - scores.get('negative', 0), 4),
            'pos': round(scores.get('positive', 0), 4),
            'neg': round(scores.get('negative', 0), 4),
            'neu': round(1.0 - scores.get('positive', 0) - scores.get('negative', 0), 4)
        }
        
        return formatted_output
    
    def extract_sentiment(self, sentiment_prediction: Dict[str, Any]) -> Tuple[str, float]:
        """
        Extract sentiment classification from sentiment model output
        
        Args:
            sentiment_prediction: Output from sentiment analysis model
            
        Returns:
            Tuple of (sentiment_label, confidence)
        """
        label = sentiment_prediction.get('label', '').lower()
        confidence = sentiment_prediction.get('score', 0.0)
        
        # Map sentiment model outputs to our 3-way classification
        if 'positive' in label or 'pos' in label:
            return 'positive', confidence
        elif 'negative' in label or 'neg' in label:
            return 'negative', confidence
        else:
            return 'neutral', confidence
    
    def extract_emotions(self, emotion_predictions: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Extract emotion scores from emotion model output
        
        Args:
            emotion_predictions: List of emotion predictions from emotion model
            
        Returns:
            Dictionary with emotion scores
        """
        emotion_scores = {emotion: 0.0 for emotion in self.emotion_categories}
        
        for prediction in emotion_predictions:
            label = prediction.get('label', '').lower()
            score = prediction.get('score', 0.0)
            
            # Map to our emotion categories
            if label in self.emotion_categories:
                emotion_scores[label] = score
            else:
                # Handle common mappings
                mappings = {
                    'disappointment': 'sadness',
                    'excitement': 'joy',
                    'nervousness': 'fear',
                    'optimism': 'joy',
                    'pessimism': 'sadness'
                }
                if label in mappings:
                    emotion_scores[mappings[label]] = score
        
        return emotion_scores
    
    def get_dominant_emotion(self, emotion_scores: Dict[str, float]) -> Tuple[str, float]:
        """
        Get the dominant emotion from emotion scores
        
        Args:
            emotion_scores: Dictionary of emotion scores
            
        Returns:
            Tuple of (dominant_emotion, confidence)
        """
        if not emotion_scores:
            return 'joy', 0.0
        
        dominant = max(emotion_scores, key=emotion_scores.get)
        confidence = emotion_scores[dominant]
        
        return dominant, confidence


# Example usage and testing
if __name__ == "__main__":
    mapper = EmotionMapper()
    
    # Test RoBERTa emotion mapping
    print("=== Emotion Mapping Examples ===\n")
    
    # Example RoBERTa output
    roberta_example = [
        {'label': 'joy', 'score': 0.8},
        {'label': 'anger', 'score': 0.1},
        {'label': 'sadness', 'score': 0.05},
        {'label': 'fear', 'score': 0.03},
        {'label': 'surprise', 'score': 0.02}
    ]
    
    print("RoBERTa Output:", roberta_example)
    emotion_scores = mapper.map_roberta_emotions(roberta_example)
    print("Mapped Emotions:", emotion_scores)
    
    # Example sentiment output
    sentiment_example = {'label': 'POSITIVE', 'score': 0.9}
    print("\nSentiment Output:", sentiment_example)
    sentiment_scores = mapper.map_sentiment_to_emotions(sentiment_example)
    print("Sentiment Emotions:", sentiment_scores)
    
    # Combine and normalize
    combined = mapper.combine_emotion_sources(emotion_scores, sentiment_scores)
    normalized = mapper.normalize_scores(combined)
    print("\nCombined & Normalized:", normalized)
    
    # Format for visualization
    visualization_format = mapper.format_for_visualization(normalized)
    print("\nVisualization Format:", visualization_format)
    
    print("\nDominant Emotion:", mapper.get_dominant_emotion(normalized))

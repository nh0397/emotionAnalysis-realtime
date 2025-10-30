# Model Evaluation Framework

This directory contains comprehensive evaluation tools for comparing NLP models on emotion analysis tasks.

## Overview

The evaluation framework tests multiple models against public datasets to determine the best-performing approach for our real-time analytics platform.

## Models Evaluated

1. **VADER** - Baseline sentiment analysis
2. **DistilRoBERTa-Emotion** - Transformer-based emotion classification
3. **GoEmotions-Electra** - Google's emotion model
4. **RoBERTa-Large** - Large-scale transformer model

## Datasets

- **Kaggle Twitter Emotion Dataset** (416,809 tweets)
- **6 emotion categories**: sadness, joy, love, anger, fear, surprise
- **Balanced distribution** across emotion classes
- **Real-world Twitter data** for authentic evaluation

## Evaluation Metrics

- **Accuracy**: Overall classification accuracy
- **F1-Score**: Harmonic mean of precision and recall
- **Speed**: Processing time per tweet
- **Consistency**: Performance across different emotion classes
- **Diversity**: Ability to detect various emotions

## Files

### Core Evaluation
- `kaggle_twitter_emotion_eval.py` - Main evaluation script
- `dataset_integration.py` - Dataset download and preprocessing
- `model_comparison_framework.py` - Evaluation framework
- `generate_report_analysis.py` - Report generation

### Outputs
- `outputs/twitter_emotion_report.md` - Comprehensive evaluation report
- `outputs/twitter_emotion_metrics_*.csv` - Performance metrics
- `database_schema_diagram.md` - Database schema visualization

## Usage

### Run Full Evaluation
```bash
cd backend/src
source ../realtime/bin/activate
python evaluation/kaggle_twitter_emotion_eval.py
```

### Environment Variables
- `KAGGLE_EVAL_SAMPLE=0` - Use full dataset (0) or sample size
- `VERBOSE=1` - Enable verbose logging
- `DISABLE_CLEAN=1` - Skip text preprocessing

### Generate Schema Diagram
```bash
python database_migration.py --yes
```

## Results

### Model Performance (Kaggle Dataset)
1. **DistilRoBERTa-Emotion**: 85.0% accuracy, 0.060s/tweet
2. **GoEmotions-Electra**: 82.3% accuracy, 0.045s/tweet  
3. **RoBERTa-Large**: 80.1% accuracy, 0.089s/tweet
4. **VADER**: 45.2% accuracy, 0.002s/tweet

### Key Findings
- **DistilRoBERTa-Emotion** provides the best balance of accuracy and speed
- **Transformer models** significantly outperform traditional sentiment analysis
- **Real-time processing** is feasible with optimized models
- **Proper evaluation** validates production model selection

## Methodology

1. **Dataset Preparation**: Download and clean public datasets
2. **Model Testing**: Run all models on identical test sets
3. **Statistical Analysis**: Calculate comprehensive metrics
4. **Performance Comparison**: Rank models by multiple criteria
5. **Report Generation**: Create detailed evaluation reports

## Integration

The evaluation results directly inform our production system:
- **Model Selection**: DistilRoBERTa-Emotion chosen for production
- **Schema Design**: Proper sentiment/emotion separation
- **Performance Optimization**: Real-time processing capabilities
- **Quality Assurance**: Validated accuracy and reliability

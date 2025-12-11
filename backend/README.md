# Backend Services

This directory contains all backend services for the TecVis 2.0 real-time analytics platform.

## Architecture

```
Tweet Agent → Kafka → Database Consumer → PostgreSQL
     ↓
API Server → React Frontend
```

## Services

### 1. Tweet Agent (`simple_tweet_agent.py`)
- **Purpose**: Generates realistic tweets using Ollama LLM
- **Frequency**: Every 10 seconds
- **Output**: JSON tweets with location, engagement metrics
- **Dependencies**: Ollama, Kafka

### 2. Database Consumer (`db_consumer.py`)
- **Purpose**: Consumes tweets from Kafka and stores in PostgreSQL
- **Features**: Real-time processing, emotion analysis, automatic aggregation
- **Schema**: Optimized 3-way sentiment + 8-way emotions
- **Dependencies**: Kafka, PostgreSQL, NLP Pipeline

### 3. API Server (`api_server.py`)
- **Purpose**: Serves real-time data via REST API and Server-Sent Events
- **Endpoints**:
  - `/emotionData` - State-level aggregated data
  - `/timeSeriesData` - Historical time series
  - `/timeSeriesData/emotion/<emotion>` - Emotion-specific time series
  - `/timeSeriesData/compare/<state1>/<state2>/<emotion>` - State comparisons
- **Features**: Real-time streaming, automatic updates

### 4. NLP Pipeline (`nlp_pipeline/`)
- **Purpose**: Advanced emotion and sentiment analysis
- **Models**: DistilRoBERTa-Emotion (85% accuracy), RoBERTa-Sentiment
- **Output**: Proper sentiment/emotion separation
- **Performance**: ~0.05s per tweet

## Database Schema

### Sentiment (3-way classification)
- `sentiment`: 'positive', 'negative', 'neutral'
- `sentiment_confidence`: Confidence score

### Emotions (8-way classification)
- `anger`, `fear`, `sadness`, `surprise`, `joy`, `anticipation`, `trust`, `disgust`
- `dominant_emotion`: Strongest emotion detected
- `emotion_confidence`: Confidence score

### Performance Features
- Automatic aggregation triggers
- Optimized indexes
- Real-time state-level metrics

## Setup

1. **Install dependencies**:
   ```bash
   cd backend
   python -m venv realtime
   source realtime/bin/activate
   pip install -r requirements.txt
   ```

2. **Start services**:
   ```bash
   # Start infrastructure
   docker-compose up -d
   
   # Start tweet agent
   python src/simple_tweet_agent.py
   
   # Start database consumer
   python src/db_consumer.py
   
   # Start API server
   python src/api_server.py
   ```

## Testing

- **NLP Pipeline**: `python src/test_nlp_pipeline.py`
- **Database Migration**: `python src/database_migration.py --yes`
- **Performance Testing**: `python src/test_nlp_performance.py`

## Evaluation

The `evaluation/` directory contains comprehensive model evaluation:
- **Kaggle Twitter Emotion Dataset** evaluation
- **Model comparison** (VADER vs Transformers)
- **Performance metrics** and reports
- **Statistical analysis** and visualizations

## Logging

All services use the unified logging system (`unified_logger.py`):
- **Structured logging** with timestamps
- **Performance metrics** tracking
- **Error handling** and debugging
- **Real-time monitoring** capabilities

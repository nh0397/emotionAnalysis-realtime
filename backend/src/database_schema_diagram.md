# Database Schema Diagram

Generated: 2026-04-08 15:49:54

## Mermaid Diagram

Copy this code into [Mermaid Live Editor](https://mermaid.live/) or any Mermaid-compatible tool:

```mermaid

graph TD
    subgraph "Tweet Analysis Database Schema"
        TWEETS["`**tweets**
        ---
        **Primary Data**
        • id (SERIAL PK)
        • tweet_id (BIGINT)
        • username (VARCHAR)
        • raw_text (TEXT)
        • timestamp (TIMESTAMP)
        • created_at (TIMESTAMP)
        
        **Location**
        • state_code (CHAR(2))
        • state_name (VARCHAR)
        • context (VARCHAR)
        
        **Social Metrics**
        • likes (INTEGER)
        • retweets (INTEGER)
        • replies (INTEGER)
        • views (INTEGER)
        
        **Sentiment (3-way)**
        • sentiment (VARCHAR)
        • sentiment_confidence (FLOAT)
        
        **Emotions (8-way)**
        • anger (FLOAT)
        • fear (FLOAT)
        • sadness (FLOAT)
        • surprise (FLOAT)
        • joy (FLOAT)
        • anticipation (FLOAT)
        • trust (FLOAT)
        • disgust (FLOAT)
        
        **Analysis Results**
        • dominant_emotion (VARCHAR)
        • emotion_confidence (FLOAT)
        • compound (FLOAT)`"]
        
        AGGREGATES["`**emotion_aggregates**
        ---
        **State-level Aggregates**
        • state_code (CHAR(2))
        • state_name (VARCHAR)
        
        **Sentiment Counts**
        • sentiment_positive_count
        • sentiment_negative_count
        • sentiment_neutral_count
        
        **Sentiment Averages**
        • sentiment_positive_avg
        • sentiment_negative_avg
        • sentiment_neutral_avg
        
        **Emotion Averages**
        • anger_avg
        • fear_avg
        • sadness_avg
        • surprise_avg
        • joy_avg
        • anticipation_avg
        • trust_avg
        • disgust_avg
        
        **Metadata**
        • tweet_count (INTEGER)
        • last_updated (TIMESTAMP)`"]
        
        TWEETS -->|"Aggregates by state"| AGGREGATES
        
        subgraph "Data Flow"
            KAFKA["`**Kafka Stream**
            Raw tweets`"]
            NLP["`**NLP Pipeline**
            DistilRoBERTa-Emotion
            • Sentiment: pos/neg/neu
            • Emotions: 8 categories`"]
            DB["`**PostgreSQL**
            Real-time storage`"]
            
            KAFKA --> NLP
            NLP --> DB
        end
        
        subgraph "API Endpoints"
            API1["`**/emotionData**
            State aggregates`"]
            API2["`**/timeSeriesData**
            Historical trends`"]
            API3["`**/timeSeriesData/compare**
            State comparisons`"]
        end
        
        AGGREGATES --> API1
        TWEETS --> API2
        TWEETS --> API3
    end
    
    classDef primaryTable fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef aggregateTable fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef processBox fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px
    classDef apiBox fill:#fff3e0,stroke:#ef6c00,stroke-width:2px
    
    class TWEETS primaryTable
    class AGGREGATES aggregateTable
    class KAFKA,NLP,DB processBox
    class API1,API2,API3 apiBox
    
```

## Schema Design Principles

### Sentiment vs Emotions
- **Sentiment**: 3-way classification (positive, negative, neutral)
- **Emotions**: 8-way classification (anger, fear, sadness, surprise, joy, anticipation, trust, disgust)

### Data Flow
1. **Kafka Stream**: Raw tweets from Twitter API
2. **NLP Pipeline**: DistilRoBERTa-Emotion analysis
3. **PostgreSQL**: Real-time storage with proper separation
4. **API Endpoints**: Serve aggregated and time-series data

### Performance Optimizations
- Indexes on timestamp, state_code, sentiment, dominant_emotion
- Automatic aggregation triggers
- Efficient query patterns for real-time dashboards

## Migration Notes
- Old schema mixed sentiment and emotions
- New schema properly separates concerns
- All existing APIs will need updates to use new column names

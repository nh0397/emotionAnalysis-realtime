# TecViz - The Real Time Analytics Platform

A modern, real-time analytics platform for analyzing emotions in tweets using state-of-the-art transformer models and a scalable Kafka-based architecture.

## Architecture Overview

```
Tweet Agent → Kafka Topic → Database Writer → PostgreSQL Database
     ↓                            ↓
API Server ← SSE Streaming ← Tweet Consumer
     ↓
React Frontend (Multi-page UI)
```

### Data Flow:
1. **Tweet Agent** generates realistic tweets every 10 seconds using Ollama LLM
2. **Custom NLP Pipeline** analyzes emotions using PyTorch transformers
3. **Kafka Topic** receives and distributes tweets for scalability
4. **Database Writer** stores tweets in PostgreSQL with full schema
5. **API Server** streams real-time data via Server-Sent Events (SSE)
6. **React Frontend** displays live tweets, historical data, and analytics

## Project Structure

```
Final Project/
├── frontend/                    # React.js multi-page application
│   ├── src/
│   │   ├── components/
│   │   │   ├── TweetDashboard.js     # Live tweet streaming
│   │   │   ├── HistoricalTweets.js   # Paginated historical data
│   │   │   ├── Analytics.js          # System metrics
│   │   │   └── Navigation.js         # Multi-page navigation
│   │   ├── App.js                    # Main application
│   │   └── App.css                   # Black/white gradient theme
│   └── package.json
├── backend/                     # Python backend services
│   ├── src/
│   │   ├── simple_tweet_agent.py    # Ollama-powered tweet generation
│   │   ├── db_consumer.py           # PostgreSQL integration
│   │   ├── api_server.py            # Flask SSE server
│   │   ├── unified_logger.py        # Single unified logging system
│   │   ├── test_nlp_performance.py  # NLP performance testing
│   │   └── nlp_pipeline/            # Custom PyTorch emotion analysis
│   │       ├── emotion_analyzer.py      # Main analyzer class
│   │       ├── text_preprocessor.py     # Text cleaning
│   │       └── emotion_mapper.py        # 10-emotion mapping
│   ├── requirements.txt
│   └── realtime/                    # Python virtual environment
├── docker-compose.yml              # PostgreSQL, Kafka, Zookeeper
├── start_system.sh                  # Automated system startup
├── stop_system.sh                   # Graceful system shutdown
└── README.md
```

## Quick Start

### Prerequisites
- Python 3.12 or higher
- Node.js (v16 or higher) 
- npm (v8 or higher)
- Docker and Docker Compose
- Git

### Installation & Running

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd "Final Project"
   ```

2. **Start the entire system**
   ```bash
   chmod +x start_system.sh
   ./start_system.sh
   ```

   This script will:
   - Start Docker services (PostgreSQL, Kafka, Zookeeper)
   - Wait for services to be ready with timeout checks
   - Create Python virtual environment and install dependencies
   - Initialize database schema
   - Start tweet generation agent
   - Start database writer
   - Start API server with SSE streaming
   - Install and start React frontend
   - Open the dashboard at http://localhost:3000

3. **Stop the system**
   ```bash
   ./stop_system.sh
   ```

### Manual Setup (Alternative)

#### Backend Setup
```bash
cd backend
python3 -m venv realtime
source realtime/bin/activate  # On Windows: realtime\Scripts\activate
pip install -r requirements.txt
```

#### Start Services Individually
```bash
# Start Docker services
docker-compose up -d

# Start tweet agent
cd backend/src
python simple_tweet_agent.py

# Start database consumer
python db_consumer.py

# Start API server
python api_server.py

# Start frontend
cd ../../frontend
npm install
npm start
```

## Access Points

- **Frontend Dashboard**: http://localhost:3000
- **API Server**: http://localhost:5000
- **Health Check**: http://localhost:5000/health
- **SSE Stream**: http://localhost:5000/stream
- **Historical API**: http://localhost:5000/api/tweets
- **Metrics API**: http://localhost:5000/api/metrics
- **PostgreSQL**: localhost:5432 (tweets database)
- **Kafka**: localhost:9092

## Custom PyTorch NLP Pipeline

### Features
- **State-of-the-art Models**: RoBERTa emotion detection + Twitter sentiment analysis
- **10-Emotion Compatibility**: Perfect drop-in replacement for VADER
- **High Performance**: 75ms average processing time per tweet
- **SafeTensors Security**: Uses secure model loading
- **Real-time Optimized**: CPU-based inference for production

### Emotion Schema
The system analyzes tweets across 10 emotions:
- **anger**: Frustrated, annoyed situations
- **fear**: Anxious, worried states
- **positive**: General positive outlook  
- **sadness**: Melancholic, down feelings
- **surprise**: Unexpected, shocking events
- **joy**: Happy, positive experiences
- **anticipation**: Excited about future
- **trust**: Faith in people, processes
- **negative**: Pessimistic views
- **disgust**: Repulsed by situations

### Testing the NLP Pipeline
```bash
cd backend/src
source ../realtime/bin/activate
python test_emotion_pipeline.py
```

## API Endpoints

### GET /health
Health check endpoint

### GET /stream
Server-Sent Events stream for real-time tweets
```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
```

### GET /api/tweets
Paginated historical tweets
```
Query Parameters:
- page: Page number (default: 1)
- limit: Items per page (default: 20)
```

### GET /api/metrics  
System performance metrics
```json
{
  "total_tweets": 1234,
  "tweets_last_hour": 36,
  "avg_processing_time": 0.075,
  "emotion_distribution": {...},
  "system_uptime": "2h 15m"
}
```

## Tweet Generation Agent

### Features
- **Ollama Integration**: Uses llama3.2:3b model via Python client
- **Realistic Content**: Tech-focused tweets with authentic language
- **Geographic Diversity**: US states only with abbreviated format (CA)
- **Automatic Generation**: Every 10 seconds
- **Kafka Integration**: Direct publishing to tweets topic
- **Structured Logging**: Comprehensive system tracking

### Data Format
```json
{
  "tweet_id": 123,
  "username": "tech_enthusiast_42",
  "raw_text": "Just discovered this amazing new AI framework!",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "state_code": "CA",
  "state_name": "California", 
  "context": "AI Technology",
  "likes": 15,
  "retweets": 3,
  "replies": 2,
  "views": 145,
  "anger": 0.021,
  "fear": 0.009,
  "positive": 0.824,
  "sadness": 0.024,
  "surprise": 0.498,
  "joy": 0.699,
  "anticipation": 0.031,
  "trust": 0.031,
  "negative": 0.008,
  "disgust": 0.002,
  "dominant_emotion": "joy",
  "confidence": 0.699,
  "compound": 0.238
}
```

## Database Schema

### PostgreSQL Tables
```sql
CREATE TABLE tweets (
  id SERIAL PRIMARY KEY,
  tweet_id INTEGER NOT NULL,
  username VARCHAR(255) NOT NULL,
  raw_text TEXT NOT NULL,
  timestamp TIMESTAMP NOT NULL,
  state_code CHAR(2) NOT NULL,
  state_name VARCHAR(255) NOT NULL,
  context VARCHAR(255) NOT NULL,
  likes INTEGER DEFAULT 0,
  retweets INTEGER DEFAULT 0,
  replies INTEGER DEFAULT 0,
  views INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Frontend Features

### Multi-Page Navigation
- **Live Stream**: Real-time tweet display with emotion analysis
- **Historical**: Paginated view of all stored tweets
- **Analytics**: System metrics and performance statistics

### Design
- **Modern UI**: Black and white gradient theme
- **Responsive**: Works on desktop, tablet, and mobile
- **Real-time Updates**: SSE-powered live streaming
- **Professional**: Clean design without emojis
- **Smooth Animations**: Glass morphism and shimmer effects

### Connection Management
- **Automatic Reconnection**: Handles network interruptions
- **Status Indicators**: Connected/Disconnected/Error states
- **Error Handling**: Graceful degradation and retry logic

## Technology Stack

### Frontend
- **React.js**: Component-based UI framework
- **Server-Sent Events**: Real-time data streaming
- **CSS3**: Modern styling with gradients and animations

### Backend
- **Python 3.12**: Main runtime
- **Flask**: Web framework for API server
- **Flask-CORS**: Cross-origin resource sharing
- **psycopg2**: PostgreSQL adapter
- **kafka-python-ng**: Kafka client library
- **ollama**: LLM integration

### NLP & AI
- **PyTorch**: Deep learning framework
- **Transformers**: Hugging Face transformer models
- **SafeTensors**: Secure model loading
- **scikit-learn**: Machine learning utilities

### Infrastructure
- **PostgreSQL**: Primary database
- **Apache Kafka**: Message streaming
- **Docker**: Containerization
- **Zookeeper**: Kafka coordination

## Performance Metrics

### NLP Pipeline
- **Average Processing**: 75ms per tweet
- **Throughput**: ~11 tweets per second
- **Accuracy**: 85%+ emotion detection accuracy
- **Memory**: Efficient CPU-based inference

### System Performance
- **Tweet Generation**: Every 10 seconds
- **Real-time Latency**: <100ms end-to-end
- **Database Performance**: Optimized with indexes
- **Frontend Updates**: Instant via SSE

## Development

### Adding New Features

1. **Backend**: Extend Flask routes in `api_server.py`
2. **Frontend**: Add components in `frontend/src/components/`
3. **NLP**: Modify pipeline in `backend/src/nlp_pipeline/`
4. **Database**: Update schema and writers

### Customizing Tweet Generation

Edit `backend/src/simple_tweet_agent.py`:
- Modify Ollama prompts for different content styles
- Adjust generation frequency
- Add new contexts or topics
- Change location distributions

### Testing

```bash
# Test NLP pipeline
cd backend/src
python test_emotion_pipeline.py

# Test individual components
python -m unittest discover

# Frontend testing
cd frontend
npm test
```

## Monitoring and Logging

### Log Files
- `backend/src/logs/system.log`: Unified system logs for all components

### System Health
- Health check endpoint: `/health`
- Metrics endpoint: `/api/metrics`
- Real-time monitoring via dashboard

## Troubleshooting

### Common Issues

1. **Models not loading**: Ensure internet connection for first-time model download
2. **Kafka connection errors**: Check Docker services are running
3. **Database connection**: Verify PostgreSQL container is healthy
4. **Port conflicts**: Default ports 3000, 5000, 5432, 9092 must be available

### Debug Commands
```bash
# Check Docker services
docker-compose ps

# View logs
docker-compose logs -f

# Check Python environment
source backend/realtime/bin/activate
pip list

# Test database connection
python backend/src/db_consumer.py
```

## License

This project is for educational purposes.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

**TecViz - Real-time analytics powered by state-of-the-art AI**
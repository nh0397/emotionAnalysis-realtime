# 🐦 Real-Time Emotion Analysis Dashboard

A modern, real-time dashboard for analyzing emotions in social media posts with a scalable Kafka-based architecture featuring WebSocket communication.

## 🏗️ Architecture Overview

```
Python Tweet Agent → Kafka Topic → Consumers → WebSocket Server → React Frontend
     (30s)              (tweets)     (2x)         (Real-time)      (Live UI)
```

### **Data Flow:**
1. **Python Tweet Agent** generates realistic tweets every 30 seconds
2. **Kafka Topic** receives and stores tweets for distribution
3. **Database Consumer** stores tweets in SQLite database
4. **WebSocket Consumer** forwards tweets to WebSocket server
5. **WebSocket Server** broadcasts tweets to connected clients
6. **React Frontend** displays real-time tweets with emotion analysis

## 📁 Project Structure

```
Final Project/
├── frontend/          # React.js frontend application
│   ├── src/
│   │   ├── components/
│   │   │   ├── TweetDashboard.js    # Twitter-like dashboard
│   │   │   └── TweetDashboard.css   # Modern styling
│   │   ├── App.js                   # WebSocket client
│   │   ├── App.css                  # App styling
│   │   └── index.js
│   └── package.json                 # Frontend dependencies
├── backend/           # Node.js/Express.js backend API
│   ├── app.js                       # WebSocket server
│   ├── tweet_agent.py              # Python tweet generation agent
│   ├── kafka_consumers.py          # Kafka consumers (DB + WebSocket)
│   ├── requirements.txt            # Python dependencies
│   └── package.json                # Backend dependencies
├── start_real_time_system.sh        # Complete system startup
└── README.md                        # Comprehensive documentation
```

## 🚀 Quick Start

### Prerequisites
- Node.js (v14 or higher)
- npm (v6 or higher)
- Python 3.7 or higher
- pip3
- **Kafka** (running on localhost:9092)

### Kafka Setup

**Option 1: Docker (Recommended)**
```bash
# Create docker-compose.yml for Kafka
docker-compose up -d
```

**Option 2: Local Kafka**
```bash
# Start Zookeeper and Kafka manually
# Ensure Kafka is running on localhost:9092
```

### Installation & Running

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd "Final Project"
   ```

2. **Start the entire system**
   ```bash
   chmod +x start_real_time_system.sh
   ./start_real_time_system.sh
   ```

   This script will:
   - Check Kafka availability
   - Install Python dependencies for tweet agent and consumers
   - Install Node.js dependencies for backend and frontend
   - Start the WebSocket server on port 9000
   - Start Kafka consumers (database + WebSocket)
   - Start the Python tweet generation agent
   - Start the frontend server on port 3000
   - Open the dashboard in your browser

### Manual Setup (Alternative)

#### Backend Setup
```bash
cd backend
pip3 install -r requirements.txt
npm install
npm start
```

#### Kafka Consumers Setup
```bash
cd backend
python3 kafka_consumers.py
```

#### Tweet Agent Setup (Optional)
```bash
cd backend
python3 tweet_agent.py
```

#### Frontend Setup
```bash
cd frontend
npm install
npm start
```

## 🌐 Access Points

- **Frontend Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:9000
- **Health Check**: http://localhost:9000/health
- **WebSocket**: ws://localhost:9000
- **Kafka**: localhost:9092

## 🔧 API Endpoints

### GET /
Returns API status and available endpoints

### GET /health
Health check endpoint

### POST /tweets
Receives tweets from Kafka consumer and broadcasts to WebSocket clients

### WebSocket Connection
Real-time tweet streaming endpoint

**Message Format:**
```json
{
  "type": "tweet",
  "data": {
    "id": 1,
    "username": "tech_enthusiast",
    "text": "Just had an amazing day at the beach! 😊",
    "timestamp": "2024-01-15T10:30:00.000Z",
    "emotion": "joy",
    "sentiment_score": 0.85,
    "location": "Miami, FL"
  },
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

## 🤖 Tweet Generation Agent

The system includes a **Python tweet generation agent** that:

### Features
- **Realistic tweet generation** with emotion-based templates
- **Automatic emotion analysis** with sentiment scoring
- **Diverse user profiles** with realistic usernames
- **Geographic diversity** with various US locations
- **Continuous generation** every 30 seconds
- **Kafka integration** for scalable message distribution

### Emotion Templates
The agent generates tweets based on 10 different emotions:
- **Joy** 😄 - Happy, positive experiences
- **Sadness** 😢 - Melancholic, missing someone
- **Anger** 😠 - Frustrated, annoyed situations
- **Fear** 😨 - Anxious, worried about future
- **Surprise** 😲 - Unexpected, shocking events
- **Trust** 🤝 - Faith in people, processes
- **Anticipation** 🤔 - Excited about possibilities
- **Disgust** 🤢 - Repulsed by situations
- **Positive** 😊 - General positive outlook
- **Negative** 😞 - Pessimistic views

### Agent Communication
- **Generates 1-3 tweets** every 30 seconds
- **Sends to Kafka topic** 'tweets' on localhost:9092
- **Includes emotion analysis** and sentiment scores
- **Realistic timestamps** and user data

## 📊 Kafka Consumers

### Database Consumer
- **Stores tweets** in SQLite database (`tweets.db`)
- **Persistent storage** for historical analysis
- **Automatic table creation** with proper schema
- **Error handling** and logging

### WebSocket Consumer
- **Forwards tweets** to WebSocket server
- **Real-time broadcasting** to connected clients
- **HTTP POST communication** with backend
- **Connection status monitoring**

## 🎨 Features

### Frontend
- **Real-time WebSocket connection** with automatic reconnection
- **Twitter-like interface** with modern design
- **Emotion analysis display** with color-coded badges
- **Connection status indicators** (Connected/Disconnected/Error)
- **Responsive design** for all devices
- **Live indicators** and smooth animations

### Backend
- **WebSocket server** with Express.js
- **Real-time data broadcasting** to multiple clients
- **Connection management** and status tracking
- **Health check endpoints** for monitoring
- **Error handling** and logging

### Tweet Agent
- **Python-based generation** with realistic content
- **Emotion-aware templates** for diverse content
- **Automatic sentiment scoring** based on emotions
- **Kafka producer** for scalable message distribution
- **Continuous operation** with configurable intervals

## 🛠️ Technology Stack

### Frontend
- **React.js** - UI framework
- **WebSocket API** - Real-time communication
- **CSS3** - Styling with modern features

### Backend
- **Node.js** - Runtime environment
- **Express.js** - Web framework
- **ws** - WebSocket library
- **CORS** - Cross-origin resource sharing

### Tweet Agent & Consumers
- **Python 3** - Scripting language
- **kafka-python** - Kafka client library
- **requests** - HTTP client for API communication
- **sqlite3** - Database storage
- **threading** - Concurrent consumer processing

### Message Queue
- **Apache Kafka** - Distributed streaming platform
- **Topic-based messaging** for scalability
- **Consumer groups** for load balancing

## 📱 Responsive Design

The dashboard is fully responsive and works on:
- Desktop computers
- Tablets
- Mobile phones

## 🔄 Real-Time Updates

- **WebSocket connection** for instant updates
- **30-second generation** from Python agent
- **Live indicators** showing system status
- **Smooth animations** for new content
- **Automatic reconnection** on connection loss
- **Error handling** with retry functionality

## 🎯 Emotion Analysis

The system analyzes and displays:
- **Joy** 😄
- **Sadness** 😢
- **Anger** 😠
- **Fear** 😨
- **Surprise** 😲
- **Trust** 🤝
- **Anticipation** 🤔
- **Disgust** 🤢
- **Positive** 😊
- **Negative** 😞

## 🛑 Stopping the System

Press `Ctrl+C` in the terminal where you ran the startup script to stop all services:
- Python tweet agent
- Kafka consumers
- Node.js backend server
- React frontend server

## 🔧 Development

### Adding New Features

1. **Backend**: Add new routes in `backend/app.js`
2. **Frontend**: Add new components in `frontend/src/components/`
3. **Tweet Agent**: Modify `backend/tweet_agent.py` for new tweet types
4. **Consumers**: Extend `backend/kafka_consumers.py` for new processing

### Customizing Tweet Generation

Edit `backend/tweet_agent.py` to:
- Add new emotion templates
- Modify generation frequency
- Change user profiles
- Add new locations

### Customizing Kafka Setup

- **Topic configuration**: Modify topic names and partitions
- **Consumer groups**: Adjust for load balancing
- **Producer settings**: Configure batching and compression

### Customizing Styles

- **App styles**: `frontend/src/App.css`
- **Dashboard styles**: `frontend/src/components/TweetDashboard.css`

## 📝 License

This project is for educational purposes.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

**Happy coding! 🚀**

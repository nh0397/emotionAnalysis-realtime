#!/bin/bash

echo "🚀 Starting Tweet System..."

# Start Docker services
echo "📦 Starting Docker services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Start Python services in background using the virtual environment
echo "🐍 Starting Python services..."

# Start database writer
echo "💾 Starting database writer..."
cd backend/src
nohup ../realtime/bin/python db_writer.py > logs/db_writer_startup.log 2>&1 &
DB_WRITER_PID=$!
echo "Database writer started with PID: $DB_WRITER_PID"

# Start API Server
echo "🌐 Starting API Server..."
nohup ../realtime/bin/python api_server.py > logs/api_startup.log 2>&1 &
API_PID=$!
echo "API Server started with PID: $API_PID"

# Start tweet generator
echo "🤖 Starting tweet generator..."
nohup ../realtime/bin/python simple_tweet_agent.py > logs/tweet_agent_startup.log 2>&1 &
TWEET_PID=$!
echo "Tweet generator started with PID: $TWEET_PID"

cd ../../

# Start React frontend
echo "⚛️ Starting React frontend..."
cd frontend
nohup npm start > ../backend/src/logs/frontend_startup.log 2>&1 &
REACT_PID=$!
echo "React frontend started with PID: $REACT_PID"

cd ..

# Save PIDs for cleanup
echo "$DB_WRITER_PID" > backend/src/logs/db_writer.pid
echo "$API_PID" > backend/src/logs/api.pid
echo "$TWEET_PID" > backend/src/logs/tweet_agent.pid
echo "$REACT_PID" > backend/src/logs/frontend.pid

echo ""
echo "✅ System started successfully!"
echo ""
echo "📊 Services:"
echo "  - PostgreSQL: localhost:5432"
echo "  - Kafka: localhost:9092" 
echo "  - API Server: http://localhost:9000"
echo "  - React Frontend: http://localhost:3000"
echo ""
echo "🔗 API Endpoints:"
echo "  - Real-time tweets: http://localhost:9000/tweets/stream"
echo "  - Historical tweets: http://localhost:9000/tweets/history"
echo "  - System metrics: http://localhost:9000/tweets/metrics"
echo "  - Health check: http://localhost:9000/health"
echo ""
echo "📁 Logs available in backend/src/logs/"
echo ""
echo "🛑 To stop all services, run: ./stop_system.sh"

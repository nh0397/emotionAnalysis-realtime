#!/bin/bash

set -e  # Exit on any error

echo "🚀 Starting Tweet System..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi

# Start Docker services
echo "📦 Starting Docker services..."
docker-compose up -d

# Give services initial time to start
sleep 5

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
POSTGRES_WAIT=0
until docker-compose exec -T postgres pg_isready -U tweetuser -d tweetdb > /dev/null 2>&1; do
  echo "  - PostgreSQL not ready yet, waiting... (${POSTGRES_WAIT}s)"
  sleep 2
  POSTGRES_WAIT=$((POSTGRES_WAIT + 2))
  if [ $POSTGRES_WAIT -gt 60 ]; then
    echo "❌ PostgreSQL failed to start within 60 seconds"
    exit 1
  fi
done
echo "✅ PostgreSQL is ready"

# Wait for Kafka to be ready
echo "⏳ Waiting for Kafka to be ready..."
KAFKA_WAIT=0
until docker-compose exec -T kafka kafka-topics --bootstrap-server localhost:9092 --list > /dev/null 2>&1; do
  echo "  - Kafka not ready yet, waiting... (${KAFKA_WAIT}s)"
  sleep 3
  KAFKA_WAIT=$((KAFKA_WAIT + 3))
  if [ $KAFKA_WAIT -gt 90 ]; then
    echo "❌ Kafka failed to start within 90 seconds"
    exit 1
  fi
done
echo "✅ Kafka is ready"

# Create tweets topic if it doesn't exist
echo "🔧 Creating Kafka topic 'tweets'..."
docker-compose exec -T kafka kafka-topics --bootstrap-server localhost:9092 --create --topic tweets --partitions 3 --replication-factor 1 --if-not-exists > /dev/null 2>&1
echo "✅ Kafka topic ready"

# Setup Python Virtual Environment if missing
if [ ! -d "backend/realtime" ]; then
    echo "🐍 Creating Python virtual environment..."
    python3 -m venv backend/realtime
    source backend/realtime/bin/activate
    echo "📦 Installing Python dependencies..."
    pip install -r backend/requirements.txt
else
    source backend/realtime/bin/activate
fi

# Setup Frontend if missing node_modules
if [ ! -d "frontend/node_modules" ]; then
    echo "⚛️ Installing Frontend dependencies (npm install)..."
    cd frontend
    npm install
    cd ..
fi

# Start Python services in background using the virtual environment
echo "🐍 Starting Python services..."

# Start database writer
echo "💾 Starting database writer..."
cd backend/src
nohup ../realtime/bin/python db_consumer.py >> logs/system.log 2>&1 &
DB_WRITER_PID=$!
echo "Database writer started with PID: $DB_WRITER_PID"

# Start API Server
echo "🌐 Starting API Server..."
nohup ../realtime/bin/python api_server.py >> logs/system.log 2>&1 &
API_PID=$!
echo "API Server started with PID: $API_PID"

# Start tweet generator
echo "🤖 Starting tweet generator..."
nohup ../realtime/bin/python simple_tweet_agent.py >> logs/system.log 2>&1 &
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

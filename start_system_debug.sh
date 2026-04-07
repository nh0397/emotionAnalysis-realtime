#!/bin/bash

set -e  # Exit on any error

echo "🐛 Starting Tweet System in DEBUG MODE..."

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

# Start Python services in FOREGROUND for debugging
echo "🐛 Starting Python services in DEBUG mode..."

cd backend/src

# Test database writer first
echo "💾 Testing database writer..."
echo "Running: ../realtime/bin/python db_writer.py"
../realtime/bin/python db_writer.py &
DB_WRITER_PID=$!
echo "Database writer started with PID: $DB_WRITER_PID"

# Wait 5 seconds and check if it's still running
sleep 5
if kill -0 $DB_WRITER_PID 2>/dev/null; then
    echo "✅ Database writer is running successfully"
else
    echo "❌ Database writer crashed! Check logs:"
    echo "   tail -20 logs/db_writer_startup.log"
    exit 1
fi

# Test API Server
echo "🌐 Testing API Server..."
echo "Running: ../realtime/bin/python api_server.py"
../realtime/bin/python api_server.py &
API_PID=$!
echo "API Server started with PID: $API_PID"

# Wait 5 seconds and check if it's still running
sleep 5
if kill -0 $API_PID 2>/dev/null; then
    echo "✅ API Server is running successfully"
else
    echo "❌ API Server crashed! Check logs:"
    echo "   tail -20 logs/api_startup.log"
    exit 1
fi

# Test tweet generator
echo "🤖 Testing tweet generator..."
echo "Running: ../realtime/bin/python simple_tweet_agent.py"
../realtime/bin/python simple_tweet_agent.py &
TWEET_PID=$!
echo "Tweet generator started with PID: $TWEET_PID"

# Wait 5 seconds and check if it's still running
sleep 5
if kill -0 $TWEET_PID 2>/dev/null; then
    echo "✅ Tweet generator is running successfully"
else
    echo "❌ Tweet generator crashed! Check logs:"
    echo "   tail -20 logs/tweet_agent_startup.log"
    exit 1
fi

cd ../../

# Start React frontend
echo "⚛️ Starting React frontend..."
cd frontend
npm start &
REACT_PID=$!
echo "React frontend started with PID: $REACT_PID"

cd ..

# Save PIDs for cleanup
echo "$DB_WRITER_PID" > backend/src/logs/db_writer.pid
echo "$API_PID" > backend/src/logs/api.pid
echo "$TWEET_PID" > backend/src/logs/tweet_agent.pid
echo "$REACT_PID" > backend/src/logs/frontend.pid

echo ""
echo "✅ System started successfully in DEBUG mode!"
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
echo "🐛 DEBUG: All services started in foreground for easier debugging"
echo "🛑 To stop all services, run: ./stop_system.sh"
echo ""
echo "📊 Monitor in real-time:"
echo "  - Database writer: tail -f backend/src/logs/db_writer_startup.log"
echo "  - Tweet generator: tail -f backend/src/logs/tweet_agent_startup.log"
echo "  - API server: tail -f backend/src/logs/api_startup.log"

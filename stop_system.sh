#!/bin/bash

echo "🛑 Stopping Tweet System..."

# Kill Python processes
if [ -f "backend/src/logs/db_writer.pid" ]; then
    PID=$(cat backend/src/logs/db_writer.pid)
    kill $PID 2>/dev/null && echo "💾 Database writer stopped"
    rm backend/src/logs/db_writer.pid
fi

if [ -f "backend/src/logs/flask.pid" ]; then
    PID=$(cat backend/src/logs/flask.pid)
    kill $PID 2>/dev/null && echo "🌐 Flask API stopped"
    rm backend/src/logs/flask.pid
fi

if [ -f "backend/src/logs/tweet_agent.pid" ]; then
    PID=$(cat backend/src/logs/tweet_agent.pid)
    kill $PID 2>/dev/null && echo "🤖 Tweet generator stopped"
    rm backend/src/logs/tweet_agent.pid
fi

if [ -f "backend/src/logs/frontend.pid" ]; then
    PID=$(cat backend/src/logs/frontend.pid)
    kill $PID 2>/dev/null && echo "⚛️ React frontend stopped"
    rm backend/src/logs/frontend.pid
fi

# Kill any remaining processes on these ports
echo "🧹 Cleaning up remaining processes..."
pkill -f "python.*simple_tweet_agent.py" 2>/dev/null
pkill -f "python.*main.py" 2>/dev/null
pkill -f "python.*db_writer.py" 2>/dev/null
lsof -ti:3000 | xargs kill 2>/dev/null
lsof -ti:9000 | xargs kill 2>/dev/null

# Stop Docker services
echo "📦 Stopping Docker services..."
docker-compose down

echo "✅ System stopped successfully!"

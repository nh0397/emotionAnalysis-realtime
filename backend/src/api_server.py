#!/usr/bin/env python3
"""
Complete API Server for Tweet System
Handles real-time streaming, historical data, and metrics
"""

from flask import Flask, Response, jsonify, request
from flask_cors import CORS
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable
import json
import time
import psycopg2
from datetime import datetime, timedelta
from system_logger import ui_logger as logger

app = Flask(__name__)
CORS(app)

# Database configuration
DB_PARAMS = {
    'host': 'localhost',
    'port': 5432,
    'database': 'tweetdb',
    'user': 'tweetuser',
    'password': 'tweetpass'
}

def get_db_connection():
    """Get database connection"""
    try:
        return psycopg2.connect(**DB_PARAMS)
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None

def get_kafka_consumer():
    """Get Kafka consumer for real-time streaming"""
    try:
        consumer = KafkaConsumer(
            'tweets',
            bootstrap_servers=['localhost:9092'],
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest',
            group_id='flask-sse-group'
        )
        return consumer
    except Exception as e:
        logger.error(f"Kafka connection failed: {e}")
        return None

def format_sse(data: dict, event=None) -> str:
    """Format data as Server-Sent Events"""
    msg = f"data: {json.dumps(data)}\n\n"
    if event is not None:
        msg = f"event: {event}\n{msg}"
    return msg

@app.route('/')
def root():
    """API root endpoint"""
    return jsonify({
        "status": "success",
        "message": "Tweet System API",
        "version": "2.0.0",
        "endpoints": {
            "real-time": "/tweets/stream",
            "historical": "/tweets/history", 
            "states": "/tweets/states",
            "metrics": "/tweets/metrics",
            "health": "/health"
        }
    })

@app.route('/health')
def health_check():
    """System health check"""
    # Check database
    db_status = "connected" if get_db_connection() else "disconnected"
    
    # Check Kafka
    kafka_status = "connected" if get_kafka_consumer() else "disconnected"
    
    return jsonify({
        "status": "healthy" if db_status == "connected" and kafka_status == "connected" else "degraded",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "database": db_status,
            "kafka": kafka_status
        }
    })

@app.route('/tweets/stream')
def stream_tweets():
    """Real-time tweet streaming via SSE"""
    def event_stream():
        logger.system_event("SSE_CLIENT_CONNECTED")
        
        while True:
            consumer = get_kafka_consumer()
            if not consumer:
                yield format_sse({"error": "Kafka unavailable"}, "error")
                time.sleep(5)
                continue

            try:
                yield format_sse({"status": "connected"}, "connection")
                
                for message in consumer:
                    tweet = message.value
                    logger.ui_streamed(tweet.get('id', 'unknown'))
                    yield format_sse(tweet, "tweet")

            except Exception as e:
                logger.error(f"Stream error: {e}")
                yield format_sse({"error": str(e)}, "error")
                if consumer:
                    consumer.close()
                time.sleep(5)
    
    return Response(
        event_stream(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*'
        }
    )

@app.route('/tweets/history')
def get_tweet_history():
    """Get paginated historical tweets from database"""
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 20))
    state_filter = request.args.get('state')
    
    offset = (page - 1) * limit
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database unavailable"}), 500
    
    try:
        cursor = conn.cursor()
        
        # Build query with optional state filter
        base_query = """
            SELECT tweet_id, username, raw_text, timestamp, state_code, 
                   state_name, context, likes, retweets, replies, views, created_at
            FROM tweets
        """
        
        count_query = "SELECT COUNT(*) FROM tweets"
        
        if state_filter:
            base_query += " WHERE state_code = %s"
            count_query += " WHERE state_code = %s"
            params = [state_filter]
        else:
            params = []
        
        base_query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        # Get total count
        cursor.execute(count_query, params[:-2] if state_filter else [])
        total_count = cursor.fetchone()[0]
        
        # Get tweets
        cursor.execute(base_query, params)
        tweets = []
        
        for row in cursor.fetchall():
            tweets.append({
                "id": row[0],
                "username": row[1],
                "raw_text": row[2],
                "timestamp": row[3].isoformat() if row[3] else None,
                "state_code": row[4],
                "state_name": row[5],
                "context": row[6],
                "likes": row[7],
                "retweets": row[8],
                "replies": row[9],
                "views": row[10],
                "created_at": row[11].isoformat() if row[11] else None
            })
        
        conn.close()
        
        return jsonify({
            "tweets": tweets,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_count,
                "pages": (total_count + limit - 1) // limit
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to get tweet history: {e}")
        return jsonify({"error": "Database query failed"}), 500

@app.route('/tweets/states')
def get_unique_states():
    """Get all unique states from the database for filtering"""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database unavailable"}), 500
    
    try:
        cursor = conn.cursor()
        
        # Get unique states with their names, ordered by state code
        cursor.execute("""
            SELECT DISTINCT state_code, state_name 
            FROM tweets 
            WHERE state_code IS NOT NULL AND state_name IS NOT NULL
            ORDER BY state_code
        """)
        
        states = [{"code": row[0], "name": row[1]} for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            "states": states,
            "count": len(states)
        })
        
    except Exception as e:
        logger.error(f"Failed to get unique states: {e}")
        return jsonify({"error": "Database query failed"}), 500

@app.route('/tweets/metrics')
def get_metrics():
    """Get system metrics and analytics"""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database unavailable"}), 500
    
    try:
        cursor = conn.cursor()
        
        # Total tweets
        cursor.execute("SELECT COUNT(*) FROM tweets")
        total_tweets = cursor.fetchone()[0]
        
        # Tweets by state (top 10)
        cursor.execute("""
            SELECT state_code, state_name, COUNT(*) as count 
            FROM tweets 
            GROUP BY state_code, state_name 
            ORDER BY count DESC 
            LIMIT 10
        """)
        tweets_by_state = [{"state": row[0], "name": row[1], "count": row[2]} for row in cursor.fetchall()]
        
        # Tweets by context/keyword (top 10)
        cursor.execute("""
            SELECT context, COUNT(*) as count 
            FROM tweets 
            GROUP BY context 
            ORDER BY count DESC 
            LIMIT 10
        """)
        tweets_by_context = [{"context": row[0], "count": row[1]} for row in cursor.fetchall()]
        
        # Recent activity (last 24 hours)
        cursor.execute("""
            SELECT DATE_TRUNC('hour', created_at) as hour, COUNT(*) as count
            FROM tweets 
            WHERE created_at >= NOW() - INTERVAL '24 hours'
            GROUP BY hour 
            ORDER BY hour
        """)
        hourly_activity = [{"hour": row[0].isoformat(), "count": row[1]} for row in cursor.fetchall()]
        
        # Average engagement
        cursor.execute("""
            SELECT AVG(likes) as avg_likes, AVG(retweets) as avg_retweets, 
                   AVG(replies) as avg_replies, AVG(views) as avg_views
            FROM tweets
        """)
        engagement = cursor.fetchone()
        
        conn.close()
        
        return jsonify({
            "total_tweets": total_tweets,
            "tweets_by_state": tweets_by_state,
            "tweets_by_context": tweets_by_context,
            "hourly_activity": hourly_activity,
            "average_engagement": {
                "likes": round(engagement[0] or 0, 1),
                "retweets": round(engagement[1] or 0, 1),
                "replies": round(engagement[2] or 0, 1),
                "views": round(engagement[3] or 0, 1)
            },
            "generated_at": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        return jsonify({"error": "Metrics query failed"}), 500

if __name__ == "__main__":
    logger.system_event("API_SERVER_STARTING", "Port 9000")
    app.run(host='0.0.0.0', port=9000, debug=True, threaded=True)

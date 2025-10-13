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
from unified_logger import logger

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
        logger.error("API_SERVER", f"Database connection failed: {e}")
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
        logger.error("API_SERVER", f"Kafka connection failed: {e}")
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
            "health": "/health",
            "visualization": {
                "dot-plot-data": "/data",
                "time-series-data": "/timeSeriesData"
            }
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
        
        # 🚀 Create consumer ONCE per connection
        consumer = get_kafka_consumer()
        if not consumer:
            yield format_sse({"error": "Kafka unavailable"}, "error")
            return  # Exit if Kafka is down
        
        try:
            yield format_sse({"status": "connected"}, "connection")
            
            # 🚀 Use the SAME consumer for all messages
            for message in consumer:
                tweet = message.value
                logger.system_event("UI_STREAMED", f"Tweet ID: {tweet.get('id', 'unknown')}")
                yield format_sse(tweet, "tweet")
                
        except Exception as e:
            logger.error("API_SERVER", f"Stream error: {e}")
            yield format_sse({"error": str(e)}, "error")
        finally:
            # 🚀 Clean up consumer when done
            if consumer:
                consumer.close()
                logger.system_event("KAFKA_CONSUMER_CLOSED")
    
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
        logger.error("API_SERVER", f"Failed to get tweet history: {e}")
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
        logger.error("API_SERVER", f"Failed to get unique states: {e}")
        return jsonify({"error": "Database query failed"}), 500

@app.route('/tweets/aggregated')
def get_aggregated_emotions():
    """Get aggregated emotion scores by state for dot plot"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                state_code,
                anger_avg, joy_avg, fear_avg, sadness_avg, surprise_avg,
                positive_avg, negative_avg, anticipation_avg, trust_avg, disgust_avg,
                tweet_count, last_updated
            FROM emotion_aggregates 
            ORDER BY state_code
        """)
        
        rows = cursor.fetchall()
        aggregated_data = []
        
        for row in rows:
            aggregated_data.append({
                'state': row[0],
                'anger': float(row[1]) if row[1] is not None else 0.0,
                'joy': float(row[2]) if row[2] is not None else 0.0,
                'fear': float(row[3]) if row[3] is not None else 0.0,
                'sadness': float(row[4]) if row[4] is not None else 0.0,
                'surprise': float(row[5]) if row[5] is not None else 0.0,
                'positive': float(row[6]) if row[6] is not None else 0.0,
                'negative': float(row[7]) if row[7] is not None else 0.0,
                'anticipation': float(row[8]) if row[8] is not None else 0.0,
                'trust': float(row[9]) if row[9] is not None else 0.0,
                'disgust': float(row[10]) if row[10] is not None else 0.0,
                'tweet_count': row[11],
                'last_updated': row[12].isoformat() if row[12] else None
            })
        
        cursor.close()
        conn.close()
        
        logger.system_event("UI_STREAMED", f"Streamed aggregated data for {len(aggregated_data)} states")
        return jsonify(aggregated_data)
        
    except Exception as e:
        logger.error("API_SERVER", f"Failed to fetch aggregated emotions: {e}")
        return jsonify({'error': 'Failed to fetch aggregated emotions'}), 500

@app.route('/tweets/aggregated/stream')
def stream_aggregated_emotions():
    """Server-Sent Events endpoint for real-time aggregated emotion updates"""
    def generate():
        try:
            conn = psycopg2.connect(**db_params)
            cursor = conn.cursor()
            
            # Get initial data
            cursor.execute("""
                SELECT 
                    state_code,
                    anger_avg, joy_avg, fear_avg, sadness_avg, surprise_avg,
                    positive_avg, negative_avg, anticipation_avg, trust_avg, disgust_avg,
                    tweet_count, last_updated
                FROM emotion_aggregates 
                ORDER BY state_code
                """)
            
            rows = cursor.fetchall()
            initial_data = []
            
            for row in rows:
                initial_data.append({
                    'state': row[0],
                    'anger': float(row[1]) if row[1] is not None else 0.0,
                    'joy': float(row[2]) if row[2] is not None else 0.0,
                    'fear': float(row[3]) if row[3] is not None else 0.0,
                    'sadness': float(row[4]) if row[4] is not None else 0.0,
                    'surprise': float(row[5]) if row[5] is not None else 0.0,
                    'positive': float(row[6]) if row[6] is not None else 0.0,
                    'negative': float(row[7]) if row[7] is not None else 0.0,
                    'anticipation': float(row[8]) if row[8] is not None else 0.0,
                    'trust': float(row[9]) if row[9] is not None else 0.0,
                    'disgust': float(row[10]) if row[10] is not None else 0.0,
                    'tweet_count': row[11],
                    'last_updated': row[12].isoformat() if row[12] else None
                })
            
            # Send initial data
            yield f"data: {json.dumps({'type': 'initial', 'data': initial_data})}\n\n"
            
            # Monitor for changes every 5 seconds
            last_check = time.time()
            while True:
                time.sleep(5)
                current_time = time.time()
                
                # Check for updates in the last 10 seconds
                cursor.execute("""
                    SELECT 
                        state_code,
                        anger_avg, joy_avg, fear_avg, sadness_avg, surprise_avg,
                        positive_avg, negative_avg, anticipation_avg, trust_avg, disgust_avg,
                        tweet_count, last_updated
                    FROM emotion_aggregates 
                    WHERE last_updated > %s
                    ORDER BY state_code
                """, (datetime.datetime.fromtimestamp(last_check - 10),))
                
                updated_rows = cursor.fetchall()
                if updated_rows:
                    updated_data = []
                    for row in updated_rows:
                        updated_data.append({
                            'state': row[0],
                            'anger': float(row[1]) if row[1] is not None else 0.0,
                            'joy': float(row[2]) if row[2] is not None else 0.0,
                            'fear': float(row[3]) if row[3] is not None else 0.0,
                            'sadness': float(row[4]) if row[4] is not None else 0.0,
                            'surprise': float(row[5]) if row[5] is not None else 0.0,
                            'positive': float(row[6]) if row[6] is not None else 0.0,
                            'negative': float(row[7]) if row[7] is not None else 0.0,
                            'anticipation': float(row[8]) if row[8] is not None else 0.0,
                            'trust': float(row[9]) if row[9] is not None else 0.0,
                            'disgust': float(row[10]) if row[10] is not None else 0.0,
                            'tweet_count': row[11],
                            'last_updated': row[12].isoformat() if row[12] else None
                        })
                    
                    yield f"data: {json.dumps({'type': 'update', 'data': updated_data})}\n\n"
                
                last_check = current_time
                
        except Exception as e:
            logger.error("API_SERVER", f"SSE stream error: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            if 'conn' in locals():
                conn.close()
    
    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*'
        }
    )

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
        logger.error("API_SERVER", f"Failed to get metrics: {e}")
        return jsonify({"error": "Metrics query failed"}), 500

@app.route('/data')
def get_dot_plot_data():
    """Get aggregated emotion data by state for dot plot visualization"""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database unavailable"}), 500
    
    try:
        cursor = conn.cursor()
        
        # Aggregate emotion data by state (exactly like sample.csv format)
        cursor.execute("""
            SELECT 
                state_code as state,
                COUNT(*) as total_tweets,
                AVG(anger) as anger,
                AVG(fear) as fear,
                AVG(positive) as positive,
                AVG(sadness) as sadness,
                AVG(surprise) as surprise,
                AVG(joy) as joy,
                AVG(anticipation) as anticipation,
                AVG(trust) as trust,
                AVG(negative) as negative,
                AVG(disgust) as disgust,
                COUNT(CASE WHEN anger > 0 THEN 1 END) as anger_count,
                COUNT(CASE WHEN fear > 0 THEN 1 END) as fear_count,
                COUNT(CASE WHEN positive > 0 THEN 1 END) as positive_count,
                COUNT(CASE WHEN sadness > 0 THEN 1 END) as sadness_count,
                COUNT(CASE WHEN surprise > 0 THEN 1 END) as surprise_count,
                COUNT(CASE WHEN joy > 0 THEN 1 END) as joy_count,
                COUNT(CASE WHEN anticipation > 0 THEN 1 END) as anticipation_count,
                COUNT(CASE WHEN trust > 0 THEN 1 END) as trust_count,
                COUNT(CASE WHEN negative > 0 THEN 1 END) as negative_count,
                COUNT(CASE WHEN disgust > 0 THEN 1 END) as disgust_count,
                SUM(anger) as anger_sum,
                SUM(anticipation) as anticipation_sum,
                SUM(disgust) as disgust_sum,
                SUM(fear) as fear_sum,
                SUM(joy) as joy_sum,
                SUM(negative) as negative_sum,
                SUM(positive) as positive_sum,
                SUM(sadness) as sadness_sum,
                COUNT(CASE WHEN compound < -0.05 THEN 1 END) as senti_negative_count,
                COUNT(CASE WHEN compound >= -0.05 AND compound <= 0.05 THEN 1 END) as senti_neutral_count,
                COUNT(CASE WHEN compound > 0.05 THEN 1 END) as senti_positive_count,
                SUM(surprise) as surprise_sum,
                SUM(trust) as trust_sum
            FROM tweets 
            WHERE state_code IS NOT NULL
            GROUP BY state_code
            ORDER BY state_code
        """)
        
        states_data = []
        for i, row in enumerate(cursor.fetchall()):
            states_data.append({
                "": i,  # Index column like in CSV
                "state": row[0],
                "anger": round(row[2] or 0.0, 17),  # High precision like CSV
                "fear": round(row[3] or 0.0, 17),
                "positive": round(row[4] or 0.0, 17),
                "sadness": round(row[5] or 0.0, 17),
                "surprise": round(row[6] or 0.0, 17),
                "joy": round(row[7] or 0.0, 17),
                "anticipation": round(row[8] or 0.0, 17),
                "trust": round(row[9] or 0.0, 17),
                "negative": round(row[10] or 0.0, 17),
                "disgust": round(row[11] or 0.0, 17),
                "anger_count": row[12] or 0,
                "fear_count": row[13] or 0,
                "positive_count": row[14] or 0,
                "sadness_count": row[15] or 0,
                "surprise_count": row[16] or 0,
                "joy_count": row[17] or 0,
                "anticipation_count": row[18] or 0,
                "trust_count": row[19] or 0,
                "negative_count": row[20] or 0,
                "disgust_count": row[21] or 0,
                "anger_sum": round(row[22] or 0.0, 15),
                "anticipation_sum": round(row[23] or 0.0, 14),
                "disgust_sum": round(row[24] or 0.0, 15),
                "fear_sum": round(row[25] or 0.0, 15),
                "joy_sum": round(row[26] or 0.0, 14),
                "negative_sum": round(row[27] or 0.0, 13),
                "positive_sum": round(row[28] or 0.0, 14),
                "sadness_sum": round(row[29] or 0.0, 15),
                "senti_negative_count": float(row[30] or 0),
                "senti_neutral_count": float(row[31] or 0),
                "senti_positive_count": float(row[32] or 0),
                "surprise_sum": round(row[33] or 0.0, 14),
                "trust_sum": round(row[34] or 0.0, 14)
            })
        
        conn.close()
        
        # Return array directly like the original expects
        return jsonify(states_data)
        
    except Exception as e:
        logger.error("API_SERVER", f"Failed to get dot plot data: {e}")
        return jsonify({"error": "Visualization query failed"}), 500

@app.route('/timeSeriesData/<state_code>')
def get_state_time_series_data(state_code):
    """Get time series emotion data for a specific state"""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database unavailable"}), 500
    
    try:
        cursor = conn.cursor()
        
        # Get daily emotion averages for the specific state
        cursor.execute("""
            SELECT 
                DATE(timestamp) as date,
                AVG(anger) as anger,
                AVG(fear) as fear,
                AVG(sadness) as sadness,
                AVG(surprise) as surprise,
                AVG(joy) as joy,
                AVG(anticipation) as anticipation,
                AVG(trust) as trust,
                AVG(disgust) as disgust
            FROM tweets 
            WHERE state_code = %s
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
        """, (state_code,))
        
        time_series_data = []
        for row in cursor.fetchall():
            time_series_data.append({
                "state": state_code,
                "date": row[0].strftime('%Y-%m-%d') if row[0] else None,
                "anger": round(row[1] or 0.0, 3),
                "fear": round(row[2] or 0.0, 3),
                "sadness": round(row[3] or 0.0, 3),
                "surprise": round(row[4] or 0.0, 3),
                "joy": round(row[5] or 0.0, 3),
                "anticipation": round(row[6] or 0.0, 3),
                "trust": round(row[7] or 0.0, 3),
                "disgust": round(row[8] or 0.0, 3)
            })
        
        conn.close()
        
        return jsonify(time_series_data)
        
    except Exception as e:
        logger.error("API_SERVER", f"Failed to get time series data for {state_code}: {e}")
        return jsonify({"error": "Time series query failed"}), 500

@app.route('/timeSeriesData/emotion/<emotion>')
def get_emotion_time_series_data(emotion):
    """Get time series data for a specific emotion across all states"""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database unavailable"}), 500
    
    try:
        cursor = conn.cursor()
        
        # Validate emotion parameter
        valid_emotions = ['anger', 'fear', 'sadness', 'surprise', 'joy', 'anticipation', 'trust', 'disgust', 'positive', 'negative']
        if emotion not in valid_emotions:
            return jsonify({"error": f"Invalid emotion: {emotion}. Valid emotions: {valid_emotions}"}), 400
        
        # Get daily emotion data for the specific emotion across all states
        query = f"""
        SELECT 
            state_code,
            DATE(created_at) as date,
            AVG({emotion}) as emotion_value
        FROM tweets 
        WHERE {emotion} IS NOT NULL
        GROUP BY state_code, DATE(created_at)
        ORDER BY state_code, date
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        # Convert to list of dictionaries
        data = []
        for row in results:
            data.append({
                'state': row[0],
                'date': row[1].isoformat(),
                emotion: float(row[2]) if row[2] is not None else 0.0
            })
        
        cursor.close()
        conn.close()
        
        print(f"Retrieved {len(data)} time series records for emotion {emotion}")
        return jsonify(data)
        
    except Exception as e:
        logger.error("API_SERVER", f"Failed to get time series data for emotion {emotion}: {e}")
        return jsonify({"error": "Time series query failed"}), 500

@app.route('/timeSeriesData/compare/<state1>/<state2>')
def get_comparison_time_series_data(state1, state2):
    """Get time series emotion data for comparing two states"""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database unavailable"}), 500
    
    try:
        cursor = conn.cursor()
        
        # Get daily emotion averages for both states
        cursor.execute("""
            SELECT 
                state_code,
                DATE(timestamp) as date,
                AVG(anger) as anger,
                AVG(fear) as fear,
                AVG(sadness) as sadness,
                AVG(surprise) as surprise,
                AVG(joy) as joy,
                AVG(anticipation) as anticipation,
                AVG(trust) as trust,
                AVG(disgust) as disgust
            FROM tweets 
            WHERE state_code IN (%s, %s)
            GROUP BY state_code, DATE(timestamp)
            ORDER BY date DESC, state_code
            LIMIT 730
        """, (state1, state2))
        
        time_series_data = []
        for row in cursor.fetchall():
            time_series_data.append({
                "state": row[0],
                "date": row[1].strftime('%Y-%m-%d') if row[1] else None,
                "anger": round(row[2] or 0.0, 3),
                "fear": round(row[3] or 0.0, 3),
                "sadness": round(row[4] or 0.0, 3),
                "surprise": round(row[5] or 0.0, 3),
                "joy": round(row[6] or 0.0, 3),
                "anticipation": round(row[7] or 0.0, 3),
                "trust": round(row[8] or 0.0, 3),
                "disgust": round(row[9] or 0.0, 3)
            })
        
        conn.close()
        
        return jsonify(time_series_data)
        
    except Exception as e:
        logger.error("API_SERVER", f"Failed to get comparison data for {state1} vs {state2}: {e}")
        return jsonify({"error": "Comparison query failed"}), 500

@app.route('/emotionAcrossStates/<emotion>')
def get_emotion_across_states(emotion):
    """Get one emotion across all states for comparison"""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database unavailable"}), 500
    
    try:
        cursor = conn.cursor()
        
        # Validate emotion parameter
        valid_emotions = ['anger', 'fear', 'sadness', 'surprise', 'joy', 'anticipation', 'trust', 'disgust']
        if emotion not in valid_emotions:
            return jsonify({"error": f"Invalid emotion. Must be one of: {valid_emotions}"}), 400
        
        # Get average emotion value for each state
        cursor.execute(f"""
            SELECT 
                state_code,
                AVG({emotion}) as avg_{emotion},
                COUNT(*) as tweet_count
            FROM tweets 
            GROUP BY state_code
            ORDER BY avg_{emotion} DESC
        """)
        
        emotion_data = []
        for row in cursor.fetchall():
            emotion_data.append({
                "state": row[0],
                "emotion": emotion,
                "value": round(row[1] or 0.0, 3),
                "tweet_count": row[2]
            })
        
        conn.close()
        
        return jsonify({
            "emotion": emotion,
            "data": emotion_data,
            "total_states": len(emotion_data)
        })
        
    except Exception as e:
        logger.error("API_SERVER", f"Failed to get {emotion} across states: {e}")
        return jsonify({"error": f"Failed to get {emotion} across states"}), 500

@app.route('/compareStates/<state1>/<state2>/<emotion>')
def compare_two_states_emotion(state1, state2, emotion):
    """Compare one emotion between two specific states"""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database unavailable"}), 500
    
    try:
        cursor = conn.cursor()
        
        # Validate emotion parameter
        valid_emotions = ['anger', 'fear', 'sadness', 'surprise', 'joy', 'anticipation', 'trust', 'disgust']
        if emotion not in valid_emotions:
            return jsonify({"error": f"Invalid emotion. Must be one of: {valid_emotions}"}), 400
        
        # Get emotion data for both states
        cursor.execute(f"""
            SELECT 
                state_code,
                AVG({emotion}) as avg_{emotion},
                MIN({emotion}) as min_{emotion},
                MAX({emotion}) as max_{emotion},
                COUNT(*) as tweet_count
            FROM tweets 
            WHERE state_code IN (%s, %s)
            GROUP BY state_code
            ORDER BY state_code
        """, (state1, state2))
        
        comparison_data = []
        for row in cursor.fetchall():
            comparison_data.append({
                "state": row[0],
                "emotion": emotion,
                "average": round(row[1] or 0.0, 3),
                "minimum": round(row[2] or 0.0, 3),
                "maximum": round(row[3] or 0.0, 3),
                "tweet_count": row[4]
            })
        
        # Calculate difference
        if len(comparison_data) == 2:
            state1_avg = comparison_data[0]['average'] if comparison_data[0]['state'] == state1 else comparison_data[1]['average']
            state2_avg = comparison_data[1]['average'] if comparison_data[1]['state'] == state2 else comparison_data[0]['average']
            difference = round(state1_avg - state2_avg, 3)
        else:
            difference = 0
        
        conn.close()
        
        return jsonify({
            "emotion": emotion,
            "state1": state1,
            "state2": state2,
            "comparison": comparison_data,
            "difference": difference,
            "higher_state": state1 if difference > 0 else state2 if difference < 0 else "equal"
        })
        
    except Exception as e:
        logger.error("API_SERVER", f"Failed to compare {state1} vs {state2} for {emotion}: {e}")
        return jsonify({"error": f"Failed to compare states for {emotion}"}), 500

if __name__ == "__main__":
    logger.system_event("API_SERVER_STARTING", "Port 9000")
    app.run(host='0.0.0.0', port=9000, debug=True, threaded=True)

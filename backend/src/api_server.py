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
                "time-series-data": "/timeSeriesData",
                "emotion-time-series": "/timeSeriesData/emotion/{emotion}",
                "state-comparison": "/timeSeriesData/compare/{state1}/{state2}/{emotion}"
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
            conn = psycopg2.connect(**DB_PARAMS)
            cursor = conn.cursor()
            
            # Get initial data
            cursor.execute("""
                SELECT 
                    state_code,
                    anger_avg, joy_avg, fear_avg, sadness_avg, surprise_avg,
                    anticipation_avg, trust_avg, disgust_avg,
                    sentiment_positive_count, sentiment_negative_count, sentiment_neutral_count,
                    tweet_count, last_updated
                FROM emotion_aggregates 
                ORDER BY state_code
                """)
            
            rows = cursor.fetchall()
            initial_data = []
            
            for row in rows:
                initial_data.append({
                    'state': row[0],
                    # Emotions (8-way)
                    'anger': float(row[1]) if row[1] is not None else 0.0,
                    'joy': float(row[2]) if row[2] is not None else 0.0,
                    'fear': float(row[3]) if row[3] is not None else 0.0,
                    'sadness': float(row[4]) if row[4] is not None else 0.0,
                    'surprise': float(row[5]) if row[5] is not None else 0.0,
                    'anticipation': float(row[6]) if row[6] is not None else 0.0,
                    'trust': float(row[7]) if row[7] is not None else 0.0,
                    'disgust': float(row[8]) if row[8] is not None else 0.0,
                    # Sentiment counts (3-way)
                    'sentiment_positive_count': row[9] if row[9] is not None else 0,
                    'sentiment_negative_count': row[10] if row[10] is not None else 0,
                    'sentiment_neutral_count': row[11] if row[11] is not None else 0,
                    'tweet_count': row[12],
                    'last_updated': row[13].isoformat() if row[13] else None
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
                            anticipation_avg, trust_avg, disgust_avg,
                            sentiment_positive_count, sentiment_negative_count, sentiment_neutral_count,
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
                            # Emotions (8-way)
                            'anger': float(row[1]) if row[1] is not None else 0.0,
                            'joy': float(row[2]) if row[2] is not None else 0.0,
                            'fear': float(row[3]) if row[3] is not None else 0.0,
                            'sadness': float(row[4]) if row[4] is not None else 0.0,
                            'surprise': float(row[5]) if row[5] is not None else 0.0,
                            'anticipation': float(row[6]) if row[6] is not None else 0.0,
                            'trust': float(row[7]) if row[7] is not None else 0.0,
                            'disgust': float(row[8]) if row[8] is not None else 0.0,
                            # Sentiment counts (3-way)
                            'sentiment_positive_count': row[9] if row[9] is not None else 0,
                            'sentiment_negative_count': row[10] if row[10] is not None else 0,
                            'sentiment_neutral_count': row[11] if row[11] is not None else 0,
                            'tweet_count': row[12],
                            'last_updated': row[13].isoformat() if row[13] else None
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
                AVG(sadness) as sadness,
                AVG(surprise) as surprise,
                AVG(joy) as joy,
                AVG(anticipation) as anticipation,
                AVG(trust) as trust,
                AVG(disgust) as disgust,
                COUNT(CASE WHEN sentiment = 'positive' THEN 1 END) as sentiment_positive_count,
                COUNT(CASE WHEN sentiment = 'negative' THEN 1 END) as sentiment_negative_count,
                COUNT(CASE WHEN sentiment = 'neutral' THEN 1 END) as sentiment_neutral_count,
                COUNT(CASE WHEN anger > 0 THEN 1 END) as anger_count,
                COUNT(CASE WHEN fear > 0 THEN 1 END) as fear_count,
                COUNT(CASE WHEN sadness > 0 THEN 1 END) as sadness_count,
                COUNT(CASE WHEN surprise > 0 THEN 1 END) as surprise_count,
                COUNT(CASE WHEN joy > 0 THEN 1 END) as joy_count,
                COUNT(CASE WHEN anticipation > 0 THEN 1 END) as anticipation_count,
                COUNT(CASE WHEN trust > 0 THEN 1 END) as trust_count,
                COUNT(CASE WHEN disgust > 0 THEN 1 END) as disgust_count,
                SUM(anger) as anger_sum,
                SUM(anticipation) as anticipation_sum,
                SUM(disgust) as disgust_sum,
                SUM(fear) as fear_sum,
                SUM(joy) as joy_sum,
                SUM(sadness) as sadness_sum,
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
                # Emotions (8-way)
                "anger": round(row[2] or 0.0, 17),
                "fear": round(row[3] or 0.0, 17),
                "sadness": round(row[4] or 0.0, 17),
                "surprise": round(row[5] or 0.0, 17),
                "joy": round(row[6] or 0.0, 17),
                "anticipation": round(row[7] or 0.0, 17),
                "trust": round(row[8] or 0.0, 17),
                "disgust": round(row[9] or 0.0, 17),
                # Sentiment counts (3-way)
                "sentiment_positive_count": row[10] or 0,
                "sentiment_negative_count": row[11] or 0,
                "sentiment_neutral_count": row[12] or 0,
                # Emotion counts
                "anger_count": row[13] or 0,
                "fear_count": row[14] or 0,
                "sadness_count": row[15] or 0,
                "surprise_count": row[16] or 0,
                "joy_count": row[17] or 0,
                "anticipation_count": row[18] or 0,
                "trust_count": row[19] or 0,
                "disgust_count": row[20] or 0,
                # Emotion sums
                "anger_sum": round(row[21] or 0.0, 15),
                "anticipation_sum": round(row[22] or 0.0, 14),
                "disgust_sum": round(row[23] or 0.0, 15),
                "fear_sum": round(row[24] or 0.0, 15),
                "joy_sum": round(row[25] or 0.0, 14),
                "sadness_sum": round(row[26] or 0.0, 15),
                "surprise_sum": round(row[27] or 0.0, 14),
                "trust_sum": round(row[28] or 0.0, 14)
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
        
        # Get minute-by-minute emotion averages for the specific state
        cursor.execute("""
            SELECT 
                DATE_TRUNC('minute', timestamp) as minute,
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
            GROUP BY DATE_TRUNC('minute', timestamp)
            ORDER BY minute DESC
            LIMIT 100
        """, (state_code,))
        
        time_series_data = []
        for row in cursor.fetchall():
            time_series_data.append({
                "state": state_code,
                "date": row[0].isoformat() if row[0] else None,
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
        
        # Get minute-by-minute emotion data for the specific emotion across all states
        query = f"""
        SELECT 
            state_code,
            DATE_TRUNC('minute', timestamp) as minute,
            AVG({emotion}) as emotion_value
        FROM tweets 
        WHERE {emotion} IS NOT NULL
        GROUP BY state_code, DATE_TRUNC('minute', timestamp)
        ORDER BY state_code, minute DESC
        LIMIT 500
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

@app.route('/timeSeriesData/compare/<state1>/<state2>/<emotion>')
def get_comparison_time_series_data(state1, state2, emotion):
    """Get time series data for comparing two states on a specific emotion"""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database unavailable"}), 500
    
    try:
        cursor = conn.cursor()
        
        # Validate emotion parameter
        valid_emotions = ['anger', 'fear', 'sadness', 'surprise', 'joy', 'anticipation', 'trust', 'disgust', 'positive', 'negative']
        if emotion not in valid_emotions:
            return jsonify({"error": f"Invalid emotion: {emotion}. Valid emotions: {valid_emotions}"}), 400
        
        # Get daily emotion data for both states for the specific emotion
        query = f"""
            SELECT 
                state_code,
                DATE(timestamp) as date,
            AVG({emotion}) as emotion_value
            FROM tweets 
        WHERE state_code IN ('{state1}', '{state2}')
        AND {emotion} IS NOT NULL
            GROUP BY state_code, DATE(timestamp)
        ORDER BY state_code, date
        """
        
        cursor.execute(query)
        
        # Convert to list of dictionaries
        data = []
        for row in cursor.fetchall():
            data.append({
                'state': row[0],
                'date': row[1].isoformat(),
                emotion: float(row[2]) if row[2] is not None else 0.0
            })
        
        cursor.close()
        conn.close()
        
        print(f"Retrieved {len(data)} comparison records for {state1} vs {state2} on {emotion}")
        return jsonify(data)
        
    except Exception as e:
        logger.error("API_SERVER", f"Failed to get comparison data for {state1} vs {state2} on {emotion}: {e}")
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

# === CHATBOT ENDPOINTS ===

# Import chatbot services
try:
    from chatbot_api.services.nl2sql import generate_sql, get_last_notice
    from chatbot_api.services.validator import validate_sql, add_limit_if_missing, ensure_group_by
    from chatbot_api.services.db import run_sql, check_explain_cost
    
    from chatbot_api.services.intent_classifier import classify_intent_smart
    from chatbot_api.services.nl_response import generate_nl_response
    from chatbot_api.config import (
        MAX_CONVERSATION_HISTORY, MAX_SQL_LIMIT, SQL_TIMEOUT, MAX_QUERY_COST
    )
    CHATBOT_AVAILABLE = True
except ImportError as e:
    logger.error("API_SERVER", f"Chatbot services not available: {e}")
    CHATBOT_AVAILABLE = False

# Conversation memory
conversation_history = {}
# LangChain memory storage (separate from conversation_history dict)
langchain_memory_store = {}

@app.route('/chat', methods=['POST'])
def chat():
    """Smart chatbot endpoint"""
    if not CHATBOT_AVAILABLE:
        return jsonify({"error": "Chatbot services not available"}), 503
    
    data = request.get_json()
    if not data or not data.get('question'):
        return jsonify({"error": "Question is required"}), 400
    
    question = data.get('question', '').strip()
    session_id = data.get('session_id', 'default')
    current_page = data.get('current_page')
    
    # Get conversation history
    history = conversation_history.get(session_id, [])
    
    # Debug logging
    print(f"[api_server.py:chat] Session {session_id}: {len(history)} previous queries, current_page: '{current_page}'")
    if history:
        recent_questions = [h.get('question', '') for h in history[-3:]]
        print(f"[api_server.py:chat] Recent questions: {recent_questions}")
    
    try:
        # 🔍 STEP 1: Context Detection (for follow-ups like "plot this", "visualize previous")
        print(f"[CHAIN] 🔍 STEP 1: Context Detection for '{question}'")
        from chatbot_api.services.context_handler import detect_contextual_followup, should_return_previous_results
        
        context = None
        use_langchain = True  # Always use LangChain pipeline
        
        # Check LangChain memory first (if available)
        if use_langchain:
            try:
                from chatbot_api.langchain_chain import AnalyticsMemory
                global langchain_memory_store
                if session_id in langchain_memory_store:
                    memory = langchain_memory_store[session_id]
                    if memory.last_query_context:
                        q_lower = question.lower().strip()
                        contextual_keywords = ['plot', 'visualize', 'visualisation', 'chart', 'graph', 'complete', 'full', 'all', 'data', 'it', 'this', 'that', 'help', 'previous']
                        if any(keyword in q_lower for keyword in contextual_keywords):
                            context = {
                                'previous_question': memory.last_query_context.get('question', ''),
                                'previous_sql': memory.last_query_context.get('sql'),
                                'previous_rows': memory.last_query_context.get('rows'),
                                'previous_chart_hint': memory.last_query_context.get('chart_hint'),
                                'previous_chart_filters': memory.last_query_context.get('chart_filters'),
                                'follow_up_type': 'visualize' if any(kw in q_lower for kw in ['plot', 'visualize', 'visualisation', 'chart', 'help me plot', 'previous']) else 'expand_data'
                            }
                            print(f"[CHAIN] ✓ Context detected using LangChain memory - Previous query: '{context['previous_question'][:50]}...'")
                        else:
                            print(f"[CHAIN] ✗ No contextual keywords found in: '{q_lower}'")
                    else:
                        print(f"[CHAIN] ✗ No last_query_context in memory")
                else:
                    print(f"[CHAIN] ✗ No memory for session {session_id}")
            except Exception as e:
                print(f"[CHAIN] ❌ LangChain memory check failed: {e}")
        
        # Fallback to conversation_history-based detection
        if not context:
            context = detect_contextual_followup(question, history)
            if context:
                print(f"[CHAIN] ✓ Context detected using conversation_history - Previous query: '{context.get('previous_question', '')[:50]}...'")
            else:
                print(f"[CHAIN] ✗ No context detected in conversation_history")
        
        # If context detected and it's a visualization request, force data_query intent
        force_data_query = False
        if context and should_return_previous_results(question, context):
            force_data_query = True
            print(f"[CHAIN] 🎯 Forcing data_query for visualization follow-up: '{question}'")
        
        # 🤖 STEP 2: Intent Classification
        print(f"[CHAIN] 🤖 STEP 2: Intent Classification")
        intent, context_info = classify_intent_smart(
            question=question,
            has_screenshot=False,
            current_page=current_page,
            previous_queries=history
        )
        
        # Override intent if we detected a visualization follow-up
        if force_data_query:
            original_intent = intent
            intent = 'data_query'
            print(f"[CHAIN] 🎯 Intent overridden: {original_intent} → {intent} (visualization follow-up)")
        
        print(f"[CHAIN] ✓ Final intent: {intent}")
        
        # Ensure current_page and session_id are in context_info
        context_info['current_page'] = current_page
        context_info['session_id'] = session_id
        if context:
            context_info['detected_context'] = context  # Pass context to handler
        
        logger.system_event("CHATBOT_INTENT", f"Question: '{question}' → Intent: {intent}")
        
        # 🔀 STEP 3: Route to Handler
        print(f"[CHAIN] 🔀 STEP 3: Routing to handler: {intent}")
        if intent == 'smalltalk':
            print(f"[CHAIN] 💬 Routing to handle_smalltalk")
            result = handle_smalltalk(question, context_info)
        elif intent == 'data_query':
            print(f"[CHAIN] 📊 Routing to handle_data_query")
            result = handle_data_query(question, context_info)
        else:
            print(f"[CHAIN] ❓ Unknown intent, returning default response")
            result = {
                "sql": None,
                "rows": [],
                "chart_hint": None,
                "message": "I'm not sure how to help with that. Can you rephrase?"
            }
        
        print(f"[CHAIN] ✅ Handler completed: {len(result.get('rows', []))} rows, chart_hint: {result.get('chart_hint')}")
        
        # Save to conversation history with full query context
        history_entry = {
            'question': question,
            'intent': intent,
            'context': context_info,
            'timestamp': time.time(),
            'result': {
                'sql': result.get('sql'),
                'rows': result.get('rows'),
                'chart_hint': result.get('chart_hint'),
                'message': result.get('message')
            } if intent == 'data_query' else None
        }
        history.append(history_entry)
        conversation_history[session_id] = history[-MAX_CONVERSATION_HISTORY:]
        
        # Add debug info
        result['intent'] = intent
        result['context'] = context_info
        
        return jsonify(result)
        
    except Exception as e:
        logger.error("API_SERVER", f"Chat error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/chat/smart_suggest', methods=['POST'])
def smart_chart_suggest():
    """Generate smart chart suggestions using LLM on demand"""
    if not CHATBOT_AVAILABLE:
        return jsonify({"error": "Chatbot services not available"}), 503
        
    data = request.get_json()
    if not data:
        return jsonify({"error": "Data is required"}), 400
        
    sql = data.get('sql')
    rows = data.get('rows')
    question = data.get('question')
    
    if not rows:
        return jsonify({"error": "No data rows provided"}), 400
        
    try:
        from chatbot_api.services.chart_llm import suggest_chart_with_llm
        print(f"[API_SERVER] 🧠 Generating smart chart for: '{question}'")
        
        # Call LLM
        chart_data = suggest_chart_with_llm(sql, rows, question)
        
        if chart_data:
            print(f"[API_SERVER] ✓ Smart chart generated: {chart_data.get('chart_type')}")
            return jsonify({
                "success": True,
                "chart_hint": chart_data.get('chart_type'),
                "chart_config": chart_data.get('chart_config'),
                "chart_reasoning": chart_data.get('reasoning'),
                "chart_code": chart_data.get('code')
            })
        else:
            print(f"[API_SERVER] ⚠ Smart chart generation returned None")
            return jsonify({"success": False, "message": "No chart suggestion found"}), 404
            
    except Exception as e:
        logger.error("API_SERVER", f"Smart chart error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


def handle_smalltalk(question, context_info=None):
    """Handle casual conversation"""
    import requests
    from chatbot_api.config import OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT, OLLAMA_TEMP_SMALLTALK
    
    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": f"You are TecVis 2.0 AI, a friendly assistant for an emotion analytics platform. Respond briefly and warmly to:\n{question}",
                "stream": False,
                "options": {"temperature": OLLAMA_TEMP_SMALLTALK}
            },
            timeout=OLLAMA_TIMEOUT
        )
        
        if response.status_code == 200:
            message = response.json().get("response", "Hello! How can I help you today?").strip()
        else:
            message = "Hello! How can I help you analyze emotion data today?"
            
    except Exception as e:
        print(f"[api_server.py:handle_smalltalk] Error: {e}")
        message = "Hello! Ask me anything about emotion data or the platform."
    
    return {
        "sql": None,
        "rows": [],
        "chart_hint": None,
        "message": message
    }

def handle_data_query(question, context_info, use_langchain: bool = True):
    """
    Handle data queries with enhanced LangChain pipeline for 90-100% accuracy.
    
    Microsoft Fabric-inspired: Auto-visualization when appropriate.
    """
    from chatbot_api.services.context_handler import (
        detect_contextual_followup, 
        inject_context_into_prompt,
        should_return_previous_results
    )
    
    # 🔗 Use LangChain pipeline (main processing)
    if use_langchain:
        try:
            print(f"[DATA_QUERY] 🔗 Using LangChain pipeline")
            from chatbot_api.langchain_chain import AnalyticsMemory, run_analytics_pipeline
            
            # Get or create memory for session
            session_id = context_info.get('session_id', 'default')
            global langchain_memory_store
            
            if session_id not in langchain_memory_store:
                langchain_memory_store[session_id] = AnalyticsMemory()
                print(f"[DATA_QUERY] ✓ Created new memory for session: {session_id}")
            else:
                print(f"[DATA_QUERY] ✓ Using existing memory for session: {session_id}")
            
            memory = langchain_memory_store[session_id]
            current_page = context_info.get('current_page')
            
            # Run LangChain pipeline
            print(f"[DATA_QUERY] 🚀 Running analytics pipeline...")
            result = run_analytics_pipeline(question, memory, current_page)
            
            # Ensure backward compatibility
            if 'auto_show_viz' not in result:
                from chatbot_api.langchain_chain import should_auto_visualize
                result['auto_show_viz'] = should_auto_visualize(result.get('rows', []), result.get('chart_hint'))
            
            print(f"[DATA_QUERY] ✅ Pipeline completed successfully")
            print(f"[DATA_QUERY] ✓ SQL: {result.get('sql', 'None')[:100]}...")
            print(f"[DATA_QUERY] ✓ Rows: {len(result.get('rows', []))}")
            print(f"[DATA_QUERY] ✓ Chart: {result.get('chart_hint')}")
            print(f"[DATA_QUERY] ✓ Auto-viz: {result.get('auto_show_viz')}")
            return result
            
        except Exception as e:
            import traceback
            print(f"[DATA_QUERY] ❌ LangChain pipeline failed: {e}")
            traceback.print_exc()
            print(f"[DATA_QUERY] 🔄 Falling back to legacy implementation")
            # Fall through to legacy implementation
    
    # LEGACY: Original implementation (fallback)
    # Get conversation history for context detection
    session_id = context_info.get('session_id', 'default')
    history = conversation_history.get(session_id, [])
    
    # Check if this is a contextual follow-up
    context = detect_contextual_followup(question, history)
    
    # If user just wants to visualize previous results, return them directly
    if context and should_return_previous_results(question, context):
        print(f"[api_server.py:handle_data_query] Returning previous results for visualization follow-up")
        return {
            "sql": context['previous_sql'],
            "rows": context['previous_rows'],
            "chart_hint": context['previous_chart_hint'],
            "message": f"Here's the visualization for your previous query about {context['previous_question']}.",
            "is_contextual": True
        }
    
    # Handle "complete data" / "full data" requests - expand previous query
    if context and context.get('follow_up_type') == 'expand_data':
        from chatbot_api.services.context_handler import expand_previous_query
        expanded_sql = expand_previous_query(context)
        if expanded_sql:
            print(f"[api_server.py:handle_data_query] Expanding previous query: {expanded_sql[:200]}...")
            # Validate and execute expanded SQL
            from chatbot_api.services.validator import fix_order_by_alias_references
            sql = add_limit_if_missing(expanded_sql, max_limit=MAX_SQL_LIMIT)
            sql = ensure_group_by(sql)
            sql = fix_order_by_alias_references(sql)  # Fix alias references in ORDER BY
            is_valid, error = validate_sql(sql)
            if is_valid:
                rows, exec_error = run_sql(sql, timeout=SQL_TIMEOUT)
                if not exec_error:
                    from chatbot_api.services.chart_llm import suggest_chart_with_llm
                    chart_response = suggest_chart_with_llm(sql, rows, question)
                    chart_hint = chart_response.get('chart_type') if chart_response else None
                    current_page = context_info.get('current_page')
                    nl_message = generate_nl_response(
                        f"Complete data for: {context['previous_question']}", 
                        sql, rows, chart_hint, current_page
                    )
                    return {
                        "sql": sql,
                        "rows": rows,
                        "chart_hint": chart_hint,
                        "message": nl_message,
                        "is_contextual": True
                    }
    
    # Enhance question with context if detected
    enhanced_question = question
    if context:
        enhanced_question = inject_context_into_prompt(question, context)
        print(f"[api_server.py:handle_data_query] Enhanced question with context: {enhanced_question[:200]}...")
    
    # Generate SQL (with or without context)
    sql = generate_sql(enhanced_question)
    provider_notice = None
    try:
        provider_notice = get_last_notice()
    except Exception:
        provider_notice = None
    if not sql:
        return {
            "sql": None,
            "rows": [],
            "chart_hint": None,
            "message": "The query engine is temporarily unavailable. Our team is looking into it—please try again in a moment."
        }
    
    # Add LIMIT
    sql = add_limit_if_missing(sql, max_limit=MAX_SQL_LIMIT)
    # Auto-fix GROUP BY consistency for Postgres
    sql = ensure_group_by(sql)
    # Fix ORDER BY alias references (PostgreSQL doesn't allow aliases in ORDER BY)
    from chatbot_api.services.validator import fix_order_by_alias_references, ensure_order_by_in_select
    sql = ensure_order_by_in_select(sql)  # Add missing aggregates to SELECT
    sql = fix_order_by_alias_references(sql)  # Expand aliases to expressions in ORDER BY
    
    # Validate SQL
    is_valid, error = validate_sql(sql)
    if not is_valid:
        return {
            "sql": sql,
            "rows": [],
            "chart_hint": None,
            "message": "The query engine is temporarily unavailable. Our team is looking into it—please try again shortly."
        }
    
    # Execute SQL
    rows, exec_error = run_sql(sql, timeout=SQL_TIMEOUT)
    if exec_error:
        return {
            "sql": sql,
            "rows": [],
            "chart_hint": None,
            "message": "The query engine is currently experiencing an issue. We're on it—please retry in a bit."
        }
    
    # Generate chart hint (pass question for LLM context if enabled)
    chart_hint_result = infer_chart_type(sql, rows, question)
    
    # Handle both new format (dict) and legacy format (string)
    chart_hint = None
    chart_filters = None
    if isinstance(chart_hint_result, dict):
        chart_hint = chart_hint_result.get('chart_type')
        if chart_hint_result.get('suggest_filters'):
            chart_filters = chart_hint_result.get('filter_types', [])
    else:
        chart_hint = chart_hint_result
    
    # Microsoft Fabric-inspired: Auto-show visualization when appropriate
    try:
        from chatbot_api.langchain_chain import should_auto_visualize
        auto_show_viz = should_auto_visualize(rows, chart_hint)
    except:
        auto_show_viz = False
    
    # Generate natural language response
    current_page = context_info.get('current_page')
    nl_message = generate_nl_response(question, sql, rows, chart_hint, current_page)
    
    return {
        "sql": sql,
        "rows": rows,
        "chart_hint": chart_hint,
        "chart_filters": chart_filters,  # New: filter suggestions
        "auto_show_viz": auto_show_viz,  # Microsoft Fabric: auto-show when appropriate
        "message": nl_message,
        "notice": provider_notice
    }

# RAG handling removed - UI help questions now handled in handle_smalltalk()

if __name__ == "__main__":
    logger.system_event("API_SERVER_STARTING", "Port 9000 (Flask)")
    app.run(host="0.0.0.0", port=9000, debug=True, threaded=True)

#!/usr/bin/env python3
"""
FastAPI Server for Tweet System - Migrated from Flask
Handles real-time streaming, historical data, metrics, and chatbot
"""

from fastapi import FastAPI, Query, Path, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict
import json
import time
import psycopg
from datetime import datetime, timedelta
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable
import asyncio
from unified_logger import logger

# Import chatbot services
from chatbot_api.services.nl2sql import generate_sql
from chatbot_api.services.validator import validate_sql, add_limit_if_missing
from chatbot_api.services.db import run_sql, check_explain_cost
from chatbot_api.services.chart_hints import infer_chart_type
from chatbot_api.services.intent_classifier import classify_intent_smart
from chatbot_api.services.nl_response import generate_nl_response
from chatbot_api.config import (
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    OLLAMA_TIMEOUT,
    OLLAMA_TEMP_SMALLTALK,
    MAX_CONVERSATION_HISTORY,
    MAX_SQL_LIMIT,
    SQL_TIMEOUT,
    MAX_QUERY_COST
)

app = FastAPI(
    title="TecViz API",
    description="Real-time emotion analytics and NL chatbot",
    version="3.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database configuration
DB_PARAMS = {
    'host': 'localhost',
    'port': 5432,
    'dbname': 'tweetdb',
    'user': 'tweetuser',
    'password': 'tweetpass'
}

def get_db_connection():
    """Get psycopg3 database connection"""
    try:
        return psycopg.connect(**DB_PARAMS)
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
            group_id='fastapi-sse-group'
        )
        return consumer
    except Exception as e:
        logger.error("API_SERVER", f"Kafka connection failed: {e}")
        return None

# Pydantic Models
class Question(BaseModel):
    question: str
    session_id: Optional[str] = "default"
    current_page: Optional[str] = None

class VisionQuestion(BaseModel):
    question: str
    screenshot: Optional[str] = None
    session_id: Optional[str] = "default"
    current_page: Optional[str] = None

# Conversation memory (in-memory; could be Redis/DB for production)
conversation_history: Dict[str, List[Dict]] = {}

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    services: Dict[str, str]

# === ROOT & HEALTH ENDPOINTS ===

@app.get("/")
def root():
    """API root endpoint"""
    return {
        "status": "success",
        "message": "TecViz API - FastAPI Edition",
        "version": "3.0.0",
        "endpoints": {
            "real-time": "/tweets/stream",
            "historical": "/tweets/history",
            "states": "/tweets/states",
            "metrics": "/tweets/metrics",
            "health": "/health",
            "chatbot": "/chat",
            "visualization": {
                "dot-plot-data": "/data",
                "emotion-time-series": "/timeSeriesData/emotion/{emotion}",
                "state-comparison": "/timeSeriesData/compare/{state1}/{state2}/{emotion}"
            }
        }
    }

@app.get("/health", response_model=HealthResponse)
def health_check():
    """System health check - simplified to avoid blocking"""
    # Skip actual DB/Kafka checks to prevent blocking
    db_status = "unknown"
    kafka_status = "unknown"
    
    return {
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "database": db_status,
            "kafka": kafka_status
        }
    }

# === REAL-TIME STREAMING ===

@app.get("/tweets/stream")
async def stream_tweets():
    """Real-time tweet streaming via SSE"""
    async def event_stream():
        logger.system_event("SSE_CLIENT_CONNECTED")
        
        consumer = get_kafka_consumer()
        if not consumer:
            yield f"event: error\ndata: {json.dumps({'error': 'Kafka unavailable'})}\n\n"
            return
        
        try:
            yield f"event: connection\ndata: {json.dumps({'status': 'connected'})}\n\n"
            
            for message in consumer:
                tweet = message.value
                logger.system_event("UI_STREAMED", f"Tweet ID: {tweet.get('id', 'unknown')}")
                yield f"event: tweet\ndata: {json.dumps(tweet)}\n\n"
                await asyncio.sleep(0)  # Allow other tasks
                
        except Exception as e:
            logger.error("API_SERVER", f"Stream error: {e}")
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
        finally:
            if consumer:
                consumer.close()
                logger.system_event("KAFKA_CONSUMER_CLOSED")
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*"
        }
    )

@app.get("/tweets/aggregated/stream")
async def stream_aggregated_emotions():
    """Server-Sent Events endpoint for real-time aggregated emotion updates"""
    async def generate():
        try:
            conn = get_db_connection()
            if not conn:
                yield f"data: {json.dumps({'error': 'Database unavailable'})}\n\n"
                return
            
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
                    'anger': float(row[1]) if row[1] is not None else 0.0,
                    'joy': float(row[2]) if row[2] is not None else 0.0,
                    'fear': float(row[3]) if row[3] is not None else 0.0,
                    'sadness': float(row[4]) if row[4] is not None else 0.0,
                    'surprise': float(row[5]) if row[5] is not None else 0.0,
                    'anticipation': float(row[6]) if row[6] is not None else 0.0,
                    'trust': float(row[7]) if row[7] is not None else 0.0,
                    'disgust': float(row[8]) if row[8] is not None else 0.0,
                    'sentiment_positive_count': row[9] if row[9] is not None else 0,
                    'sentiment_negative_count': row[10] if row[10] is not None else 0,
                    'sentiment_neutral_count': row[11] if row[11] is not None else 0,
                    'tweet_count': row[12],
                    'last_updated': row[13].isoformat() if row[13] else None
                })
            
            yield f"data: {json.dumps({'type': 'initial', 'data': initial_data})}\n\n"
            
            # Monitor for changes every 5 seconds
            last_check = time.time()
            while True:
                await asyncio.sleep(5)
                current_time = time.time()
                
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
                """, (datetime.fromtimestamp(last_check - 10),))
                
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
                            'anticipation': float(row[6]) if row[6] is not None else 0.0,
                            'trust': float(row[7]) if row[7] is not None else 0.0,
                            'disgust': float(row[8]) if row[8] is not None else 0.0,
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
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*"
        }
    )

# === HISTORICAL DATA ===

@app.get("/tweets/history")
def get_tweet_history(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    state: Optional[str] = Query(None)
):
    """Get paginated historical tweets from database"""
    offset = (page - 1) * limit
    
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database unavailable")
    
    try:
        cursor = conn.cursor()
        
        base_query = """
            SELECT tweet_id, username, raw_text, timestamp, state_code, 
                   state_name, context, likes, retweets, replies, views, created_at
            FROM tweets
        """
        
        count_query = "SELECT COUNT(*) FROM tweets"
        
        params = []
        if state:
            base_query += " WHERE state_code = %s"
            count_query += " WHERE state_code = %s"
            params.append(state)
        
        base_query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        
        # Get total count
        cursor.execute(count_query, params if state else [])
        total_count = cursor.fetchone()[0]
        
        # Get tweets
        cursor.execute(base_query, params + [limit, offset])
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
        
        return {
            "tweets": tweets,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_count,
                "pages": (total_count + limit - 1) // limit
            }
        }
        
    except Exception as e:
        logger.error("API_SERVER", f"Failed to get tweet history: {e}")
        raise HTTPException(status_code=500, detail="Database query failed")

@app.get("/tweets/states")
def get_unique_states():
    """Get all unique states from the database for filtering"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database unavailable")
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT state_code, state_name 
            FROM tweets 
            WHERE state_code IS NOT NULL AND state_name IS NOT NULL
            ORDER BY state_code
        """)
        
        states = [{"code": row[0], "name": row[1]} for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            "states": states,
            "count": len(states)
        }
        
    except Exception as e:
        logger.error("API_SERVER", f"Failed to get unique states: {e}")
        raise HTTPException(status_code=500, detail="Database query failed")

@app.get("/tweets/metrics")
def get_metrics():
    """Get system metrics and analytics"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database unavailable")
    
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
        
        return {
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
        }
        
    except Exception as e:
        logger.error("API_SERVER", f"Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail="Metrics query failed")

# === VISUALIZATION ENDPOINTS ===

@app.get("/data")
def get_dot_plot_data():
    """Get aggregated emotion data by state for dot plot visualization"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database unavailable")
    
    try:
        cursor = conn.cursor()
        
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
                "": i,
                "state": row[0],
                "anger": round(row[2] or 0.0, 17),
                "fear": round(row[3] or 0.0, 17),
                "sadness": round(row[4] or 0.0, 17),
                "surprise": round(row[5] or 0.0, 17),
                "joy": round(row[6] or 0.0, 17),
                "anticipation": round(row[7] or 0.0, 17),
                "trust": round(row[8] or 0.0, 17),
                "disgust": round(row[9] or 0.0, 17),
                "sentiment_positive_count": row[10] or 0,
                "sentiment_negative_count": row[11] or 0,
                "sentiment_neutral_count": row[12] or 0,
                "anger_count": row[13] or 0,
                "fear_count": row[14] or 0,
                "sadness_count": row[15] or 0,
                "surprise_count": row[16] or 0,
                "joy_count": row[17] or 0,
                "anticipation_count": row[18] or 0,
                "trust_count": row[19] or 0,
                "disgust_count": row[20] or 0,
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
        return states_data
        
    except Exception as e:
        logger.error("API_SERVER", f"Failed to get dot plot data: {e}")
        raise HTTPException(status_code=500, detail="Visualization query failed")

@app.get("/timeSeriesData/{state_code}")
def get_state_time_series_data(state_code: str = Path(...)):
    """Get time series emotion data for a specific state"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database unavailable")
    
    try:
        cursor = conn.cursor()
        
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
        return time_series_data
        
    except Exception as e:
        logger.error("API_SERVER", f"Failed to get time series data for {state_code}: {e}")
        raise HTTPException(status_code=500, detail="Time series query failed")

@app.get("/timeSeriesData/emotion/{emotion}")
def get_emotion_time_series_data(emotion: str = Path(...)):
    """Get time series data for a specific emotion across all states"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database unavailable")
    
    try:
        valid_emotions = ['anger', 'fear', 'sadness', 'surprise', 'joy', 'anticipation', 'trust', 'disgust', 'positive', 'negative']
        if emotion not in valid_emotions:
            raise HTTPException(status_code=400, detail=f"Invalid emotion: {emotion}")
        
        cursor = conn.cursor()
        
        query = f"""
        SELECT 
            state_code,
            DATE(timestamp) as date,
            AVG({emotion}) as emotion_value
        FROM tweets 
        WHERE {emotion} IS NOT NULL
        GROUP BY state_code, DATE(timestamp)
        ORDER BY state_code, date
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        data = []
        for row in results:
            data.append({
                'state': row[0],
                'date': row[1].isoformat(),
                emotion: float(row[2]) if row[2] is not None else 0.0
            })
        
        cursor.close()
        conn.close()
        
        print(f"[api_server.py:646] Retrieved {len(data)} time series records for emotion {emotion}")
        return data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("API_SERVER", f"Failed to get time series data for emotion {emotion}: {e}")
        raise HTTPException(status_code=500, detail="Time series query failed")

@app.get("/timeSeriesData/compare/{state1}/{state2}/{emotion}")
def get_comparison_time_series_data(
    state1: str = Path(...),
    state2: str = Path(...),
    emotion: str = Path(...)
):
    """Get time series data for comparing two states on a specific emotion"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database unavailable")
    
    try:
        valid_emotions = ['anger', 'fear', 'sadness', 'surprise', 'joy', 'anticipation', 'trust', 'disgust', 'positive', 'negative']
        if emotion not in valid_emotions:
            raise HTTPException(status_code=400, detail=f"Invalid emotion: {emotion}")
        
        cursor = conn.cursor()
        
        query = f"""
            SELECT 
                state_code,
                DATE(timestamp) as date,
                AVG({emotion}) as emotion_value
            FROM tweets 
            WHERE state_code IN (%s, %s)
              AND {emotion} IS NOT NULL
            GROUP BY state_code, DATE(timestamp)
            ORDER BY state_code, date
        """
        
        cursor.execute(query, (state1, state2))
        
        data = []
        for row in cursor.fetchall():
            data.append({
                'state': row[0],
                'date': row[1].isoformat(),
                emotion: float(row[2]) if row[2] is not None else 0.0
            })
        
        cursor.close()
        conn.close()
        
        print(f"[api_server.py:698] Retrieved {len(data)} comparison records for {state1} vs {state2} on {emotion}")
        return data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("API_SERVER", f"Failed to get comparison data for {state1} vs {state2} on {emotion}: {e}")
        raise HTTPException(status_code=500, detail="Comparison query failed")

# === CHATBOT ENDPOINTS ===

@app.post("/chat")
def chat(q: Question):
    """Smart chatbot: classify intent → route to appropriate handler"""
    if not q.question or not q.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    # Get conversation history for this session
    session_id = q.session_id or "default"
    history = conversation_history.get(session_id, [])
    
    # Debug: Log conversation context
    print(f"[api_server.py:720] Session {session_id}: {len(history)} previous queries, current_page: {q.current_page}")
    if history:
        recent_questions = [h.get('question', '') for h in history[-3:]]
        print(f"[api_server.py:722] Recent questions: {recent_questions}")
    
    # Classify intent with full context
    intent, context_info = classify_intent_smart(
        question=q.question,
        has_screenshot=False,
        current_page=q.current_page,
        previous_queries=history
    )
    
    logger.system_event("CHATBOT_INTENT", f"Question: '{q.question}' → Intent: {intent}, Reason: {context_info.get('reason')}, Confidence: {context_info.get('confidence', 'N/A')}")
    
    # Route to appropriate handler
    if intent == 'smalltalk':
        result = handle_smalltalk(q.question)
    elif intent == 'data_query':
        result = handle_data_query(q.question, context_info)
    elif intent == 'rag_query':
        result = handle_rag_query(q.question, None, context_info)
    else:
        result = {
            "sql": None,
            "rows": [],
            "chart_hint": None,
            "message": "I'm not sure how to help with that. Can you rephrase?"
        }
    
    # Save to conversation history
    history.append({
        'question': q.question,
        'intent': intent,
        'context': context_info,
        'timestamp': time.time()
    })
    conversation_history[session_id] = history[-MAX_CONVERSATION_HISTORY:]
    
    # Add intent to response for debugging
    result['intent'] = intent
    result['context'] = context_info
    
    return result

def handle_smalltalk(question: str) -> dict:
    """Handle casual conversation with friendly responses"""
    try:
        import requests
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": f"You are TecViz AI, a friendly assistant for an emotion analytics platform. Respond briefly and warmly to:\n{question}",
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
        logger.error("CHATBOT", f"Smalltalk error: {e}")
        message = "Hello! Ask me anything about emotion data or the platform."
    
    return {
        "sql": None,
        "rows": [],
        "chart_hint": None,
        "message": message
    }

def handle_data_query(question: str, context_info: dict) -> dict:
    """Handle data queries with NL→SQL pipeline"""
    # Step 1: Generate SQL from natural language
    sql = generate_sql(question)
    if not sql:
        return {
            "sql": None,
            "rows": [],
            "chart_hint": None,
            "message": "I couldn't generate a valid SQL query. Try being more specific about states, emotions, or time periods."
        }
    
    # Step 2: Ensure LIMIT is present
    sql = add_limit_if_missing(sql, max_limit=MAX_SQL_LIMIT)
    
    # Step 3: Validate SQL for safety
    is_valid, error = validate_sql(sql)
    if not is_valid:
        return {
            "sql": sql,
            "rows": [],
            "chart_hint": None,
            "message": f"Query validation failed: {error}"
        }
    
    # Step 4: Check query cost with EXPLAIN (skip if no limit set)
    if MAX_QUERY_COST is not None:
        is_safe, cost_error = check_explain_cost(sql, max_cost=MAX_QUERY_COST)
        if not is_safe:
            return {
                "sql": sql,
                "rows": [],
                "chart_hint": None,
                "message": f"Query too expensive. Try adding more filters or reducing the date range."
            }
    
    # Step 5: Execute SQL
    rows, exec_error = run_sql(sql, timeout=SQL_TIMEOUT)
    if exec_error:
        return {
            "sql": sql,
            "rows": [],
            "chart_hint": None,
            "message": f"Execution error: {exec_error}"
        }
    
    # Step 6: Infer chart type
    chart_hint = infer_chart_type(sql, rows)
    
    # Step 7: Generate natural language response
    current_page = context_info.get('current_page')
    nl_message = generate_nl_response(question, sql, rows, chart_hint, current_page)
    
    # Step 8: Return results with natural language explanation
    return {
        "sql": sql,
        "rows": rows,
        "chart_hint": chart_hint,
        "message": nl_message
    }

def get_data_date_range():
    """Get the actual date range from the database"""
    try:
        conn = get_db_connection()
        if not conn:
            return "recent data"
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                MIN(DATE(timestamp)) as min_date,
                MAX(DATE(timestamp)) as max_date,
                COUNT(*) as total_tweets
            FROM tweets 
            WHERE timestamp IS NOT NULL
        """)
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result and result[0] and result[1]:
            min_date = result[0].strftime('%B %d, %Y')
            max_date = result[1].strftime('%B %d, %Y')
            total_tweets = result[2]
            
            if min_date == max_date:
                return f"{min_date} ({total_tweets:,} tweets)"
            else:
                return f"{min_date} to {max_date} ({total_tweets:,} tweets)"
        else:
            return "recent data"
            
    except Exception as e:
        print(f"[api_server.py:get_data_date_range] Error getting date range: {e}")
        return "recent data"

def handle_rag_query(question: str, screenshot: Optional[str], context_info: dict) -> dict:
    """Handle RAG/UI help queries with detailed, action-oriented explanations"""
    current_page = context_info.get('current_page', 'unknown')
    question_lower = question.lower()
    
    # Get actual date range from database
    date_range = get_data_date_range()
    
    # Detailed, action-oriented page explanations
    page_explanations = {
        'visualization': f"""This page showcases **multidimensional visualizations** for the various emotions across different states for the time frame: **{date_range}**.

**What you can do here:**
🎯 **Filter & Explore:**
- Use emotion filters (anger, joy, fear, sadness, surprise, anticipation, trust, disgust)
- Filter by specific states or regions
- Adjust time ranges to see trends over different periods

📊 **Visualizations Available:**
- **Dot Plot**: See emotion intensity by state (larger dots = higher intensity)
- **Horizon Chart**: View emotion trends over time with layered visualization
- **Time Series**: Track how emotions change over days/weeks/months
- **State Comparisons**: Compare emotion patterns between different states

💡 **Interactive Features:**
- Hover over dots to see detailed emotion breakdowns
- Click states to drill down into specific data
- Use the legend to toggle emotions on/off
- Export visualizations for presentations""",
        
        'metrics': f"""This is the **Analytics** page showing comprehensive insights about all the data present in our system.

**Data Overview:**
📈 **System Metrics** covering **{date_range}**:
- Total tweet counts and processing statistics
- Geographic distribution across all US states
- Emotion analysis performance metrics

📊 **What you'll find:**
- **Top States by Volume**: Which states generate the most tweets
- **Engagement Analytics**: Likes, retweets, replies, and views patterns  
- **Hourly Activity**: When people are most active on social media
- **Context Analysis**: Most common keywords and topics
- **Sentiment Distribution**: Overall positive/negative/neutral breakdown
- **System Performance**: Processing speed and accuracy metrics

💡 **Use this data to:**
- Understand overall platform performance
- Identify trending topics and peak activity times
- Compare engagement patterns across different regions""",
        
        'history': f"""This is the **History** page showing all the tweets stored in our database from **{date_range}**.

**What you can see:**
📝 **Tweet Archive**: Browse through all processed tweets with complete emotion analysis
- **20 tweets per page** with pagination controls
- **Filter by state** using the dropdown menu
- Each tweet shows detailed emotion scores for all 8 emotions
- Complete metadata: username, timestamp, location, engagement stats

🔍 **Features:**
- **Search & Filter**: Find tweets from specific states or time periods
- **Emotion Scores**: See how each tweet scored on anger, joy, fear, sadness, etc.
- **Engagement Data**: View likes, retweets, replies, and views
- **Geographic Context**: See which state each tweet originated from

💡 **Perfect for:**
- Exploring past trends and patterns
- Finding specific tweets or topics
- Understanding how emotions vary by location and time""",
        
        'live': f"""This is the **Live Stream** page showing tweets as they are generated and processed in real-time.

**What's happening:**
🔴 **Real-Time Processing**: Watch tweets flow through our emotion analysis system live
- Tweets appear instantly as they're captured and analyzed
- Each tweet gets processed for all 8 emotions (anger, joy, fear, sadness, surprise, anticipation, trust, disgust)
- Sentiment analysis (positive/negative/neutral) happens in real-time
- Geographic tagging shows which state each tweet comes from

⚡ **Live Features:**
- **Connection Status**: See if the data stream is active
- **Real-Time Scores**: Watch emotion analysis happen instantly
- **Geographic Distribution**: See tweets from different states as they arrive
- **Engagement Tracking**: Live likes, retweets, and replies data

💡 **Use this to:**
- Monitor current social media sentiment
- See breaking trends as they happen
- Watch how emotions shift in real-time across different states
- Understand the live pulse of social media activity"""
    }
    
    # Get explanation for current page
    explanation = page_explanations.get(current_page, 
        f"This is the TecViz emotion analytics platform analyzing social media data from {date_range}.")
    
    # Handle contextual questions like "and this one?"
    contextual_phrases = ['and this one', 'this one', 'and this', 'what about this', 'and here']
    is_contextual = any(phrase in question_lower for phrase in contextual_phrases)
    
    if is_contextual:
        # For contextual questions, be more direct
        page_names = {
            'live': 'Live Stream',
            'history': 'History', 
            'metrics': 'Analytics',
            'visualization': 'Emotion Map'
        }
        page_name = page_names.get(current_page, 'this page')
        message = f"Now you're looking at the **{page_name}** page.\n\n{explanation}"
    elif any(word in question_lower for word in ['what', 'explain', 'about', 'show', 'page']):
        message = explanation
    elif 'how' in question_lower:
        message = f"{explanation}\n\n💡 **Need help with specific features?** Ask me about filtering, visualizations, or data analysis!"
    else:
        message = f"{explanation}\n\nWhat specific aspect would you like me to explain further?"
    
    return {
        "sql": None,
        "rows": [],
        "chart_hint": None,
        "message": message
    }

@app.post("/chat/vision")
def chat_vision(q: VisionQuestion):
    """Vision-based chat: screenshot + question → LLM (LLaVA or GPT-4V) → answer"""
    if not q.question or not q.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    # Get conversation history
    session_id = q.session_id or "default"
    history = conversation_history.get(session_id, [])
    
    # Classify intent (screenshot always triggers RAG)
    intent, context_info = classify_intent_smart(
        question=q.question,
        has_screenshot=bool(q.screenshot),
        current_page=q.current_page,
        previous_queries=history
    )
    
    # Route to RAG handler
    result = handle_rag_query(q.question, q.screenshot, context_info)
    
    # Save to history
    history.append({
        'question': q.question,
        'intent': intent,
        'context': context_info,
        'has_screenshot': bool(q.screenshot),
        'timestamp': time.time()
    })
    conversation_history[session_id] = history[-MAX_CONVERSATION_HISTORY:]
    
    result['intent'] = intent
    return result

if __name__ == "__main__":
    import uvicorn
    logger.system_event("API_SERVER_STARTING", "Port 9000 (FastAPI)")
    uvicorn.run(app, host="0.0.0.0", port=9000, log_level="info")



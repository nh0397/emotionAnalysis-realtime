from flask import Flask, Response, jsonify
from flask_cors import CORS
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable
import json
import time
from datetime import datetime
from system_logger import ui_logger as logger

app = Flask(__name__)
CORS(app)

def get_kafka_consumer(max_retries=30, retry_interval=2):
    """
    Creates a Kafka consumer instance with retry logic.
    Returns a consumer that reads from the 'tweets' topic.
    """
    retries = 0
    while retries < max_retries:
        try:
            consumer = KafkaConsumer(
                'tweets',
                bootstrap_servers=['localhost:9092'],
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='latest',
                group_id='flask-sse-group',
                enable_auto_commit=True,
                api_version_auto_timeout_ms=30000
            )
            print("✅ Connected to Kafka successfully")
            return consumer
        except NoBrokersAvailable:
            retries += 1
            print(f"⏳ Waiting for Kafka... Attempt {retries}/{max_retries}")
            time.sleep(retry_interval)
        except Exception as e:
            retries += 1
            print(f"❌ Kafka connection error: {e}")
            time.sleep(retry_interval)
    
    print("❌ Failed to connect to Kafka after maximum retries")
    return None

@app.route('/')
def root():
    """API root endpoint providing service information."""
    return jsonify({
        "status": "success",
        "message": "Tweet Stream API is running",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "stream": "/tweets/stream"
        }
    })

@app.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    })

def format_sse(data: dict, event=None) -> str:
    """Format data as SSE"""
    msg = f"data: {json.dumps(data)}\n\n"
    if event is not None:
        msg = f"event: {event}\n{msg}"
    return msg

def event_stream():
    """Generate SSE stream from Kafka messages"""
    print("📡 Client connected to SSE stream")
    
    while True:
        # Try to get consumer
        consumer = get_kafka_consumer()
        if not consumer:
            yield format_sse({"error": "Waiting for Kafka connection..."}, "error")
            time.sleep(5)
            continue

        try:
            # Send initial connection message
            yield format_sse({"status": "connected"}, "connection")
            
            # Start consuming messages
            for message in consumer:
                tweet = message.value
                logger.ui_streamed(tweet.get('id', 'unknown'))
                yield format_sse(tweet, "tweet")

        except Exception as e:
            print(f"❌ Error in stream: {e}")
            yield format_sse({"error": str(e)}, "error")
            if consumer:
                consumer.close()
            time.sleep(5)

@app.route('/tweets/stream')
def stream_tweets():
    """SSE endpoint for real-time tweets."""
    return Response(
        event_stream(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no',
            'Access-Control-Allow-Origin': '*'
        }
    )

if __name__ == "__main__":
    print("🚀 Starting Flask Tweet Stream API...")
    app.run(host='0.0.0.0', port=9000, debug=True, threaded=True)
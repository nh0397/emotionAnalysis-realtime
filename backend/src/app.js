const express = require('express');
const http = require('http');
const WebSocket = require('ws');
const { Kafka } = require('kafkajs');
const cors = require('cors');

const app = express();
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

const PORT = process.env.PORT || 9000;

// Middleware
app.use(cors());
app.use(express.json());

// Initialize Kafka
const kafka = new Kafka({
  clientId: 'tweet-backend',
  brokers: ['localhost:9092']
});

const consumer = kafka.consumer({ groupId: 'tweet-backend-group' });

// Store connected WebSocket clients
const clients = new Set();

// WebSocket connection handling
wss.on('connection', (ws) => {
  console.log('🔌 New WebSocket client connected');
  clients.add(ws);

  // Send welcome message
  ws.send(JSON.stringify({
    type: 'connection',
    message: 'Connected to Real-Time Tweet Stream',
    timestamp: new Date().toISOString()
  }));

  // Handle client disconnect
  ws.on('close', () => {
    console.log('🔌 WebSocket client disconnected');
    clients.delete(ws);
  });
});

// Function to broadcast tweets to all connected clients
function broadcastTweet(tweet) {
  const message = JSON.stringify({
    type: 'tweet',
    data: tweet,
    timestamp: new Date().toISOString()
  });

  clients.forEach((client) => {
    if (client.readyState === WebSocket.OPEN) {
      client.send(message);
    }
  });
}

// Connect to Kafka and start consuming messages
async function startKafkaConsumer() {
  try {
    await consumer.connect();
    await consumer.subscribe({ topic: 'tweets', fromBeginning: true });

    await consumer.run({
      eachMessage: async ({ topic, partition, message }) => {
        const tweet = JSON.parse(message.value.toString());
        console.log('📥 Received tweet from Kafka:', tweet);
        broadcastTweet(tweet);
      },
    });

    console.log('✅ Connected to Kafka and consuming messages');
  } catch (error) {
    console.error('❌ Error connecting to Kafka:', error);
    process.exit(1);
  }
}

// API Routes
app.get('/', (req, res) => {
  res.json({
    status: 'success',
    message: 'Tweet Stream API is running',
    version: '1.0.0',
    endpoints: {
      websocket: `ws://localhost:${PORT}`,
      health: '/health'
    },
    connectedClients: clients.size
  });
});

app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    connectedClients: clients.size
  });
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({
    status: 'error',
    message: 'Something went wrong!',
    error: err.message
  });
});

// Start server
server.listen(PORT, () => {
  console.log(`🚀 Server running on port ${PORT}`);
  console.log(`📊 API available at http://localhost:${PORT}`);
  console.log(`🔗 Health check: http://localhost:${PORT}/health`);
  console.log(`🔌 WebSocket endpoint: ws://localhost:${PORT}`);
  
  // Start consuming from Kafka
  startKafkaConsumer();
});

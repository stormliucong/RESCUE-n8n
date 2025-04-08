require('dotenv').config();
const WebSocket = require('ws');
const redis = require('redis');

// Load environment variables
const REDIS_SERVER = `redis://${process.env.REACT_APP_REDIS_HOST}:${process.env.REACT_APP_REDIS_PORT}`;
const REDIS_PASSWORD = process.env.REACT_APP_REDIS_PASSWORD;
const WEB_SOCKET_PORT = process.env.REACT_APP_WS_PORT || 8080;
const REDIS_CHANNEL = process.env.REACT_APP_REDIS_STREAM_KEY || 'chat_stream';

// Create Redis client
const redisClient = redis.createClient({
  url: REDIS_SERVER,
  password: REDIS_PASSWORD,
});

// Create WebSocket server
const wss = new WebSocket.Server({ port: WEB_SOCKET_PORT });
console.log(`✅ WebSocket server started on port ${WEB_SOCKET_PORT}`);

// Track all connected WebSocket clients
const clients = new Set();

// Handle new WebSocket connection
wss.on('connection', (ws) => {
  console.log('🔗 New WebSocket client connected');
  clients.add(ws);

  ws.on('close', () => {
    clients.delete(ws);
    console.log('❌ WebSocket client disconnected');
  });

  ws.on('error', (err) => {
    console.error('⚠️ WebSocket error:', err);
  });
});

// Initialize Redis connection and subscription
(async () => {
  try {
    console.log(`🔧 Connecting to Redis at ${REDIS_SERVER}`);
    await redisClient.connect();
    console.log('✅ Connected to Redis');

    console.log(`🔔 Subscribing to channel "${REDIS_CHANNEL}"`);
    await redisClient.subscribe(REDIS_CHANNEL, (message) => {
      console.log(`📨 Redis message received on "${REDIS_CHANNEL}":`, message);

      let parsed;
      try {
        parsed = JSON.parse(message);
      } catch (err) {
        console.warn('⚠️ Could not parse message as JSON, sending raw:', message);
        parsed = { message };
      }

      for (const client of clients) {
        if (client.readyState === WebSocket.OPEN) {
          client.send(JSON.stringify(parsed));
        }
      }
    });

    console.log(`📡 Subscribed to Redis channel: ${REDIS_CHANNEL}`);
  } catch (err) {
    console.error('❌ Redis connection or subscription failed:', err);
  }
})();

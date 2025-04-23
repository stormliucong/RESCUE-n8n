// redis-test.js
require('dotenv').config();
const redis = require('redis');

const client = redis.createClient({
  url: `redis://${process.env.REACT_APP_REDIS_HOST}:${process.env.REACT_APP_REDIS_PORT}`,
  password: process.env.REACT_APP_REDIS_PASSWORD
});

client.on('error', (err) => {
  console.error('❌ Redis error:', err);
});

client.on('connect', () => {
  console.log('✅ Connected to Redis');
});

client.connect();

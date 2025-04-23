require('dotenv').config();

module.exports = {
  redis: {
    host: process.env.REACT_APP_REDIS_HOST || 'localhost',
    port: process.env.REACT_APP_REDIS_PORT || 6379,
    password: process.env.REACT_APP_REDIS_PASSWORD || '',
    streamKey: process.env.REACT_APP_REDIS_STREAM_KEY || 'chat_stream'
  },
  websocket: {
    port: process.env.REACT_APP_WS_PORT || 8080
  }
}; 
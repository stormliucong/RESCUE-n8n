export default {
  // Mock mode settings
  mock: {
    enabled: process.env.REACT_APP_MOCK_ENABLED === 'true',
    responseDelay: 1000, // milliseconds
  },
  
  // Redis Configuration
  redis: {
    host: process.env.REACT_APP_REDIS_HOST || 'localhost',
    port: process.env.REACT_APP_REDIS_PORT || 6379,
    password: process.env.REACT_APP_REDIS_PASSWORD || '',
    streamKey: process.env.REACT_APP_REDIS_STREAM_KEY || 'chat_stream',
  },
  
  websocket: {
    host: process.env.REACT_APP_WS_HOST || 'localhost',
    port: process.env.REACT_APP_WS_PORT || 8080
  },
  
  // Agent Configuration
  agents: {
    frontdesk: {
      name: 'Frontdesk Agent',
      endpoint: process.env.REACT_APP_FRONTDESK_ENDPOINT || 'http://localhost:3000/api/frontdesk',
      avatar: {
        src: '/avatars/frontdesk.png',
        alt: 'Frontdesk Agent'
      },
    },
    education: {
      name: 'Education Agent',
      endpoint: process.env.REACT_APP_EDUCATION_ENDPOINT || 'http://localhost:3000/api/education',
      avatar: {
        src: '/avatars/education.png',
        alt: 'Education Agent'
      },
    },
  },
}; 
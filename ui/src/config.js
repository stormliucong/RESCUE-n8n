const config = {
  // Mock mode settings
  mock: {
    enabled: process.env.REACT_APP_MOCK_MODE === 'true',
    responseDelay: 1000, // milliseconds
  },
  
  // Redis Configuration
  redis: {
    host: process.env.REACT_APP_REDIS_HOST || 'localhost',
    port: process.env.REACT_APP_REDIS_PORT || 6379,
    streamKey: process.env.REACT_APP_REDIS_STREAM_KEY || 'chat_messages',
  },
  
  // API Endpoints
  api: {
    baseUrl: process.env.REACT_APP_API_BASE_URL || 'http://localhost:3001',
    endpoints: {
      frontdesk: '/api/frontdesk',
      education: '/api/education',
    },
  },
  
  // Agent Configuration
  agents: {
    frontdesk: {
      name: 'Front Desk Agent',
      endpoint: process.env.REACT_APP_FRONTDESK_ENDPOINT || 'http://localhost:3001/api/frontdesk',
      avatar: {
        type: 'icon',
        value: 'person',
        color: '#1976d2', // Blue color for frontdesk
      },
    },
    education: {
      name: 'Education Agent',
      endpoint: process.env.REACT_APP_EDUCATION_ENDPOINT || 'http://localhost:3001/api/education',
      avatar: {
        type: 'icon',
        value: 'school',
        color: '#2e7d32', // Green color for education
      },
    },
  },
};

export default config; 
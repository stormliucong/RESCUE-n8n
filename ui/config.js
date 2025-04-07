const config = {
  redis: {
    host: process.env.REACT_APP_REDIS_HOST || 'localhost',
    port: process.env.REACT_APP_REDIS_PORT || 6379,
    streamKey: process.env.REACT_APP_REDIS_STREAM_KEY || 'chat_messages',
  },
  agents: {
    frontdesk: {
      name: 'Front Desk Agent',
      endpoint: process.env.REACT_APP_FRONTDESK_ENDPOINT || 'http://localhost:3001/api/frontdesk',
    },
    education: {
      name: 'Education Agent',
      endpoint: process.env.REACT_APP_EDUCATION_ENDPOINT || 'http://localhost:3001/api/education',
    },
  },
};

export default config; 
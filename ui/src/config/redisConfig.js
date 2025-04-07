const redisConfig = {
  username: process.env.REACT_APP_REDIS_USERNAME || 'default',
  password: process.env.REACT_APP_REDIS_PASSWORD,
  socket: {
    host: process.env.REACT_APP_REDIS_HOST,
    port: parseInt(process.env.REACT_APP_REDIS_PORT || '11302', 10)
  }
};

export default redisConfig; 
import { createClient } from 'redis';

class RedisService {
  constructor() {
    this.client = createClient({
      url: `redis://${process.env.REACT_APP_REDIS_USERNAME}:${process.env.REACT_APP_REDIS_PASSWORD}@${process.env.REACT_APP_REDIS_HOST}:${process.env.REACT_APP_REDIS_PORT}`
    });
    this.isConnected = false;
    this.subscribers = new Set();
    this.setupErrorHandling();
  }

  setupErrorHandling() {
    this.client.on('error', (err) => {
      console.error('Redis Client Error:', err);
      this.isConnected = false;
    });

    this.client.on('connect', () => {
      console.log('Redis Client Connected');
      this.isConnected = true;
      this.setupStreamSubscription();
    });

    this.client.on('disconnect', () => {
      console.log('Redis Client Disconnected');
      this.isConnected = false;
    });
  }

  async setupStreamSubscription() {
    if (!this.isConnected) {
      await this.connect();
    }

    try {
      // Subscribe to the stream
      const streamKey = process.env.REACT_APP_REDIS_STREAM_KEY || 'chat:messages';
      console.log('Setting up stream subscription for:', streamKey);

      // Start reading from the beginning of the stream
      let lastId = '0-0';

      // Function to process new messages
      const processMessages = async () => {
        try {
          const response = await this.client.xRead(
            { key: streamKey, id: lastId },
            { COUNT: 1, BLOCK: 0 }
          );

          if (response) {
            for (const stream of response) {
              const [key, messages] = stream;
              for (const message of messages) {
                const [id, fields] = message;
                lastId = id;

                // Convert fields array to object
                const messageObj = {};
                for (let i = 0; i < fields.length; i += 2) {
                  messageObj[fields[i]] = fields[i + 1];
                }

                // Notify subscribers
                this.notifySubscribers(messageObj);
              }
            }
          }
        } catch (error) {
          console.error('Error reading from stream:', error);
        }

        // Continue reading
        processMessages();
      };

      // Start processing messages
      processMessages();
    } catch (error) {
      console.error('Error setting up stream subscription:', error);
    }
  }

  subscribe(callback) {
    console.log('Adding new subscriber to RedisService');
    this.subscribers.add(callback);
    return () => {
      console.log('Removing subscriber from RedisService');
      this.subscribers.delete(callback);
    };
  }

  notifySubscribers(message) {
    console.log('Notifying', this.subscribers.size, 'subscribers with message:', message);
    this.subscribers.forEach(callback => {
      try {
        callback(message);
      } catch (error) {
        console.error('Error in subscriber callback:', error);
      }
    });
  }

  async connect() {
    if (!this.isConnected) {
      try {
        await this.client.connect();
        this.isConnected = true;
      } catch (error) {
        console.error('Failed to connect to Redis:', error);
        throw error;
      }
    }
  }

  async disconnect() {
    if (this.isConnected) {
      try {
        await this.client.disconnect();
        this.isConnected = false;
      } catch (error) {
        console.error('Failed to disconnect from Redis:', error);
        throw error;
      }
    }
  }

  async sendMessage(agent, content) {
    if (!this.isConnected) {
      await this.connect();
    }

    try {
      const streamKey = process.env.REACT_APP_REDIS_STREAM_KEY || 'chat:messages';
      const message = {
        type: 'user',
        agent,
        content,
        timestamp: new Date().toISOString()
      };

      // Add message to stream
      await this.client.xAdd(streamKey, '*', {
        type: message.type,
        agent: message.agent,
        content: message.content,
        timestamp: message.timestamp
      });

      return { status: 'sent', timestamp: message.timestamp };
    } catch (error) {
      console.error('Error sending message:', error);
      throw error;
    }
  }

  async set(key, value) {
    if (!this.isConnected) {
      await this.connect();
    }
    try {
      await this.client.set(key, JSON.stringify(value));
    } catch (error) {
      console.error(`Error setting key ${key}:`, error);
      throw error;
    }
  }

  async get(key) {
    if (!this.isConnected) {
      await this.connect();
    }
    try {
      const value = await this.client.get(key);
      return value ? JSON.parse(value) : null;
    } catch (error) {
      console.error(`Error getting key ${key}:`, error);
      throw error;
    }
  }

  async delete(key) {
    if (!this.isConnected) {
      await this.connect();
    }
    try {
      await this.client.del(key);
    } catch (error) {
      console.error(`Error deleting key ${key}:`, error);
      throw error;
    }
  }

  async exists(key) {
    if (!this.isConnected) {
      await this.connect();
    }
    try {
      return await this.client.exists(key);
    } catch (error) {
      console.error(`Error checking existence of key ${key}:`, error);
      throw error;
    }
  }
}

// Export a singleton instance
const redisService = new RedisService();
export default redisService; 
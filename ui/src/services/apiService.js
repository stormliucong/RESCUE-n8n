import config from '../config';
import mockApiService from '../mock/services/mockApiService';
import axios from 'axios';

class ApiService {
  constructor() {
    this.ws = null;
    this.subscribers = new Set();
  }

  async initialize() {
    if (config.mock.enabled) {
      return; // No initialization needed for mock mode
    }

    // Initialize WebSocket connection for real mode
    this.ws = new WebSocket(`ws://${config.redis.host}:${config.redis.port}/ws`);
    
    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.notifySubscribers(message);
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    this.ws.onclose = () => {
      console.log('WebSocket connection closed');
    };
  }

  async sendMessage(agent, message) {
    if (config.mock.enabled) {
      return mockApiService.sendMessage(agent, message);
    }

    try {
      const response = await axios.post(
        `${config.api.baseUrl}${config.api.endpoints[agent]}`,
        { message }
      );
      return response.data;
    } catch (error) {
      console.error('Error sending message:', error);
      throw error;
    }
  }

  subscribe(callback) {
    if (config.mock.enabled) {
      return mockApiService.subscribe(callback);
    }

    this.subscribers.add(callback);
    return () => this.subscribers.delete(callback);
  }

  notifySubscribers(message) {
    this.subscribers.forEach(callback => callback(message));
  }

  cleanup() {
    if (!config.mock.enabled && this.ws) {
      this.ws.close();
    }
  }
}

// Create and initialize the service
const apiService = new ApiService();
apiService.initialize();

export default apiService; 
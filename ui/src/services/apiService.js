import config from '../config';
import mockApiService from '../mock/services/mockApiService';
import axios from 'axios';

class ApiService {
  constructor() {
    this.ws = null;
    this.subscribers = new Set();
    this.sessionId = this.generateSessionId();
    this.messageCounter = 0;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000; // 1 second
  }

  generateSessionId() {
    return 'session_' + Math.random().toString(36).substr(2, 9);
  }

  async initialize() {
    if (config.mock.enabled) {
      return; // No initialization needed for mock mode
    }

    this.connectWebSocket();
  }

  connectWebSocket() {
    const wsUrl = `ws://${config.websocket.host}:${config.websocket.port}?session=${this.sessionId}`;
    this.ws = new WebSocket(wsUrl);
    
    this.ws.onopen = () => {
      console.log('WebSocket connection established');
      this.reconnectAttempts = 0;
    };
    
    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.type !== 'user') {
        this.messageCounter++;
        this.notifySubscribers(message);
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    this.ws.onclose = () => {
      console.log('WebSocket connection closed');
      this.handleReconnect();
    };
  }

  handleReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
      setTimeout(() => this.connectWebSocket(), this.reconnectDelay * this.reconnectAttempts);
    } else {
      console.error('Max reconnection attempts reached');
      this.notifySubscribers({
        type: 'system',
        content: 'Connection lost. Please refresh the page.',
        timestamp: new Date().toISOString()
      });
    }
  }

  async sendMessage(agent, message) {
    if (config.mock.enabled) {
      await new Promise(resolve => setTimeout(resolve, config.mock.responseDelay));
      return { status: 'received', message: 'Message received and being processed' };
    }

    try {
      const response = await axios.post(
        config.agents[agent].endpoint,
        { 
          sessionId: this.sessionId,
          message: message,
          counter: this.messageCounter
        }
      );
      
      return { 
        status: 'received', 
        message: 'Message received and being processed',
        ...response.data 
      };
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

  getSessionInfo() {
    return {
      sessionId: this.sessionId,
      messageCount: this.messageCounter
    };
  }
}

// Create and initialize the service
const apiService = new ApiService();
apiService.initialize();

export default apiService; 
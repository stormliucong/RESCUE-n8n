import config from '../config';
import mockApiService from '../mock/services/mockApiService';
import axios from 'axios';
import redisService from './redisService';

class ApiService {
  constructor() {
    this.subscribers = new Set();
    this.setupRedisSubscription();
  }

  setupRedisSubscription() {
    // Subscribe to Redis service
    this.redisUnsubscribe = redisService.subscribe((message) => {
      console.log('ApiService received message from Redis:', message);
      this.notifySubscribers(message);
    });
  }

  async sendMessage(agent, content) {
    console.log('ApiService sending message:', { agent, content });
    
    try {
      // Send message through Redis service
      const response = await redisService.sendMessage(agent, content);
      console.log('Message sent successfully:', response);
      return response;
    } catch (error) {
      console.error('Error sending message:', error);
      throw error;
    }
  }

  subscribe(callback) {
    console.log('Adding new subscriber to ApiService');
    this.subscribers.add(callback);
    return () => {
      console.log('Removing subscriber from ApiService');
      this.subscribers.delete(callback);
    };
  }

  notifySubscribers(message) {
    console.log('ApiService notifying', this.subscribers.size, 'subscribers');
    this.subscribers.forEach(callback => {
      try {
        callback(message);
      } catch (error) {
        console.error('Error in subscriber callback:', error);
      }
    });
  }

  cleanup() {
    console.log('Cleaning up ApiService');
    this.subscribers.clear();
    if (this.redisUnsubscribe) {
      this.redisUnsubscribe();
    }
  }
}

// Export a singleton instance
const apiService = new ApiService();
export default apiService; 
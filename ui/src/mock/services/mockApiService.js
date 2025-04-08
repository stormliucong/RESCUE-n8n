import mockRedisService from './mockRedisService';

class MockApiService {
  constructor() {
    this.subscribers = new Set();
  }

  async sendMessage(agent, message) {
    // Simulate message receipt confirmation
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // Forward the message to mock Redis service
    await mockRedisService.receiveUserMessage(message);
    
    return { 
      status: 'received', 
      message: 'Message received and being processed',
      agent: agent
    };
  }

  subscribe(callback) {
    // Subscribe to both this service and mock Redis service
    const unsubscribeRedis = mockRedisService.subscribe(callback);
    this.subscribers.add(callback);
    
    return () => {
      unsubscribeRedis();
      this.subscribers.delete(callback);
    };
  }

  notifySubscribers(message) {
    this.subscribers.forEach(callback => callback(message));
  }

  cleanup() {
    // Reset the mock Redis service for next test
    mockRedisService.reset();
  }
}

// Create the service
const mockApiService = new MockApiService();

export default mockApiService; 
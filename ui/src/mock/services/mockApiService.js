import conversations from '../data/conversations.json';

class MockApiService {
  constructor() {
    this.conversations = conversations.conversations;
    this.currentConversation = this.conversations[0];
    this.messageIndex = 0;
    this.subscribers = new Set();
  }

  // Simulate sending a message to an agent
  async sendMessage(agent, message) {
    // In a real implementation, this would send to the actual backend
    console.log(`Sending message to ${agent}:`, message);
    
    // Simulate response delay
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Find the next message from the mock data
    const nextMessage = this.getNextMessage();
    if (nextMessage) {
      this.notifySubscribers(nextMessage);
    }
    
    return { success: true };
  }

  // Get the next message from the mock conversation
  getNextMessage() {
    if (this.messageIndex < this.currentConversation.messages.length) {
      const message = this.currentConversation.messages[this.messageIndex];
      this.messageIndex++;
      return message;
    }
    return null;
  }

  // Simulate Redis stream subscription
  subscribe(callback) {
    this.subscribers.add(callback);
    return () => this.subscribers.delete(callback);
  }

  // Notify all subscribers of a new message
  notifySubscribers(message) {
    this.subscribers.forEach(callback => callback(message));
  }

  // Reset the conversation (for demo purposes)
  resetConversation() {
    this.messageIndex = 0;
  }
}

export const mockApiService = new MockApiService();

// Export the service as a singleton
export default mockApiService; 
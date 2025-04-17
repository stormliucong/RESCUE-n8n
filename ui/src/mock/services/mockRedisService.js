import conversations from '../data/conversations.json';

class MockRedisService {
  constructor() {
    this.subscribers = new Set();
    this.messageQueue = [];
    this.currentIndex = 0;
    this.isProcessing = false;
  }

  // Initialize with conversation data
  initialize() {
    // Flatten all messages from all conversations
    this.messageQueue = conversations.conversations.flatMap(conv => 
      conv.messages.map(msg => ({
        ...msg,
        conversationId: conv.id
      }))
    );
  }

  // Simulate Redis stream subscription
  subscribe(callback) {
    this.subscribers.add(callback);
    return () => this.subscribers.delete(callback);
  }

  // Simulate receiving a user message and trigger appropriate responses
  async receiveUserMessage(message) {
    // Find the next relevant messages in the queue
    const nextMessages = this.findNextMessages(message);
    
    // Simulate processing delay
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Send each message to subscribers
    for (const msg of nextMessages) {
      this.notifySubscribers(msg);
    }
  }

  // Find the next relevant messages based on the user's message
  findNextMessages(userMessage) {
    const messages = [];
    let foundUserMessage = false;

    // Start from current index and look for matching user message
    for (let i = this.currentIndex; i < this.messageQueue.length; i++) {
      const msg = this.messageQueue[i];
      
      if (msg.type === 'user' && !foundUserMessage) {
        // Found the matching user message
        if (msg.content.toLowerCase().includes(userMessage.toLowerCase())) {
          foundUserMessage = true;
          this.currentIndex = i + 1;
        }
      } else if (foundUserMessage && msg.type !== 'user') {
        // Collect all non-user messages until next user message
        messages.push(msg);
        if (i + 1 < this.messageQueue.length && this.messageQueue[i + 1].type === 'user') {
          break;
        }
      }
    }

    return messages;
  }

  notifySubscribers(message) {
    this.subscribers.forEach(callback => callback(message));
  }

  // Reset the conversation (for testing purposes)
  reset() {
    this.currentIndex = 0;
  }
}

// Create and initialize the service
const mockRedisService = new MockRedisService();
mockRedisService.initialize();

export default mockRedisService; 
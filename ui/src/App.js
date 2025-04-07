import React, { useState, useEffect, useRef } from 'react';
import { Box, Container, TextField, Button, Typography, Paper, Avatar } from '@mui/material';
import { styled } from '@mui/material/styles';
import config from './config';
import apiService from './services/apiService';

const ChatContainer = styled(Paper)(({ theme }) => ({
  height: '80vh',
  display: 'flex',
  flexDirection: 'column',
  padding: theme.spacing(2),
}));

const MessageList = styled(Box)({
  flex: 1,
  overflowY: 'auto',
  marginBottom: '16px',
});

const Message = styled(Box)(({ theme, isUser }) => ({
  display: 'flex',
  justifyContent: isUser ? 'flex-end' : 'flex-start',
  marginBottom: theme.spacing(1),
}));

const MessageContent = styled(Paper)(({ theme, isUser }) => ({
  padding: theme.spacing(1, 2),
  maxWidth: '70%',
  backgroundColor: isUser ? theme.palette.primary.main : theme.palette.grey[100],
  color: isUser ? theme.palette.primary.contrastText : theme.palette.text.primary,
}));

const SystemMessage = styled(Typography)(({ theme }) => ({
  textAlign: 'center',
  color: theme.palette.text.secondary,
  margin: theme.spacing(1, 0),
}));

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [currentAgent, setCurrentAgent] = useState('frontdesk');
  const messagesEndRef = useRef(null);

  useEffect(() => {
    // Set initial system message
    setMessages([{
      type: 'system',
      content: `Now talking to ${config.agents.frontdesk.name}`,
      timestamp: new Date().toISOString()
    }]);

    // Subscribe to message stream (either mock or real)
    const unsubscribe = apiService.subscribe((message) => {
      handleNewMessage(message);
    });

    return () => {
      unsubscribe();
      apiService.cleanup();
    };
  }, []);

  const handleNewMessage = (message) => {
    setMessages((prev) => [...prev, message]);
    
    // If the agent has changed, add a system message
    if (currentAgent && message.agent && message.agent !== currentAgent) {
      setMessages((prev) => [
        ...prev,
        {
          type: 'system',
          content: `Now talking to ${config.agents[message.agent].name}`,
          timestamp: new Date().toISOString()
        },
      ]);
    }
    if (message.agent) {
      setCurrentAgent(message.agent);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = {
      type: 'user',
      content: input,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');

    try {
      // Send message using the API service (mock or real)
      await apiService.sendMessage(currentAgent, input);
    } catch (error) {
      console.error('Error sending message:', error);
    }
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <Container maxWidth="md">
      <Typography variant="h4" component="h1" gutterBottom align="center">
        Multi-Agent Chatbot
      </Typography>
      <ChatContainer elevation={3}>
        <MessageList>
          {messages.map((message, index) => (
            <React.Fragment key={index}>
              {message.type === 'system' ? (
                <SystemMessage variant="body2">
                  {message.content}
                </SystemMessage>
              ) : (
                <Message isUser={message.type === 'user'}>
                  <MessageContent isUser={message.type === 'user'}>
                    <Typography variant="body1">{message.content}</Typography>
                    {message.type !== 'user' && (
                      <Typography variant="caption" display="block">
                        {config.agents[message.agent].name}
                      </Typography>
                    )}
                  </MessageContent>
                </Message>
              )}
            </React.Fragment>
          ))}
          <div ref={messagesEndRef} />
        </MessageList>
        <form onSubmit={handleSubmit}>
          <Box display="flex" gap={1}>
            <TextField
              fullWidth
              variant="outlined"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type your message..."
            />
            <Button
              type="submit"
              variant="contained"
              color="primary"
              disabled={!input.trim()}
            >
              Send
            </Button>
          </Box>
        </form>
      </ChatContainer>
    </Container>
  );
}

export default App; 
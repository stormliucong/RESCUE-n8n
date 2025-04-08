import React, { useState, useEffect, useRef } from 'react';
import { Box, Container, TextField, Button, Typography, Paper, Avatar } from '@mui/material';
import { styled } from '@mui/material/styles';
import PersonIcon from '@mui/icons-material/Person';
import SchoolIcon from '@mui/icons-material/School';
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

const MessageAvatar = styled(Avatar)(({ theme, color }) => ({
  backgroundColor: color,
  marginRight: theme.spacing(1),
  marginLeft: theme.spacing(1),
}));

const MessageWrapper = styled(Box)(({ theme, isUser }) => ({
  display: 'flex',
  alignItems: 'flex-start',
  justifyContent: isUser ? 'flex-end' : 'flex-start',
  marginBottom: theme.spacing(1),
  width: '100%',
}));

const MessageContent = styled(Paper)(({ theme, isUser }) => ({
  padding: theme.spacing(1, 2),
  maxWidth: '70%',
  backgroundColor: isUser ? theme.palette.primary.main : theme.palette.grey[100],
  color: isUser ? theme.palette.primary.contrastText : theme.palette.text.primary,
  display: 'flex',
  flexDirection: 'column',
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
  const [isSending, setIsSending] = useState(false);
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
    if (!input.trim() || isSending) return;

    const userMessage = {
      type: 'user',
      content: input,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsSending(true);

    try {
      // Send message and wait for receipt confirmation
      const response = await apiService.sendMessage(currentAgent, input);
      console.log('Message receipt:', response);
    } catch (error) {
      console.error('Error sending message:', error);
      // Optionally show error message to user
      setMessages((prev) => [
        ...prev,
        {
          type: 'system',
          content: 'Error sending message. Please try again.',
          timestamp: new Date().toISOString()
        },
      ]);
    } finally {
      setIsSending(false);
    }
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const getAgentAvatar = (agent) => {
    if (!agent) return null;
    const agentConfig = config.agents[agent];
    if (!agentConfig?.avatar) return null;

    const { type, value, color } = agentConfig.avatar;
    
    if (type === 'icon') {
      return (
        <MessageAvatar sx={{ bgcolor: color }}>
          {value === 'person' ? <PersonIcon /> : <SchoolIcon />}
        </MessageAvatar>
      );
    }
    
    return (
      <MessageAvatar src={value} alt={agentConfig.name} sx={{ bgcolor: color }} />
    );
  };

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
                <MessageWrapper isUser={message.type === 'user'}>
                  {message.type !== 'user' && getAgentAvatar(message.agent)}
                  <MessageContent isUser={message.type === 'user'}>
                    <Typography variant="body1">{message.content}</Typography>
                    {message.type !== 'user' && (
                      <Typography variant="caption" display="block">
                        {config.agents[message.agent].name}
                      </Typography>
                    )}
                  </MessageContent>
                </MessageWrapper>
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
// ChatWindow.jsx
import React, { useState, useEffect, useRef } from 'react';
import { io } from 'socket.io-client';
import ChatBubble from './ChatBubble';

// Connect to your Flask server's Socket.IO endpoint.
// IMPORTANT: Make sure this URL matches your Flask server domain/port (or ngrok URL if used)
const socket = io('/', {
  path: '/socket.io',
  transports: ['websocket'],
});

function ChatWindow({ sessionId }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isWaiting, setIsWaiting] = useState(false);
  const chatEndRef = useRef(null);

  useEffect(() => {
    socket.on('connect', () => {
      console.log("Socket connected. Emitting register for session:", sessionId);
      socket.emit('register', { sessionId });
    });

    socket.on('connect_error', (err) => {
      console.error("Socket connect error:", err);
    });

    // Listen for reply events from the server
    socket.on('reply', (data) => {
      console.log("Received reply:", data);
      setIsWaiting(false); // remove loading indicator on reply arrival
      setMessages((prev) => [
        ...prev,
        {
          sender: data.responding_agent || 'Agent',
          text: data.message,
        },
      ]);
    });

    return () => {
      socket.off('connect');
      socket.off('connect_error');
      socket.off('reply');
      // Optional: don't disconnect if you plan for persistent socket connection
      // socket.disconnect();
    };
  }, [sessionId]);

  useEffect(() => {
    // Scroll to bottom whenever messages update
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isWaiting]);

  const sendMessage = async () => {
    if (!input.trim()) return;

    // Append user message locally
    setMessages((prev) => [
      ...prev,
      { sender: 'You', text: input },
    ]);
    // Indicate that the app is waiting for an answer
    setIsWaiting(true);

    setInput('');

    try {
      await fetch('/route_message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sessionId,
          message: input,
        }),
      });
    } catch (err) {
      console.error('Error sending message:', err);
      setIsWaiting(false); // clear waiting indicator on error
    }
    
  };

  return (
    <div style={{
      backgroundColor: "#fff",
      width: "700px",
      height: "600px",
      borderRadius: "10px",
      display: "flex",
      flexDirection: "column",
      overflow: "hidden",
      boxShadow: "0 0 10px rgba(0,0,0,0.2)"
    }}>
      <div style={{
        flex: 1,
        padding: "10px",
        overflowY: "auto"
      }}>
        {messages.map((msg, i) => (
          <ChatBubble key={i} sender={msg.sender} text={msg.text} />
        ))}
        {isWaiting && (
          <ChatBubble sender="Agent" text="Typing..." isLoading={true} />
        )}
        <div ref={chatEndRef} />
      </div>
      <div style={{
        display: "flex",
        padding: "10px",
        borderTop: "1px solid #ddd"
      }}>
        <input
          type="text"
          style={{
            flex: 1,
            padding: "10px",
            border: "1px solid #ccc",
            borderRadius: "5px"
          }}
          placeholder="Type your message..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
        />
        <button
          onClick={sendMessage}
          style={{
            marginLeft: "10px",
            padding: "10px 20px",
            backgroundColor: "#007bff",
            color: "#fff",
            border: "none",
            borderRadius: "5px"
          }}
        >
          Send
        </button>
      </div>
    </div>
  );
}

export default ChatWindow;

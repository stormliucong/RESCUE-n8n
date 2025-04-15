// ChatBubble.jsx
import React from 'react';
import './ChatBubble.css';

export default function ChatBubble({ sender, text, isLoading }) {
  const isUser = sender === 'You';
  const isFrontdesk = sender === 'frontdesk_agent';
  const isEducation = sender === 'education_agent';

  let bubbleStyle = {
    maxWidth: '75%',
    padding: '10px',
    marginBottom: '8px',
    borderRadius: '12px',
    clear: 'both'
  };

  let wrapperStyle = {
    display: 'flex',
    justifyContent: isUser ? 'flex-end' : 'flex-start'
  };

  if (isUser) {
    bubbleStyle = {
      ...bubbleStyle,
      backgroundColor: '#007bff',
      color: 'white'
    };
  } else if (isFrontdesk) {
    bubbleStyle = {
      ...bubbleStyle,
      backgroundColor: '#28a745',
      color: 'white'
    };
  } else if (isEducation) {
    bubbleStyle = {
      ...bubbleStyle,
      backgroundColor: '#6f42c1',
      color: 'white'
    };
  } else {
    bubbleStyle = {
      ...bubbleStyle,
      backgroundColor: '#e0e0e0',
      color: 'black'
    };
  }

  const label =
    isFrontdesk ? 'Front Desk' :
    isEducation ? 'Education' :
    isUser ? 'You' : sender;

  return (
    <div style={wrapperStyle}>
    <div style={bubbleStyle}>
      <strong>{label}:</strong>{" "}
      {isLoading ? (
        /* The 3-dot typing indicator */
        <div className="typing-indicator">
          <span className="dot dot1"></span>
          <span className="dot dot2"></span>
          <span className="dot dot3"></span>
        </div>
      ) : (
        text
      )}
    </div>
  </div>
  );
}

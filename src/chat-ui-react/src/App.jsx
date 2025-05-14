// App.jsx
import React from 'react';
import ChatWindow from './ChatWindow';

// Generate a stable sessionId here; once the app loads it stays constant.
const sessionId = `user_${Math.floor(Math.random() * 101)}`;

const App = () => {
  return (
    <div style={{
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      minHeight: "100vh",
      backgroundColor: "#f4f4f4",
      padding: "20px"
    }}>
      <header style={{ marginBottom: "20px", textAlign: "center" }}>
        <h1 style={{ color: "#000" , margin: 0, fontSize: "36px", fontWeight: "bold" }}>Multi-Agent Chat Test</h1>
        <h3 style={{ margin: 0, fontSize: "20px", fontWeight: "normal", color: "gray" }}>
          Session: {sessionId}
        </h3>
      </header>
      {/* Pass the same sessionId to ChatWindow */}
      <ChatWindow sessionId={sessionId} />
    </div>
  );
};

export default App;

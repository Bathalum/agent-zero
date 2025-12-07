import React from 'react';
import { AGUIProvider, useAGUI } from '@argent/agui-client/react';
import './App.css';

function ChatComponent() {
  const { messages, streamingMessage, isStreaming, sendMessage, isConnected, error } = useAGUI();
  const [input, setInput] = React.useState('');
  
  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || !isConnected) return;
    
    try {
      await sendMessage(input);
      setInput('');
    } catch (err) {
      console.error('Failed to send message:', err);
    }
  };
  
  const allMessages = [...messages];
  if (streamingMessage) {
    allMessages.push(streamingMessage);
  }
  
  return (
    <div className="chat-container">
      <div className="chat-header">
        <h1>AG-UI React Chat</h1>
        <div className={`status ${isConnected ? 'connected' : 'disconnected'}`}>
          {isConnected ? 'Connected' : 'Disconnected'}
        </div>
      </div>
      
      {error && (
        <div className="error-banner">
          Error: {error.message}
        </div>
      )}
      
      <div className="messages">
        {allMessages.map((msg) => (
          <div key={msg.id} className={`message message-${msg.type}`}>
            <div className="message-content">{msg.content}</div>
            <div className="message-time">
              {new Date(msg.timestamp).toLocaleTimeString()}
            </div>
          </div>
        ))}
        {isStreaming && <div className="streaming-indicator">...</div>}
      </div>
      
      <form onSubmit={handleSend} className="input-form">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type a message..."
          disabled={!isConnected}
        />
        <button type="submit" disabled={!isConnected || !input.trim()}>
          Send
        </button>
      </form>
    </div>
  );
}

function App() {
  const contextId = new URLSearchParams(window.location.search).get('context_id') || 'default';
  
  return (
    <AGUIProvider
      url="http://localhost:50080"
      contextId={contextId}
      transport="auto"
    >
      <ChatComponent />
    </AGUIProvider>
  );
}

export default App;


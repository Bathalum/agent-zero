# AG-UI Examples

Complete examples demonstrating AG-UI client library usage.

## Table of Contents

- [Basic Chat](#basic-chat)
- [Streaming Response](#streaming-response)
- [Error Handling](#error-handling)
- [Reconnection](#reconnection)
- [React Example](#react-example)
- [Vue Example](#vue-example)
- [Vanilla JS Example](#vanilla-js-example)
- [Custom Integration](#custom-integration)

## Basic Chat

Simple chat interface with message sending and receiving.

```javascript
import { AGUIClient } from '@argent/agui-client';

const client = new AGUIClient({
  url: 'http://localhost:50080',
  contextId: 'chat-123',
  transport: 'auto'
});

// Set up event handlers
client.on('message', (event) => {
  console.log('User message:', event.data.content);
});

client.on('response', (event) => {
  console.log('Agent response:', event.data.content);
});

// Connect
await client.connect();

// Send message
await client.sendMessage('Hello, agent!');
```

## Streaming Response

Handle streaming responses with incremental updates.

```javascript
let currentStream = null;

client.on('stream_chunk', (event) => {
  const messageId = event.data.message_id;
  const chunk = event.data.chunk;
  const full = event.data.full;
  
  // Create or update streaming message
  if (!currentStream || currentStream.id !== messageId) {
    currentStream = {
      id: messageId,
      content: ''
    };
    // Add to UI
    addMessageToUI(currentStream);
  }
  
  // Update content
  currentStream.content = full;
  updateMessageInUI(currentStream);
});

client.on('stream_end', (event) => {
  if (currentStream && currentStream.id === event.data.message_id) {
    // Finalize message
    currentStream.content = event.data.final_text || currentStream.content;
    finalizeMessageInUI(currentStream);
    currentStream = null;
  }
});
```

## Error Handling

Comprehensive error handling with user feedback.

```javascript
client.on('error', (error) => {
  console.error('Connection error:', error);
  showErrorNotification(error.message);
});

client.on('reconnecting', ({ attempt, delay }) => {
  console.log(`Reconnecting (attempt ${attempt})...`);
  showReconnectingStatus(attempt, delay);
});

client.on('reconnect_failed', () => {
  console.error('Failed to reconnect');
  showReconnectFailedMessage();
  promptUserToRefresh();
});

// Handle send errors
try {
  await client.sendMessage('Hello!');
} catch (error) {
  console.error('Failed to send:', error);
  showSendError(error);
}
```

## Reconnection

Custom reconnection logic with exponential backoff.

```javascript
const client = new AGUIClient({
  url: 'http://localhost:50080',
  contextId: 'my-context',
  reconnect: true,
  reconnectInterval: 1000,
  maxReconnectAttempts: 10,
  reconnectBackoff: 1.5
});

client.on('reconnecting', ({ attempt, delay }) => {
  updateUI(`Reconnecting... (attempt ${attempt}/${client.config.maxReconnectAttempts})`);
});

client.on('connected', () => {
  updateUI('Connected');
  // Flush any queued messages
  flushMessageQueue();
});
```

## React Example

Complete React chat application.

```jsx
import React, { useState } from 'react';
import { AGUIProvider, useAGUI } from '@argent/agui-client/react';

function ChatMessages() {
  const { messages, streamingMessage, isStreaming } = useAGUI();
  
  const allMessages = [...messages];
  if (streamingMessage) {
    allMessages.push(streamingMessage);
  }
  
  return (
    <div className="messages">
      {allMessages.map(msg => (
        <div key={msg.id} className={`message message-${msg.type}`}>
          <div className="content">{msg.content}</div>
          <div className="time">
            {new Date(msg.timestamp).toLocaleTimeString()}
          </div>
        </div>
      ))}
      {isStreaming && <div className="streaming">...</div>}
    </div>
  );
}

function ChatInput() {
  const { sendMessage, isConnected } = useAGUI();
  const [input, setInput] = useState('');
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || !isConnected) return;
    
    try {
      await sendMessage(input);
      setInput('');
    } catch (error) {
      console.error('Failed to send:', error);
    }
  };
  
  return (
    <form onSubmit={handleSubmit}>
      <input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Type a message..."
        disabled={!isConnected}
      />
      <button type="submit" disabled={!isConnected || !input.trim()}>
        Send
      </button>
    </form>
  );
}

function ChatApp() {
  return (
    <AGUIProvider
      url="http://localhost:50080"
      contextId="chat-123"
    >
      <div className="chat-app">
        <ChatMessages />
        <ChatInput />
      </div>
    </AGUIProvider>
  );
}

export default ChatApp;
```

## Vue Example

Complete Vue chat application.

```vue
<template>
  <div class="chat-app">
    <div class="messages">
      <div
        v-for="msg in allMessages"
        :key="msg.id"
        :class="['message', `message-${msg.type}`]"
      >
        <div class="content">{{ msg.content }}</div>
        <div class="time">{{ formatTime(msg.timestamp) }}</div>
      </div>
      <div v-if="isStreaming" class="streaming">...</div>
    </div>
    
    <form @submit.prevent="handleSend">
      <input
        v-model="input"
        placeholder="Type a message..."
        :disabled="!isConnected"
      />
      <button type="submit" :disabled="!isConnected || !input.trim()">
        Send
      </button>
    </form>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useAgui } from '@argent/agui-client/vue';

const {
  messages,
  streamingMessage,
  isStreaming,
  sendMessage,
  isConnected
} = useAgui({
  url: 'http://localhost:50080',
  contextId: 'chat-123'
});

const input = ref('');

const allMessages = computed(() => {
  const msgs = [...messages.value];
  if (streamingMessage.value) {
    msgs.push(streamingMessage.value);
  }
  return msgs;
});

const handleSend = async () => {
  if (!input.value.trim() || !isConnected.value) return;
  
  try {
    await sendMessage(input.value);
    input.value = '';
  } catch (error) {
    console.error('Failed to send:', error);
  }
};

const formatTime = (timestamp) => {
  return new Date(timestamp).toLocaleTimeString();
};
</script>
```

## Vanilla JS Example

Complete vanilla JavaScript chat application.

```html
<!DOCTYPE html>
<html>
<head>
  <title>AG-UI Chat</title>
  <style>
    .chat-container {
      max-width: 800px;
      margin: 0 auto;
      padding: 20px;
    }
    .messages {
      height: 400px;
      overflow-y: auto;
      border: 1px solid #ddd;
      padding: 10px;
      margin-bottom: 10px;
    }
    .message {
      margin-bottom: 10px;
      padding: 8px;
      border-radius: 4px;
    }
    .message-message {
      background: #e3f2fd;
    }
    .message-response {
      background: #f1f8e9;
    }
    .input-form {
      display: flex;
    }
    .input-form input {
      flex: 1;
      padding: 8px;
      margin-right: 8px;
    }
    .input-form button {
      padding: 8px 16px;
    }
  </style>
</head>
<body>
  <div class="chat-container">
    <div id="messages" class="messages"></div>
    <form id="input-form" class="input-form">
      <input id="message-input" type="text" placeholder="Type a message..." />
      <button type="submit">Send</button>
    </form>
  </div>

  <script type="module">
    import { createChatInterface } from '@argent/agui-client/vanilla';
    
    const chat = createChatInterface({
      url: 'http://localhost:50080',
      contextId: 'chat-123',
      messageContainer: document.getElementById('messages'),
      inputElement: document.getElementById('message-input'),
      sendButton: document.querySelector('#input-form button'),
      statusElement: null
    });
    
    // Update button state
    chat.client.on('connected', () => {
      document.getElementById('message-input').disabled = false;
      document.querySelector('#input-form button').disabled = false;
    });
    
    chat.client.on('disconnected', () => {
      document.getElementById('message-input').disabled = true;
      document.querySelector('#input-form button').disabled = true;
    });
  </script>
</body>
</html>
```

## Custom Integration

Custom integration with state management.

```javascript
import { AGUIClient } from '@argent/agui-client';
import { createStore } from 'redux';

// Redux store
const store = createStore((state = { messages: [] }, action) => {
  switch (action.type) {
    case 'AGUI_MESSAGE':
      return {
        ...state,
        messages: [...state.messages, action.payload]
      };
    case 'AGUI_STREAM_UPDATE':
      return {
        ...state,
        messages: state.messages.map(msg =>
          msg.id === action.payload.id
            ? { ...msg, content: action.payload.content }
            : msg
        )
      };
    default:
      return state;
  }
});

// Create client
const client = new AGUIClient({
  url: 'http://localhost:50080',
  contextId: 'my-context'
});

// Dispatch to Redux
client.on('message', (event) => {
  store.dispatch({
    type: 'AGUI_MESSAGE',
    payload: {
      id: event.data.message_id,
      type: 'message',
      content: event.data.content,
      timestamp: event.timestamp
    }
  });
});

client.on('stream_chunk', (event) => {
  store.dispatch({
    type: 'AGUI_STREAM_UPDATE',
    payload: {
      id: event.data.message_id,
      content: event.data.full
    }
  });
});

// Connect
await client.connect();
```

## Running Examples

### React Example

```bash
cd examples/react-chat
npm install
npm run dev
```

### Vue Example

```bash
cd examples/vue-chat
npm install
npm run dev
```

### Vanilla JS Example

Open `examples/vanilla-chat/index.html` in a browser (requires a local server for ES modules).

## Next Steps

- See [Integration Guide](./integration.md) for detailed integration instructions
- Check [Client API](./client-api.md) for complete API reference
- Read [Troubleshooting](./troubleshooting.md) for common issues


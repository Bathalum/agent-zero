# AG-UI Integration Guide

This guide explains how to integrate AG-UI into your application.

## Table of Contents

- [Installation](#installation)
- [Basic Usage](#basic-usage)
- [Framework Integration](#framework-integration)
- [Configuration](#configuration)
- [Event Handling](#event-handling)
- [Error Handling](#error-handling)
- [Best Practices](#best-practices)

## Installation

### NPM

```bash
npm install @argent/agui-client
```

### CDN (Browser)

```html
<script type="module">
  import { AGUIClient } from 'https://cdn.jsdelivr.net/npm/@argent/agui-client/dist/client.esm.js';
</script>
```

## Basic Usage

### 1. Create a Client Instance

```javascript
import { AGUIClient } from '@argent/agui-client';

const client = new AGUIClient({
  url: 'http://localhost:50080',
  contextId: 'my-context-id',
  transport: 'auto' // or 'sse', 'ws'
});
```

### 2. Set Up Event Handlers

```javascript
// Listen for messages
client.on('message', (event) => {
  console.log('Message:', event.data.content);
});

// Listen for stream chunks
client.on('stream_chunk', (event) => {
  console.log('Chunk:', event.data.chunk);
  console.log('Full text so far:', event.data.full);
});

// Listen for stream completion
client.on('stream_end', (event) => {
  console.log('Stream complete:', event.data.final_text);
});

// Listen for errors
client.on('error', (error) => {
  console.error('Error:', error);
});
```

### 3. Connect and Send Messages

```javascript
// Connect
await client.connect();

// Send a message
await client.sendMessage('Hello, agent!');

// Send with options
await client.sendMessage('Hello!', {
  messageId: 'msg-123',
  attachments: ['/path/to/file.txt']
});
```

### 4. Disconnect

```javascript
client.disconnect();
```

## Framework Integration

### React

```jsx
import { AGUIProvider, useAGUI } from '@argent/agui-client/react';

function ChatComponent() {
  const { messages, sendMessage, isConnected } = useAGUI();
  
  return (
    <div>
      {messages.map(msg => (
        <div key={msg.id}>{msg.content}</div>
      ))}
      <button onClick={() => sendMessage('Hello!')}>
        Send
      </button>
    </div>
  );
}

function App() {
  return (
    <AGUIProvider
      url="http://localhost:50080"
      contextId="my-context"
    >
      <ChatComponent />
    </AGUIProvider>
  );
}
```

### Vue

```vue
<template>
  <div>
    <div v-for="msg in messages" :key="msg.id">
      {{ msg.content }}
    </div>
    <button @click="sendMessage('Hello!')">Send</button>
  </div>
</template>

<script setup>
import { useAgui } from '@argent/agui-client/vue';

const { messages, sendMessage, isConnected } = useAgui({
  url: 'http://localhost:50080',
  contextId: 'my-context'
});
</script>
```

### Vanilla JavaScript

```javascript
import { createChatInterface } from '@argent/agui-client/vanilla';

const chat = createChatInterface({
  url: 'http://localhost:50080',
  contextId: 'my-context',
  messageContainer: document.getElementById('messages'),
  inputElement: document.getElementById('input'),
  sendButton: document.getElementById('send'),
  statusElement: document.getElementById('status')
});
```

## Configuration

### Client Options

```javascript
const client = new AGUIClient({
  url: 'http://localhost:50080',        // Server URL
  contextId: 'my-context-id',            // Required: Context ID
  transport: 'auto',                     // 'sse', 'ws', or 'auto'
  reconnect: true,                        // Enable auto-reconnection
  reconnectInterval: 1000,               // Initial reconnect delay (ms)
  maxReconnectAttempts: 10,               // Max reconnect attempts
  reconnectBackoff: 1.5,                  // Exponential backoff multiplier
  pingInterval: 30000,                   // Ping interval (ms)
  timeout: 30000                         // Connection timeout (ms)
});
```

### Transport Selection

- **`auto`** (default): Automatically selects the best available transport
  - Prefers WebSocket if available
  - Falls back to SSE if WebSocket is not supported
- **`ws`**: Force WebSocket transport (bidirectional)
- **`sse`**: Force SSE transport (server → client only, client sends via POST)

## Event Handling

### Available Events

#### Connection Events

- `connected` - Connection established
- `disconnected` - Connection lost
- `error` - Error occurred
- `statechange` - Connection state changed
- `reconnecting` - Attempting to reconnect
- `reconnect_failed` - Reconnection attempts exhausted

#### Protocol Events

- `message` - User message logged
- `response` - Agent response
- `stream_chunk` - Response stream chunk
- `stream_end` - Stream completion
- `tool_call` - Tool call initiated
- `tool_result` - Tool call result
- `progress` - Progress update
- `context_state` - Context state change
- `notification` - Notification event
- `log_update` - Log item update
- `log_reset` - Log reset (GUID change)
- `agent_action` - Agent action event

### Event Object Structure

```javascript
{
  type: 'stream_chunk',           // Event type
  context_id: 'my-context-id',    // Context ID
  timestamp: 1234567890.123,      // Unix timestamp
  data: {                         // Event-specific data
    chunk: 'Hello ',
    full: 'Hello world',
    message_id: 'msg-123'
  }
}
```

### Handling Streams

```javascript
let currentStream = null;

client.on('stream_chunk', (event) => {
  const messageId = event.data.message_id;
  const chunk = event.data.chunk;
  const full = event.data.full;
  
  // Update UI with streaming content
  if (currentStream?.id !== messageId) {
    currentStream = {
      id: messageId,
      content: ''
    };
  }
  
  currentStream.content = full;
  updateStreamingMessage(currentStream);
});

client.on('stream_end', (event) => {
  // Finalize the stream
  if (currentStream?.id === event.data.message_id) {
    finalizeMessage(currentStream, event.data.final_text);
    currentStream = null;
  }
});
```

## Error Handling

### Connection Errors

```javascript
client.on('error', (error) => {
  console.error('Connection error:', error);
  // Show error to user
  showErrorNotification(error.message);
});
```

### Reconnection Handling

```javascript
client.on('reconnecting', ({ attempt, delay }) => {
  console.log(`Reconnecting (attempt ${attempt}) in ${delay}ms...`);
  showReconnectingStatus(attempt);
});

client.on('reconnect_failed', () => {
  console.error('Failed to reconnect');
  showReconnectFailedMessage();
  // Optionally prompt user to refresh
});
```

### Message Send Errors

```javascript
try {
  await client.sendMessage('Hello!');
} catch (error) {
  console.error('Failed to send message:', error);
  // Handle error (e.g., show notification, retry)
}
```

## Best Practices

### 1. Connection Management

- Always check connection state before sending messages
- Handle reconnection gracefully
- Clean up event listeners on component unmount

```javascript
useEffect(() => {
  const client = new AGUIClient({ ... });
  
  const handler = (event) => { /* ... */ };
  client.on('event', handler);
  
  client.connect();
  
  return () => {
    client.off('event', handler);
    client.disconnect();
  };
}, []);
```

### 2. Message Queueing

The client automatically queues messages when disconnected. However, you may want to implement your own queue for better control:

```javascript
const messageQueue = [];

function sendMessage(text) {
  if (client.isConnected()) {
    client.sendMessage(text);
  } else {
    messageQueue.push(text);
  }
}

client.on('connected', () => {
  // Flush queue
  while (messageQueue.length > 0) {
    client.sendMessage(messageQueue.shift());
  }
});
```

### 3. State Management

For complex applications, consider using a state management library:

```javascript
// With Redux
const messageReducer = (state = [], action) => {
  switch (action.type) {
    case 'AGUI_MESSAGE':
      return [...state, action.payload];
    case 'AGUI_STREAM_UPDATE':
      return state.map(msg =>
        msg.id === action.payload.id
          ? { ...msg, content: action.payload.content }
          : msg
      );
    default:
      return state;
  }
};

client.on('message', (event) => {
  store.dispatch({ type: 'AGUI_MESSAGE', payload: event });
});
```

### 4. Performance Optimization

- Debounce rapid stream updates for better UI performance
- Use virtual scrolling for large message lists
- Limit message history to prevent memory issues

```javascript
import { debounce } from 'lodash';

const updateUI = debounce((content) => {
  setMessageContent(content);
}, 50);

client.on('stream_chunk', (event) => {
  updateUI(event.data.full);
});
```

## Next Steps

- Read the [Protocol Reference](./protocol.md) for detailed protocol specification
- Check out [Examples](./examples.md) for complete application examples
- See [Troubleshooting](./troubleshooting.md) for common issues


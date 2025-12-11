# AG-UI Quick Start Guide

Get your frontend connected to Agent Zero in 5 minutes.

## Step 1: Install the Client Library

```bash
npm install @argent/agui-client
```

Or use CDN:
```html
<script type="module">
  import { AGUIClient } from 'https://cdn.jsdelivr.net/npm/@argent/agui-client/dist/client.esm.js';
</script>
```

## Step 2: Create a Client Instance

```javascript
import { AGUIClient } from '@argent/agui-client';

const client = new AGUIClient({
  url: 'http://localhost:8080',  // Your Agent Zero backend URL (Docker: 8080, Native: 50080)
  contextId: 'chat-' + Date.now(), // Unique identifier (generate your own)
  transport: 'auto'                // Automatically selects best transport
});
```

## Step 3: Set Up Event Handlers

```javascript
// Listen for streaming responses
client.on('stream_chunk', (event) => {
  // event.data.chunk - new chunk of text
  // event.data.full - complete text so far
  // event.data.message_id - unique message ID
  console.log('Chunk:', event.data.chunk);
  updateUI(event.data.full);
});

// Listen for stream completion
client.on('stream_end', (event) => {
  console.log('Stream complete:', event.data.final_text);
  finalizeMessage(event.data.message_id);
});

// Listen for errors
client.on('error', (error) => {
  console.error('Error:', error);
});
```

## Step 4: Connect and Send Messages

```javascript
// Connect to the server
await client.connect();

// Send a message
await client.sendMessage('Hello, agent!');

// Send with options
await client.sendMessage('Process this file', {
  messageId: 'msg-123',
  attachments: ['/path/to/file.txt']
});
```

## Complete Minimal Example

```javascript
import { AGUIClient } from '@argent/agui-client';

// Create client
const client = new AGUIClient({
  url: 'http://localhost:8080',  // Docker: 8080, Native: 50080
  contextId: 'chat-123',
  transport: 'auto'
});

// Handle streaming
let currentMessage = null;

client.on('stream_chunk', (event) => {
  const messageId = event.data.message_id;
  const fullText = event.data.full;
  
  if (!currentMessage || currentMessage.id !== messageId) {
    currentMessage = { id: messageId, content: '' };
    addMessageToUI(currentMessage);
  }
  
  currentMessage.content = fullText;
  updateMessageInUI(currentMessage);
});

client.on('stream_end', (event) => {
  if (currentMessage && currentMessage.id === event.data.message_id) {
    currentMessage.content = event.data.final_text;
    finalizeMessage(currentMessage);
    currentMessage = null;
  }
});

// Connect
await client.connect();

// Send message
document.getElementById('send-button').onclick = async () => {
  const input = document.getElementById('message-input');
  await client.sendMessage(input.value);
  input.value = '';
};
```

## Framework-Specific Quick Starts

### React

```jsx
import { AGUIProvider, useAGUI } from '@argent/agui-client/react';

function ChatApp() {
  return (
    <AGUIProvider url="http://localhost:50080" contextId="chat-123">
      <ChatComponent />
    </AGUIProvider>
  );
}

function ChatComponent() {
  const { messages, streamingMessage, sendMessage, isConnected } = useAGUI();
  
  return (
    <div>
      {messages.map(msg => <div key={msg.id}>{msg.content}</div>)}
      {streamingMessage && <div>{streamingMessage.content}</div>}
      <button onClick={() => sendMessage('Hello!')} disabled={!isConnected}>
        Send
      </button>
    </div>
  );
}
```

### Vue

```vue
<template>
  <div>
    <div v-for="msg in messages" :key="msg.id">{{ msg.content }}</div>
    <button @click="sendMessage('Hello!')" :disabled="!isConnected">Send</button>
  </div>
</template>

<script setup>
import { useAgui } from '@argent/agui-client/vue';

const { messages, sendMessage, isConnected } = useAgui({
  url: 'http://localhost:50080',
  contextId: 'chat-123'
});
</script>
```

## Context ID

You need a unique **context ID** for each conversation. You can:

- Generate your own: `const contextId = 'chat-' + Date.now() + '-' + Math.random()`
- Use REST API: `POST /api/chat_create` to create a context
- Reuse existing: Store and reuse context IDs for conversation continuity

See [CONTEXT_MANAGEMENT.md](./CONTEXT_MANAGEMENT.md) for detailed guidance.

## Server Configuration

**📘 For complete setup instructions with troubleshooting, see [SETUP_GUIDE.md](./SETUP_GUIDE.md)**

### Development Setup (Docker)

1. **Add to `docker-compose.local.yml`:**
   ```yaml
   environment:
     - TZ=UTC
     - AGUI_ENABLED=true  # REQUIRED
     - AGUI_TRANSPORT=both  # OPTIONAL (default)
   ```

2. **Recreate container** (important: not just restart):
   ```powershell
   docker-compose -f docker-compose.local.yml down
   docker-compose -f docker-compose.local.yml up -d
   ```

3. **Verify AG-UI is enabled:**
   ```powershell
   # Check environment variable
   docker exec agent-zero-local printenv AGUI_ENABLED
   # Should output: true
   
   # Test endpoint
   curl.exe -N -m 3 "http://localhost:8080/agui/sse?context_id=test"
   # Should return SSE stream with connected event
   ```

4. **CORS is automatically configured** for localhost origins (`localhost:3000`, `localhost:5173`). No additional setup needed!

### Production Setup

For production deployments, set environment variables:

```bash
AGUI_ENABLED=true
AGUI_TRANSPORT=both
CORS_ALLOWED_ORIGINS=https://app.vercel.app,https://yourdomain.com
```

**Important:** 
- `CORS_ALLOWED_ORIGINS` is **required** in production (comma-separated, no spaces)
- Never use wildcards (`*`) in production
- Restart/recreate container after setting environment variables

**Note:** In development, CORS automatically allows `localhost:3000` and `localhost:5173`. Only configure `CORS_ALLOWED_ORIGINS` in production.

## Development Setup Summary

### Quick Test (Local Development)

1. **Start Agent Zero in Docker:**
   ```powershell
   docker-compose -f docker-compose.local.yml up -d
   ```

2. **Start your dev UI:**
   ```bash
   npm run dev  # Runs on localhost:3000
   ```

3. **Connect with AG-UI:**
   ```javascript
   const client = new AGUIClient({
     url: 'http://localhost:8080',  // Docker port
     contextId: 'chat-' + Date.now(),
     transport: 'auto'
   });
   await client.connect();
   ```

4. **CORS is automatically configured** - no setup needed for localhost!

### Using REST API Endpoints

If you need to call REST API endpoints (like `/api/profile_list`, `/api/instrument_list`), you'll need an API key:

1. Get API key from Agent Zero settings (MCP Server Token)
2. Include in requests:
   ```javascript
   fetch('http://localhost:8080/api/profile_list', {
     method: 'POST',
     headers: {
       'Content-Type': 'application/json',
       'X-API-KEY': 'your-api-key-here'
     },
     body: JSON.stringify({})
   })
   ```

**Note:** AG-UI endpoints (`/agui/*`) don't require API keys. REST API endpoints (`/api/*`) do.

## Next Steps

- **Server Setup:** Read [SETUP_GUIDE.md](./SETUP_GUIDE.md) for complete server configuration
- **API Documentation:** Read [API_REFERENCE.md](./API_REFERENCE.md) for complete API documentation
- **Code Examples:** Check [EXAMPLES.md](./EXAMPLES.md) for more detailed examples
- **Context Management:** See [CONTEXT_MANAGEMENT.md](./CONTEXT_MANAGEMENT.md) for context ID management
- **Troubleshooting:** See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) if you encounter issues
- **Configuration Reference:** See [CONFIGURATION.md](./CONFIGURATION.md) for detailed configuration options


# Context ID Management

Guide for managing conversation contexts in AG-UI.

## What is a Context ID?

A **Context ID** is a unique identifier for each conversation/session with the agent. It allows:
- Multiple clients to connect to the same conversation
- Conversation continuity across page reloads
- Session management and history tracking

## Generating Context IDs

### Option 1: Generate Your Own (Recommended)

You can use any string as a context ID. Common approaches:

```javascript
// Using UUID
import { v4 as uuidv4 } from 'uuid';
const contextId = uuidv4();

// Using timestamp + random
const contextId = `chat-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

// Using user ID + session
const contextId = `user-${userId}-${sessionId}`;

// Simple incrementing ID
let chatCounter = 0;
const contextId = `chat-${++chatCounter}`;
```

### Option 2: Use REST API to Create Context

You can use the Agent Zero REST API to create a context:

```javascript
// Create a new chat context
async function createContext() {
  const response = await fetch('http://localhost:50080/api/chat_create', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-KEY': 'your-api-key' // If authentication is enabled
    },
    body: JSON.stringify({
      new_context: null // Let server generate, or provide your own
    })
  });
  
  const data = await response.json();
  return data.ctxid; // Use this as your contextId
}

// Then use it with AG-UI
const contextId = await createContext();
const client = new AGUIClient({
  url: 'http://localhost:50080',
  contextId: contextId
});
```

### Option 3: Reuse Existing Context

If you have an existing context ID (e.g., from a previous session), you can reuse it:

```javascript
// Store context ID in localStorage
localStorage.setItem('agui-context-id', contextId);

// Retrieve on page load
const savedContextId = localStorage.getItem('agui-context-id');
if (savedContextId) {
  const client = new AGUIClient({
    url: 'http://localhost:50080',
    contextId: savedContextId
  });
}
```

## Context ID Best Practices

### 1. Uniqueness

Ensure each conversation has a unique context ID:

```javascript
// Good: Unique IDs
const contextId1 = `chat-${Date.now()}-${Math.random()}`;
const contextId2 = `chat-${Date.now()}-${Math.random()}`;

// Bad: Same ID for different conversations
const contextId = 'my-chat'; // Will share conversation history
```

### 2. Persistence

Store context IDs to maintain conversation continuity:

```javascript
// Save context ID
function saveContextId(contextId) {
  localStorage.setItem('agui-context-id', contextId);
  // Or save to your backend
}

// Load context ID
function loadContextId() {
  return localStorage.getItem('agui-context-id') || generateNewContextId();
}
```

### 3. User-Specific Contexts

Use user identifiers in context IDs for multi-user applications:

```javascript
const contextId = `user-${userId}-chat-${chatId}`;
```

### 4. Session Management

Create new contexts for new conversations:

```javascript
function startNewConversation() {
  const newContextId = generateContextId();
  saveContextId(newContextId);
  
  // Disconnect old client
  if (currentClient) {
    currentClient.disconnect();
  }
  
  // Create new client with new context
  currentClient = new AGUIClient({
    url: 'http://localhost:50080',
    contextId: newContextId
  });
  
  return currentClient;
}
```

## Context Lifecycle

### Creating a Context

```javascript
// Context is created automatically when you connect with a new context ID
const client = new AGUIClient({
  url: 'http://localhost:50080',
  contextId: 'my-new-context-id' // This context will be created on first connection
});

await client.connect(); // Context is now active
```

### Multiple Clients, Same Context

Multiple clients can connect to the same context:

```javascript
// Client 1
const client1 = new AGUIClient({
  url: 'http://localhost:50080',
  contextId: 'shared-context'
});

// Client 2 (same context)
const client2 = new AGUIClient({
  url: 'http://localhost:50080',
  contextId: 'shared-context' // Same context ID
});

// Both clients will receive events from the same conversation
```

### Context Cleanup

Contexts are automatically cleaned up by the server after inactivity. You don't need to manually delete them, but you can reset a conversation:

```javascript
// Reset conversation (if supported by your backend)
await fetch('http://localhost:50080/api/reset_chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    context_id: contextId
  })
});
```

## Example: Complete Context Management

```javascript
class ChatManager {
  constructor(serverUrl) {
    this.serverUrl = serverUrl;
    this.client = null;
    this.contextId = this.loadOrCreateContextId();
  }
  
  loadOrCreateContextId() {
    // Try to load from storage
    const saved = localStorage.getItem('chat-context-id');
    if (saved) {
      return saved;
    }
    
    // Generate new one
    const newId = `chat-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    localStorage.setItem('chat-context-id', newId);
    return newId;
  }
  
  async connect() {
    this.client = new AGUIClient({
      url: this.serverUrl,
      contextId: this.contextId
    });
    
    // Set up event handlers
    this.client.on('stream_chunk', (event) => {
      this.handleStreamChunk(event);
    });
    
    await this.client.connect();
  }
  
  startNewConversation() {
    // Generate new context ID
    this.contextId = `chat-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    localStorage.setItem('chat-context-id', this.contextId);
    
    // Disconnect old client
    if (this.client) {
      this.client.disconnect();
    }
    
    // Connect with new context
    return this.connect();
  }
  
  handleStreamChunk(event) {
    // Update UI with streaming content
    console.log('Stream chunk:', event.data.chunk);
  }
}

// Usage
const chatManager = new ChatManager('http://localhost:50080');
await chatManager.connect();

// Start new conversation
await chatManager.startNewConversation();
```

## Context ID Format

**Any string is valid** as a context ID. Common formats:

- UUID: `550e8400-e29b-41d4-a716-446655440000`
- Timestamp-based: `chat-1703123456789-abc123`
- User-based: `user-123-chat-456`
- Simple: `my-chat-1`

**Recommendations:**
- Use descriptive prefixes (e.g., `chat-`, `user-`)
- Include timestamp or random component for uniqueness
- Keep it reasonably short (under 100 characters)
- Use URL-safe characters (alphanumeric, hyphens, underscores)

## Troubleshooting

### Context Not Found

If you get errors about context not found:

1. **Check context ID format**: Ensure it's a valid string
2. **Verify context exists**: Contexts are created on first connection
3. **Check server logs**: Look for context creation errors

### Multiple Contexts Created

If you're creating too many contexts:

1. **Reuse context IDs**: Store and reuse them
2. **Check for typos**: Ensure context ID is consistent
3. **Implement context pooling**: Reuse contexts for similar conversations

### Context Sharing Issues

If multiple clients aren't sharing the same context:

1. **Verify context ID**: Ensure all clients use the exact same string
2. **Check connection**: Ensure all clients are connected
3. **Server logs**: Check if contexts are being created separately


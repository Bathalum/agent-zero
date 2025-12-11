# AG-UI Frequently Asked Questions

Common questions and answers about AG-UI integration.

## General Questions

### What is AG-UI?

AG-UI (Agent-User Interface) is a real-time communication protocol that connects frontend applications to Agent Zero backends. It provides streaming responses, bidirectional communication, and event-driven architecture.

### Do I need to use AG-UI?

AG-UI is optional. Agent Zero also provides REST API endpoints (`/api/message`) for simple request/response patterns. AG-UI is recommended for:
- Real-time streaming responses
- Live updates during agent processing
- Interactive chat interfaces
- Multi-client applications

### Can I use both AG-UI and REST API?

Yes! You can use REST API for some operations (like creating contexts) and AG-UI for real-time communication. They complement each other.

## Context ID Questions

### How do I generate a context ID?

You can use any string as a context ID. Common approaches:

```javascript
// Simple timestamp-based
const contextId = 'chat-' + Date.now();

// UUID
import { v4 as uuidv4 } from 'uuid';
const contextId = uuidv4();

// User-specific
const contextId = `user-${userId}-chat-${chatId}`;
```

See [CONTEXT_MANAGEMENT.md](./CONTEXT_MANAGEMENT.md) for detailed guidance.

### Can I reuse a context ID?

Yes! Reusing a context ID allows you to continue the same conversation. Store the context ID and reuse it:

```javascript
// Save
localStorage.setItem('context-id', contextId);

// Reuse
const savedContextId = localStorage.getItem('context-id');
```

### What happens if I use the same context ID in multiple clients?

All clients connecting to the same context ID will receive the same events. This is useful for:
- Multi-tab applications
- Collaborative interfaces
- Real-time synchronization

## Connection Questions

### Which transport should I use?

- **`auto`** (recommended): Automatically selects the best available transport
- **`ws`**: WebSocket - full bidirectional, best for real-time apps
- **`sse`**: Server-Sent Events - simpler, unidirectional (server→client)

### Why is my connection failing?

Common causes:
1. **AG-UI not enabled**: Set `AGUI_ENABLED=true` on server
2. **Wrong URL**: Verify the server URL is correct
3. **CORS issues**: Configure `ALLOWED_ORIGINS` if accessing from different domain
4. **Network issues**: Check firewall/proxy settings

See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for solutions.

### How do I handle reconnection?

The client automatically handles reconnection by default. You can customize:

```javascript
const client = new AGUIClient({
  reconnect: true,              // Enable auto-reconnect
  maxReconnectAttempts: 10,     // Max attempts
  reconnectInterval: 1000,      // Initial delay
  reconnectBackoff: 1.5         // Exponential backoff
});
```

## Streaming Questions

### How do I handle streaming responses?

Listen for `stream_chunk` events:

```javascript
client.on('stream_chunk', (event) => {
  // event.data.chunk - new chunk
  // event.data.full - complete text so far
  updateUI(event.data.full);
});

client.on('stream_end', (event) => {
  // Stream complete
  finalizeMessage(event.data.final_text);
});
```

### Why am I not receiving stream chunks?

1. **Check event handler**: Ensure `stream_chunk` handler is registered
2. **Verify connection**: Ensure client is connected
3. **Check server**: Verify server is sending stream events
4. **Message ID tracking**: Ensure you're tracking message IDs correctly

## Framework Questions

### Can I use AG-UI with [Framework X]?

Yes! The core client is framework-agnostic. Framework adapters are available for:
- **React**: Hooks and Provider
- **Vue**: Composables
- **Vanilla JS**: Direct client usage

For other frameworks, use the core `AGUIClient` class directly.

### Do I need React/Vue to use AG-UI?

No! The core client works with any JavaScript environment. Framework adapters are optional convenience wrappers.

## Server Questions

### How do I enable AG-UI on the server?

Set environment variables:

```bash
export AGUI_ENABLED=true
export AGUI_TRANSPORT=both
```

Or in Docker:

```yaml
environment:
  - AGUI_ENABLED=true
  - AGUI_TRANSPORT=both
```

See [CONFIGURATION.md](./CONFIGURATION.md) for details.

### What ports does AG-UI use?

AG-UI uses the same port as the main Agent Zero web server (default: 50080). Endpoints:
- `GET /agui/sse?context_id=<id>`
- `WS /agui/ws?context_id=<id>`
- `POST /agui/events`

### Do I need authentication?

**Currently, no authentication is required** for AG-UI connections. The `AGUI_AUTH_REQUIRED` setting exists but is not yet fully implemented. 

**Note:** This is different from REST API endpoints (like `/api/message`) which may require `X-API-KEY` headers. AG-UI connections work without API keys.

For production, consider:
- Using HTTPS/WSS (encrypts traffic)
- Configuring CORS properly (restrict origins)
- Rate limiting connections
- Monitoring for abuse
- Future: Enable authentication when implemented

## Performance Questions

### How many connections can I have?

There's no hard limit, but consider:
- Server resources (CPU, memory)
- Network bandwidth
- Browser connection limits (typically 6 per domain)

### How do I limit message history?

Implement your own message limiting:

```javascript
const MAX_MESSAGES = 100;
const messages = [];

client.on('message', (event) => {
  messages.push(event);
  if (messages.length > MAX_MESSAGES) {
    messages.shift();
  }
});
```

### Should I debounce stream updates?

For better UI performance with rapid updates:

```javascript
import { debounce } from 'lodash';

const updateUI = debounce((content) => {
  setMessageContent(content);
}, 50);

client.on('stream_chunk', (event) => {
  updateUI(event.data.full);
});
```

## Error Handling Questions

### How do I handle errors?

Listen for error events:

```javascript
client.on('error', (error) => {
  console.error('Error:', error);
  showErrorToUser(error.message);
});

client.on('reconnect_failed', () => {
  showReconnectFailedMessage();
  promptUserToRefresh();
});
```

### What should I do if reconnection fails?

Options:
1. **Prompt user to refresh**: `window.location.reload()`
2. **Show manual reconnect button**: Allow user to retry
3. **Switch to REST API**: Fallback to non-streaming API
4. **Show error message**: Inform user of connection issues

## Production Questions

### Is AG-UI production-ready?

AG-UI is functional and tested, but for production consider:
- Implementing authentication
- Adding rate limiting
- Monitoring connection metrics
- Setting up error logging
- Using HTTPS/WSS
- Configuring CORS properly

### How do I monitor AG-UI connections?

Server-side monitoring:

```python
from python.agui.connection_manager import ConnectionManager

manager = ConnectionManager.get_instance()
count = manager.connection_count()
context_ids = manager.get_context_ids()
```

Client-side monitoring:

```javascript
client.on('statechange', (newState, oldState) => {
  console.log(`State: ${oldState} → ${newState}`);
  // Send to your analytics
});
```

### What about security?

Security best practices:
1. **Use HTTPS/WSS** in production
2. **Configure CORS** to restrict origins
3. **Implement authentication** if needed
4. **Rate limit** connections
5. **Validate context IDs** on server
6. **Monitor** for abuse

## Integration Questions

### Can I use AG-UI with existing REST API code?

Yes! AG-UI and REST API can coexist:

```javascript
// Use REST API to create context
const response = await fetch('/api/chat_create', { ... });
const { ctxid } = await response.json();

// Use AG-UI for real-time communication
const client = new AGUIClient({
  contextId: ctxid
});
```

### How do I migrate from REST API to AG-UI?

1. Keep REST API for context creation
2. Use AG-UI for real-time messaging
3. Gradually migrate features
4. Both can work together

### Can I use AG-UI without the client library?

Yes, but not recommended. You can implement the protocol directly:

```javascript
// WebSocket example
const ws = new WebSocket('ws://localhost:50080/agui/ws?context_id=my-context');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // Handle event
};
```

However, the client library handles:
- Reconnection
- Error handling
- Event management
- Transport selection
- Message queueing

## Still Have Questions?

1. Check [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
2. Review [EXAMPLES.md](./EXAMPLES.md)
3. Read [PROTOCOL.md](./PROTOCOL.md) for protocol details
4. Check server logs for errors
5. Enable debug logging (see [CONFIGURATION.md](./CONFIGURATION.md))


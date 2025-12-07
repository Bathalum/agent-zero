# @argent/agui-client

Client library for AG-UI protocol integration with Argent.

## Installation

```bash
npm install @argent/agui-client
```

## Quick Start

```javascript
import { AGUIClient } from '@argent/agui-client';

const client = new AGUIClient({
  url: 'http://localhost:50080',
  contextId: 'my-context-id',
  transport: 'auto', // or 'sse', 'ws'
});

// Subscribe to events
client.on('message', (event) => {
  console.log('Message received:', event);
});

client.on('stream_chunk', (event) => {
  console.log('Stream chunk:', event.data.chunk);
});

// Connect
await client.connect();

// Send a message
await client.sendMessage('Hello, agent!');
```

## API Reference

### AGUIClient

Main client class for connecting to AG-UI protocol servers.

#### Constructor

```javascript
new AGUIClient(config)
```

**Configuration Options:**

- `url` (string, default: `'http://localhost:50080'`) - Server URL
- `contextId` (string, required) - Context ID for this connection
- `transport` (string, default: `'auto'`) - Transport type: `'sse'`, `'ws'`, or `'auto'`
- `reconnect` (boolean, default: `true`) - Enable auto-reconnection
- `reconnectInterval` (number, default: `1000`) - Initial reconnect interval in ms
- `maxReconnectAttempts` (number, default: `10`) - Maximum reconnect attempts
- `reconnectBackoff` (number, default: `1.5`) - Exponential backoff multiplier
- `pingInterval` (number, default: `30000`) - Ping interval in ms
- `timeout` (number, default: `30000`) - Connection timeout in ms

#### Methods

##### `connect()`

Connect to the AG-UI server.

```javascript
await client.connect();
```

##### `disconnect()`

Disconnect from the server.

```javascript
client.disconnect();
```

##### `sendMessage(text, options)`

Send a message to the agent.

```javascript
await client.sendMessage('Hello!', {
  messageId: 'msg-123',
  attachments: ['/path/to/file.txt']
});
```

##### `sendEvent(type, data)`

Send a protocol event.

```javascript
await client.sendEvent('tool_call', {
  tool_name: 'example_tool',
  tool_args: { arg1: 'value' }
});
```

##### `on(event, handler)`

Subscribe to an event.

```javascript
client.on('message', (event) => {
  console.log('Received:', event);
});
```

##### `off(event, handler)`

Unsubscribe from an event.

```javascript
client.off('message', handler);
```

##### `once(event, handler)`

Subscribe to an event once.

```javascript
client.once('connected', (event) => {
  console.log('Connected!');
});
```

##### `getState()`

Get current connection state.

```javascript
const state = client.getState();
// Returns: 'disconnected' | 'connecting' | 'connected' | 'reconnecting' | 'error'
```

##### `isConnected()`

Check if connected.

```javascript
if (client.isConnected()) {
  // Send message
}
```

#### Events

The client emits the following events:

- `connected` - Connection established
- `disconnected` - Connection lost
- `error` - Error occurred
- `statechange` - Connection state changed
- `reconnecting` - Attempting to reconnect
- `reconnect_failed` - Reconnection attempts exhausted
- `event` - Generic protocol event
- `message` - User message logged
- `response` - Agent response
- `stream_chunk` - Response stream chunk
- `stream_end` - Stream completion
- `tool_call` - Tool call initiated
- `tool_result` - Tool call result
- `error` - Error occurred
- `progress` - Progress update
- `context_state` - Context state change
- `notification` - Notification event
- `log_update` - Log item update
- `log_reset` - Log reset (GUID change)
- `agent_action` - Agent action event

## Transport Types

### SSE (Server-Sent Events)

Unidirectional transport (server → client). Client sends events via HTTP POST to `/agui/events`.

### WebSocket

Bidirectional transport with full duplex communication.

### Auto

Automatically selects the best available transport (WebSocket preferred, falls back to SSE).

## Examples

### Basic Chat

```javascript
import { AGUIClient } from '@argent/agui-client';

const client = new AGUIClient({
  url: 'http://localhost:50080',
  contextId: 'chat-123'
});

client.on('stream_chunk', (event) => {
  const chunk = event.data.chunk;
  // Append to UI
  appendToChat(chunk);
});

client.on('stream_end', (event) => {
  console.log('Stream complete:', event.data.final_text);
});

await client.connect();

// Send message
await client.sendMessage('What is the weather?');
```

### Error Handling

```javascript
client.on('error', (error) => {
  console.error('Connection error:', error);
});

client.on('reconnecting', ({ attempt, delay }) => {
  console.log(`Reconnecting (attempt ${attempt}) in ${delay}ms...`);
});

client.on('reconnect_failed', () => {
  console.error('Failed to reconnect. Please refresh.');
});
```

### State Management

```javascript
client.on('statechange', (newState, oldState) => {
  console.log(`State: ${oldState} → ${newState}`);
  
  if (newState === 'connected') {
    // Update UI to show connected
  } else if (newState === 'disconnected') {
    // Update UI to show disconnected
  }
});
```

## Framework Adapters

See the framework-specific adapters:

- [React](./src/adapters/react.js) - React hooks and provider
- [Vue](./src/adapters/vue.js) - Vue composables
- [Vanilla JS](./src/adapters/vanilla.js) - Vanilla JS helpers

## License

MIT


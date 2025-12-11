# AG-UI Client API Reference

Complete API documentation for the `@argent/agui-client` library.

## AGUIClient Class

Main client class for connecting to AG-UI protocol servers.

### Constructor

```javascript
new AGUIClient(config)
```

#### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `url` | string | `'http://localhost:8080'` | Server URL (Docker: 8080, Native: 50080) |
| `contextId` | string | **required** | Context ID for this connection |
| `transport` | string | `'auto'` | Transport type: `'sse'`, `'ws'`, or `'auto'` |
| `reconnect` | boolean | `true` | Enable auto-reconnection |
| `reconnectInterval` | number | `1000` | Initial reconnect interval in ms |
| `maxReconnectAttempts` | number | `10` | Maximum reconnect attempts |
| `reconnectBackoff` | number | `1.5` | Exponential backoff multiplier |
| `pingInterval` | number | `30000` | Ping interval in ms (WebSocket only) |
| `timeout` | number | `30000` | Connection timeout in ms |

### Methods

#### `connect()`

Connect to the AG-UI server.

```javascript
await client.connect();
```

**Returns:** `Promise<void>`

**Throws:** `Error` if connection fails

#### `disconnect()`

Disconnect from the server.

```javascript
client.disconnect();
```

**Returns:** `void`

#### `sendMessage(text, options)`

Send a message to the agent.

```javascript
await client.sendMessage('Hello!', {
  messageId: 'msg-123',
  attachments: ['/path/to/file.txt']
});
```

**Parameters:**
- `text` (string) - Message text
- `options` (Object, optional) - Message options
  - `messageId` (string) - Optional message ID
  - `attachments` (Array<string>) - Optional file attachments

**Returns:** `Promise<void>`

**Throws:** `Error` if send fails

#### `sendEvent(type, data)`

Send a protocol event.

```javascript
await client.sendEvent('tool_call', {
  tool_name: 'example_tool',
  tool_args: { arg1: 'value' }
});
```

**Parameters:**
- `type` (string) - Event type
- `data` (Object) - Event data

**Returns:** `Promise<void>`

**Throws:** `Error` if send fails

#### `on(event, handler)`

Subscribe to an event.

```javascript
client.on('message', (event) => {
  console.log('Received:', event);
});
```

**Parameters:**
- `event` (string) - Event name
- `handler` (Function) - Event handler function

**Returns:** `void`

#### `off(event, handler)`

Unsubscribe from an event.

```javascript
client.off('message', handler);
```

**Parameters:**
- `event` (string) - Event name
- `handler` (Function, optional) - Specific handler to remove. If omitted, removes all handlers for the event.

**Returns:** `void`

#### `once(event, handler)`

Subscribe to an event once.

```javascript
client.once('connected', (event) => {
  console.log('Connected!');
});
```

**Parameters:**
- `event` (string) - Event name
- `handler` (Function) - Event handler function

**Returns:** `void`

#### `getState()`

Get current connection state.

```javascript
const state = client.getState();
// Returns: 'disconnected' | 'connecting' | 'connected' | 'reconnecting' | 'error'
```

**Returns:** `string`

#### `isConnected()`

Check if connected.

```javascript
if (client.isConnected()) {
  // Send message
}
```

**Returns:** `boolean`

## Events

### Connection Events

#### `connected`

Connection established.

```javascript
client.on('connected', (event) => {
  console.log('Connection ID:', event.data.connection_id);
  console.log('Context ID:', event.data.context_id);
});
```

#### `disconnected`

Connection lost.

```javascript
client.on('disconnected', () => {
  console.log('Disconnected');
});
```

#### `error`

Error occurred.

```javascript
client.on('error', (error) => {
  console.error('Error:', error);
});
```

#### `statechange`

Connection state changed.

```javascript
client.on('statechange', (newState, oldState) => {
  console.log(`State: ${oldState} → ${newState}`);
});
```

#### `reconnecting`

Attempting to reconnect.

```javascript
client.on('reconnecting', ({ attempt, delay }) => {
  console.log(`Reconnecting (attempt ${attempt}) in ${delay}ms...`);
});
```

#### `reconnect_failed`

Reconnection attempts exhausted.

```javascript
client.on('reconnect_failed', () => {
  console.error('Failed to reconnect');
});
```

### Protocol Events

#### `message`

User message logged.

```javascript
client.on('message', (event) => {
  console.log('Message:', event.data.content);
  console.log('Message ID:', event.data.message_id);
});
```

#### `response`

Agent response.

```javascript
client.on('response', (event) => {
  console.log('Response:', event.data.content);
});
```

#### `stream_chunk`

Response stream chunk.

```javascript
client.on('stream_chunk', (event) => {
  console.log('Chunk:', event.data.chunk);
  console.log('Full text:', event.data.full);
  console.log('Message ID:', event.data.message_id);
});
```

#### `stream_end`

Stream completion.

```javascript
client.on('stream_end', (event) => {
  console.log('Final text:', event.data.final_text);
  console.log('Message ID:', event.data.message_id);
});
```

#### `tool_call`

Tool call initiated.

```javascript
client.on('tool_call', (event) => {
  console.log('Tool:', event.data.tool_name);
  console.log('Args:', event.data.tool_args);
});
```

#### `tool_result`

Tool call result.

```javascript
client.on('tool_result', (event) => {
  console.log('Result:', event.data.result);
  if (event.data.error) {
    console.error('Error:', event.data.error);
  }
});
```

#### `progress`

Progress update.

```javascript
client.on('progress', (event) => {
  console.log('Progress:', event.data.progress);
  console.log('Active:', event.data.active);
});
```

#### `context_state`

Context state change.

```javascript
client.on('context_state', (event) => {
  console.log('Context:', event.data.context);
  console.log('Paused:', event.data.paused);
});
```

#### `notification`

Notification event.

```javascript
client.on('notification', (event) => {
  console.log('Notification:', event.data.notification);
});
```

#### `log_update`

Log item update.

```javascript
client.on('log_update', (event) => {
  console.log('Updated content:', event.data.content);
});
```

#### `log_reset`

Log reset (GUID change).

```javascript
client.on('log_reset', (event) => {
  console.log('Old GUID:', event.data.old_guid);
  console.log('New GUID:', event.data.new_guid);
});
```

#### `agent_action`

Agent action event.

```javascript
client.on('agent_action', (event) => {
  console.log('Action:', event.data.action);
  console.log('Details:', event.data.details);
});
```

## Framework Adapters

### React

#### `AGUIProvider`

React context provider.

```jsx
<AGUIProvider
  url="http://localhost:8080"  {/* Docker: 8080, Native: 50080 */}
  contextId="my-context"
  transport="auto"
  config={{ reconnect: true }}
>
  <YourComponent />
</AGUIProvider>
```

#### `useAGUI`

Main hook for AG-UI functionality.

```jsx
const {
  client,
  isConnected,
  error,
  messages,
  streamingMessage,
  isStreaming,
  sendMessage,
  sendEvent,
  clearMessages
} = useAGUI();
```

### Vue

#### `useAgui`

Main composable.

```javascript
const {
  client,
  isConnected,
  error,
  messages,
  streamingMessage,
  isStreaming,
  sendMessage,
  sendEvent,
  clearMessages
} = useAgui({
  url: 'http://localhost:8080',  // Docker: 8080, Native: 50080
  contextId: 'my-context',
  transport: 'auto'
});
```

### Vanilla JS

#### `createAguiClient`

Create and configure an AG-UI client instance.

```javascript
import { createAguiClient } from '@argent/agui-client/vanilla';

const client = createAguiClient({
  url: 'http://localhost:8080',  // Docker: 8080, Native: 50080
  contextId: 'my-context',
  transport: 'auto'
});
```

#### `createChatInterface`

Create a basic chat interface bound to DOM elements.

```javascript
import { createChatInterface } from '@argent/agui-client/vanilla';

const chat = createChatInterface({
  url: 'http://localhost:8080',  // Docker: 8080, Native: 50080
  contextId: 'my-context',
  messageContainer: document.getElementById('messages'),
  inputElement: document.getElementById('input'),
  sendButton: document.getElementById('send'),
  statusElement: document.getElementById('status')
});
```

## Event Object Structure

All events follow this structure:

```javascript
{
  type: 'event_type',           // Event type
  context_id: 'my-context-id',  // Context ID
  timestamp: 1234567890.123,     // Unix timestamp
  data: {                        // Event-specific data
    // ... event-specific fields
  }
}
```

## Connection States

- `'disconnected'` - Not connected
- `'connecting'` - Attempting to connect
- `'connected'` - Connected and ready
- `'reconnecting'` - Attempting to reconnect
- `'error'` - Connection error occurred

## Transport Types

- `'sse'` - Server-Sent Events (unidirectional)
- `'ws'` - WebSocket (bidirectional)
- `'auto'` - Automatically select best available


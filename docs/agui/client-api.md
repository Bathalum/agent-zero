# AG-UI Client API Reference

Complete API reference for the `@argent/agui-client` library.

## Table of Contents

- [AGUIClient](#aguiclient)
- [ConnectionState](#connectionstate)
- [TransportType](#transporttype)
- [React Adapter](#react-adapter)
- [Vue Adapter](#vue-adapter)
- [Vanilla JS Adapter](#vanilla-js-adapter)

## AGUIClient

Main client class for connecting to AG-UI protocol servers.

### Constructor

```javascript
new AGUIClient(config)
```

#### Parameters

- `config` (Object) - Client configuration
  - `url` (string, default: `'http://localhost:50080'`) - Server URL
  - `contextId` (string, **required**) - Context ID for this connection
  - `transport` (string, default: `'auto'`) - Transport type: `'sse'`, `'ws'`, or `'auto'`
  - `reconnect` (boolean, default: `true`) - Enable auto-reconnection
  - `reconnectInterval` (number, default: `1000`) - Initial reconnect interval in ms
  - `maxReconnectAttempts` (number, default: `10`) - Maximum reconnect attempts
  - `reconnectBackoff` (number, default: `1.5`) - Exponential backoff multiplier
  - `pingInterval` (number, default: `30000`) - Ping interval in ms
  - `timeout` (number, default: `30000`) - Connection timeout in ms

#### Example

```javascript
const client = new AGUIClient({
  url: 'http://localhost:50080',
  contextId: 'my-context-id',
  transport: 'auto',
  reconnect: true
});
```

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
```

**Returns:** `string` - One of: `'disconnected'`, `'connecting'`, `'connected'`, `'reconnecting'`, `'error'`

#### `isConnected()`

Check if connected.

```javascript
if (client.isConnected()) {
  // Send message
}
```

**Returns:** `boolean`

### Events

The client emits the following events:

#### Connection Events

- **`connected`** - Connection established
  - Event data: `{ connection_id, context_id }`
- **`disconnected`** - Connection lost
- **`error`** - Error occurred
  - Event data: `Error` object
- **`statechange`** - Connection state changed
  - Event data: `(newState, oldState)`
- **`reconnecting`** - Attempting to reconnect
  - Event data: `{ attempt, delay }`
- **`reconnect_failed`** - Reconnection attempts exhausted

#### Protocol Events

- **`event`** - Generic protocol event
  - Event data: Protocol event object
- **`message`** - User message logged
- **`response`** - Agent response
- **`stream_chunk`** - Response stream chunk
- **`stream_end`** - Stream completion
- **`tool_call`** - Tool call initiated
- **`tool_result`** - Tool call result
- **`progress`** - Progress update
- **`context_state`** - Context state change
- **`notification`** - Notification event
- **`log_update`** - Log item update
- **`log_reset`** - Log reset (GUID change)
- **`agent_action`** - Agent action event

## ConnectionState

Connection state enumeration.

```javascript
import { ConnectionState } from '@argent/agui-client';

ConnectionState.DISCONNECTED  // 'disconnected'
ConnectionState.CONNECTING    // 'connecting'
ConnectionState.CONNECTED     // 'connected'
ConnectionState.RECONNECTING  // 'reconnecting'
ConnectionState.ERROR         // 'error'
```

## TransportType

Transport type enumeration.

```javascript
import { TransportType } from '@argent/agui-client';

TransportType.SSE        // 'sse'
TransportType.WEBSOCKET  // 'ws'
TransportType.AUTO       // 'auto'
```

## React Adapter

### AGUIProvider

React context provider for AG-UI client.

```jsx
<AGUIProvider
  url="http://localhost:50080"
  contextId="my-context"
  transport="auto"
  config={{ reconnect: true }}
>
  <YourComponent />
</AGUIProvider>
```

**Props:**
- `url` (string) - Server URL
- `contextId` (string) - Context ID
- `transport` (string, default: `'auto'`) - Transport type
- `config` (Object, optional) - Additional client configuration

### useAGUI

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

**Returns:**
- `client` (AGUIClient) - Client instance
- `isConnected` (boolean) - Connection state
- `error` (Error | null) - Error object if any
- `messages` (Array) - Array of message objects
- `streamingMessage` (Object | null) - Current streaming message
- `isStreaming` (boolean) - Whether currently streaming
- `sendMessage` (Function) - Send message function
- `sendEvent` (Function) - Send event function
- `clearMessages` (Function) - Clear messages function

### useAGUIContext

Hook for context operations.

```jsx
const { getContextState } = useAGUIContext();
```

**Returns:**
- `getContextState` (Function) - Get context state (returns Promise)

### useAGUIMessages

Hook for message handling.

```jsx
const { messages, streamingMessage, isStreaming, clearMessages } = useAGUIMessages();
```

**Returns:**
- `messages` (Array) - Array of message objects
- `streamingMessage` (Object | null) - Current streaming message
- `isStreaming` (boolean) - Whether currently streaming
- `clearMessages` (Function) - Clear messages function

## Vue Adapter

### useAgui

Main composable for AG-UI functionality.

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
  url: 'http://localhost:50080',
  contextId: 'my-context',
  transport: 'auto'
});
```

**Parameters:**
- `options` (Object) - Configuration options
  - `url` (string) - Server URL
  - `contextId` (string) - Context ID
  - `transport` (string) - Transport type
  - `config` (Object, optional) - Additional client configuration

**Returns:** Same as React `useAGUI` hook

### useAguiContext

Composable for context operations.

```javascript
const { getContextState } = useAguiContext({
  url: 'http://localhost:50080',
  contextId: 'my-context'
});
```

### useAguiMessages

Composable for message handling.

```javascript
const { messages, streamingMessage, isStreaming, clearMessages } = useAguiMessages({
  url: 'http://localhost:50080',
  contextId: 'my-context'
});
```

## Vanilla JS Adapter

### createAguiClient

Create and configure an AG-UI client instance.

```javascript
import { createAguiClient } from '@argent/agui-client/vanilla';

const client = createAguiClient({
  url: 'http://localhost:50080',
  contextId: 'my-context',
  transport: 'auto'
});
```

### createChatInterface

Create a basic chat interface bound to DOM elements.

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

**Returns:**
- `client` (AGUIClient) - Client instance
- `addMessage` (Function) - Add message to UI
- `sendMessage` (Function) - Send message
- `clearMessages` (Function) - Clear messages

### bindClientToDOM

Bind client events to DOM elements.

```javascript
import { bindClientToDOM } from '@argent/agui-client/vanilla';

bindClientToDOM(client, {
  status: document.getElementById('status'),
  messages: document.getElementById('messages')
});
```


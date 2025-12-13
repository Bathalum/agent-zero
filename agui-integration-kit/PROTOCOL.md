# AG-UI Protocol Reference

This document describes the AG-UI protocol specification.

**This protocol specification is part of the [Frontend Contract](./FRONTEND_CONTRACT.md)**. The backend defines these protocol requirements, and frontend implementations must follow them exactly. See [FRONTEND_CONTRACT.md](./FRONTEND_CONTRACT.md) for the complete contract.

## Protocol Version

Current version: **1.0.0**

## Transport

AG-UI supports two transport mechanisms:

1. **Server-Sent Events (SSE)** - Unidirectional (server → client)
2. **WebSocket** - Bidirectional (full duplex)

## Endpoints

### SSE Endpoint

```
GET /agui/sse?context_id=<context_id>
```

Returns a Server-Sent Events stream. Client sends events via POST to `/agui/events`.

### WebSocket Endpoint

```
WS /agui/ws?context_id=<context_id>
```

Full bidirectional WebSocket connection.

### Events Endpoint (SSE only)

```
POST /agui/events
Headers:
  Content-Type: application/json
  X-AGUI-Connection: <connection_id> (optional)
  X-AGUI-Context: <context_id> (optional)

Body: {
  "type": "message",
  "context_id": "<context_id>",
  "data": { ... }
}
```

## Event Format

All events follow this structure:

```json
{
  "type": "event_type",
  "context_id": "context_id",
  "timestamp": 1234567890.123,
  "data": {
    // Event-specific data
  }
}
```

## Incoming Events (Client → Server)

### message

Send a message to the agent.

```json
{
  "type": "message",
  "context_id": "my-context",
  "data": {
    "text": "Hello, agent!",
    "message_id": "msg-123",
    "attachments": ["/path/to/file.txt"]
  }
}
```

### tool_call

Execute a tool call.

```json
{
  "type": "tool_call",
  "context_id": "my-context",
  "data": {
    "tool_name": "example_tool",
    "tool_args": {
      "arg1": "value1"
    },
    "call_id": "call-123"
  }
}
```

### ping

Health check ping.

```json
{
  "type": "ping"
}
```

### pong

Ping response.

```json
{
  "type": "pong"
}
```

## Outgoing Events (Server → Client)

### connected

Connection established.

```json
{
  "type": "connected",
  "context_id": "my-context",
  "timestamp": 1234567890.123,
  "data": {
    "connection_id": "conn-123",
    "context_id": "my-context"
  }
}
```

### message

User message logged.

```json
{
  "type": "message",
  "context_id": "my-context",
  "timestamp": 1234567890.123,
  "data": {
    "message_id": "msg-123",
    "content": "Hello, agent!",
    "text": "Hello, agent!",
    "heading": "",
    "temp": false,
    "log_item": { ... }
  }
}
```

### response

Agent response.

```json
{
  "type": "response",
  "context_id": "my-context",
  "timestamp": 1234567890.123,
  "data": {
    "message_id": "msg-456",
    "content": "Hello! How can I help you?",
    "heading": "",
    "temp": false,
    "log_item": { ... }
  }
}
```

### stream_chunk

Response stream chunk.

```json
{
  "type": "stream_chunk",
  "context_id": "my-context",
  "timestamp": 1234567890.123,
  "data": {
    "chunk": "Hello ",
    "full": "Hello world",
    "message_id": "msg-456"
  }
}
```

### stream_end

Stream completion.

```json
{
  "type": "stream_end",
  "context_id": "my-context",
  "timestamp": 1234567890.123,
  "data": {
    "message_id": "msg-456",
    "final_text": "Hello world!"
  }
}
```

### tool_call

Tool call initiated.

```json
{
  "type": "tool_call",
  "context_id": "my-context",
  "timestamp": 1234567890.123,
  "data": {
    "call_id": "call-123",
    "tool_name": "example_tool",
    "tool_args": {
      "arg1": "value1"
    }
  }
}
```

### tool_result

Tool call result.

```json
{
  "type": "tool_result",
  "context_id": "my-context",
  "timestamp": 1234567890.123,
  "data": {
    "call_id": "call-123",
    "result": { ... },
    "error": null
  }
}
```

### error

Error occurred.

```json
{
  "type": "error",
  "context_id": "my-context",
  "timestamp": 1234567890.123,
  "data": {
    "error": "Error message",
    "message_id": "msg-123"
  }
}
```

### progress

Progress update.

```json
{
  "type": "progress",
  "context_id": "my-context",
  "timestamp": 1234567890.123,
  "data": {
    "progress": "Processing...",
    "active": true
  }
}
```

### context_state

Context state change.

```json
{
  "type": "context_state",
  "context_id": "my-context",
  "timestamp": 1234567890.123,
  "data": {
    "context": { ... },
    "paused": false,
    "log_guid": "guid-123",
    "log_version": 42
  }
}
```

### context_list

Context list update.

```json
{
  "type": "context_list",
  "context_id": "",
  "timestamp": 1234567890.123,
  "data": {
    "contexts": [
      { "id": "context-1", "name": "Context 1" },
      { "id": "context-2", "name": "Context 2" }
    ]
  }
}
```

### notification

Notification event.

```json
{
  "type": "notification",
  "context_id": "my-context",
  "timestamp": 1234567890.123,
  "data": {
    "notification": {
      "type": "info",
      "message": "Notification message",
      "title": "Title"
    }
  }
}
```

### log_update

Log item update.

```json
{
  "type": "log_update",
  "context_id": "my-context",
  "timestamp": 1234567890.123,
  "data": {
    "log_item": { ... },
    "message_id": "msg-123",
    "content": "Updated content",
    "heading": "",
    "temp": false
  }
}
```

### log_reset

Log reset (GUID change).

```json
{
  "type": "log_reset",
  "context_id": "my-context",
  "timestamp": 1234567890.123,
  "data": {
    "old_guid": "guid-123",
    "new_guid": "guid-456"
  }
}
```

### agent_action

Agent action event.

```json
{
  "type": "agent_action",
  "context_id": "my-context",
  "timestamp": 1234567890.123,
  "data": {
    "action": "action_name",
    "details": { ... },
    "log_item": { ... }
  }
}
```

## Connection Lifecycle

### SSE Connection

1. Client opens SSE connection: `GET /agui/sse?context_id=<id>`
2. Server sends `connected` event
3. Client receives events via SSE stream
4. Client sends events via `POST /agui/events`
5. Connection closes on error or explicit disconnect

### WebSocket Connection

1. Client opens WebSocket: `WS /agui/ws?context_id=<id>`
2. Server sends `connected` event
3. Both client and server can send events via WebSocket
4. Server sends periodic `ping` events
5. Client responds with `pong` events
6. Connection closes on error or explicit disconnect

## Error Handling

### Connection Errors

- **400 Bad Request**: Missing or invalid `context_id`
- **503 Service Unavailable**: AG-UI is disabled
- **WebSocket 1008**: AG-UI is disabled or invalid request

### Event Errors

Events with `type: "error"` indicate protocol-level errors. The `data.error` field contains the error message.

## Best Practices

1. **Always include `context_id`** in events
2. **Handle reconnection** gracefully
3. **Use `message_id`** for tracking message lifecycle
4. **Implement ping/pong** for connection health (WebSocket)
5. **Queue messages** when disconnected
6. **Handle stream chunks** incrementally for better UX

## Versioning

Protocol version is included in the server implementation. Future versions may add new event types or modify existing ones while maintaining backward compatibility.

**Contract Guarantee:** Backend maintains backward compatibility within the same MAJOR version. See [FRONTEND_CONTRACT.md](./FRONTEND_CONTRACT.md) for versioning and breaking changes policy.

## Contract Compliance

**Frontend implementations must:**
- Follow this protocol specification exactly
- Not extend or modify the protocol
- Handle all event types (required and optional)
- Implement error handling as specified
- Comply with connection lifecycle requirements

**Deviations from this specification may result in:**
- Compatibility issues
- Security vulnerabilities
- Connection failures
- Unsupported behavior

See [FRONTEND_CONTRACT.md](./FRONTEND_CONTRACT.md) for complete contract requirements and compliance guidelines.


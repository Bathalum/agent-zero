# AG-UI Integration for Argent

This package provides the AG-UI protocol integration for Argent, allowing external UIs to connect and communicate with the agent in real-time.

## Overview

The AG-UI integration enables external user interfaces to:
- Connect via SSE (Server-Sent Events) or WebSocket
- Send messages to the agent
- Receive real-time responses and stream updates
- Monitor agent state and progress
- Receive notifications

## Architecture

The implementation follows the plan outlined in `.cursor/plans/ag-ui_integration_for_argent.plan.md` and consists of:

### Core Components

1. **Configuration** (`config.py`)
   - Environment variable-based configuration
   - Feature flag: `AGUI_ENABLED`
   - Transport selection: `AGUI_TRANSPORT` (sse/ws/both)
   - Authentication: `AGUI_AUTH_REQUIRED`

2. **Connection Management** (`connection_manager.py`)
   - Tracks connections per context
   - Multi-client support
   - Connection lifecycle management
   - Automatic cleanup

3. **Transport Layer** (`transport.py`)
   - SSE (Server-Sent Events) transport
   - WebSocket transport
   - Bidirectional communication support
   - Connection health monitoring

4. **Adapter Layer** (`adapter.py`)
   - Message conversion (AG-UI ↔ Agent Zero)
   - Response mapping
   - Tool call handling
   - State synchronization

5. **Log Bridge** (`log_bridge.py`)
   - Subscribes to Log updates
   - Converts log items to AG-UI events
   - Handles log versioning and GUID changes

6. **Protocol Server** (`server.py`)
   - Main AG-UI protocol implementation
   - Event routing and distribution
   - Background log polling
   - Connection coordination

7. **Flask Integration** (`flask_integration.py`)
   - ASGI middleware integration
   - Mounted at `/agui` endpoint
   - Follows same pattern as MCP/A2A servers

## Configuration

Set environment variables to enable and configure AG-UI:

```bash
# Enable AG-UI (default: false)
AGUI_ENABLED=true

# Transport selection (default: both)
# Options: sse, ws, both
AGUI_TRANSPORT=both

# Require authentication (default: false)
AGUI_AUTH_REQUIRED=false
```

## Endpoints

When enabled, AG-UI provides the following endpoints:

- **SSE**: `GET /agui/sse?context_id=<context_id>`
- **WebSocket**: `WS /agui/ws?context_id=<context_id>`
- **Events**: `POST /agui/events` (for receiving client events)

## Protocol Events

### Incoming Events (Client → Server)

- `message` - Send a message to the agent
- `tool_call` - Execute a tool call
- `ping` - Health check
- `pong` - Ping response

### Outgoing Events (Server → Client)

- `connected` - Connection established
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

## Usage Example

### SSE Connection

```javascript
const eventSource = new EventSource('/agui/sse?context_id=my-context-id');

eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Received event:', data);
};

// Send a message (via separate HTTP POST)
fetch('/agui/events', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-AGUI-Connection': connectionId,
    },
    body: JSON.stringify({
        type: 'message',
        context_id: 'my-context-id',
        data: {
            text: 'Hello, agent!',
            message_id: 'msg-123',
        },
    }),
});
```

### WebSocket Connection

```javascript
const ws = new WebSocket('ws://localhost:50080/agui/ws?context_id=my-context-id');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Received event:', data);
};

// Send a message
ws.send(JSON.stringify({
    type: 'message',
    context_id: 'my-context-id',
    data: {
        text: 'Hello, agent!',
        message_id: 'msg-123',
    },
}));
```

## Extension Integration

The integration hooks into the extension system:

- `response_stream_chunk` - Bridges stream chunks to AG-UI events
- `response_stream_end` - Sends stream completion events

Extensions are located at:
- `python/extensions/response_stream_chunk/_20_agui_bridge.py`
- `python/extensions/response_stream_end/_20_agui_bridge.py`

## Status

### Completed (Chunks 1-10)

✅ Foundation & Module Structure  
✅ Connection Management System  
✅ Transport Layer - SSE Implementation  
✅ Transport Layer - WebSocket Implementation  
✅ Adapter Layer - Message & Response Mapping  
✅ Adapter Layer - Tool Calls & State Sync  
✅ Log System Integration  
✅ Extension Point Integration  
✅ AG-UI Protocol Server  
✅ Flask Integration  

### Remaining (Chunks 11-14)

⏳ Client Library Foundation  
⏳ Framework Adapters (React, Vue, Vanilla JS)  
⏳ Testing & Quality Assurance  
⏳ Documentation & Examples  

## Notes

- The implementation follows the same patterns as MCP/A2A servers for consistency
- All components gracefully handle the feature being disabled
- The server starts automatically when enabled via environment variable
- Connections are automatically cleaned up when contexts are removed
- The protocol is designed to be extensible for future enhancements

## Future Enhancements

- Client library with framework adapters
- Comprehensive test suite
- Full protocol documentation
- Example applications
- Authentication support
- Rate limiting
- Connection pooling optimizations


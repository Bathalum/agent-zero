# AG-UI Server API Reference

Server-side configuration and API reference for AG-UI integration.

## Configuration

AG-UI is configured via environment variables:

### Environment Variables

- **`AGUI_ENABLED`** (boolean, default: `false`)
  - Enable or disable AG-UI server
  - Set to `true` to enable

- **`AGUI_TRANSPORT`** (string, default: `'both'`)
  - Transport selection: `'sse'`, `'ws'`, or `'both'`
  - `'sse'`: Only SSE transport
  - `'ws'`: Only WebSocket transport
  - `'both'`: Both transports available

- **`AGUI_AUTH_REQUIRED`** (boolean, default: `false`)
  - Require authentication for connections
  - Currently not fully implemented

### Example Configuration

```bash
# Enable AG-UI
export AGUI_ENABLED=true

# Use both transports
export AGUI_TRANSPORT=both

# No authentication required
export AGUI_AUTH_REQUIRED=false
```

## Endpoints

### SSE Endpoint

```
GET /agui/sse?context_id=<context_id>
```

**Query Parameters:**
- `context_id` (required) - Context ID for the connection

**Headers:**
- `X-AGUI-Context` (optional) - Alternative way to provide context_id

**Response:**
- Content-Type: `text/event-stream`
- Stream of Server-Sent Events

**Example:**

```bash
curl -N "http://localhost:50080/agui/sse?context_id=my-context"
```

### WebSocket Endpoint

```
WS /agui/ws?context_id=<context_id>
```

**Query Parameters:**
- `context_id` (required) - Context ID for the connection

**Headers:**
- `X-AGUI-Context` (optional) - Alternative way to provide context_id

**Protocol:**
- WebSocket protocol
- JSON message format

**Example:**

```javascript
const ws = new WebSocket('ws://localhost:50080/agui/ws?context_id=my-context');
```

### Events Endpoint (SSE only)

```
POST /agui/events
```

**Headers:**
- `Content-Type: application/json`
- `X-AGUI-Connection` (optional) - Connection ID
- `X-AGUI-Context` (optional) - Context ID

**Body:**
```json
{
  "type": "message",
  "context_id": "my-context",
  "data": {
    "text": "Hello, agent!",
    "message_id": "msg-123"
  }
}
```

**Response:**
- `200 OK` - Event received successfully
- `400 Bad Request` - Invalid request
- `503 Service Unavailable` - AG-UI disabled

**Example:**

```bash
curl -X POST http://localhost:50080/agui/events \
  -H "Content-Type: application/json" \
  -H "X-AGUI-Connection: conn-123" \
  -d '{
    "type": "message",
    "context_id": "my-context",
    "data": {
      "text": "Hello!"
    }
  }'
```

## Server Architecture

### Components

1. **AGUIServer** (`python/agui/server.py`)
   - Main protocol server
   - Event routing and distribution
   - Connection coordination

2. **ConnectionManager** (`python/agui/connection_manager.py`)
   - Tracks connections per context
   - Multi-client support
   - Connection lifecycle management

3. **Transport Layer** (`python/agui/transport.py`)
   - SSE transport implementation
   - WebSocket transport implementation
   - Bidirectional communication support

4. **Adapter Layer** (`python/agui/adapter.py`)
   - Message conversion (AG-UI ↔ Agent Zero)
   - Response mapping
   - Tool call handling

5. **Log Bridge** (`python/agui/log_bridge.py`)
   - Subscribes to Log updates
   - Converts log items to AG-UI events
   - Handles log versioning

### Integration Points

#### Flask Integration

AG-UI is integrated into the Flask application via ASGI middleware:

```python
from python.agui.flask_integration import DynamicAGUIProxy

# In run_ui.py
agui_proxy = DynamicAGUIProxy()
app.mount("/agui", agui_proxy)
```

#### Extension Integration

AG-UI hooks into the extension system:

- `response_stream_chunk` - Bridges stream chunks to AG-UI events
- `response_stream_end` - Sends stream completion events

Extensions are located at:
- `python/extensions/response_stream_chunk/_20_agui_bridge.py`
- `python/extensions/response_stream_end/_20_agui_bridge.py`

## Connection Management

### Connection Lifecycle

1. **Registration**: Client connects, server registers connection
2. **Active**: Connection is active and receiving events
3. **Disconnection**: Connection closes (client disconnect, error, or timeout)
4. **Cleanup**: Connection removed from registry

### Multi-Client Support

Multiple clients can connect to the same context. All connections receive broadcast events.

### Connection Cleanup

Connections are automatically cleaned up when:
- Client disconnects
- Context is removed
- Server shuts down

## Event Broadcasting

Events are broadcast to all connections in a context:

```python
server = AGUIServer.get_instance()
server.broadcast_event(event)
```

This sends the event to all connected clients for that context.

## Protocol Version

Current protocol version: **1.0.0**

The protocol version is defined in `AGUIServer.PROTOCOL_VERSION`.

## Error Handling

### Server Errors

- **503 Service Unavailable**: AG-UI is disabled
- **400 Bad Request**: Missing or invalid `context_id`
- **WebSocket 1008**: AG-UI disabled or invalid request

### Connection Errors

Connections are automatically cleaned up on error. Clients should implement reconnection logic.

## Performance Considerations

### Connection Limits

Currently, there are no hard limits on connections. Consider implementing rate limiting for production use.

### Message Queueing

Messages are queued per connection. Large message volumes may require optimization.

### Log Polling

The log bridge polls for updates. Consider optimizing polling frequency for high-volume scenarios.

## Security

### Authentication

Currently, authentication is not fully implemented. For production use:

1. Implement authentication middleware
2. Validate context access permissions
3. Add rate limiting
4. Implement CORS policies

### CORS

Configure CORS appropriately for your deployment:

```python
# Example CORS configuration
from flask_cors import CORS

CORS(app, resources={
    r"/agui/*": {
        "origins": ["https://yourdomain.com"],
        "methods": ["GET", "POST"],
        "allow_headers": ["Content-Type", "X-AGUI-Connection", "X-AGUI-Context"]
    }
})
```

## Monitoring

### Connection Metrics

Monitor connection counts and health:

```python
from python.agui.connection_manager import ConnectionManager

manager = ConnectionManager.get_instance()
count = manager.connection_count()
context_ids = manager.get_context_ids()
```

### Logging

AG-UI uses standard Python logging. Enable debug logging for troubleshooting:

```python
import logging
logging.getLogger('python.agui').setLevel(logging.DEBUG)
```

## Troubleshooting

See [Troubleshooting Guide](./troubleshooting.md) for common issues and solutions.


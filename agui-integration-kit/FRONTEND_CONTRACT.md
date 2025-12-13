# AG-UI Frontend Contract

**This document establishes the formal contract between the Agent Zero backend (Port) and frontend implementations (Adaptor).**

## Architecture Philosophy

### Backend as Port, Frontend as Adaptor

This contract follows the Ports and Adaptors (Hexagonal Architecture) pattern:

- **Backend (Port)**: Defines the protocol, endpoints, and requirements. The backend is the **source of truth**.
- **Frontend (Adaptor)**: Implements client-side logic to adapt to the backend's contract. The frontend **must conform** to backend specifications.

**Key Principles:**
1. The backend defines all protocol specifications - frontend implementations must follow exactly
2. The contract is immutable from the frontend's perspective - changes come from backend
3. Backend maintains backward compatibility within major versions
4. Frontend must adapt to backend changes through version migration

## Protocol Version

**Current Version:** `1.0.0`

Version format: `MAJOR.MINOR.PATCH`
- **MAJOR**: Breaking changes - frontend must migrate
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

**Compatibility Guarantee:** Backend maintains backward compatibility within the same MAJOR version.

## Backend Requirements (What Backend Provides)

### Endpoint Specifications

The backend provides three endpoints, all mounted under `/agui/`:

#### 1. SSE Endpoint
```
GET /agui/sse?context_id=<context_id>
```

**Request Requirements:**
- Method: `GET`
- Query Parameter: `context_id` (required, string)
- Optional Header: `X-AGUI-Context` (alternative way to provide context_id)

**Response:**
- Status: `200 OK` (if AG-UI enabled)
- Status: `503 Service Unavailable` (if AG-UI disabled)
- Content-Type: `text/event-stream`
- Stream: Server-Sent Events (SSE) format
- First Event: `connected` event with `connection_id`

**CORS Headers:** Only added if origin is in allowed list (see CORS Requirements section)

#### 2. WebSocket Endpoint
```
WS /agui/ws?context_id=<context_id>
```

**Request Requirements:**
- Protocol: WebSocket upgrade
- Query Parameter: `context_id` (required, string)
- Optional Header: `X-AGUI-Context` (alternative way to provide context_id)

**Response:**
- Connection: WebSocket upgrade
- First Message: `connected` event with `connection_id` (JSON format)
- Messages: JSON format
- Close Codes:
  - `1008`: AG-UI disabled or `context_id` missing
  - `1006`: Abnormal closure (network/endpoint issue)

**CORS:** WebSocket connections validate origin during upgrade handshake

#### 3. Events Endpoint (SSE Only)
```
POST /agui/events
```

**Request Requirements:**
- Method: `POST`
- Headers:
  - `Content-Type: application/json` (required)
  - `X-AGUI-Connection: <connection_id>` (optional, for SSE)
  - `X-AGUI-Context: <context_id>` (optional)
- Body: JSON event object

**Response:**
- `200 OK`: Event received successfully
- `400 Bad Request`: Invalid request or missing required fields
- `503 Service Unavailable`: AG-UI disabled

### Port Configuration

Backend runs on different ports depending on deployment:

**Docker Deployment:**
- Default Host Port: `8080` (configurable via `WEB_PORT` environment variable)
- Container Port: `80`
- Base URL: `http://localhost:8080` (or `http://localhost:${WEB_PORT}`)

**Native Deployment:**
- Default Port: `50080` (configurable via `WEB_UI_PORT` or `--port` argument)
- Base URL: `http://localhost:50080`

**Frontend must:** Determine correct port based on deployment type and connect to appropriate URL.

### Protocol Event Format

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

**Required Fields:**
- `type`: Event type identifier (string)
- `context_id`: Context identifier (string)
- `timestamp`: Unix timestamp with milliseconds (number)
- `data`: Event-specific payload (object)

**Event Types:** See [PROTOCOL.md](./PROTOCOL.md) for complete event specification.

### Error Response Formats

#### HTTP Error Responses

**503 Service Unavailable:**
```json
{
  "enabled": false,
  "message": "AG-UI is disabled or not available"
}
```

Or plain text: `"AG-UI is disabled or not available"`

**400 Bad Request:**
```json
{
  "error": "context_id required"
}
```

Or plain text: `"context_id required"` or `"connection_id required"`

**500 Internal Server Error:**
Plain text error message describing the server error.

#### WebSocket Close Codes

- `1008`: Policy violation - AG-UI disabled or `context_id` missing
- `1006`: Abnormal closure - endpoint doesn't exist, network issue, or connection dropped

#### Protocol-Level Errors

Events with `type: "error"`:
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

### CORS Configuration Requirements

**Backend CORS Behavior:**

1. **Development Mode:**
   - Automatically allows these origins:
     - `http://localhost:3000`
     - `http://localhost:5173`
     - `http://127.0.0.1:3000`
     - `http://127.0.0.1:5173`
   - No configuration required

2. **Production Mode:**
   - Requires `CORS_ALLOWED_ORIGINS` environment variable
   - Format: Comma-separated list (no spaces): `https://app.vercel.app,https://yourdomain.com`
   - Only whitelisted origins receive CORS headers
   - No wildcards (`*`) allowed for security

3. **CORS Headers Applied:**
   - `Access-Control-Allow-Origin: <origin>` (validated origin only)
   - `Access-Control-Allow-Methods: GET, POST, OPTIONS`
   - `Access-Control-Allow-Headers: Content-Type, X-AGUI-Connection, X-AGUI-Context`
   - `Access-Control-Max-Age: 3600`
   - `Access-Control-Allow-Credentials: false` (never set to true)

**CORS Validation:** Applied consistently across ALL endpoints (SSE, WebSocket, Events).

**Frontend must:** Ensure its origin is whitelisted in production or use allowed localhost origins in development.

## Frontend Adaptor Requirements (What Frontend Must Implement)

### Required Client Configuration

Frontend must configure the client with:

1. **Backend URL:** Correct base URL based on deployment (Docker: `http://localhost:8080`, Native: `http://localhost:50080`)
2. **Context ID:** Unique identifier for the conversation/session (string)
3. **Transport Selection:** Support for `auto`, `sse`, or `ws`

**Example:**
```javascript
const client = new AGUIClient({
  url: 'http://localhost:8080',  // Backend base URL
  contextId: 'my-context-id',    // Required context ID
  transport: 'auto'               // Transport selection
});
```

### Connection Lifecycle Requirements

Frontend must implement this connection sequence:

1. **Initialize Client:** Create client instance with required configuration
2. **Register Event Handlers:** Set up handlers for all event types before connecting
3. **Connect:** Call `connect()` method
4. **Wait for Connected Event:** Wait for `connected` event before sending messages
5. **Handle Disconnection:** Implement reconnection logic for connection failures
6. **Disconnect:** Clean disconnect on application shutdown

**Required Event Handlers:**
- `connected`: Handle connection confirmation
- `stream_chunk`: Handle streaming responses (required for real-time updates)
- `stream_end`: Handle stream completion
- `error`: Handle protocol-level errors
- `response`: Handle complete responses (if not using streaming)

**Optional Event Handlers:**
- `tool_call`: Handle tool execution
- `tool_result`: Handle tool results
- `progress`: Handle progress updates
- `notification`: Handle notifications
- `log_update`: Handle log updates
- `context_state`: Handle context state changes

### Event Handling Requirements

1. **All events must be handled:** Frontend must handle or explicitly ignore all received events
2. **Stream handling:** Frontend must process `stream_chunk` events incrementally
3. **Message ID tracking:** Frontend must track `message_id` to manage message lifecycle
4. **Error handling:** Frontend must handle `error` events and display appropriate user feedback

### Error Handling Requirements

1. **Connection errors:** Handle connection failures gracefully
2. **Reconnection logic:** Implement automatic reconnection with exponential backoff
3. **HTTP errors:** Handle 503, 400, 500 status codes appropriately
4. **WebSocket errors:** Handle close codes (1008, 1006) and implement fallback to SSE
5. **Protocol errors:** Handle `error` event types with user-friendly messages
6. **Network errors:** Handle timeouts, network failures, and offline scenarios

### CORS Origin Requirements

**Frontend must:**

1. **Development:** Run on one of the auto-allowed origins:
   - `http://localhost:3000`
   - `http://localhost:5173`
   - `http://127.0.0.1:3000`
   - `http://127.0.0.1:5173`

2. **Production:**
   - Ensure backend has `CORS_ALLOWED_ORIGINS` configured with frontend's exact origin
   - Use exact origin match (protocol + domain + port)
   - Handle CORS errors gracefully with user-friendly messages

3. **Error handling:** Detect CORS errors and provide clear guidance to developers/users

### Context ID Management

Frontend must:

1. **Generate or obtain context ID:** Either generate unique ID or obtain from backend API
2. **Persist context ID:** Store context ID for session continuity
3. **Reuse context ID:** Use same context ID for conversation continuity
4. **Handle context changes:** React appropriately to `context_state` events

**Context ID Format:**
- Any valid string
- Backend does not validate format (frontend can use any string)
- Recommended: Use descriptive IDs like `chat-${timestamp}` or UUIDs

### Transport Selection Logic

Frontend must implement transport selection:

1. **Auto Mode:** Try WebSocket first, fallback to SSE if WebSocket fails
2. **WebSocket Mode:** Use WebSocket only, handle failures gracefully
3. **SSE Mode:** Use SSE only, send events via POST to `/agui/events`

**Transport Requirements:**
- WebSocket: Full bidirectional communication
- SSE: Server→client streaming, client→server via HTTP POST
- Fallback: If WebSocket fails, automatically fallback to SSE

### Security Requirements

1. **No credentials:** Do not send credentials or sensitive data in requests
2. **Validate origins:** Verify backend URL is from trusted source
3. **Handle CORS errors:** Don't expose backend URLs in error messages to users
4. **HTTPS in production:** Always use HTTPS/WSS in production environments
5. **Input validation:** Validate user inputs before sending to backend

### Testing Requirements

Frontend must verify:

1. **Connection:** Can connect to backend successfully
2. **Event handling:** All event types are handled correctly
3. **Streaming:** Streaming responses display incrementally
4. **Reconnection:** Handles disconnections and reconnects automatically
5. **Error handling:** All error scenarios are handled gracefully
6. **CORS:** Works with backend CORS configuration (dev and production)

## Contract Guarantees

### Backend Guarantees

1. **Protocol Stability:** Backend will not change protocol without version bump
2. **Backward Compatibility:** Backend maintains backward compatibility within major version
3. **Error Responses:** Backend provides clear, actionable error responses
4. **Input Validation:** Backend validates all inputs and returns clear error messages
5. **CORS Consistency:** CORS validation is consistent across all endpoints
6. **Documentation:** Backend provides complete protocol documentation

### Frontend Expectations

1. **Compliance:** Frontend must implement exactly as specified in contract
2. **Version Tracking:** Frontend must track protocol version and handle version mismatches
3. **Migration:** Frontend must migrate when breaking changes are introduced
4. **Error Handling:** Frontend must handle all specified error scenarios
5. **Testing:** Frontend must test against backend contract specifications

## Breaking Changes Policy

### How Backend Communicates Breaking Changes

1. **Version Bump:** MAJOR version increment indicates breaking changes
2. **Migration Guide:** Backend provides migration guide for major version changes
3. **Deprecation Notice:** Backend provides advance notice of deprecated features
4. **Documentation Updates:** All breaking changes documented in protocol specification

### Version Migration

**MAJOR Version Changes:**
- Backend maintains previous MAJOR version for deprecation period
- Frontend must migrate before deprecation period ends
- Backend provides migration guide and examples

**MINOR/PATCH Changes:**
- Backward compatible, no migration required
- New features may be added but existing features unchanged

### Deprecation Process

1. **Notice Period:** Backend announces deprecation with timeline
2. **Documentation:** Deprecated features clearly marked in documentation
3. **Support:** Backend maintains deprecated features during notice period
4. **Removal:** Features removed only in next MAJOR version

## Compliance and Testing

### Contract Compliance Checklist

Frontend implementations must verify:

- [ ] Correct endpoint URLs (SSE, WebSocket, Events)
- [ ] Required query parameters and headers
- [ ] Event format compliance (type, context_id, timestamp, data)
- [ ] All required event handlers implemented
- [ ] Error handling for all error types
- [ ] CORS origin requirements met
- [ ] Transport selection logic implemented
- [ ] Reconnection logic implemented
- [ ] Context ID management implemented
- [ ] Security requirements followed

### Testing Against Backend

Frontend must test:

1. **Connection:** Connect to backend with valid configuration
2. **Event Reception:** Receive and handle all event types
3. **Event Sending:** Send events in correct format
4. **Error Scenarios:** Handle all documented error responses
5. **Reconnection:** Verify reconnection works correctly
6. **CORS:** Test with allowed and disallowed origins
7. **Transport Fallback:** Verify WebSocket→SSE fallback works

## Related Documentation

- **[PROTOCOL.md](./PROTOCOL.md)** - Complete protocol specification (part of this contract)
- **[SETUP_GUIDE.md](./SETUP_GUIDE.md)** - Backend setup requirements (part of this contract)
- **[CONFIGURATION.md](./CONFIGURATION.md)** - Backend configuration reference
- **[API_REFERENCE.md](./API_REFERENCE.md)** - Client library API reference
- **[EXAMPLES.md](./EXAMPLES.md)** - Implementation examples
- **[TROUBLESHOOTING.md](./TROUBLESHOOTING.md)** - Common issues and solutions

## Summary

**This contract establishes:**
- Backend (Port) as the source of truth for all protocol specifications
- Frontend (Adaptor) requirements for compliance
- Guarantees and policies for stability and evolution
- Clear boundaries for what frontend must implement

**Frontend implementations must follow this contract exactly.** Any deviation may result in compatibility issues or security vulnerabilities.

---

**Contract Version:** 1.0.0  
**Last Updated:** 2025-12-11  
**Protocol Version:** 1.0.0


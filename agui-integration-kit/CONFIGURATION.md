# AG-UI Server Configuration

Complete guide for configuring the Agent Zero backend to enable AG-UI.

**For a step-by-step setup guide, see [SETUP_GUIDE.md](./SETUP_GUIDE.md)**

## Environment Variables

### Required Configuration

```bash
# Enable AG-UI
export AGUI_ENABLED=true

# Transport selection
export AGUI_TRANSPORT=both  # Options: 'sse', 'ws', or 'both'
```

### Optional Configuration

```bash
# Require authentication (not fully implemented - currently no auth required)
export AGUI_AUTH_REQUIRED=false

# CORS origins (for production - development auto-allows localhost)
export CORS_ALLOWED_ORIGINS=https://app.vercel.app,https://yourdomain.com
```

**Note:** In development mode, CORS is automatically configured for localhost origins. Only set `CORS_ALLOWED_ORIGINS` in production.

**Note:** Currently, AG-UI connections do **not** require authentication or API keys. This is different from REST API endpoints which may require `X-API-KEY` headers. Authentication support is planned but not yet implemented.

## Endpoints

Once enabled, AG-UI provides these endpoints:

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

## Docker Configuration

### Development (docker-compose.local.yml)

If running in Docker for development, add environment variables to `docker-compose.local.yml`:

```yaml
services:
  agent-zero-local:
    environment:
      - TZ=UTC
      # REQUIRED: Enable AG-UI endpoints (SSE/WebSocket)
      - AGUI_ENABLED=true
      # OPTIONAL: Transport selection (default: both)
      - AGUI_TRANSPORT=both  # Options: 'sse', 'ws', or 'both'
      # OPTIONAL: CORS - Not needed in dev (auto-allows localhost), only set in production
      # - CORS_ALLOWED_ORIGINS=https://app.vercel.app
```

**Important:** After adding `AGUI_ENABLED=true`, you must **recreate** the container (not just restart):

```powershell
# Windows PowerShell
docker-compose -f docker-compose.local.yml down
docker-compose -f docker-compose.local.yml up -d
```

### Production Docker Deployment

For production deployments (e.g., AWS ECS), set environment variables in your task definition:

```json
{
  "environment": [
    {
      "name": "AGUI_ENABLED",
      "value": "true"
    },
    {
      "name": "AGUI_TRANSPORT",
      "value": "both"
    },
    {
      "name": "CORS_ALLOWED_ORIGINS",
      "value": "https://app.vercel.app,https://yourdomain.com"
    }
  ]
}
```

### Using .env File

Alternatively, you can use a `.env` file:

```bash
AGUI_ENABLED=true
AGUI_TRANSPORT=both
# CORS: Not needed in dev (auto-allows localhost), required in production
# CORS_ALLOWED_ORIGINS=https://app.vercel.app
```

## CORS Configuration

CORS is **automatically configured** in Agent Zero for AG-UI endpoints. The configuration uses Starlette's CORSMiddleware at the ASGI level, which is separate from Flask-CORS.

### Development Mode (Automatic)

**Docker and Native Development:** CORS is **automatically enabled** for these local origins:

- `http://localhost:3000`
- `http://localhost:5173`
- `http://127.0.0.1:3000`
- `http://127.0.0.1:5173`

**No configuration needed!** Just start your dev server and connect. CORS headers are automatically added by the server when it detects these origins.

**How it works:** The server checks if `CORS_ALLOWED_ORIGINS` is set. If not set AND the server is in development mode, it automatically allows localhost origins.

### Production Mode (Environment Variable)

For production deployments, set the `CORS_ALLOWED_ORIGINS` environment variable:

```bash
export CORS_ALLOWED_ORIGINS=https://app.vercel.app,https://yourdomain.com
```

**Format:** Comma-separated list of allowed origins (no spaces around commas)

### Docker Configuration

In `docker-compose.local.yml` or production deployment:

```yaml
environment:
  - CORS_ALLOWED_ORIGINS=https://app.vercel.app,https://yourdomain.com
```

### AWS ECS Task Definition

```json
{
  "name": "CORS_ALLOWED_ORIGINS",
  "value": "https://app.vercel.app,https://yourdomain.com"
}
```

### What Gets CORS Enabled

The following routes automatically get CORS headers:

- `/api/*` - REST API endpoints (Flask-CORS, requires `X-API-KEY` header)
- `/agui/*` - AG-UI protocol endpoints (Starlette CORSMiddleware + manual SSE validation, no API key required)

**Important:** AG-UI endpoints (`/agui/*`) have CORS configured at the **ASGI/Starlette level**, not Flask level. This is because AG-UI routes are handled by ASGI middleware, not Flask routes. The CORS middleware is automatically applied when AG-UI is initialized.

**CORS Headers for AG-UI:**
- `Access-Control-Allow-Origin`: Your frontend origin (validated, only if in allowed list)
- `Access-Control-Allow-Methods`: GET, POST, OPTIONS
- `Access-Control-Allow-Headers`: Content-Type, X-AGUI-Connection, X-AGUI-Context
- `Access-Control-Max-Age`: 3600

**Security:** CORS headers are **only** added if the request origin matches the allowed list. Requests from disallowed origins receive no CORS headers and are blocked by browsers.

## Security

### CORS Origin Validation

**All AG-UI endpoints validate request origins for security:**

1. **SSE Endpoint** (`/agui/sse`): 
   - Manually validates origin (bypasses Starlette middleware due to streaming)
   - Uses same validation logic as Starlette CORSMiddleware
   - Only adds CORS headers if origin is in allowed list

2. **WebSocket Endpoint** (`/agui/ws`):
   - Uses Starlette CORSMiddleware for origin validation
   - Validates during WebSocket upgrade handshake
   - Rejects connections from disallowed origins with close code 1008

3. **Events Endpoint** (`/agui/events`):
   - Uses Starlette CORSMiddleware for origin validation
   - Validates on each POST request
   - Returns appropriate error responses for disallowed origins

**Validation Logic (consistent across all endpoints):**
- Check `CORS_ALLOWED_ORIGINS` environment variable (comma-separated list)
- If unset and development mode: Allow localhost origins only
- If unset and production: Empty list (no CORS, all requests rejected)
- If set: Only allow origins in the list
- Exact match required (protocol + domain + port)

**Security Best Practices:**

1. **Never use wildcards (`*`)** in production
   - Allows any origin to connect
   - Major security vulnerability

2. **Always whitelist specific origins**
   - Only your frontend domains
   - Use exact origin match (including protocol and port)

3. **Use HTTPS in production**
   - Always use `https://` origins
   - Never allow `http://` origins in production

4. **Validate configuration**
   - Test that only allowed origins can connect
   - Verify CORS headers are present for allowed origins
   - Verify CORS headers are absent for disallowed origins

5. **Monitor CORS rejections**
   - Check server logs for blocked origin attempts
   - Investigate unexpected CORS rejections

### Authentication

**Current Status:** AG-UI endpoints do **not** require authentication or API keys.

- No `X-API-KEY` header required (unlike REST API endpoints)
- No authentication tokens needed
- Access controlled only through CORS origin validation

**Security Implications:**
- Any client from an allowed origin can connect
- Context IDs are user-provided strings (not validated)
- Consider implementing authentication for production use

**Future Plans:** Authentication support is planned but not yet implemented.

### Manual Configuration (Advanced)

If you need custom CORS configuration, you can modify `run_ui.py`:

```python
CORS(webapp, resources={
    r"/agui/*": {
        "origins": ["https://yourdomain.com"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "X-AGUI-Connection", "X-AGUI-Context"],
        "allow_credentials": False,
        "max_age": 3600
    }
})
```

## Verification

### Verify AG-UI is Enabled and Working

**Step 1: Check Environment Variable (Docker)**
```powershell
# Windows PowerShell
docker exec agent-zero-local printenv AGUI_ENABLED
# Should output: true
```

**Step 2: Test SSE Endpoint**

**Docker (port 8080):**
```powershell
# Windows PowerShell
curl.exe -N -m 5 "http://localhost:8080/agui/sse?context_id=test"
```

**Native (port 50080):**
```bash
curl -N -m 5 "http://localhost:50080/agui/sse?context_id=test"
```

**Expected Successful Response:**
```
data: {"type": "connected", "connection_id": "xxx-xxx-xxx", "context_id": "test"}

: keepalive

: keepalive
...
```

**If you get:**
- `503 Service Unavailable` or `AG-UI is disabled` → AG-UI not enabled (set `AGUI_ENABLED=true` and recreate container)
- `500 Internal Server Error` → Check server logs for errors
- `Empty reply from server` → Check server logs, might be connection issue
- SSE stream with `connected` event → ✅ AG-UI is working correctly!

**Step 3: Check WebSocket**

```bash
# Using wscat (install with: npm install -g wscat)
wscat -c ws://localhost:8080/agui/ws?context_id=test

# Docker port: 8080
# Native port: 50080
# Should connect successfully and receive connection confirmation
```

**Step 4: Check Server Logs**

```powershell
# Windows PowerShell - Look for AG-UI initialization messages
docker logs agent-zero-local 2>&1 | Select-String -Pattern "AG-UI" -CaseSensitive:$false

# Should see messages like:
# [AG-UI] Server started
# [AG-UI] Initialized and ready
# [AG-UI] SSE transport enabled at /agui/sse
# [AG-UI] WebSocket transport enabled at /agui/ws
```

**Step 5: Verify CORS (if connecting from frontend)**

Open browser DevTools → Network tab → Check response headers for:
- `Access-Control-Allow-Origin` - Should match your frontend origin
- `Access-Control-Allow-Methods` - Should include GET, POST, OPTIONS
- `Access-Control-Allow-Headers` - Should include Content-Type, X-AGUI-Connection, X-AGUI-Context

## Troubleshooting

### AG-UI Not Available (404)

**Cause:** AG-UI is disabled

**Solution:**
```bash
export AGUI_ENABLED=true
# Restart server
```

### CORS Errors

**Cause:** Origin not allowed

**Solutions:**

1. **Development:** CORS should work automatically. Check:
   - Your UI is running on `localhost:3000` or `localhost:5173`
   - Agent Zero logs show: `CORS enabled for origins: ...`
   - You're not dockerized (development mode)

2. **Production:** Set environment variable:
   ```bash
   export CORS_ALLOWED_ORIGINS=https://yourdomain.com
   ```

3. **Verify CORS headers:**
   - Open browser DevTools → Network tab
   - Check response headers for `Access-Control-Allow-Origin`
   - Should match your frontend origin

### Connection Timeout

**Cause:** Server not responding

**Solution:**
- Check server is running
- Verify port is correct
- Check firewall settings

## Security Considerations

### Production Deployment

1. **Enable Authentication:**
   ```bash
   export AGUI_AUTH_REQUIRED=true
   ```

2. **Restrict CORS:**
   ```bash
   export CORS_ALLOWED_ORIGINS=https://yourdomain.com
   ```
   
   **Important:** Never use wildcards (`*`) in production. Only whitelist your specific domains.

3. **Use HTTPS:**
   - Always use `wss://` for WebSocket in production
   - Use `https://` for SSE

4. **Rate Limiting:**
   - Implement rate limiting for production
   - Monitor connection counts

## Monitoring

### Connection Metrics

```python
from python.agui.connection_manager import ConnectionManager

manager = ConnectionManager.get_instance()
count = manager.connection_count()
context_ids = manager.get_context_ids()
```

### Debug Logging

```python
import logging
logging.getLogger('python.agui').setLevel(logging.DEBUG)
```

## Protocol Version

Current protocol version: **1.0.0**

The protocol version is defined in `AGUIServer.PROTOCOL_VERSION`.


# AG-UI Complete Setup Guide

Step-by-step guide for setting up AG-UI on the Agent Zero backend. 

**This guide is part of the [Frontend Contract](./FRONTEND_CONTRACT.md)** - it defines backend requirements that frontends must adapt to. See [FRONTEND_CONTRACT.md](./FRONTEND_CONTRACT.md) for the complete contract specification.

## Overview

AG-UI enables real-time communication between frontend applications and Agent Zero backends via:
- **SSE (Server-Sent Events)** - `GET /agui/sse?context_id=<id>`
- **WebSocket** - `WS /agui/ws?context_id=<id>`

All endpoints are mounted at `/agui/*` and require CORS configuration for cross-origin access.

## Required Environment Variables

### 1. AGUI_ENABLED (REQUIRED)

**Purpose:** Enable or disable AG-UI endpoints

**Values:** `true`, `false`, `1`, `0`, `yes`, `no`, `on`, `off`

**Default:** `false` (disabled)

**Example:**
```bash
AGUI_ENABLED=true
```

**Critical:** If not set to `true`, all `/agui/*` endpoints return **503 Service Unavailable**.

### 2. AGUI_TRANSPORT (OPTIONAL)

**Purpose:** Select which transport protocols to enable

**Values:** `sse`, `ws`, `both`

**Default:** `both`

**Example:**
```bash
AGUI_TRANSPORT=both  # Enable both SSE and WebSocket
AGUI_TRANSPORT=sse   # Only SSE
AGUI_TRANSPORT=ws    # Only WebSocket
```

### 3. CORS_ALLOWED_ORIGINS (PRODUCTION ONLY)

**Purpose:** Whitelist frontend origins for CORS

**Format:** Comma-separated list of origins (no spaces around commas)

**Development:** NOT REQUIRED - automatically allows localhost origins

**Production:** REQUIRED - must specify your frontend domain(s)

**Example:**
```bash
CORS_ALLOWED_ORIGINS=https://app.vercel.app,https://yourdomain.com
```

**Security:** Never use wildcards (`*`) in production. Only whitelist specific domains.

## Docker Setup (Development)

### File: `docker-compose.local.yml`

Add environment variables to the `agent-zero-local` service:

```yaml
version: '3.8'

services:
  agent-zero-local:
    container_name: agent-zero-local
    # ... other configuration ...
    
    environment:
      - TZ=UTC
      # REQUIRED: Enable AG-UI
      - AGUI_ENABLED=true
      # OPTIONAL: Transport selection (default: both)
      - AGUI_TRANSPORT=both
      # OPTIONAL: CORS for production (not needed in dev)
      # - CORS_ALLOWED_ORIGINS=https://app.vercel.app
```

### Apply Changes

**Important:** Environment variable changes require container **recreation**, not just restart:

```powershell
# Windows PowerShell
docker-compose -f docker-compose.local.yml down
docker-compose -f docker-compose.local.yml up -d
```

### Verify Setup

```powershell
# Check environment variable is set
docker exec agent-zero-local printenv AGUI_ENABLED
# Expected output: true

# Test SSE endpoint
curl.exe -N -m 5 "http://localhost:8080/agui/sse?context_id=test"
# Expected: SSE stream with connected event

# Check server logs
docker logs agent-zero-local 2>&1 | Select-String -Pattern "AG-UI"
# Should see:
# [AG-UI] Server started
# [AG-UI] Initialized and ready
# [AG-UI] SSE transport enabled at /agui/sse
# [AG-UI] WebSocket transport enabled at /agui/ws
```

## Production Setup (AWS ECS / Docker)

### AWS ECS Task Definition

Add environment variables to your ECS task definition:

```json
{
  "containerDefinitions": [
    {
      "name": "agent-zero",
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
  ]
}
```

### Production Docker Compose

```yaml
services:
  agent-zero:
    environment:
      - AGUI_ENABLED=true
      - AGUI_TRANSPORT=both
      - CORS_ALLOWED_ORIGINS=https://app.vercel.app,https://yourdomain.com
```

## Endpoints Reference

Once AG-UI is enabled, these endpoints become available:

### SSE Endpoint

```
GET /agui/sse?context_id=<context_id>
```

**Request:**
- Method: `GET`
- Path: `/agui/sse`
- Query Parameter: `context_id` (required, string)
- Optional Header: `X-AGUI-Context` (alternative way to provide context_id)

**Response:**
- Status: `200 OK` (if enabled)
- Status: `503 Service Unavailable` (if disabled)
- Content-Type: `text/event-stream`
- Stream: Server-Sent Events

**Example Request:**
```bash
curl -N "http://localhost:8080/agui/sse?context_id=my-context"
```

**Example Successful Response:**
```
data: {"type": "connected", "connection_id": "xxx-xxx-xxx", "context_id": "my-context"}

: keepalive

: keepalive
```

### WebSocket Endpoint

```
WS /agui/ws?context_id=<context_id>
```

**Request:**
- Protocol: WebSocket
- Path: `/agui/ws`
- Query Parameter: `context_id` (required, string)
- Optional Header: `X-AGUI-Context` (alternative way to provide context_id)

**Response:**
- Connection: WebSocket upgrade
- Messages: JSON format

**Example:**
```javascript
const ws = new WebSocket('ws://localhost:8080/agui/ws?context_id=my-context');
```

### Events Endpoint (SSE Only)

```
POST /agui/events
```

**Request:**
- Method: `POST`
- Headers:
  - `Content-Type: application/json`
  - `X-AGUI-Connection` (optional) - Connection ID
  - `X-AGUI-Context` (optional) - Context ID
- Body: JSON event

**Response:**
- `200 OK` - Event received
- `400 Bad Request` - Invalid request
- `503 Service Unavailable` - AG-UI disabled

## CORS Configuration Details

### Security: CORS Origin Validation

**IMPORTANT:** All AG-UI endpoints (SSE, WebSocket, and Events) validate request origins for security. CORS headers are **only** added if the request origin matches the allowed list.

**Security Behavior:**
- **SSE Endpoint:** Manually validates origin and adds CORS headers (bypasses Starlette middleware due to streaming)
- **WebSocket Endpoint:** Uses Starlette CORSMiddleware for origin validation
- **Events Endpoint:** Uses Starlette CORSMiddleware for origin validation
- **Consistent Validation:** All endpoints use the same origin validation logic

### How CORS Works for AG-UI

AG-UI endpoints use **Starlette CORSMiddleware** at the ASGI level (not Flask-CORS) for WebSocket and Events endpoints. SSE endpoint manually implements the same validation logic for security consistency. This is configured automatically when AG-UI initializes.

### Development Mode (Automatic)

**No configuration needed!** The server automatically allows these origins:
- `http://localhost:3000`
- `http://localhost:5173`
- `http://127.0.0.1:3000`
- `http://127.0.0.1:5173`

**Detection:** Server checks if `CORS_ALLOWED_ORIGINS` is unset AND server is in development mode.

**Security:** Only these specific localhost origins are allowed. Any other origin will be rejected, even in development mode.

### Production Mode (Required)

**MUST set** `CORS_ALLOWED_ORIGINS` environment variable:

```bash
CORS_ALLOWED_ORIGINS=https://app.vercel.app,https://yourdomain.com
```

**Security Requirements:** 
- Comma-separated, no spaces
- **No wildcards (`*`) allowed** - security risk
- Must be exact origin match (protocol + domain + port)
- Only whitelisted origins receive CORS headers
- If not configured, **no CORS headers** are added (all requests rejected)

**Warning:** If `CORS_ALLOWED_ORIGINS` is not set in production, frontend connections will fail due to CORS policy. Always configure this environment variable in production deployments.

### CORS Headers Applied

All `/agui/*` requests receive these CORS headers **only if origin is validated**:

```
Access-Control-Allow-Origin: <validated-frontend-origin>
Access-Control-Allow-Methods: GET, POST, OPTIONS
Access-Control-Allow-Headers: Content-Type, X-AGUI-Connection, X-AGUI-Context
Access-Control-Max-Age: 3600
```

**Security Notes:** 
- `Access-Control-Allow-Credentials` is **never** set to `true` (security requirement)
- Origin must exactly match an entry in the allowed list
- Requests from disallowed origins receive no CORS headers and are blocked by browsers

### Security Best Practices

1. **Never use wildcards (`*`)** in production - allows any origin to connect
2. **Always whitelist specific origins** - only your frontend domains
3. **Use HTTPS in production** - Always use `https://` origins, never `http://`
4. **Verify CORS configuration** - Test that only allowed origins can connect
5. **Monitor CORS rejections** - Check server logs for blocked origin attempts

## Port Configuration

### Docker Deployment

- **Container Port:** `80` (internal)
- **Host Port:** `8080` (default, configurable via `WEB_PORT`)
- **URL:** `http://localhost:8080`

### Native Deployment

- **Default Port:** `50080`
- **Configurable:** Via `WEB_UI_PORT` environment variable or `--port` argument
- **URL:** `http://localhost:50080`

### Frontend Configuration

```javascript
// Docker (default)
const client = new AGUIClient({
  url: 'http://localhost:8080',
  contextId: 'my-context'
});

// Native (default)
const client = new AGUIClient({
  url: 'http://localhost:50080',
  contextId: 'my-context'
});
```

## Verification Checklist

Use this checklist to verify AG-UI is properly configured:

- [ ] `AGUI_ENABLED=true` in environment variables
- [ ] Container recreated after setting environment variable (not just restarted)
- [ ] `docker exec agent-zero-local printenv AGUI_ENABLED` returns `true`
- [ ] Server logs show: `[AG-UI] Initialized and ready`
- [ ] Server logs show: `[AG-UI] SSE transport enabled at /agui/sse`
- [ ] Server logs show: `[AG-UI] WebSocket transport enabled at /agui/ws`
- [ ] `curl -N "http://localhost:8080/agui/sse?context_id=test"` returns SSE stream
- [ ] SSE stream contains `connected` event (not 503 error)
- [ ] CORS headers present in browser DevTools Network tab (if accessing from frontend)
- [ ] `Access-Control-Allow-Origin` matches frontend origin

## Error Responses

### 503 Service Unavailable (SSE)

**Response Body:** `AG-UI is disabled or not available`

**Causes:**
1. `AGUI_ENABLED` not set to `true`
2. AG-UI failed to initialize
3. Environment variable not applied (container not recreated)

**Solution:** Set `AGUI_ENABLED=true` and recreate container

### WebSocket Close Code 1008

**Close Reason:** `AG-UI is disabled` or `context_id required`

**Causes:**
1. AG-UI is disabled (`AGUI_ENABLED` not `true`)
2. Missing `context_id` query parameter or header

**Solution:**
- If disabled: Set `AGUI_ENABLED=true` and recreate container
- If missing context_id: Include `context_id` in WebSocket URL: `ws://localhost:8080/agui/ws?context_id=your-context-id`

### WebSocket Close Code 1006

**Close Reason:** Abnormal closure (connection closed without proper close frame)

**Causes:**
1. Endpoint doesn't exist (path incorrect or AG-UI not mounted)
2. Network connection issue
3. Server crashed or restarted during connection
4. Firewall/proxy blocking WebSocket

**Solution:**
- Verify endpoint URL is correct: `/agui/ws`
- Check if AG-UI is enabled and initialized (check logs)
- Test SSE endpoint as fallback: Use `transport: 'sse'` in client config
- Check network/firewall settings

### 400 Bad Request

**Response Body:** `context_id required` or `connection_id required`

**Cause:** Missing `context_id` query parameter or header

**Solution:** Include `context_id` in request:
```
GET /agui/sse?context_id=your-context-id
```

### 500 Internal Server Error

**Causes:**
1. Server-side error in AG-UI initialization
2. ASGI routing issue
3. Connection manager error
4. Exception during request handling

**Solution:** Check server logs for detailed error messages:
```powershell
docker logs agent-zero-local --tail 50
```

### CORS Errors (Browser)

**Browser Console Error:**
```
Access to fetch at 'http://localhost:8080/agui/sse' from origin 'http://localhost:3000' 
has been blocked by CORS policy
```

**Causes:**
1. Frontend origin not in allowed list
2. `CORS_ALLOWED_ORIGINS` not set in production
3. CORS middleware not initialized

**Solutions:**
- Development: Ensure frontend runs on `localhost:3000` or `localhost:5173`
- Production: Set `CORS_ALLOWED_ORIGINS` with your exact frontend origin(s)

## Security Notes

1. **No Authentication:** AG-UI endpoints currently do NOT require authentication or API keys
2. **CORS Restrictions:** Always whitelist specific origins, never use `*`
3. **HTTPS in Production:** Always use HTTPS/WSS in production
4. **Context IDs:** Context IDs are user-provided strings - validate on your side if needed

## Architecture Notes

### Request Flow

```
Frontend Request
  ↓
DispatcherMiddleware (Flask)
  ↓
ASGIMiddleware (a2wsgi)
  ↓
DynamicAGUIProxy.__call__()
  ↓
AGUIServer.create_asgi_app()
  ↓
Starlette App (with CORS middleware)
  ↓
SSE/WebSocket Transport Handler
```

### CORS Application

- **Flask Routes** (`/api/*`): Use Flask-CORS
- **AG-UI Routes** (`/agui/*`): 
  - **WebSocket and Events:** Use Starlette CORSMiddleware
  - **SSE:** Manual origin validation (same logic as middleware, for streaming compatibility)
  - Both use identical origin validation logic for security consistency
- All configured in `run_ui.py` and `python/agui/server.py` / `python/agui/transport.py`

### Contract Information

This setup guide is part of the [Frontend Contract](./FRONTEND_CONTRACT.md). The backend defines these requirements, and frontend implementations must adapt to them. See [FRONTEND_CONTRACT.md](./FRONTEND_CONTRACT.md) for complete contract details.

## Testing the Setup

### Quick Test Script

```powershell
# Windows PowerShell - Complete Verification
Write-Output "=== Checking Environment ==="
docker exec agent-zero-local printenv AGUI_ENABLED

Write-Output "`n=== Testing SSE Endpoint ==="
curl.exe -N -m 3 "http://localhost:8080/agui/sse?context_id=test"

Write-Output "`n=== Checking Logs ==="
docker logs agent-zero-local 2>&1 | Select-String -Pattern "AG-UI" -CaseSensitive:$false | Select-Object -Last 5
```

### Expected Output

```
=== Checking Environment ===
true

=== Testing SSE Endpoint ===
data: {"type": "connected", "connection_id": "xxx-xxx-xxx", "context_id": "test"}

: keepalive

=== Checking Logs ===
[AG-UI] Server started
[AG-UI] Initialized and ready
[AG-UI] SSE transport enabled at /agui/sse
[AG-UI] WebSocket transport enabled at /agui/ws
```

## Next Steps

Once AG-UI is verified working:

1. **Frontend Integration:** Follow [QUICK_START.md](./QUICK_START.md)
2. **Context Management:** See [CONTEXT_MANAGEMENT.md](./CONTEXT_MANAGEMENT.md)
3. **Protocol Details:** Read [PROTOCOL.md](./PROTOCOL.md)
4. **API Reference:** Check [API_REFERENCE.md](./API_REFERENCE.md)

---

**This guide provides a complete contract for AG-UI setup. All steps are verified and tested.**


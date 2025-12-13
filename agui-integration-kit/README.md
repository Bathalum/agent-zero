# AG-UI Integration Kit for Frontend Builders

Complete information package for integrating AG-UI protocol into any frontend application.

## What is AG-UI?

AG-UI (Agent-User Interface) is a real-time communication protocol that connects frontend applications to Agent Zero (Argent) backends. It provides:

- **Real-time streaming** of agent responses
- **Bidirectional communication** via WebSocket or SSE
- **Event-driven architecture** for all agent interactions
- **Framework-agnostic** client library
- **Auto-reconnection** and error handling

## Contract Model: Backend as Port, Frontend as Adaptor

**Important:** This integration follows the Ports and Adaptors (Hexagonal Architecture) pattern:

- **Backend defines the protocol** (Port) - The backend is the **source of truth** for all specifications
- **Frontend adapts to backend requirements** (Adaptor) - Frontend implementations **must conform** to backend specifications

**See [FRONTEND_CONTRACT.md](./FRONTEND_CONTRACT.md) for the authoritative contract specification.**

## Quick Navigation

1. **[FRONTEND_CONTRACT.md](./FRONTEND_CONTRACT.md)** - ⭐ **AUTHORITATIVE CONTRACT** - Backend as Port, Frontend as Adaptor
2. **[QUICK_START.md](./QUICK_START.md)** - Get up and running in 5 minutes
3. **[SETUP_GUIDE.md](./SETUP_GUIDE.md)** - Complete server setup guide (Docker, Production, CORS, Verification)
4. **[PROTOCOL.md](./PROTOCOL.md)** - Protocol specification and event types (backend contract)
5. **[API_REFERENCE.md](./API_REFERENCE.md)** - Complete API documentation
6. **[EXAMPLES.md](./EXAMPLES.md)** - Working code examples for React, Vue, Vanilla JS
7. **[CONFIGURATION.md](./CONFIGURATION.md)** - Server configuration reference
8. **[CONTEXT_MANAGEMENT.md](./CONTEXT_MANAGEMENT.md)** - Context ID generation and management
9. **[TROUBLESHOOTING.md](./TROUBLESHOOTING.md)** - Common issues and solutions
10. **[INTEGRATION_CHECKLIST.md](./INTEGRATION_CHECKLIST.md)** - Pre-deployment checklist

## Architecture Overview

```
Frontend Application
    ↓
AG-UI Client Library (@argent/agui-client)
    ↓
Transport Layer (WebSocket or SSE)
    ↓
Agent Zero Backend (/agui/ws or /agui/sse)
    ↓
Agent Processing
```

## Key Concepts

### Context ID
A unique identifier for each conversation/session. Multiple clients can connect to the same context. You can generate your own (any string) or use the REST API to create one. See [CONTEXT_MANAGEMENT.md](./CONTEXT_MANAGEMENT.md) for details.

### Transport Types
- **WebSocket** (`ws`): Full bidirectional communication
- **SSE** (`sse`): Server-to-client streaming, client sends via HTTP POST
- **Auto** (`auto`): Automatically selects best available transport

### Events
All communication happens through events:
- **Incoming** (Client → Server): `message`, `tool_call`, `ping`
- **Outgoing** (Server → Client): `connected`, `response`, `stream_chunk`, `stream_end`, `tool_call`, `tool_result`, `error`, etc.

## Installation

```bash
npm install @argent/agui-client
```

Or use CDN:
```html
<script type="module">
  import { AGUIClient } from 'https://cdn.jsdelivr.net/npm/@argent/agui-client/dist/client.esm.js';
</script>
```

## Basic Usage

```javascript
import { AGUIClient } from '@argent/agui-client';

const client = new AGUIClient({
  url: 'http://localhost:50080',  // Your Agent Zero backend URL
  contextId: 'my-context-id',     // Unique context identifier
  transport: 'auto'                // 'auto', 'ws', or 'sse'
});

// Listen for messages
client.on('stream_chunk', (event) => {
  console.log('Chunk:', event.data.chunk);
  console.log('Full text:', event.data.full);
});

// Connect
await client.connect();

// Send message
await client.sendMessage('Hello, agent!');
```

## Server Requirements

The Agent Zero backend must have AG-UI enabled. **See [SETUP_GUIDE.md](./SETUP_GUIDE.md) for complete setup instructions.**

**Quick Setup:**
```yaml
# docker-compose.local.yml
environment:
  - AGUI_ENABLED=true  # REQUIRED
  - AGUI_TRANSPORT=both  # Optional (default: both)
```

**Important:** After setting `AGUI_ENABLED=true`, you must **recreate** the container:
```powershell
docker-compose -f docker-compose.local.yml down
docker-compose -f docker-compose.local.yml up -d
```

**Endpoints Available (after setup):**
- `GET /agui/sse?context_id=<id>` - SSE endpoint
- `WS /agui/ws?context_id=<id>` - WebSocket endpoint  
- `POST /agui/events` - Send events (for SSE)

**Ports:**
- Docker: `http://localhost:8080` (default, check `WEB_PORT`)
- Native: `http://localhost:50080` (default)

## Framework Support

- ✅ **React** - Hooks and Provider components
- ✅ **Vue** - Composable functions
- ✅ **Vanilla JS** - Direct client usage
- ✅ **Any Framework** - Core client is framework-agnostic

## Protocol Version

Current version: **1.0.0**

## Next Steps

**For Frontend Developers (START HERE):**
1. **Read [FRONTEND_CONTRACT.md](./FRONTEND_CONTRACT.md)** - Understand the contract: Backend as Port, Frontend as Adaptor
2. Read [QUICK_START.md](./QUICK_START.md) to get started immediately
3. Review [EXAMPLES.md](./EXAMPLES.md) for framework-specific code
4. Reference [API_REFERENCE.md](./API_REFERENCE.md) for detailed API docs
5. Check [CONTEXT_MANAGEMENT.md](./CONTEXT_MANAGEMENT.md) for context ID guidance

**For Server Setup:**
1. **Read [SETUP_GUIDE.md](./SETUP_GUIDE.md)** - Complete step-by-step server setup guide (part of backend contract)

**Additional Resources:**
- See [FAQ.md](./FAQ.md) for common questions
- Check [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) if you encounter issues
- Use [INTEGRATION_CHECKLIST.md](./INTEGRATION_CHECKLIST.md) before production deployment

## Support

- **Documentation**: See files in this kit
- **Examples**: Check `examples/` directory in the repository
- **Issues**: Report on GitHub

---

**Ready to build?** Start with [QUICK_START.md](./QUICK_START.md)!


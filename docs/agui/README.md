# AG-UI Integration Guide

This guide covers the AG-UI protocol integration for Argent, including both server-side and client-side implementation.

## Overview

AG-UI (Agent User Interface) is a protocol that enables external user interfaces to connect and communicate with Argent agents in real-time. It supports both Server-Sent Events (SSE) and WebSocket transports for flexible integration.

## Quick Start

### Server-Side

The server-side implementation is already integrated into Argent. To enable it:

1. Set environment variables:
```bash
AGUI_ENABLED=true
AGUI_TRANSPORT=both  # or 'sse', 'ws'
AGUI_AUTH_REQUIRED=false
```

2. The server will automatically start and expose endpoints at `/agui/sse` and `/agui/ws`.

### Client-Side

Install the client library:

```bash
npm install @argent/agui-client
```

Basic usage:

```javascript
import { AGUIClient } from '@argent/agui-client';

const client = new AGUIClient({
  url: 'http://localhost:50080',
  contextId: 'my-context-id',
  transport: 'auto'
});

client.on('stream_chunk', (event) => {
  console.log('Chunk:', event.data.chunk);
});

await client.connect();
await client.sendMessage('Hello, agent!');
```

## Documentation

- [Integration Guide](./integration.md) - How to integrate AG-UI into your application
- [Protocol Reference](./protocol.md) - Detailed protocol specification
- [Client API](./client-api.md) - Client library API reference
- [Server API](./server-api.md) - Server configuration and endpoints
- [Examples](./examples.md) - Example applications and code samples
- [Troubleshooting](./troubleshooting.md) - Common issues and solutions

## Examples

See the example applications in the `examples/` directory:

- [React Chat](./../../examples/react-chat/) - React example with hooks
- [Vue Chat](./../../examples/vue-chat/) - Vue example with composables
- [Vanilla JS Chat](./../../examples/vanilla-chat/) - Plain JavaScript example

## Architecture

The AG-UI integration consists of:

1. **Server Layer** (`python/agui/`) - Protocol server implementation
2. **Client Library** (`agui-client/`) - JavaScript/TypeScript client library
3. **Framework Adapters** - React, Vue, and vanilla JS helpers
4. **Extension Integration** - Hooks into Argent's extension system

## Protocol Version

Current protocol version: **1.0.0**

## Support

For issues and questions, please refer to the [Troubleshooting Guide](./troubleshooting.md) or open an issue on GitHub.


# 🚀 Start Here - AG-UI Integration Kit

Welcome! This kit contains everything you need to integrate AG-UI into your frontend application.

## 📦 What's Included

This integration kit contains:

1. **[README.md](./README.md)** - Overview and navigation
2. **[QUICK_START.md](./QUICK_START.md)** - Get started in 5 minutes ⚡
3. **[SETUP_GUIDE.md](./SETUP_GUIDE.md)** - Complete server setup guide (Docker, Production, CORS) ⭐ **START HERE FOR SETUP**
4. **[API_REFERENCE.md](./API_REFERENCE.md)** - Complete API documentation
5. **[PROTOCOL.md](./PROTOCOL.md)** - Protocol specification
6. **[EXAMPLES.md](./EXAMPLES.md)** - Working code examples
7. **[CONFIGURATION.md](./CONFIGURATION.md)** - Server configuration reference
8. **[CONTEXT_MANAGEMENT.md](./CONTEXT_MANAGEMENT.md)** - Context ID management
9. **[TROUBLESHOOTING.md](./TROUBLESHOOTING.md)** - Common issues and solutions
10. **[FAQ.md](./FAQ.md)** - Frequently asked questions
11. **[INTEGRATION_CHECKLIST.md](./INTEGRATION_CHECKLIST.md)** - Integration checklist
12. **[SUMMARY.md](./SUMMARY.md)** - Complete kit summary

## 🎯 Quick Paths

### I want to...

**...get started immediately:**
→ Read [QUICK_START.md](./QUICK_START.md)

**...see working examples:**
→ Check [EXAMPLES.md](./EXAMPLES.md)

**...understand the API:**
→ Read [API_REFERENCE.md](./API_REFERENCE.md)

**...configure the server:**
→ Read [SETUP_GUIDE.md](./SETUP_GUIDE.md) for step-by-step setup
→ Read [CONFIGURATION.md](./CONFIGURATION.md) for configuration reference

**...troubleshoot issues:**
→ Read [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)

**...understand the protocol:**
→ Read [PROTOCOL.md](./PROTOCOL.md)

**...manage context IDs:**
→ Read [CONTEXT_MANAGEMENT.md](./CONTEXT_MANAGEMENT.md)

**...have questions:**
→ Read [FAQ.md](./FAQ.md)

## ⚡ 30-Second Overview

AG-UI connects your frontend to Agent Zero (Argent) backends:

```javascript
import { AGUIClient } from '@argent/agui-client';

const client = new AGUIClient({
  url: 'http://localhost:50080',
  contextId: 'my-chat',
  transport: 'auto'
});

client.on('stream_chunk', (event) => {
  updateUI(event.data.full);
});

await client.connect();
await client.sendMessage('Hello!');
```

That's it! Your frontend is now connected to Agent Zero.

## 📋 Prerequisites

- Agent Zero backend running with AG-UI enabled
- Node.js project (or ability to use CDN)
- Basic JavaScript knowledge

## 🏗️ Architecture

```
Your Frontend App
    ↓
@argent/agui-client (this library)
    ↓
WebSocket or SSE
    ↓
Agent Zero Backend (/agui/ws or /agui/sse)
    ↓
Agent Processing & Responses
```

## 📚 Reading Order

**For LLMs/AI Builders:**
1. Start with [QUICK_START.md](./QUICK_START.md)
2. Reference [API_REFERENCE.md](./API_REFERENCE.md) as needed
3. Use [EXAMPLES.md](./EXAMPLES.md) for code patterns
4. Check [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) if stuck

**For Developers:**
1. Read [README.md](./README.md) for overview
2. Follow [QUICK_START.md](./QUICK_START.md) to get running
3. Study [EXAMPLES.md](./EXAMPLES.md) for your framework
4. Keep [API_REFERENCE.md](./API_REFERENCE.md) handy
5. Use [INTEGRATION_CHECKLIST.md](./INTEGRATION_CHECKLIST.md) before production

## 🔑 Key Concepts

- **Context ID**: Unique identifier for each conversation
- **Transport**: WebSocket (bidirectional) or SSE (server→client)
- **Events**: All communication via events (message, stream_chunk, etc.)
- **Streaming**: Real-time incremental text updates

## 💡 Pro Tips

1. **Start Simple**: Use the basic example first, then add features
2. **Handle Errors**: Always implement error handling
3. **Track Message IDs**: Use message IDs to manage streaming state
4. **Test Reconnection**: Ensure your app handles disconnections
5. **Use Framework Adapters**: React/Vue adapters make life easier

## 🆘 Need Help?

1. Check [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
2. Review [EXAMPLES.md](./EXAMPLES.md) for similar use cases
3. Verify server configuration in [CONFIGURATION.md](./CONFIGURATION.md)
4. Check protocol details in [PROTOCOL.md](./PROTOCOL.md)

## ✅ Ready?

**Start here:** [QUICK_START.md](./QUICK_START.md)

---

**This kit is self-contained and includes everything needed for integration. No external dependencies required beyond the documentation itself.**


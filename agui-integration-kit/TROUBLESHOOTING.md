# AG-UI Troubleshooting Guide

Common issues and solutions for AG-UI integration.

## Table of Contents

- [Connection Issues](#connection-issues)
- [Event Issues](#event-issues)
- [Streaming Issues](#streaming-issues)
- [Framework-Specific Issues](#framework-specific-issues)
- [Performance Issues](#performance-issues)
- [Debugging](#debugging)

## Connection Issues

### Cannot Connect to Server

**Symptoms:**
- Connection fails immediately
- Error: "Connection timeout"
- Error: "Failed to connect"

**Solutions:**

1. **Check server is running:**
   ```bash
   curl http://localhost:50080/agui/sse?context_id=test
   ```

2. **Verify AG-UI is enabled:**
   ```bash
   # Check environment variable
   echo $AGUI_ENABLED
   # Should be 'true'
   ```

3. **Check URL and context ID:**
   ```javascript
   const client = new AGUIClient({
     url: 'http://localhost:50080',  // Verify this is correct
     contextId: 'my-context-id'       // Verify context exists
   });
   ```

4. **Check CORS settings** (if accessing from different origin):
   ```python
   # In server configuration
   CORS(app, resources={r"/agui/*": {"origins": ["*"]}})
   ```

### Connection Drops Frequently

**Symptoms:**
- Connection disconnects and reconnects repeatedly
- "Reconnecting" messages appear frequently

**Solutions:**

1. **Check network stability:**
   - Verify network connection is stable
   - Check for firewall or proxy issues

2. **Increase timeout:**
   ```javascript
   const client = new AGUIClient({
     timeout: 60000,  // Increase to 60 seconds
     pingInterval: 30000
   });
   ```

3. **Check server logs** for errors:
   ```bash
   # Check server logs
   tail -f logs/server.log | grep agui
   ```

4. **Verify server resources:**
   - Check CPU and memory usage
   - Verify server isn't overloaded

### WebSocket Connection Fails

**Symptoms:**
- WebSocket connection fails
- Falls back to SSE

**Solutions:**

1. **Check WebSocket support:**
   ```javascript
   if (typeof WebSocket === 'undefined') {
     console.log('WebSocket not supported, using SSE');
   }
   ```

2. **Verify WebSocket endpoint:**
   ```bash
   # Test WebSocket endpoint
   wscat -c ws://localhost:50080/agui/ws?context_id=test
   ```

3. **Check proxy/firewall:**
   - Some proxies don't support WebSocket
   - Use SSE if WebSocket is blocked

## Event Issues

### Events Not Received

**Symptoms:**
- Connected but no events received
- Messages sent but no response

**Solutions:**

1. **Verify event handlers are registered:**
   ```javascript
   client.on('message', (event) => {
     console.log('Received message:', event);
   });
   ```

2. **Check event types:**
   ```javascript
   // Listen to generic event for debugging
   client.on('event', (event) => {
     console.log('All events:', event);
   });
   ```

3. **Verify context ID:**
   - Ensure context ID matches server context
   - Check context exists on server

4. **Check server logs** for event broadcasting:
   ```python
   # Enable debug logging
   import logging
   logging.getLogger('python.agui').setLevel(logging.DEBUG)
   ```

### Events Received Multiple Times

**Symptoms:**
- Same event received multiple times
- Duplicate messages in UI

**Solutions:**

1. **Check for duplicate event handlers:**
   ```javascript
   // Remove old handlers before adding new ones
   client.off('message', handler);
   client.on('message', handler);
   ```

2. **Use `once` for one-time events:**
   ```javascript
   client.once('connected', (event) => {
     console.log('Connected once');
   });
   ```

3. **Check for multiple client instances:**
   - Ensure only one client instance per context
   - Clean up old instances

## Streaming Issues

### Stream Chunks Not Updating

**Symptoms:**
- Stream starts but doesn't update
- Only final message appears

**Solutions:**

1. **Verify stream_chunk handler:**
   ```javascript
   client.on('stream_chunk', (event) => {
     console.log('Chunk:', event.data.chunk);
     console.log('Full:', event.data.full);
     // Update UI with event.data.full
   });
   ```

2. **Check message ID tracking:**
   ```javascript
   let currentMessageId = null;
   
   client.on('stream_chunk', (event) => {
     const messageId = event.data.message_id;
     if (currentMessageId !== messageId) {
       // New stream started
       currentMessageId = messageId;
     }
     // Update UI
   });
   ```

3. **Verify server streaming:**
   - Check server logs for stream_chunk events
   - Verify extension is enabled

### Stream Never Ends

**Symptoms:**
- Stream continues indefinitely
- No `stream_end` event received

**Solutions:**

1. **Add timeout:**
   ```javascript
   let streamTimeout;
   
   client.on('stream_chunk', (event) => {
     clearTimeout(streamTimeout);
     streamTimeout = setTimeout(() => {
       // Force end stream after 30 seconds
       console.warn('Stream timeout');
     }, 30000);
   });
   
   client.on('stream_end', () => {
     clearTimeout(streamTimeout);
   });
   ```

2. **Check server for stream_end events:**
   - Verify extension is sending stream_end
   - Check server logs

## Framework-Specific Issues

### React: Hooks Not Working

**Symptoms:**
- `useAGUI` returns undefined
- Provider not found error

**Solutions:**

1. **Ensure Provider wraps components:**
   ```jsx
   <AGUIProvider url="..." contextId="...">
     <YourComponent />
   </AGUIProvider>
   ```

2. **Check React version:**
   ```bash
   npm list react
   # Should be >= 16.8.0
   ```

3. **Verify imports:**
   ```jsx
   import { AGUIProvider, useAGUI } from '@argent/agui-client/react';
   ```

### Vue: Composables Not Reactive

**Symptoms:**
- State not updating
- UI not reactive

**Solutions:**

1. **Use refs correctly:**
   ```javascript
   const { messages } = useAgui({ ... });
   // messages is already a ref, use .value in template
   ```

2. **Check Vue version:**
   ```bash
   npm list vue
   # Should be >= 3.0.0
   ```

3. **Verify setup script:**
   ```vue
   <script setup>
   // Not <script>
   ```

## Performance Issues

### High Memory Usage

**Symptoms:**
- Browser memory increases over time
- Application becomes slow

**Solutions:**

1. **Limit message history:**
   ```javascript
   const MAX_MESSAGES = 100;
   
   client.on('message', (event) => {
     messages.push(event);
     if (messages.length > MAX_MESSAGES) {
       messages.shift();
     }
   });
   ```

2. **Clean up event handlers:**
   ```javascript
   useEffect(() => {
     const handler = (event) => { /* ... */ };
     client.on('event', handler);
     
     return () => {
       client.off('event', handler);
     };
   }, []);
   ```

3. **Use virtual scrolling** for large message lists

### Slow UI Updates

**Symptoms:**
- UI lags during streaming
- Chunks update slowly

**Solutions:**

1. **Debounce stream updates:**
   ```javascript
   import { debounce } from 'lodash';
   
   const updateUI = debounce((content) => {
     setMessageContent(content);
   }, 50);
   
   client.on('stream_chunk', (event) => {
     updateUI(event.data.full);
   });
   ```

2. **Throttle rapid updates:**
   ```javascript
   import { throttle } from 'lodash';
   
   const updateUI = throttle((content) => {
     setMessageContent(content);
   }, 100);
   ```

## Debugging

### Enable Debug Logging

**Client-side:**
```javascript
// Enable verbose logging
client.on('event', (event) => {
  console.log('Event:', event);
});

client.on('statechange', (newState, oldState) => {
  console.log(`State: ${oldState} → ${newState}`);
});
```

**Server-side:**
```python
import logging
logging.getLogger('python.agui').setLevel(logging.DEBUG)
```

### Network Inspection

1. **Chrome DevTools:**
   - Network tab → Filter by "agui"
   - Check WebSocket frames
   - Inspect SSE events

2. **Firefox DevTools:**
   - Network tab → Filter by "agui"
   - Check WebSocket messages
   - Inspect SSE stream

### Connection State Monitoring

```javascript
client.on('statechange', (newState, oldState) => {
  console.log(`Connection state: ${oldState} → ${newState}`);
  
  if (newState === 'error') {
    console.error('Connection error');
  }
  
  if (newState === 'reconnecting') {
    console.log('Attempting to reconnect...');
  }
});
```

### Event Tracing

```javascript
// Log all events
client.on('event', (event) => {
  console.log(`[${event.type}]`, event);
});

// Track message flow
let messageFlow = [];
client.on('message', (event) => {
  messageFlow.push({ type: 'sent', time: Date.now(), id: event.data.message_id });
});

client.on('response', (event) => {
  messageFlow.push({ type: 'received', time: Date.now(), id: event.data.message_id });
  console.log('Message flow:', messageFlow);
});
```

## Getting Help

If you're still experiencing issues:

1. **Check server logs** for errors
2. **Enable debug logging** (see above)
3. **Check protocol version** compatibility
4. **Review example code** in `examples/` directory
5. **Open an issue** on GitHub with:
   - Error messages
   - Server logs
   - Client configuration
   - Steps to reproduce

## Common Error Messages

### "context_id required"

**Cause:** Missing or invalid context ID

**Solution:** Provide a valid context ID:
```javascript
const client = new AGUIClient({
  contextId: 'your-context-id'  // Required!
});
```

### "AG-UI is disabled" (503 Error)

**Cause:** Server has AG-UI disabled or environment variable not set

**Symptoms:**
- Response: `AG-UI is disabled or not available`
- HTTP Status: 503
- Server logs: No AG-UI initialization messages

**Solution for Docker:**
```yaml
# Add to docker-compose.local.yml
environment:
  - AGUI_ENABLED=true
```

**Then recreate container (required, not just restart):**
```powershell
docker-compose -f docker-compose.local.yml down
docker-compose -f docker-compose.local.yml up -d
```

**Verify:**
```powershell
docker exec agent-zero-local printenv AGUI_ENABLED
# Should output: true

docker logs agent-zero-local 2>&1 | Select-String -Pattern "AG-UI.*Initialized"
# Should see: [AG-UI] Initialized and ready
```

**Solution for Native/Production:**
```bash
export AGUI_ENABLED=true
# Restart server
```

### "Connection timeout"

**Cause:** Server not responding within timeout period

**Solution:** Increase timeout or check server:
```javascript
const client = new AGUIClient({
  timeout: 60000  // 60 seconds
});
```

### "WebSocket is not connected"

**Cause:** Trying to send on disconnected WebSocket

**Solution:** Check connection state:
```javascript
if (client.isConnected()) {
  await client.sendMessage('Hello!');
} else {
  console.log('Not connected, waiting...');
  await client.connect();
}
```


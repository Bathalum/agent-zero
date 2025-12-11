# AG-UI Integration Checklist

Use this checklist to ensure your integration is complete.

## Pre-Integration

- [ ] Agent Zero backend is running
- [ ] AG-UI is enabled on backend (`AGUI_ENABLED=true` in environment)
- [ ] Container recreated after setting `AGUI_ENABLED=true` (not just restarted)
- [ ] Verified AG-UI enabled: `docker exec agent-zero-local printenv AGUI_ENABLED` returns `true`
- [ ] Backend URL is known:
  - Docker: `http://localhost:8080` (default, check `WEB_PORT` if different)
  - Native: `http://localhost:50080` (default)
- [ ] CORS configured:
  - Development: Auto-configured for localhost (no action needed)
  - Production: `CORS_ALLOWED_ORIGINS` environment variable set with exact origins
- [ ] Verified endpoints working:
  - [ ] `curl -N "http://localhost:8080/agui/sse?context_id=test"` returns SSE stream
  - [ ] Server logs show: `[AG-UI] Initialized and ready`
  - [ ] Server logs show: `[AG-UI] SSE transport enabled at /agui/sse`

## Installation

- [ ] Client library installed (`npm install @argent/agui-client`)
- [ ] Or CDN script added to HTML

## Basic Setup

- [ ] Client instance created with correct URL and contextId
- [ ] Event handlers registered for key events:
  - [ ] `stream_chunk` - for streaming responses
  - [ ] `stream_end` - for stream completion
  - [ ] `error` - for error handling
  - [ ] `connected` - for connection status
- [ ] Client connected (`await client.connect()`)

## Message Handling

- [ ] Message sending implemented (`client.sendMessage()`)
- [ ] Streaming responses handled (`stream_chunk` events)
- [ ] Stream completion handled (`stream_end` events)
- [ ] Message state management (tracking message IDs)

## Error Handling

- [ ] Connection errors handled
- [ ] Reconnection logic implemented
- [ ] User feedback for connection status
- [ ] Error messages displayed to user

## UI Integration

- [ ] Message display implemented
- [ ] Streaming text updates in real-time
- [ ] Input field for sending messages
- [ ] Send button or form submission
- [ ] Connection status indicator
- [ ] Error message display

## Testing

- [ ] Can connect to backend
- [ ] Can send messages
- [ ] Receives streaming responses
- [ ] Handles disconnection gracefully
- [ ] Reconnects automatically
- [ ] Error states handled properly

## Production Readiness

- [ ] CORS configured for production domain (`CORS_ALLOWED_ORIGINS` environment variable)
- [ ] HTTPS/WSS used in production
- [ ] Error logging implemented
- [ ] Connection monitoring in place
- [ ] Rate limiting considered
- [ ] Security measures in place

## Framework-Specific (if applicable)

### React
- [ ] `AGUIProvider` wraps application
- [ ] `useAGUI` hook used in components
- [ ] Event handlers cleaned up on unmount

### Vue
- [ ] `useAgui` composable used
- [ ] Reactive state updates working
- [ ] Lifecycle hooks properly handled

### Vanilla JS
- [ ] Event listeners properly managed
- [ ] DOM updates handled efficiently
- [ ] Cleanup on page unload

## Performance

- [ ] Message history limited (if needed)
- [ ] Stream updates debounced/throttled (if needed)
- [ ] Memory leaks checked
- [ ] Large message lists handled (virtual scrolling if needed)

## Documentation

- [ ] Integration documented in your codebase
- [ ] Team members know how to use it
- [ ] Configuration documented

---

**Status:** Track your progress above. All items should be checked before production deployment.


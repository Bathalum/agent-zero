/**
 * AG-UI Client Library
 * 
 * Main entry point for the client library.
 */

export { AGUIClient, ConnectionState, TransportType } from './client.js';
export { SSETransport } from './transport/sse.js';
export { WebSocketTransport } from './transport/websocket.js';

// Framework adapters
export * from './adapters/react.js';
export * from './adapters/vue.js';
export * from './adapters/vanilla.js';

// Default export
export { AGUIClient as default } from './client.js';


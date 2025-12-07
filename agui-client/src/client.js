/**
 * AG-UI Client Library
 * 
 * Core client implementation for connecting to AG-UI protocol servers.
 */

import { SSETransport } from './transport/sse.js';
import { WebSocketTransport } from './transport/websocket.js';

/**
 * Connection state enumeration
 */
export const ConnectionState = {
  DISCONNECTED: 'disconnected',
  CONNECTING: 'connecting',
  CONNECTED: 'connected',
  RECONNECTING: 'reconnecting',
  ERROR: 'error'
};

/**
 * Transport types
 */
export const TransportType = {
  SSE: 'sse',
  WEBSOCKET: 'ws',
  AUTO: 'auto'
};

/**
 * Default configuration
 */
const DEFAULT_CONFIG = {
  url: 'http://localhost:50080',
  contextId: null,
  transport: TransportType.AUTO,
  reconnect: true,
  reconnectInterval: 1000,
  maxReconnectAttempts: 10,
  reconnectBackoff: 1.5,
  pingInterval: 30000,
  timeout: 30000
};

/**
 * AG-UI Client
 * 
 * Main client class for connecting to AG-UI protocol servers.
 */
export class AGUIClient {
  /**
   * Create a new AG-UI client instance
   * 
   * @param {Object} config - Client configuration
   * @param {string} config.url - Server URL (default: 'http://localhost:50080')
   * @param {string} config.contextId - Context ID for this connection
   * @param {string} config.transport - Transport type: 'sse', 'ws', or 'auto' (default: 'auto')
   * @param {boolean} config.reconnect - Enable auto-reconnection (default: true)
   * @param {number} config.reconnectInterval - Initial reconnect interval in ms (default: 1000)
   * @param {number} config.maxReconnectAttempts - Maximum reconnect attempts (default: 10)
   * @param {number} config.reconnectBackoff - Exponential backoff multiplier (default: 1.5)
   * @param {number} config.pingInterval - Ping interval in ms (default: 30000)
   * @param {number} config.timeout - Connection timeout in ms (default: 30000)
   */
  constructor(config = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    
    if (!this.config.contextId) {
      throw new Error('contextId is required');
    }
    
    // State
    this.state = ConnectionState.DISCONNECTED;
    this.connectionId = null;
    this.transport = null;
    this.transportType = null;
    
    // Event handlers
    this._eventHandlers = new Map();
    this._onceHandlers = new Map();
    
    // Reconnection state
    this._reconnectAttempts = 0;
    this._reconnectTimer = null;
    this._isManualDisconnect = false;
    
    // Message queue for reconnection
    this._messageQueue = [];
    
    // Bind methods
    this.connect = this.connect.bind(this);
    this.disconnect = this.disconnect.bind(this);
    this.sendMessage = this.sendMessage.bind(this);
    this.sendEvent = this.sendEvent.bind(this);
    this.on = this.on.bind(this);
    this.off = this.off.bind(this);
    this.once = this.once.bind(this);
  }
  
  /**
   * Connect to the AG-UI server
   * 
   * @returns {Promise<void>}
   */
  async connect() {
    if (this.state === ConnectionState.CONNECTED || 
        this.state === ConnectionState.CONNECTING) {
      return;
    }
    
    this._isManualDisconnect = false;
    this.setState(ConnectionState.CONNECTING);
    
    try {
      // Determine transport type
      const transportType = await this._selectTransport();
      
      // Create transport instance
      this.transportType = transportType;
      if (transportType === TransportType.SSE) {
        this.transport = new SSETransport(this.config, this);
      } else {
        this.transport = new WebSocketTransport(this.config, this);
      }
      
      // Connect
      await this.transport.connect();
      
      // Set up transport event handlers
      this.transport.on('connected', (event) => {
        this.connectionId = event.connection_id;
        this._reconnectAttempts = 0;
        this.setState(ConnectionState.CONNECTED);
        this._flushMessageQueue();
        this.emit('connected', event);
      });
      
      this.transport.on('disconnected', () => {
        this.setState(ConnectionState.DISCONNECTED);
        this.emit('disconnected');
        if (this.config.reconnect && !this._isManualDisconnect) {
          this._scheduleReconnect();
        }
      });
      
      this.transport.on('error', (error) => {
        this.setState(ConnectionState.ERROR);
        this.emit('error', error);
        if (this.config.reconnect && !this._isManualDisconnect) {
          this._scheduleReconnect();
        }
      });
      
      // Forward all protocol events
      this.transport.on('event', (event) => {
        this.emit('event', event);
        this.emit(event.type, event);
      });
      
    } catch (error) {
      this.setState(ConnectionState.ERROR);
      this.emit('error', error);
      if (this.config.reconnect && !this._isManualDisconnect) {
        this._scheduleReconnect();
      }
      throw error;
    }
  }
  
  /**
   * Disconnect from the server
   */
  disconnect() {
    this._isManualDisconnect = true;
    this._cancelReconnect();
    
    if (this.transport) {
      this.transport.disconnect();
      this.transport = null;
    }
    
    this.setState(ConnectionState.DISCONNECTED);
    this.connectionId = null;
  }
  
  /**
   * Send a message to the agent
   * 
   * @param {string} text - Message text
   * @param {Object} options - Message options
   * @param {string} options.messageId - Optional message ID
   * @param {Array<string>} options.attachments - Optional file attachments
   * @returns {Promise<void>}
   */
  async sendMessage(text, options = {}) {
    return this.sendEvent('message', {
      text,
      message_id: options.messageId,
      attachments: options.attachments || []
    });
  }
  
  /**
   * Send a protocol event
   * 
   * @param {string} type - Event type
   * @param {Object} data - Event data
   * @returns {Promise<void>}
   */
  async sendEvent(type, data = {}) {
    const event = {
      type,
      context_id: this.config.contextId,
      data
    };
    
    // If not connected, queue the message
    if (this.state !== ConnectionState.CONNECTED || !this.transport) {
      this._messageQueue.push(event);
      return;
    }
    
    try {
      await this.transport.send(event);
    } catch (error) {
      // Queue for retry on reconnect
      this._messageQueue.push(event);
      throw error;
    }
  }
  
  /**
   * Subscribe to an event
   * 
   * @param {string} event - Event name
   * @param {Function} handler - Event handler
   */
  on(event, handler) {
    if (!this._eventHandlers.has(event)) {
      this._eventHandlers.set(event, []);
    }
    this._eventHandlers.get(event).push(handler);
  }
  
  /**
   * Unsubscribe from an event
   * 
   * @param {string} event - Event name
   * @param {Function} handler - Optional specific handler to remove
   */
  off(event, handler) {
    if (!this._eventHandlers.has(event)) {
      return;
    }
    
    if (handler) {
      const handlers = this._eventHandlers.get(event);
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    } else {
      this._eventHandlers.delete(event);
    }
  }
  
  /**
   * Subscribe to an event once
   * 
   * @param {string} event - Event name
   * @param {Function} handler - Event handler
   */
  once(event, handler) {
    const wrappedHandler = (...args) => {
      handler(...args);
      this.off(event, wrappedHandler);
    };
    this.on(event, wrappedHandler);
  }
  
  /**
   * Emit an event
   * 
   * @private
   * @param {string} event - Event name
   * @param {...any} args - Event arguments
   */
  emit(event, ...args) {
    const handlers = this._eventHandlers.get(event) || [];
    handlers.forEach(handler => {
      try {
        handler(...args);
      } catch (error) {
        console.error(`Error in event handler for ${event}:`, error);
      }
    });
  }
  
  /**
   * Get current connection state
   * 
   * @returns {string}
   */
  getState() {
    return this.state;
  }
  
  /**
   * Check if connected
   * 
   * @returns {boolean}
   */
  isConnected() {
    return this.state === ConnectionState.CONNECTED;
  }
  
  /**
   * Set connection state
   * 
   * @private
   * @param {string} newState
   */
  setState(newState) {
    if (this.state !== newState) {
      const oldState = this.state;
      this.state = newState;
      this.emit('statechange', newState, oldState);
    }
  }
  
  /**
   * Select transport type
   * 
   * @private
   * @returns {Promise<string>}
   */
  async _selectTransport() {
    const { transport } = this.config;
    
    if (transport === TransportType.AUTO) {
      // Try WebSocket first, fallback to SSE
      if (typeof WebSocket !== 'undefined') {
        return TransportType.WEBSOCKET;
      } else if (typeof EventSource !== 'undefined') {
        return TransportType.SSE;
      } else {
        throw new Error('No supported transport available');
      }
    }
    
    return transport;
  }
  
  /**
   * Schedule reconnection attempt
   * 
   * @private
   */
  _scheduleReconnect() {
    if (this._reconnectTimer) {
      return;
    }
    
    if (this._reconnectAttempts >= this.config.maxReconnectAttempts) {
      this.emit('reconnect_failed');
      return;
    }
    
    const delay = Math.min(
      this.config.reconnectInterval * Math.pow(this.config.reconnectBackoff, this._reconnectAttempts),
      30000 // Max 30 seconds
    );
    
    this._reconnectAttempts++;
    this.setState(ConnectionState.RECONNECTING);
    
    this._reconnectTimer = setTimeout(() => {
      this._reconnectTimer = null;
      this.connect().catch(() => {
        // Error already handled in connect()
      });
    }, delay);
    
    this.emit('reconnecting', {
      attempt: this._reconnectAttempts,
      delay
    });
  }
  
  /**
   * Cancel scheduled reconnection
   * 
   * @private
   */
  _cancelReconnect() {
    if (this._reconnectTimer) {
      clearTimeout(this._reconnectTimer);
      this._reconnectTimer = null;
    }
    this._reconnectAttempts = 0;
  }
  
  /**
   * Flush queued messages
   * 
   * @private
   */
  _flushMessageQueue() {
    if (this._messageQueue.length === 0) {
      return;
    }
    
    const queue = [...this._messageQueue];
    this._messageQueue = [];
    
    queue.forEach(event => {
      this.sendEvent(event.type, event.data).catch(error => {
        console.error('Failed to send queued message:', error);
        // Re-queue on failure
        this._messageQueue.push(event);
      });
    });
  }
}

// Export default
export default AGUIClient;


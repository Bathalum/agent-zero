/**
 * WebSocket Transport
 * 
 * Implements WebSocket transport for AG-UI protocol.
 */

/**
 * WebSocket Transport implementation
 */
export class WebSocketTransport {
  /**
   * Create a new WebSocket transport
   * 
   * @param {Object} config - Client configuration
   * @param {AGUIClient} client - Client instance
   */
  constructor(config, client) {
    this.config = config;
    this.client = client;
    this.ws = null;
    this._eventHandlers = new Map();
    this._connectionId = null;
    this._pingTimer = null;
    this._pongTimeout = null;
  }
  
  /**
   * Connect to the server
   * 
   * @returns {Promise<void>}
   */
  async connect() {
    return new Promise((resolve, reject) => {
      try {
        const url = this._buildUrl();
        this.ws = new WebSocket(url);
        
        // Handle connection open
        this.ws.onopen = () => {
          // Start ping loop
          this._startPingLoop();
        };
        
        // Handle messages
        this.ws.onmessage = (e) => {
          try {
            const event = JSON.parse(e.data);
            this._handleEvent(event);
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        };
        
        // Handle errors
        this.ws.onerror = (error) => {
          this.emit('error', error);
        };
        
        // Handle close
        this.ws.onclose = (event) => {
          this._stopPingLoop();
          if (event.code !== 1000) { // Not a normal closure
            this.emit('error', new Error(`WebSocket closed: ${event.code} ${event.reason || ''}`));
          }
          this.emit('disconnected');
        };
        
        // Wait for connected event
        this.once('connected', (event) => {
          this._connectionId = event.connection_id;
          resolve();
        });
        
        // Timeout
        setTimeout(() => {
          if (!this._connectionId && this.ws.readyState !== WebSocket.OPEN) {
            this.ws.close();
            reject(new Error('Connection timeout'));
          }
        }, this.config.timeout);
        
      } catch (error) {
        reject(error);
      }
    });
  }
  
  /**
   * Disconnect from the server
   */
  disconnect() {
    this._stopPingLoop();
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }
    this._connectionId = null;
  }
  
  /**
   * Send an event to the server
   * 
   * @param {Object} event - Event to send
   * @returns {Promise<void>}
   */
  async send(event) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket is not connected');
    }
    
    try {
      this.ws.send(JSON.stringify(event));
    } catch (error) {
      throw new Error(`Failed to send WebSocket event: ${error.message}`);
    }
  }
  
  /**
   * Subscribe to transport events
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
   * Unsubscribe from an event
   * 
   * @param {string} event - Event name
   * @param {Function} handler - Optional specific handler
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
        console.error(`Error in WebSocket transport event handler for ${event}:`, error);
      }
    });
  }
  
  /**
   * Handle incoming event
   * 
   * @private
   * @param {Object} event - Event data
   */
  _handleEvent(event) {
    // Handle ping/pong
    if (event.type === 'ping') {
      this.send({ type: 'pong' });
      return;
    }
    
    // Emit specific event type
    this.emit('event', event);
    
    // Handle special events
    if (event.type === 'connected') {
      this.emit('connected', event);
    } else if (event.type === 'error') {
      this.emit('error', new Error(event.data?.error || 'Unknown error'));
    }
  }
  
  /**
   * Start ping loop
   * 
   * @private
   */
  _startPingLoop() {
    this._stopPingLoop();
    
    this._pingTimer = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        try {
          this.ws.send(JSON.stringify({ type: 'ping' }));
          
          // Set pong timeout
          this._pongTimeout = setTimeout(() => {
            console.warn('Pong timeout, closing connection');
            if (this.ws) {
              this.ws.close();
            }
          }, this.config.pingInterval);
        } catch (error) {
          console.error('Failed to send ping:', error);
        }
      }
    }, this.config.pingInterval);
  }
  
  /**
   * Stop ping loop
   * 
   * @private
   */
  _stopPingLoop() {
    if (this._pingTimer) {
      clearInterval(this._pingTimer);
      this._pingTimer = null;
    }
    if (this._pongTimeout) {
      clearTimeout(this._pongTimeout);
      this._pongTimeout = null;
    }
  }
  
  /**
   * Build WebSocket URL
   * 
   * @private
   * @returns {string}
   */
  _buildUrl() {
    const baseUrl = this.config.url.replace(/\/$/, '');
    // Convert http/https to ws/wss
    const wsUrl = baseUrl.replace(/^http/, 'ws');
    const url = new URL(`${wsUrl}/agui/ws`);
    url.searchParams.set('context_id', this.config.contextId);
    return url.toString();
  }
}


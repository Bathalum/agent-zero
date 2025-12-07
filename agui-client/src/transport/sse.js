/**
 * Server-Sent Events (SSE) Transport
 * 
 * Implements SSE transport for AG-UI protocol.
 */

/**
 * SSE Transport implementation
 */
export class SSETransport {
  /**
   * Create a new SSE transport
   * 
   * @param {Object} config - Client configuration
   * @param {AGUIClient} client - Client instance
   */
  constructor(config, client) {
    this.config = config;
    this.client = client;
    this.eventSource = null;
    this._eventHandlers = new Map();
    this._connectionId = null;
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
        this.eventSource = new EventSource(url);
        
        // Handle connection
        this.eventSource.onopen = () => {
          // Connection opened, wait for 'connected' event
        };
        
        // Handle messages
        this.eventSource.onmessage = (e) => {
          try {
            const event = JSON.parse(e.data);
            this._handleEvent(event);
          } catch (error) {
            console.error('Failed to parse SSE message:', error);
          }
        };
        
        // Handle errors
        this.eventSource.onerror = (error) => {
          if (this.eventSource.readyState === EventSource.CLOSED) {
            this.emit('disconnected');
            reject(new Error('SSE connection closed'));
          } else {
            this.emit('error', error);
          }
        };
        
        // Wait for connected event
        this.once('connected', (event) => {
          this._connectionId = event.connection_id;
          resolve();
        });
        
        // Timeout
        setTimeout(() => {
          if (!this._connectionId) {
            this.eventSource.close();
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
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
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
    // SSE is unidirectional, use POST to /agui/events
    const url = `${this.config.url}/agui/events`;
    
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-AGUI-Connection': this._connectionId || '',
          'X-AGUI-Context': this.config.contextId
        },
        body: JSON.stringify(event)
      });
      
      if (!response.ok) {
        throw new Error(`Failed to send event: ${response.statusText}`);
      }
    } catch (error) {
      throw new Error(`Failed to send SSE event: ${error.message}`);
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
        console.error(`Error in SSE transport event handler for ${event}:`, error);
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
   * Build SSE URL
   * 
   * @private
   * @returns {string}
   */
  _buildUrl() {
    const baseUrl = this.config.url.replace(/\/$/, '');
    const url = new URL(`${baseUrl}/agui/sse`);
    url.searchParams.set('context_id', this.config.contextId);
    return url.toString();
  }
}


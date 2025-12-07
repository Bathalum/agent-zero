/**
 * Vanilla JS Adapter for AG-UI Client
 * 
 * Provides simple wrapper functions and DOM utilities for vanilla JavaScript.
 */

import { AGUIClient } from '../client.js';

/**
 * Create and configure an AG-UI client instance
 * 
 * @param {Object} config - Client configuration
 * @returns {AGUIClient} Configured client instance
 */
export function createAguiClient(config) {
  return new AGUIClient(config);
}

/**
 * Simple chat interface helper
 * 
 * Creates a basic chat interface bound to DOM elements.
 * 
 * @param {Object} options - Configuration options
 * @param {string} options.url - Server URL
 * @param {string} options.contextId - Context ID
 * @param {HTMLElement} options.messageContainer - Container for messages
 * @param {HTMLElement} options.inputElement - Input element for messages
 * @param {HTMLElement} options.sendButton - Send button
 * @param {HTMLElement} options.statusElement - Status indicator element
 * @param {Object} options.config - Additional client configuration
 * @returns {Object} Helper object with client and methods
 */
export function createChatInterface(options) {
  const {
    url,
    contextId,
    messageContainer,
    inputElement,
    sendButton,
    statusElement,
    config = {}
  } = options;
  
  // Create client
  const client = new AGUIClient({
    url,
    contextId,
    ...config
  });
  
  // State
  let messages = [];
  
  // Update status
  function updateStatus(text, className = '') {
    if (statusElement) {
      statusElement.textContent = text;
      if (className) {
        statusElement.className = className;
      }
    }
  }
  
  // Render messages
  function renderMessages() {
    if (!messageContainer) {
      return;
    }
    
    messageContainer.innerHTML = messages.map(msg => {
      const className = msg.type === 'error' ? 'error' : msg.type;
      return `
        <div class="agui-message agui-message-${className}">
          <div class="agui-message-content">${escapeHtml(msg.content)}</div>
          <div class="agui-message-time">${formatTime(msg.timestamp)}</div>
        </div>
      `;
    }).join('');
    
    // Scroll to bottom
    messageContainer.scrollTop = messageContainer.scrollHeight;
  }
  
  // Add message
  function addMessage(message) {
    messages.push(message);
    renderMessages();
  }
  
  // Send message
  async function sendMessage() {
    if (!inputElement) {
      return;
    }
    
    const text = inputElement.value.trim();
    if (!text) {
      return;
    }
    
    if (!client.isConnected()) {
      updateStatus('Not connected', 'error');
      return;
    }
    
    // Clear input
    inputElement.value = '';
    
    // Add user message
    addMessage({
      id: Date.now().toString(),
      type: 'message',
      content: text,
      timestamp: Date.now()
    });
    
    try {
      await client.sendMessage(text);
    } catch (error) {
      addMessage({
        id: Date.now().toString(),
        type: 'error',
        content: `Failed to send: ${error.message}`,
        timestamp: Date.now()
      });
    }
  }
  
  // Set up event handlers
  client.on('connected', () => {
    updateStatus('Connected', 'connected');
  });
  
  client.on('disconnected', () => {
    updateStatus('Disconnected', 'disconnected');
  });
  
  client.on('error', (error) => {
    updateStatus(`Error: ${error.message}`, 'error');
  });
  
  client.on('message', (event) => {
    addMessage({
      id: event.data?.message_id || Date.now().toString(),
      type: 'message',
      content: event.data?.content || event.data?.text || '',
      timestamp: event.timestamp || Date.now()
    });
  });
  
  client.on('response', (event) => {
    addMessage({
      id: event.data?.message_id || Date.now().toString(),
      type: 'response',
      content: event.data?.content || '',
      timestamp: event.timestamp || Date.now()
    });
  });
  
  let streamingMessageId = null;
  let streamingContent = '';
  
  client.on('stream_chunk', (event) => {
    const chunk = event.data?.chunk || '';
    streamingContent = event.data?.full || '';
    streamingMessageId = event.data?.message_id || 'streaming';
    
    // Update or create streaming message
    const existingIndex = messages.findIndex(m => m.id === streamingMessageId);
    if (existingIndex >= 0) {
      messages[existingIndex].content = streamingContent;
    } else {
      messages.push({
        id: streamingMessageId,
        type: 'response',
        content: streamingContent,
        timestamp: event.timestamp || Date.now()
      });
    }
    renderMessages();
  });
  
  client.on('stream_end', (event) => {
    if (streamingMessageId) {
      const index = messages.findIndex(m => m.id === streamingMessageId);
      if (index >= 0) {
        messages[index].content = event.data?.final_text || streamingContent;
        renderMessages();
      }
      streamingMessageId = null;
      streamingContent = '';
    }
  });
  
  client.on('error', (event) => {
    addMessage({
      id: Date.now().toString(),
      type: 'error',
      content: event.data?.error || 'An error occurred',
      timestamp: event.timestamp || Date.now()
    });
  });
  
  // Set up DOM event handlers
  if (sendButton) {
    sendButton.addEventListener('click', sendMessage);
  }
  
  if (inputElement) {
    inputElement.addEventListener('keypress', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });
  }
  
  // Connect
  client.connect().catch((error) => {
    updateStatus(`Connection failed: ${error.message}`, 'error');
  });
  
  return {
    client,
    addMessage,
    sendMessage,
    clearMessages: () => {
      messages = [];
      renderMessages();
    }
  };
}

/**
 * Utility: Escape HTML
 * 
 * @private
 * @param {string} text - Text to escape
 * @returns {string} Escaped text
 */
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

/**
 * Utility: Format timestamp
 * 
 * @private
 * @param {number} timestamp - Unix timestamp
 * @returns {string} Formatted time
 */
function formatTime(timestamp) {
  const date = new Date(timestamp);
  return date.toLocaleTimeString();
}

/**
 * Bind client to DOM elements
 * 
 * Simple helper to bind client events to DOM elements.
 * 
 * @param {AGUIClient} client - Client instance
 * @param {Object} elements - DOM elements to bind
 * @param {HTMLElement} elements.status - Status element
 * @param {HTMLElement} elements.messages - Messages container
 */
export function bindClientToDOM(client, elements) {
  const { status, messages } = elements;
  
  if (status) {
    client.on('statechange', (newState) => {
      status.textContent = newState;
      status.className = `agui-status agui-status-${newState}`;
    });
  }
  
  if (messages) {
    client.on('message', (event) => {
      const div = document.createElement('div');
      div.className = 'agui-message agui-message-user';
      div.textContent = event.data?.text || event.data?.content || '';
      messages.appendChild(div);
      messages.scrollTop = messages.scrollHeight;
    });
    
    client.on('stream_chunk', (event) => {
      const chunk = event.data?.chunk || '';
      let lastDiv = messages.querySelector('.agui-message-streaming');
      if (!lastDiv) {
        lastDiv = document.createElement('div');
        lastDiv.className = 'agui-message agui-message-streaming';
        messages.appendChild(lastDiv);
      }
      lastDiv.textContent = event.data?.full || '';
      messages.scrollTop = messages.scrollHeight;
    });
    
    client.on('stream_end', (event) => {
      const streamingDiv = messages.querySelector('.agui-message-streaming');
      if (streamingDiv) {
        streamingDiv.className = 'agui-message agui-message-response';
        streamingDiv.textContent = event.data?.final_text || streamingDiv.textContent;
      }
    });
  }
}

// Default export
export default {
  createAguiClient,
  createChatInterface,
  bindClientToDOM
};


/**
 * Vue Adapter for AG-UI Client
 * 
 * Provides Vue composables for AG-UI integration.
 */

import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import { AGUIClient, ConnectionState } from '../client.js';

/**
 * Main composable for AG-UI functionality
 * 
 * @param {Object} options - Configuration options
 * @param {string} options.url - Server URL
 * @param {string} options.contextId - Context ID
 * @param {string} options.transport - Transport type
 * @param {Object} options.config - Additional client configuration
 * @returns {Object} AG-UI client state and methods
 */
export function useAgui(options) {
  const {
    url = 'http://localhost:50080',
    contextId,
    transport = 'auto',
    config = {}
  } = options;
  
  // State
  const client = ref(null);
  const isConnected = ref(false);
  const error = ref(null);
  const messages = ref([]);
  const streamingMessage = ref(null);
  const isStreaming = ref(false);
  
  // Initialize client
  onMounted(() => {
    if (!contextId) {
      return;
    }
    
    const clientInstance = new AGUIClient({
      url,
      contextId,
      transport,
      ...config
    });
    
    // Set up event handlers
    clientInstance.on('connected', () => {
      isConnected.value = true;
      error.value = null;
    });
    
    clientInstance.on('disconnected', () => {
      isConnected.value = false;
    });
    
    clientInstance.on('error', (err) => {
      error.value = err;
      isConnected.value = false;
    });
    
    const handleMessage = (event) => {
      messages.value.push({
        id: event.data?.message_id || Date.now().toString(),
        type: 'message',
        content: event.data?.content || event.data?.text || '',
        timestamp: event.timestamp || Date.now()
      });
    };
    
    const handleResponse = (event) => {
      messages.value.push({
        id: event.data?.message_id || Date.now().toString(),
        type: 'response',
        content: event.data?.content || '',
        timestamp: event.timestamp || Date.now()
      });
    };
    
    const handleStreamChunk = (event) => {
      const messageId = event.data?.message_id;
      const chunk = event.data?.chunk || '';
      const full = event.data?.full || '';
      
      isStreaming.value = true;
      streamingMessage.value = {
        id: messageId || 'streaming',
        type: 'response',
        content: full,
        timestamp: event.timestamp || Date.now()
      };
    };
    
    const handleStreamEnd = (event) => {
      isStreaming.value = false;
      if (streamingMessage.value) {
        messages.value.push({
          ...streamingMessage.value,
          content: event.data?.final_text || streamingMessage.value.content
        });
        streamingMessage.value = null;
      }
    };
    
    const handleError = (event) => {
      messages.value.push({
        id: Date.now().toString(),
        type: 'error',
        content: event.data?.error || 'An error occurred',
        timestamp: event.timestamp || Date.now()
      });
    };
    
    // Register event handlers
    clientInstance.on('message', handleMessage);
    clientInstance.on('response', handleResponse);
    clientInstance.on('stream_chunk', handleStreamChunk);
    clientInstance.on('stream_end', handleStreamEnd);
    clientInstance.on('error', handleError);
    
    // Connect
    clientInstance.connect().catch((err) => {
      error.value = err;
    });
    
    client.value = clientInstance;
  });
  
  // Cleanup
  onUnmounted(() => {
    if (client.value) {
      client.value.disconnect();
    }
  });
  
  // Send message
  const sendMessage = async (text, messageOptions = {}) => {
    if (!client.value || !isConnected.value) {
      throw new Error('Client not connected');
    }
    
    try {
      await client.value.sendMessage(text, messageOptions);
    } catch (err) {
      console.error('Failed to send message:', err);
      throw err;
    }
  };
  
  // Send event
  const sendEvent = async (type, data = {}) => {
    if (!client.value || !isConnected.value) {
      throw new Error('Client not connected');
    }
    
    try {
      await client.value.sendEvent(type, data);
    } catch (err) {
      console.error('Failed to send event:', err);
      throw err;
    }
  };
  
  // Clear messages
  const clearMessages = () => {
    messages.value = [];
    streamingMessage.value = null;
  };
  
  return {
    client,
    isConnected,
    error,
    messages,
    streamingMessage,
    isStreaming,
    sendMessage,
    sendEvent,
    clearMessages
  };
}

/**
 * Composable for context operations
 * 
 * @param {Object} options - Same as useAgui
 * @returns {Object} Context-related methods
 */
export function useAguiContext(options) {
  const { client, isConnected } = useAgui(options);
  
  const getContextState = async () => {
    if (!client.value || !isConnected.value) {
      return null;
    }
    
    // Wait for context_state event
    return new Promise((resolve) => {
      const handler = (event) => {
        if (event.type === 'context_state') {
          client.value.off('event', handler);
          resolve(event.data);
        }
      };
      client.value.on('event', handler);
      
      // Timeout
      setTimeout(() => {
        client.value.off('event', handler);
        resolve(null);
      }, 5000);
    });
  };
  
  return {
    getContextState
  };
}

/**
 * Composable for message handling
 * 
 * @param {Object} options - Same as useAgui
 * @returns {Object} Message-related state and methods
 */
export function useAguiMessages(options) {
  const { messages, streamingMessage, isStreaming, clearMessages } = useAgui(options);
  
  return {
    messages,
    streamingMessage,
    isStreaming,
    clearMessages
  };
}

// Default export
export default {
  useAgui,
  useAguiContext,
  useAguiMessages
};


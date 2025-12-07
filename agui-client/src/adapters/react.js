/**
 * React Adapter for AG-UI Client
 * 
 * Provides React hooks and context provider for AG-UI integration.
 */

import React, { createContext, useContext, useEffect, useState, useCallback, useRef } from 'react';
import { AGUIClient, ConnectionState } from '../client.js';

/**
 * AG-UI Context
 */
const AGUIContext = createContext(null);

/**
 * AG-UI Provider Component
 * 
 * Provides AG-UI client instance to child components.
 * 
 * @param {Object} props
 * @param {string} props.url - Server URL
 * @param {string} props.contextId - Context ID
 * @param {string} props.transport - Transport type
 * @param {Object} props.config - Additional client configuration
 * @param {React.ReactNode} props.children - Child components
 */
export function AGUIProvider({ url, contextId, transport = 'auto', config = {}, children }) {
  const [client, setClient] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState(null);
  
  useEffect(() => {
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
      setIsConnected(true);
      setError(null);
    });
    
    clientInstance.on('disconnected', () => {
      setIsConnected(false);
    });
    
    clientInstance.on('error', (err) => {
      setError(err);
      setIsConnected(false);
    });
    
    // Connect
    clientInstance.connect().catch((err) => {
      setError(err);
    });
    
    setClient(clientInstance);
    
    // Cleanup
    return () => {
      clientInstance.disconnect();
    };
  }, [url, contextId, transport]);
  
  return (
    <AGUIContext.Provider value={{ client, isConnected, error }}>
      {children}
    </AGUIContext.Provider>
  );
}

/**
 * Hook to access AG-UI context
 * 
 * @returns {Object} Context value with client, isConnected, and error
 */
export function useAGUIContext() {
  const context = useContext(AGUIContext);
  if (!context) {
    throw new Error('useAGUIContext must be used within AGUIProvider');
  }
  return context;
}

/**
 * Main hook for AG-UI functionality
 * 
 * Provides connection state, messages, and send functionality.
 * 
 * @returns {Object} AG-UI client state and methods
 */
export function useAGUI() {
  const { client, isConnected, error } = useAGUIContext();
  const [messages, setMessages] = useState([]);
  const [streamingMessage, setStreamingMessage] = useState(null);
  const [isStreaming, setIsStreaming] = useState(false);
  
  // Set up event listeners
  useEffect(() => {
    if (!client) {
      return;
    }
    
    const handleMessage = (event) => {
      setMessages(prev => [...prev, {
        id: event.data?.message_id || Date.now().toString(),
        type: 'message',
        content: event.data?.content || event.data?.text || '',
        timestamp: event.timestamp || Date.now()
      }]);
    };
    
    const handleResponse = (event) => {
      setMessages(prev => [...prev, {
        id: event.data?.message_id || Date.now().toString(),
        type: 'response',
        content: event.data?.content || '',
        timestamp: event.timestamp || Date.now()
      }]);
    };
    
    const handleStreamChunk = (event) => {
      const messageId = event.data?.message_id;
      const chunk = event.data?.chunk || '';
      const full = event.data?.full || '';
      
      setIsStreaming(true);
      setStreamingMessage({
        id: messageId || 'streaming',
        type: 'response',
        content: full,
        timestamp: event.timestamp || Date.now()
      });
    };
    
    const handleStreamEnd = (event) => {
      setIsStreaming(false);
      if (streamingMessage) {
        setMessages(prev => [...prev, {
          ...streamingMessage,
          content: event.data?.final_text || streamingMessage.content
        }]);
        setStreamingMessage(null);
      }
    };
    
    const handleError = (event) => {
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        type: 'error',
        content: event.data?.error || 'An error occurred',
        timestamp: event.timestamp || Date.now()
      }]);
    };
    
    // Register event handlers
    client.on('message', handleMessage);
    client.on('response', handleResponse);
    client.on('stream_chunk', handleStreamChunk);
    client.on('stream_end', handleStreamEnd);
    client.on('error', handleError);
    
    // Cleanup
    return () => {
      client.off('message', handleMessage);
      client.off('response', handleResponse);
      client.off('stream_chunk', handleStreamChunk);
      client.off('stream_end', handleStreamEnd);
      client.off('error', handleError);
    };
  }, [client, streamingMessage]);
  
  // Send message
  const sendMessage = useCallback(async (text, options = {}) => {
    if (!client || !isConnected) {
      throw new Error('Client not connected');
    }
    
    try {
      await client.sendMessage(text, options);
    } catch (error) {
      console.error('Failed to send message:', error);
      throw error;
    }
  }, [client, isConnected]);
  
  // Send event
  const sendEvent = useCallback(async (type, data = {}) => {
    if (!client || !isConnected) {
      throw new Error('Client not connected');
    }
    
    try {
      await client.sendEvent(type, data);
    } catch (error) {
      console.error('Failed to send event:', error);
      throw error;
    }
  }, [client, isConnected]);
  
  // Clear messages
  const clearMessages = useCallback(() => {
    setMessages([]);
    setStreamingMessage(null);
  }, []);
  
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
 * Hook for context operations
 * 
 * @returns {Object} Context-related methods
 */
export function useAGUIContextOps() {
  const { client, isConnected } = useAGUIContext();
  
  const getContextState = useCallback(async () => {
    if (!client || !isConnected) {
      return null;
    }
    
    // Wait for context_state event
    return new Promise((resolve) => {
      const handler = (event) => {
        if (event.type === 'context_state') {
          client.off('event', handler);
          resolve(event.data);
        }
      };
      client.on('event', handler);
      
      // Timeout
      setTimeout(() => {
        client.off('event', handler);
        resolve(null);
      }, 5000);
    });
  }, [client, isConnected]);
  
  return {
    getContextState
  };
}

/**
 * Hook for message handling
 * 
 * @returns {Object} Message-related state and methods
 */
export function useAGUIMessages() {
  const { messages, streamingMessage, isStreaming, clearMessages } = useAGUI();
  
  return {
    messages,
    streamingMessage,
    isStreaming,
    clearMessages
  };
}

// Default export
export default {
  AGUIProvider,
  useAGUI,
  useAGUIContext,
  useAGUIMessages
};


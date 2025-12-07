<template>
  <div class="chat-container">
    <div class="chat-header">
      <h1>AG-UI Vue Chat</h1>
      <div :class="['status', isConnected ? 'connected' : 'disconnected']">
        {{ isConnected ? 'Connected' : 'Disconnected' }}
      </div>
    </div>
    
    <div v-if="error" class="error-banner">
      Error: {{ error.message }}
    </div>
    
    <div class="messages">
      <div
        v-for="msg in allMessages"
        :key="msg.id"
        :class="['message', `message-${msg.type}`]"
      >
        <div class="message-content">{{ msg.content }}</div>
        <div class="message-time">
          {{ formatTime(msg.timestamp) }}
        </div>
      </div>
      <div v-if="isStreaming" class="streaming-indicator">...</div>
    </div>
    
    <form @submit.prevent="handleSend" class="input-form">
      <input
        v-model="input"
        type="text"
        placeholder="Type a message..."
        :disabled="!isConnected"
      />
      <button type="submit" :disabled="!isConnected || !input.trim()">
        Send
      </button>
    </form>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useAgui } from '@argent/agui-client/vue';

const contextId = new URLSearchParams(window.location.search).get('context_id') || 'default';

const {
  messages,
  streamingMessage,
  isStreaming,
  sendMessage,
  isConnected,
  error
} = useAgui({
  url: 'http://localhost:50080',
  contextId,
  transport: 'auto'
});

const input = ref('');

const allMessages = computed(() => {
  const msgs = [...messages.value];
  if (streamingMessage.value) {
    msgs.push(streamingMessage.value);
  }
  return msgs;
});

const handleSend = async () => {
  if (!input.value.trim() || !isConnected.value) return;
  
  try {
    await sendMessage(input.value);
    input.value = '';
  } catch (err) {
    console.error('Failed to send message:', err);
  }
};

const formatTime = (timestamp) => {
  return new Date(timestamp).toLocaleTimeString();
};
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  max-width: 800px;
  margin: 0 auto;
  border: 1px solid #ddd;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid #ddd;
  background: #f5f5f5;
}

.chat-header h1 {
  margin: 0;
  font-size: 1.5rem;
}

.status {
  padding: 0.25rem 0.75rem;
  border-radius: 4px;
  font-size: 0.875rem;
}

.status.connected {
  background: #4caf50;
  color: white;
}

.status.disconnected {
  background: #f44336;
  color: white;
}

.error-banner {
  padding: 0.75rem;
  background: #ffebee;
  color: #c62828;
  border-bottom: 1px solid #ddd;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}

.message {
  margin-bottom: 1rem;
  padding: 0.75rem;
  border-radius: 4px;
}

.message-message {
  background: #e3f2fd;
  margin-left: 20%;
}

.message-response {
  background: #f1f8e9;
  margin-right: 20%;
}

.message-error {
  background: #ffebee;
  color: #c62828;
}

.message-content {
  margin-bottom: 0.25rem;
}

.message-time {
  font-size: 0.75rem;
  color: #666;
}

.streaming-indicator {
  padding: 0.5rem;
  text-align: center;
  color: #666;
}

.input-form {
  display: flex;
  padding: 1rem;
  border-top: 1px solid #ddd;
}

.input-form input {
  flex: 1;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  margin-right: 0.5rem;
}

.input-form button {
  padding: 0.75rem 1.5rem;
  background: #2196f3;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.input-form button:disabled {
  background: #ccc;
  cursor: not-allowed;
}
</style>


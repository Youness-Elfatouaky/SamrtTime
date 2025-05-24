<script setup>
import { ref, onMounted, nextTick } from 'vue'
import Layout from '../components/Layout.vue'
import { chatService } from '../services/api'
import moment from 'moment'
import { marked } from 'marked'

const messages = ref([])
const newMessage = ref('')
const loading = ref(false)
const messagesContainer = ref(null)

// Setup markdown renderer
marked.setOptions({
  gfm: true,
  breaks: true,
  langPrefix: 'language-'
})

const sendMessage = async () => {
  if (!newMessage.value.trim()) return

  const userMessage = newMessage.value
  const timestamp = new Date()
  
  // Add user message
  messages.value.push({
    role: 'user',
    content: userMessage,
    timestamp
  })
  
  newMessage.value = ''
  
  // Scroll to bottom
  await nextTick()
  messagesContainer.value.scrollTo({
    top: messagesContainer.value.scrollHeight,
    behavior: 'smooth'
  })
  
  loading.value = true
  try {
    const response = await chatService.sendMessage(userMessage)
    messages.value.push({
      role: 'assistant',
      content: response.data.reply,
      timestamp: new Date()
    })
    
    // Scroll to bottom again after receiving response
    await nextTick()
    messagesContainer.value.scrollTo({
      top: messagesContainer.value.scrollHeight,
      behavior: 'smooth'
    })
  } catch (error) {
    console.error('Error sending message:', error)
    messages.value.push({
      role: 'assistant',
      content: 'Sorry, I encountered an error. Please try again.',
      timestamp: new Date(),
      isError: true
    })
  } finally {
    loading.value = false
  }
}

const formatTimestamp = (date) => {
  return moment(date).calendar(null, {
    sameDay: 'h:mm A',
    lastDay: '[Yesterday] h:mm A',
    lastWeek: 'dddd h:mm A',
    sameElse: 'MMM D, YYYY h:mm A'
  })
}

const renderMarkdown = (text) => {
  return marked(text)
}

const getMessageClass = (message) => {
  const baseClasses = 'max-w-[80%] rounded-lg px-4 py-3 shadow-sm'
  if (message.role === 'user') {
    return `${baseClasses} bg-blue-600 text-white self-end`
  }
  if (message.isError) {
    return `${baseClasses} bg-red-100 text-red-900 self-start`
  }
  return `${baseClasses} bg-gray-100 text-gray-900 self-start`
}

// Handle Ctrl+Enter to send message
const handleKeydown = (e) => {
  if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
    e.preventDefault()
    sendMessage()
  }
}

onMounted(() => {
  // Load chat history here if needed
})
</script>

<template>
  <Layout>
    <div class="max-w-4xl mx-auto h-screen flex flex-col">
      <div class="bg-white shadow sm:rounded-lg flex-1 flex flex-col">
        <!-- Header -->
        <div class="px-6 py-4 border-b border-gray-200">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-lg font-medium text-gray-900">
                Chat with your AI Assistant
              </h3>
              <p class="mt-1 text-sm text-gray-500">
                Get help with scheduling, tasks, and more
              </p>
            </div>
            <div class="flex items-center space-x-2 text-sm text-gray-500">
              <button class="hover:text-gray-900">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                </svg>
              </button>
            </div>
          </div>
        </div>
        
        <!-- Messages -->
        <div 
          ref="messagesContainer"
          class="flex-1 overflow-y-auto px-6 py-4"
        >
          <div class="space-y-6">
            <template v-if="messages.length === 0">
              <div class="text-center py-8">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mx-auto text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
                <p class="text-gray-500 mb-4">
                  Start a conversation with your AI assistant. You can ask about:
                </p>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-lg mx-auto text-left">
                  <div class="bg-gray-50 p-4 rounded-lg">
                    <h4 class="font-medium text-gray-900 mb-2">Schedule Management</h4>
                    <ul class="text-sm text-gray-600 space-y-2">
                      <li>• Create new meetings</li>
                      <li>• Find free time slots</li>
                      <li>• Manage calendar</li>
                    </ul>
                  </div>
                  <div class="bg-gray-50 p-4 rounded-lg">
                    <h4 class="font-medium text-gray-900 mb-2">Task Management</h4>
                    <ul class="text-sm text-gray-600 space-y-2">
                      <li>• Create and track tasks</li>
                      <li>• Set priorities</li>
                      <li>• Get reminders</li>
                    </ul>
                  </div>
                </div>
              </div>
            </template>
            
            <div
              v-for="(message, index) in messages"
              :key="index"
              class="flex flex-col space-y-1"
            >
              <div
                :class=" [
                  getMessageClass(message)
                ]"
              >
                <div 
                  v-if="message.role === 'assistant'"
                  class="prose prose-sm max-w-none"
                  v-html="renderMarkdown(message.content)"
                >
                </div>
                <div v-else>
                  {{ message.content }}
                </div>
              </div>
              <span 
                :class=" [
                  'text-xs',
                  message.role === 'user' ? 'text-right mr-1' : 'ml-1'
                ]"
              >
                {{ formatTimestamp(message.timestamp) }}
              </span>
            </div>
            
            <div v-if="loading" class="flex items-center space-x-2 text-gray-500">
              <div class="flex space-x-1">
                <div class="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style="animation-delay: 0ms"></div>
                <div class="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style="animation-delay: 150ms"></div>
                <div class="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style="animation-delay: 300ms"></div>
              </div>
              <span class="text-sm">AI is thinking</span>
            </div>
          </div>
        </div>

        <!-- Message Input -->
        <div class="px-6 py-4 border-t border-gray-200">
          <form @submit.prevent="sendMessage" class="flex space-x-4">
            <div class="flex-1 min-w-0">
              <textarea
                v-model="newMessage"
                @keydown="handleKeydown"
                rows="1"
                placeholder="Type your message... (Ctrl + Enter to send)"
                class="block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 resize-none"
                :disabled="loading"
              ></textarea>
              <div class="mt-1 text-xs text-gray-500">
                Supports Markdown formatting
              </div>
            </div>
            <div class="flex items-end space-x-2">
              <button
                type="button"
                class="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                title="Upload File (Coming Soon)"
                disabled
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                </svg>
              </button>
              <button
                type="submit"
                :disabled="loading || !newMessage.trim()"
                class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed h-[38px]"
              >
                <svg 
                  v-if="!loading"
                  xmlns="http://www.w3.org/2000/svg" 
                  class="h-5 w-5" 
                  fill="none" 
                  viewBox="0 0 24 24" 
                  stroke="currentColor"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
                <svg 
                  v-else
                  class="animate-spin h-5 w-5" 
                  xmlns="http://www.w3.org/2000/svg" 
                  fill="none" 
                  viewBox="0 0 24 24"
                >
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </Layout>
</template>

<style>
.prose {
  max-width: none;
}

.prose pre {
  background-color: #f3f4f6;
  padding: 1rem;
  border-radius: 0.5rem;
  margin: 1rem 0;
  overflow-x: auto;
}

.prose code {
  background-color: #f3f4f6;
  padding: 0.2rem 0.4rem;
  border-radius: 0.25rem;
  font-size: 0.875em;
  color: #374151;
}

/* Basic syntax highlighting */
.prose pre code {
  color: #374151;
  padding: 0;
  background-color: transparent;
}

.prose .language-javascript,
.prose .language-typescript,
.prose .language-python {
  color: #000;
}

.prose .keyword { color: #7c3aed; }
.prose .string { color: #059669; }
.prose .number { color: #0891b2; }
.prose .comment { color: #6b7280; }
.prose .function { color: #2563eb; }
</style>

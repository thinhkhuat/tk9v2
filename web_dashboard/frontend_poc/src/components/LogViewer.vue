<script setup lang="ts">
import { useSessionStore } from '@/stores/sessionStore'
import { ref, computed, watch, nextTick } from 'vue'
import type { WebSocketEvent } from '@/types/events'

const store = useSessionStore()

// Auto-scroll toggle
const autoScroll = ref(true)
const logContainer = ref<HTMLElement | null>(null)

// Filter options
const selectedLogLevel = ref<string>('all')
const searchQuery = ref('')

// Filtered logs
const filteredLogs = computed(() => {
  let logs = store.events.filter(e => e.event_type === 'log')

  // Filter by log level
  if (selectedLogLevel.value !== 'all') {
    logs = logs.filter(e => {
      const payload = e.payload as any
      return payload.level === selectedLogLevel.value
    })
  }

  // Filter by search query
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    logs = logs.filter(e => {
      const payload = e.payload as any
      return payload.message?.toLowerCase().includes(query)
    })
  }

  return logs
})

// Auto-scroll on new logs
watch(
  () => store.events.length,
  async () => {
    if (autoScroll.value && logContainer.value) {
      await nextTick()
      logContainer.value.scrollTop = logContainer.value.scrollHeight
    }
  }
)

// Log level styling
function getLogLevelClass(level: string) {
  switch (level) {
    case 'error':
    case 'critical':
      return 'text-red-600 bg-red-50'
    case 'warning':
      return 'text-yellow-600 bg-yellow-50'
    case 'info':
      return 'text-blue-600 bg-blue-50'
    case 'debug':
      return 'text-gray-600 bg-gray-50'
    default:
      return 'text-gray-800'
  }
}

// Format timestamp
function formatTimestamp(timestamp: string) {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('en-US', {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// Clear logs
function clearLogs() {
  store.events.splice(0, store.events.length)
}
</script>

<template>
  <div class="log-viewer">
    <div class="header flex justify-between items-center mb-4">
      <h2 class="text-2xl font-bold">Event Stream</h2>
      <div class="controls flex gap-2">
        <!-- Auto-scroll toggle -->
        <label class="flex items-center gap-2 text-sm">
          <input v-model="autoScroll" type="checkbox" class="rounded" />
          <span>Auto-scroll</span>
        </label>

        <!-- Clear button -->
        <button
          @click="clearLogs"
          class="bg-gray-500 hover:bg-gray-600 text-white px-3 py-1 rounded text-sm"
        >
          Clear
        </button>
      </div>
    </div>

    <!-- Filters -->
    <div class="filters flex gap-4 mb-4">
      <!-- Log level filter -->
      <div class="filter-group">
        <label class="text-sm font-medium mr-2">Level:</label>
        <select
          v-model="selectedLogLevel"
          class="border rounded px-2 py-1 text-sm"
        >
          <option value="all">All</option>
          <option value="debug">Debug</option>
          <option value="info">Info</option>
          <option value="warning">Warning</option>
          <option value="error">Error</option>
          <option value="critical">Critical</option>
        </select>
      </div>

      <!-- Search -->
      <div class="filter-group flex-1">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search logs..."
          class="w-full border rounded px-3 py-1 text-sm"
        />
      </div>
    </div>

    <!-- Log stats -->
    <div class="log-stats flex gap-4 mb-4 text-sm">
      <span class="text-gray-600">Total Events: {{ store.events.length }}</span>
      <span class="text-gray-600">Showing: {{ filteredLogs.length }}</span>
      <span class="text-gray-600">Session: {{ store.sessionId || 'None' }}</span>
    </div>

    <!-- Log container -->
    <div
      ref="logContainer"
      class="log-container bg-gray-900 text-gray-100 rounded-lg p-4 h-96 overflow-y-auto font-mono text-sm"
    >
      <div v-if="filteredLogs.length === 0" class="text-center text-gray-500 py-8">
        No log entries to display
      </div>

      <div
        v-for="(event, index) in filteredLogs"
        :key="`${event.timestamp}-${index}`"
        class="log-entry py-1 border-b border-gray-800 hover:bg-gray-800 transition-colors"
        :class="getLogLevelClass((event.payload as any).level)"
      >
        <span class="timestamp text-gray-500 mr-2">
          {{ formatTimestamp(event.timestamp) }}
        </span>
        <span class="level font-semibold mr-2 uppercase">
          [{{ (event.payload as any).level }}]
        </span>
        <span v-if="(event.payload as any).source" class="source text-gray-400 mr-2">
          ({{ (event.payload as any).source }})
        </span>
        <span class="message">
          {{ (event.payload as any).message }}
        </span>
      </div>
    </div>

    <!-- Connection status footer -->
    <div class="footer mt-4 flex justify-between items-center text-sm">
      <div class="ws-status">
        <span :class="{
          'text-green-500': store.wsStatus === 'connected',
          'text-yellow-500': store.wsStatus === 'connecting',
          'text-red-500': store.wsStatus === 'error',
          'text-gray-500': store.wsStatus === 'disconnected'
        }">
          ● {{ store.wsStatus.toUpperCase() }}
        </span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.log-container {
  scrollbar-width: thin;
  scrollbar-color: #4B5563 #1F2937;
}

.log-container::-webkit-scrollbar {
  width: 8px;
}

.log-container::-webkit-scrollbar-track {
  background: #1F2937;
}

.log-container::-webkit-scrollbar-thumb {
  background: #4B5563;
  border-radius: 4px;
}

.log-container::-webkit-scrollbar-thumb:hover {
  background: #6B7280;
}

.log-entry {
  font-size: 0.875rem;
  line-height: 1.5;
}
</style>

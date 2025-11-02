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

// Scroll to bottom manually
async function scrollToBottom() {
  if (logContainer.value) {
    await nextTick()
    logContainer.value.scrollTop = logContainer.value.scrollHeight
  }
}
</script>

<template>
  <div
    class="log-viewer bg-white rounded shadow p-3 h-[500px] flex flex-col transition-shadow duration-500"
    :class="{
      'logs-running-glow': store.isResearchRunning && filteredLogs.length > 0,
      'logs-completed-glow': store.totalFilesGenerated > 0 && !store.isResearchRunning
    }"
  >
    <div class="header flex justify-between items-center mb-2">
      <h2 class="text-sm font-bold">Logs</h2>
      <div class="controls flex gap-1">
        <!-- Auto-scroll toggle -->
        <label class="flex items-center gap-1 text-xs">
          <input v-model="autoScroll" type="checkbox" class="rounded w-3 h-3" />
          <span>Auto</span>
        </label>

        <!-- Clear button -->
        <button
          @click="clearLogs"
          class="bg-gray-500 hover:bg-gray-600 text-white px-2 py-1 rounded text-xs"
        >
          Clear
        </button>
      </div>
    </div>

    <!-- Compact Filters -->
    <div class="filters flex gap-2 mb-2">
      <!-- Log level filter -->
      <select
        v-model="selectedLogLevel"
        class="border rounded px-1.5 py-0.5 text-xs flex-1"
      >
        <option value="all">All Levels</option>
        <option value="debug">Debug</option>
        <option value="info">Info</option>
        <option value="warning">Warning</option>
        <option value="error">Error</option>
      </select>
    </div>

    <!-- Log container -->
    <div
      ref="logContainer"
      class="log-container bg-gray-900 text-gray-100 rounded p-2 flex-1 overflow-y-auto font-mono text-[10px]"
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

      <!-- Scroll to bottom button -->
      <button
        @click="scrollToBottom"
        class="bg-blue-500 hover:bg-blue-600 text-white px-2 py-1 rounded text-xs font-medium flex items-center gap-1"
        title="Jump to the latest log entries"
      >
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="12" y1="5" x2="12" y2="19"></line>
          <polyline points="19 12 12 19 5 12"></polyline>
        </svg>
        Bottom
      </button>
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
  font-size: 0.75rem;
  line-height: 1.4;
}

/* Subtle orange/yellow glow during research */
.logs-running-glow {
  box-shadow: 0 0 20px rgba(251, 191, 36, 0.3), 0 0 40px rgba(251, 191, 36, 0.15);
}

/* Subtle green glow when research completed */
.logs-completed-glow {
  box-shadow: 0 0 20px rgba(34, 197, 94, 0.3), 0 0 40px rgba(34, 197, 94, 0.15);
}
</style>

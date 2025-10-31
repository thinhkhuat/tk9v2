<script setup lang="ts">
import { useSessionStore } from '@/stores/sessionStore'
import { computed } from 'vue'

const store = useSessionStore()

// Computed properties for component display
const progressPercentage = computed(() => `${store.overallProgress}%`)
const statusColor = computed(() => {
  switch (store.overallStatus) {
    case 'running':
      return 'bg-blue-500'
    case 'completed':
      return 'bg-green-500'
    case 'failed':
      return 'bg-red-500'
    default:
      return 'bg-gray-400'
  }
})
</script>

<template>
  <div class="progress-tracker">
    <h2 class="text-2xl font-bold mb-4">Agent Pipeline</h2>

    <!-- Status Summary -->
    <div class="status-summary grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <div class="stat-card bg-white p-4 rounded-lg shadow">
        <div class="text-sm text-gray-600">Current Stage</div>
        <div class="text-lg font-semibold">{{ store.currentStage }}</div>
      </div>

      <div class="stat-card bg-white p-4 rounded-lg shadow">
        <div class="text-sm text-gray-600">Status</div>
        <div class="text-lg font-semibold capitalize">{{ store.overallStatus }}</div>
      </div>

      <div class="stat-card bg-white p-4 rounded-lg shadow">
        <div class="text-sm text-gray-600">Agents</div>
        <div class="text-lg font-semibold">
          {{ store.agentsCompleted }} / {{ store.agentsTotal }}
        </div>
      </div>

      <div class="stat-card bg-white p-4 rounded-lg shadow">
        <div class="text-sm text-gray-600">Files</div>
        <div class="text-lg font-semibold">{{ store.totalFilesGenerated }}</div>
      </div>
    </div>

    <!-- Error Display -->
    <div v-if="store.hasErrors" class="error-banner bg-red-100 border border-red-400 text-red-700 p-4 rounded-lg mt-6">
      <h3 class="font-semibold mb-2">⚠️ Error Detected</h3>
      <p v-if="store.lastError">{{ store.lastError.message }}</p>
      <div v-if="store.failedAgents.length > 0" class="mt-2">
        <p class="text-sm">Failed agents: {{ store.failedAgents.map(a => a.agent_name).join(', ') }}</p>
      </div>
      <button
        @click="store.clearError"
        class="mt-2 bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded text-sm"
      >
        Clear Error
      </button>
    </div>
  </div>
</template>

<style scoped>
.progress-tracker {
  /* Component container styles */
}

.agent-card {
  transition: all 0.3s ease;
}

.agent-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.agent-card.active {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.9;
  }
}
</style>

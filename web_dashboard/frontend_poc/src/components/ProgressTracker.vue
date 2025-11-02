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
    <!-- Error Display (Compact) -->
    <div v-if="store.hasErrors" class="error-banner bg-red-100 border border-red-400 text-red-700 p-2 rounded">
      <h3 class="font-semibold text-xs mb-1">⚠️ Error</h3>
      <p v-if="store.lastError" class="text-xs">{{ store.lastError.message }}</p>
      <div v-if="store.failedAgents.length > 0" class="mt-1">
        <p class="text-[10px]">Failed: {{ store.failedAgents.map(a => a.agent_name).join(', ') }}</p>
      </div>
      <button
        @click="store.clearError"
        class="mt-1 bg-red-500 hover:bg-red-600 text-white px-2 py-1 rounded text-xs"
      >
        Clear
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

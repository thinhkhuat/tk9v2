<script setup lang="ts">
import { computed, ref } from 'vue'
import type { AgentUpdatePayload } from '@/types/events'

const props = defineProps<{
  agent: AgentUpdatePayload
}>()

// Expandable details (Phase 4: Interactive cards)
const isExpanded = ref(false)

// Human-friendly workflow step names
const WORKFLOW_STEP_NAMES: Record<string, string> = {
  'Browser': 'Initial Research',
  'Editor': 'Planning',
  'Researcher': 'Parallel Research',
  'Writer': 'Writing',
  'Translator': 'Translation',
  'Publisher': 'Publishing',
  'Orchestrator': 'Orchestrator'
}

const displayName = computed(() => {
  return WORKFLOW_STEP_NAMES[props.agent.agent_name] || props.agent.agent_name
})

const statusStyles = computed(() => {
  switch (props.agent.status) {
    case 'running':
      return {
        bgColor: 'bg-yellow-50 border-yellow-500 running-glow',
        textColor: 'text-yellow-800',
        icon: '🔄'
      }
    case 'completed':
      return {
        bgColor: 'bg-green-50 border-green-500',
        textColor: 'text-green-800',
        icon: '✅'
      }
    case 'error':
      return {
        bgColor: 'bg-red-50 border-red-500',
        textColor: 'text-red-800',
        icon: '❌'
      }
    case 'pending':
    default:
      return {
        bgColor: 'bg-gray-50 border-gray-300',
        textColor: 'text-gray-500',
        icon: '⏳'
      }
  }
})

function toggleDetails() {
  isExpanded.value = !isExpanded.value
}
</script>

<template>
  <div
    class="p-1.5 rounded border-2 transition-all duration-300 w-28 text-center cursor-pointer hover:shadow"
    :class="statusStyles.bgColor"
    @click="toggleDetails"
  >
    <!-- Workflow Step Name -->
    <h3 class="font-semibold text-xs truncate" :class="statusStyles.textColor">
      {{ displayName }}
    </h3>

    <!-- Status Badge -->
    <div class="text-[10px] capitalize mt-0.5" :class="statusStyles.textColor">
      {{ statusStyles.icon }} {{ agent.status }}
    </div>

    <!-- Expandable Details -->
    <div v-if="isExpanded" class="mt-2 pt-2 border-t border-gray-300">
      <p class="text-[10px] text-left" :class="statusStyles.textColor">
        {{ agent.message }}
      </p>
    </div>
  </div>
</template>

<style scoped>
.running-glow {
  box-shadow: 0 4px 6px -1px rgba(234, 179, 8, 0.4), 0 2px 4px -1px rgba(234, 179, 8, 0.3);
}
</style>

<!--
  AgentCard - Visual representation of a single agent in the pipeline
  Phase 5: Agent Flow Visualization with real-time state indicators
  Features:
  - Color-coded status (pending/running/completed/error)
  - Click to expand for detailed message
  - Smooth transitions and hover effects
  - Bright yellow glow for running execution agents (yellow-500)
  - Distinct from orange Orchestrator to differentiate overseer vs workers
-->

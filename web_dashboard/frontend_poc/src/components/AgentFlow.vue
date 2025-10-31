<script setup lang="ts">
import { useSessionStore } from '@/stores/sessionStore'
import AgentCard from './AgentCard.vue'
import { computed } from 'vue'

const store = useSessionStore()

// Separate orchestrator from execution agents
const orchestratorAgent = computed(() => {
  return store.orderedAgents.find(a => a.agent_name === 'Orchestrator')
})

const executionAgents = computed(() => {
  return store.orderedAgents.filter(a => a.agent_name !== 'Orchestrator')
})
</script>

<template>
  <div class="bg-white p-6 rounded-lg shadow-md">
    <h2 class="text-xl font-bold mb-6 text-gray-700">
      🤖 Agent Pipeline
    </h2>

    <!-- Two-Tier Layout with Grid for Proper Alignment -->
    <div class="pipeline-container">
      <!-- Orchestrator Agent (Supervisor) - Spans 3 columns to center over 6 agents -->
      <div class="orchestrator-tier mb-4">
        <!-- Grid container for orchestrator (centered over middle of 6-agent grid) -->
        <div class="grid grid-cols-6 gap-2">
          <!-- Empty spacer for first 1.5 columns -->
          <div class="col-span-2"></div>

          <!-- Orchestrator in middle 3 columns (centered) -->
          <div class="col-span-2 flex flex-col items-center">
            <AgentCard v-if="orchestratorAgent" :agent="orchestratorAgent" class="orchestrator-card" />

            <!-- Supervision Label -->
            <div class="text-center mt-2 mb-2 text-xs text-gray-500 font-medium">
              ⬇ Oversees Research Pipeline ⬇
            </div>
          </div>

          <!-- Empty spacer for last 1.5 columns -->
          <div class="col-span-2"></div>
        </div>
      </div>

      <!-- Execution Pipeline (6 Agents in Grid) -->
      <div class="execution-tier">
        <div class="grid grid-cols-6 gap-2">
          <template v-for="(agent, index) in executionAgents" :key="agent.agent_id">
            <!-- Agent Card Column -->
            <div class="flex flex-col items-center">
              <AgentCard :agent="agent" />

              <!-- Arrow to next agent (except last) -->
              <div v-if="index < executionAgents.length - 1"
                   class="absolute"
                   :style="{ left: '100%', top: '50%', transform: 'translate(8px, -50%)' }">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" class="text-gray-400">
                  <path d="M5 12H19M19 12L12 5M19 12L12 19"
                        stroke="currentColor"
                        stroke-width="2"
                        stroke-linecap="round"
                        stroke-linejoin="round"/>
                </svg>
              </div>
            </div>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.orchestrator-card {
  box-shadow: 0 4px 6px -1px rgba(249, 115, 22, 0.4), 0 2px 4px -1px rgba(249, 115, 22, 0.3);
  border: 2px solid #f97316;
}
</style>

<!--
  AgentFlow - Container for the agent pipeline visualization
  Phase 5: Two-Tier Architecture Visualization

  Features:
  - Orchestrator Agent positioned at top (supervisor tier)
  - 6 Execution Agents in horizontal pipeline below (Browser → Editor → Researcher → Writer → Publisher → Translator)
  - Visual connection lines showing Orchestrator oversees all agents
  - Distinct styling for Orchestrator (blue border/shadow)
  - Horizontal scroll for execution pipeline
  - Arrow connectors between execution agents
  - Real-time updates via reactive store

  Layout:
  ┌─────────────────────────────────────────────┐
  │           [Orchestrator Agent]              │ ← Supervisor Tier
  │        "Oversees Research Pipeline"         │
  │         ╱  │  │  │  │  │  ╲                 │
  │       ╱    │  │  │  │  │    ╲               │
  └──────────────────────────────────────────────┘
         │    │  │  │  │  │    │
  ┌─────────────────────────────────────────────┐
  │ [Browser]→[Editor]→[Researcher]→[Writer]→   │ ← Execution Tier
  │ →[Publisher]→[Translator]                   │
  └─────────────────────────────────────────────┘
-->

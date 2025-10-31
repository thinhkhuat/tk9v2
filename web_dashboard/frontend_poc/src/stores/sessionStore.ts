/**
 * Production Pinia store for research session management.
 * Handles WebSocket connection, event processing, and state updates.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  WebSocketEvent,
  AgentUpdatePayload,
  FileGeneratedPayload,
  ResearchStatusPayload,
  LogPayload,
  ErrorPayload,
  AgentStatus,
  ResearchStatus
} from '@/types/events'

export const useSessionStore = defineStore('session', () => {
  // ============================================================================
  // State
  // ============================================================================

  const sessionId = ref<string | null>(null)
  const wsStatus = ref<'disconnected' | 'connecting' | 'connected' | 'error'>('disconnected')

  // Agent states (map of agent_id → state)
  const agents = ref<Map<string, AgentUpdatePayload>>(new Map())

  // Event log (circular buffer with max size)
  const events = ref<WebSocketEvent[]>([])
  const maxEvents = 1000 // Keep last 1000 events

  // Files generated during research
  const files = ref<FileGeneratedPayload[]>([])

  // Overall research progress
  const overallProgress = ref(0)
  const overallStatus = ref<ResearchStatus>('initializing')
  const currentStage = ref<string>('Idle')
  const agentsCompleted = ref(0)
  const agentsTotal = ref(8)

  // Error state
  const lastError = ref<ErrorPayload | null>(null)

  // WebSocket instance
  let ws: WebSocket | null = null

  // ============================================================================
  // Computed Properties
  // ============================================================================

  const activeAgent = computed(() => {
    return Array.from(agents.value.values()).find(a => a.status === 'running')
  })

  const completedAgents = computed(() => {
    return Array.from(agents.value.values()).filter(a => a.status === 'completed')
  })

  const pendingAgents = computed(() => {
    return Array.from(agents.value.values()).filter(a => a.status === 'pending')
  })

  const failedAgents = computed(() => {
    return Array.from(agents.value.values()).filter(a => a.status === 'error')
  })

  const isResearchRunning = computed(() => {
    return overallStatus.value === 'running'
  })

  const isResearchCompleted = computed(() => {
    return overallStatus.value === 'completed'
  })

  const hasErrors = computed(() => {
    return lastError.value !== null || failedAgents.value.length > 0
  })

  const recentLogs = computed(() => {
    return events.value
      .filter(e => e.event_type === 'log')
      .slice(-50) // Last 50 log entries
  })

  const totalFilesGenerated = computed(() => {
    return files.value.length
  })

  const totalFileSize = computed(() => {
    return files.value.reduce((sum, f) => sum + f.size_bytes, 0)
  })

  // ============================================================================
  // Actions
  // ============================================================================

  function connect(sessionIdParam: string) {
    sessionId.value = sessionIdParam
    wsStatus.value = 'connecting'

    // Close existing connection if any
    if (ws) {
      ws.close()
    }

    // Create new WebSocket connection
    ws = new WebSocket(`ws://localhost:12656/ws/${sessionIdParam}`)

    ws.onopen = () => {
      wsStatus.value = 'connected'
      console.log('✅ WebSocket connected')
    }

    ws.onmessage = (event) => {
      try {
        const data: WebSocketEvent = JSON.parse(event.data)
        handleEvent(data)
      } catch (error) {
        console.error('Error parsing WebSocket message:', error)
      }
    }

    ws.onerror = (error) => {
      wsStatus.value = 'error'
      console.error('❌ WebSocket error:', error)
    }

    ws.onclose = (event) => {
      wsStatus.value = 'disconnected'
      console.log('🔌 WebSocket disconnected', event.code, event.reason)

      // Auto-reconnect if connection was not closed cleanly
      if (!event.wasClean && sessionId.value) {
        console.log('🔄 Attempting to reconnect in 3 seconds...')
        setTimeout(() => {
          if (sessionId.value) {
            connect(sessionId.value)
          }
        }, 3000)
      }
    }
  }

  function disconnect() {
    if (ws) {
      ws.close()
      ws = null
    }
    wsStatus.value = 'disconnected'
  }

  function handleEvent(event: WebSocketEvent) {
    // Add to event log (circular buffer)
    events.value.push(event)
    if (events.value.length > maxEvents) {
      events.value = events.value.slice(-maxEvents)
    }

    // Handle by event type - TypeScript automatically narrows the payload type!
    switch (event.event_type) {
      case 'agent_update':
        // TypeScript knows event.payload is AgentUpdatePayload here
        handleAgentUpdate(event.payload)
        break
      case 'file_generated':
        // TypeScript knows event.payload is FileGeneratedPayload here
        handleFileGenerated(event.payload)
        break
      case 'research_status':
        // TypeScript knows event.payload is ResearchStatusPayload here
        handleResearchStatus(event.payload)
        break
      case 'error':
        // TypeScript knows event.payload is ErrorPayload here
        handleError(event.payload)
        break
      case 'log':
        // TypeScript knows event.payload is LogPayload here
        handleLog(event.payload)
        break
      case 'connection_status':
        // Connection status handled separately if needed
        console.log('Connection status:', event.payload.status)
        break
      case 'files_ready':
        // Files ready - might trigger UI notification
        console.log(`📁 ${event.payload.file_count} files ready for download`)
        break
    }
  }

  function handleAgentUpdate(payload: AgentUpdatePayload) {
    // Update agent state
    agents.value.set(payload.agent_id, payload)

    // Update overall progress (average of all agents)
    const allAgents = Array.from(agents.value.values())
    if (allAgents.length > 0) {
      const avgProgress = allAgents.reduce((sum, a) => sum + a.progress, 0) / allAgents.length
      overallProgress.value = Math.round(avgProgress)
    }

    console.log(`🤖 Agent ${payload.agent_name}: ${payload.status} (${payload.progress}%)`)
  }

  function handleFileGenerated(payload: FileGeneratedPayload) {
    files.value.push(payload)
    console.log(`📄 File generated: ${payload.filename} (${payload.size_bytes} bytes)`)
  }

  function handleResearchStatus(payload: ResearchStatusPayload) {
    overallStatus.value = payload.overall_status
    overallProgress.value = Math.round(payload.progress)
    if (payload.current_stage) {
      currentStage.value = payload.current_stage
    }
    agentsCompleted.value = payload.agents_completed
    agentsTotal.value = payload.agents_total

    console.log(`📊 Research status: ${payload.overall_status} (${payload.progress}%)`)
  }

  function handleLog(payload: LogPayload) {
    // Logs are stored in events array
    // Could add specific handling here if needed
    if (payload.level === 'error' || payload.level === 'critical') {
      console.error(`[${payload.level.toUpperCase()}] ${payload.message}`)
    }
  }

  function handleError(payload: ErrorPayload) {
    lastError.value = payload
    console.error(`❌ Error: ${payload.message}`, payload.details)

    // Update overall status if error is not recoverable
    if (!payload.recoverable) {
      overallStatus.value = 'failed'
    }
  }

  function clearError() {
    lastError.value = null
  }

  function reset() {
    // Reset all state
    sessionId.value = null
    agents.value.clear()
    events.value = []
    files.value = []
    overallProgress.value = 0
    overallStatus.value = 'initializing'
    currentStage.value = 'Idle'
    agentsCompleted.value = 0
    agentsTotal.value = 8
    lastError.value = null

    disconnect()
  }

  async function rehydrate(sessionIdParam: string) {
    /**
     * Re-hydrate store from server state (for reconnection after page refresh)
     */
    try {
      // Fetch current session state from server
      const { api } = await import('@/services/api')
      const state = await api.getSessionState(sessionIdParam)

      sessionId.value = sessionIdParam

      // Re-populate files
      if (state.files && state.files.length > 0) {
        files.value = state.files.map((f: any) => ({
          file_id: f.file_id || f.filename,
          filename: f.filename,
          file_type: f.file_type,
          language: f.language,
          size_bytes: f.size_bytes,
          path: f.download_url
        }))
      }

      // Set overall status based on CLI status
      if (state.status === 'completed') {
        overallStatus.value = 'completed'
        overallProgress.value = 100
        currentStage.value = 'Research completed'
      } else if (state.status === 'running') {
        overallStatus.value = 'running'
        currentStage.value = 'Research in progress...'
      } else if (state.status === 'failed') {
        overallStatus.value = 'failed'
        lastError.value = {
          error_type: 'session_error',
          message: state.error || 'Session failed',
          recoverable: false
        }
      }

      console.log('✅ Store re-hydrated from server state:', state)

      // Now connect to WebSocket for real-time updates
      connect(sessionIdParam)
    } catch (error) {
      console.error('Failed to re-hydrate session:', error)
      // If session doesn't exist on server, clear localStorage
      localStorage.removeItem('tk9_session_id')
      throw error
    }
  }

  // ============================================================================
  // Return public API
  // ============================================================================

  return {
    // State
    sessionId,
    wsStatus,
    agents,
    events,
    files,
    overallProgress,
    overallStatus,
    currentStage,
    agentsCompleted,
    agentsTotal,
    lastError,

    // Computed
    activeAgent,
    completedAgents,
    pendingAgents,
    failedAgents,
    isResearchRunning,
    isResearchCompleted,
    hasErrors,
    recentLogs,
    totalFilesGenerated,
    totalFileSize,

    // Actions
    connect,
    disconnect,
    clearError,
    reset,
    rehydrate
  }
})

/**
 * Production Pinia store for research session management.
 * Handles WebSocket connection, event processing, and state updates.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useToast } from 'vue-toastification'
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

const toast = useToast()

// Agent pipeline order (Phase 4: Agent Flow Visualization)
// NOTE: Reviewer and Reviser are DISABLED in the backend workflow for performance optimization
// Full workflow: Browser → Editor → Researcher → Writer → Publisher → Translator → Orchestrator
const AGENT_PIPELINE_ORDER = [
  'Browser', 'Editor', 'Researcher', 'Writer',
  'Publisher', 'Translator', 'Orchestrator'
]

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
  const agentsTotal = ref(7)  // 7 active agents (Browser, Editor, Researcher, Writer, Publisher, Translator, Orchestrator)

  // Error state
  const lastError = ref<ErrorPayload | null>(null)

  // UI State Management (Phase 3)
  const isLoading = ref(true) // Start true for initial hydration check
  const isSubmitting = ref(false) // Track form submission state
  const appError = ref<string | null>(null) // App-level errors (API, network, etc.)

  // WebSocket instance
  let ws: WebSocket | null = null

  // ============================================================================
  // Computed Properties
  // ============================================================================

  // Phase 4: Agent flow visualization - ordered agents computed first (needed by other computeds)
  const orderedAgents = computed(() => {
    return AGENT_PIPELINE_ORDER.map(agentName => {
      // KEY FIX: Direct O(1) lookup using agent_name as key
      // This is much faster and more reliable than Array.from().find()
      const agentData = agents.value.get(agentName)

      // Return actual data or default pending state
      return agentData || {
        agent_id: agentName.toLowerCase(),
        agent_name: agentName,
        status: 'pending' as const,
        progress: null, // Phase 2: No artificial progress
        message: 'Waiting to start...'
      }
    })
  })

  // Summary statistics computed from orderedAgents (not raw agents Map)
  // This ensures cards and summary always match
  const activeAgent = computed(() => {
    return orderedAgents.value.find(a => a.status === 'running')
  })

  const runningAgents = computed(() => {
    return orderedAgents.value.filter(a => a.status === 'running')
  })

  const completedAgents = computed(() => {
    return orderedAgents.value.filter(a => a.status === 'completed')
  })

  const pendingAgents = computed(() => {
    return orderedAgents.value.filter(a => a.status === 'pending')
  })

  const failedAgents = computed(() => {
    return orderedAgents.value.filter(a => a.status === 'error')
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
    // Use environment variable or construct from current location
    const wsBaseUrl = import.meta.env.VITE_WS_BASE_URL || 
      (window.location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host
    ws = new WebSocket(`${wsBaseUrl}/ws/${sessionIdParam}`)

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
    // Update agent state - KEY FIX: Use agent_name as key (not agent_id)
    // This aligns with how orderedAgents computed property looks up agents
    agents.value.set(payload.agent_name, payload)

    // Update overall progress (average of agents with explicit progress)
    const allAgents = Array.from(agents.value.values())
    const agentsWithProgress = allAgents.filter(a => a.progress !== null)

    if (agentsWithProgress.length > 0) {
      const avgProgress = agentsWithProgress.reduce((sum, a) => sum + (a.progress || 0), 0) / agentsWithProgress.length
      overallProgress.value = Math.round(avgProgress)
    }

    const progressStr = payload.progress !== null ? `${payload.progress}%` : 'status update'
    console.log(`🤖 Agent ${payload.agent_name}: ${payload.status} (${progressStr})`)
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

    // Show toast notification on completion
    if (payload.overall_status === 'completed') {
      toast.success('🎉 Research completed successfully! Files are ready for download.')
    } else if (payload.overall_status === 'failed') {
      toast.error('❌ Research failed. Please check the error logs.')
    }
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
    agentsTotal.value = 7
    lastError.value = null

    disconnect()
  }

  async function startNewSession(subject: string, language: string) {
    /**
     * Start a new research session (Phase 3: centralized in store)
     */
    isSubmitting.value = true
    appError.value = null

    try {
      // Reset any previous session data
      reset()

      // Submit research via API
      const { api } = await import('@/services/api')
      const response = await api.submitResearch(subject, language)

      // Save session ID
      localStorage.setItem('tk9_session_id', response.session_id)
      sessionId.value = response.session_id

      // Connect WebSocket for real-time updates
      connect(response.session_id)

      console.log('✅ New research session started:', response.session_id)
      toast.success('Research started successfully!') // Phase 3: Success toast
    } catch (error) {
      console.error('Failed to submit research:', error)
      const errorMsg = 'There was a problem starting the research. Please try again.'
      appError.value = errorMsg
      toast.error(errorMsg) // Phase 3: Toast notification
    } finally {
      isSubmitting.value = false
    }
  }

  function initializeNew() {
    /**
     * Initialize a fresh state (no session to rehydrate)
     */
    reset()
    isLoading.value = false
  }

  async function rehydrate(sessionIdParam: string) {
    /**
     * Re-hydrate store from server state (for reconnection after page refresh)
     * Phase 3: Enhanced with proper loading/error states
     */
    isLoading.value = true
    appError.value = null

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
      const errorMsg = 'Failed to restore your previous session. Please start a new research project.'
      appError.value = errorMsg
      toast.error(errorMsg) // Phase 3: Toast notification
      // If session doesn't exist on server, clear localStorage
      localStorage.removeItem('tk9_session_id')
    } finally {
      isLoading.value = false
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
    // Phase 3: UI State
    isLoading,
    isSubmitting,
    appError,

    // Computed
    activeAgent,
    runningAgents,
    completedAgents,
    pendingAgents,
    failedAgents,
    isResearchRunning,
    isResearchCompleted,
    hasErrors,
    recentLogs,
    totalFilesGenerated,
    totalFileSize,
    // Phase 4: Agent flow visualization
    orderedAgents,

    // Actions
    connect,
    disconnect,
    clearError,
    reset,
    rehydrate,
    // Phase 3: New Actions
    startNewSession,
    initializeNew
  }
})

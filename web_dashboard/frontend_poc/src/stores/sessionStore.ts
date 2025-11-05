/**
 * Production Pinia store for research session management.
 * Handles WebSocket connection, event processing, and state updates.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useToast } from 'vue-toastification'
import { WS_RECONNECT_DELAY } from '@/config/api'
import { getNormalizedFileType } from '@/utils/file-display-utils'
import type {
  WebSocketEvent,
  AgentUpdatePayload,
  FileGeneratedPayload,
  ResearchStatusPayload,
  LogPayload,
  ErrorPayload,
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
  const researchSubject = ref<string>('') // Research topic/title for display
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
    // Research is only truly completed when:
    // 1. Overall status is 'completed'
    // 2. We have files in BOTH languages (English + translated)
    // This prevents premature "Research Completed!" banner when only English files exist

    if (overallStatus.value !== 'completed') {
      return false
    }

    // Count files by language
    const englishFiles = files.value.filter(f => f.language === 'en' || f.language === 'english')
    const translatedFiles = files.value.filter(f => f.language !== 'en' && f.language !== 'english')

    // True completion requires both language sets
    // If we have English files but no translations, research is still ongoing
    const hasBothLanguages = englishFiles.length > 0 && translatedFiles.length > 0
    const hasOnlyOneLanguage = files.value.length > 0 && (englishFiles.length === 0 || translatedFiles.length === 0)

    if (hasOnlyOneLanguage) {
      console.log(`⚠️ Partial completion: ${englishFiles.length} EN, ${translatedFiles.length} translated - waiting for translations`)
      return false
    }

    return hasBothLanguages
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
    // Use environment variable or construct from current location with backend port
    const wsBaseUrl = import.meta.env.VITE_WS_BASE_URL ||
      `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.hostname}:12689`
    ws = new WebSocket(`${wsBaseUrl}/ws/${sessionIdParam}`)

    ws.onopen = () => {
      wsStatus.value = 'connected'
      console.log(
        `✅ [${new Date().toISOString()}] WebSocket connected`,
        { sessionId: sessionIdParam.substring(0, 8), url: ws?.url }
      )
    }

    ws.onmessage = (event) => {
      try {
        const data: WebSocketEvent = JSON.parse(event.data)

        // HEARTBEAT: Respond to server pings
        if (data.type === 'ping') {
          ws?.send(JSON.stringify({
            type: 'pong',
            timestamp: new Date().toISOString()
          }))
          console.debug(`💓 Responded to ping from server`)
          return
        }

        // HEARTBEAT: Log pong responses from server
        if (data.type === 'pong') {
          console.debug(`💓 Received pong from server`)
          return
        }

        // DIAGNOSTIC LOGGING: Track received events
        const eventType = data.event_type
        const timestamp = new Date().toISOString()
        console.log(
          `📥 [${timestamp}] WebSocket received: ${eventType}`,
          {
            eventType,
            payloadSize: JSON.stringify(data.payload).length,
            sessionId: sessionId.value?.substring(0, 8)
          }
        )

        // Track event processing
        const startTime = performance.now()
        handleEvent(data)
        const duration = performance.now() - startTime

        if (duration > 100) {
          console.warn(
            `⚠️ Slow event processing: ${eventType} took ${duration.toFixed(2)}ms`
          )
        }
      } catch (error) {
        console.error('❌ Error parsing WebSocket message:', error, event.data)
      }
    }

    ws.onerror = (error) => {
      wsStatus.value = 'error'
      console.error(
        `❌ [${new Date().toISOString()}] WebSocket error:`,
        { sessionId: sessionId.value?.substring(0, 8), error, readyState: ws?.readyState }
      )
    }

    ws.onclose = (event) => {
      wsStatus.value = 'disconnected'
      console.log(
        `🔌 [${new Date().toISOString()}] WebSocket disconnected`,
        {
          sessionId: sessionId.value?.substring(0, 8),
          code: event.code,
          reason: event.reason,
          wasClean: event.wasClean
        }
      )

      // Auto-reconnect if connection was not closed cleanly
      if (!event.wasClean && sessionId.value) {
        console.log(
          `🔄 Attempting to reconnect in ${WS_RECONNECT_DELAY / 1000} seconds...`
        )
        setTimeout(() => {
          if (sessionId.value) {
            console.log(`🔄 Reconnecting to session ${sessionId.value.substring(0, 8)}...`)
            connect(sessionId.value)
          }
        }, WS_RECONNECT_DELAY)
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

    // CRITICAL FIX: Clear stale error state when real agent updates arrive
    // This handles duplicated sessions where initial state showed "failed"
    // but research actually started successfully
    if (lastError.value && lastError.value.error_type === 'session_error') {
      console.log('✅ Clearing stale session error - research is actually running')
      lastError.value = null
    }

    // If we were in failed state but now receiving agent updates, switch to running
    if (overallStatus.value === 'failed' && payload.status !== 'error') {
      console.log('✅ Overriding failed status - research is actually running')
      overallStatus.value = 'running'
    }

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
    // MIGRATION: Handle old events that don't have friendly_name
    // TODO: Remove this after all sessions use new backend
    if (!payload.friendly_name) {
      payload.friendly_name = generateFriendlyNameFallback(payload.filename)
      console.warn(`⚠️ Generated fallback friendly_name for ${payload.filename}`)
    }

    // DRY: Use shared utility for file type detection with fallback
    if (!payload.file_type || payload.file_type === 'undefined') {
      payload.file_type = getNormalizedFileType(payload.file_type, payload.filename)
      console.warn(`⚠️ Used fallback file_type detection for ${payload.filename}: ${payload.file_type}`)
    }

    files.value.push(payload)
    console.log(`📄 File generated: ${payload.filename} (${payload.size_bytes} bytes)`)
  }

  /**
   * TEMPORARY: Generate friendly_name for old events
   * This fallback handles transition period before backend update
   */
  function generateFriendlyNameFallback(uuidFilename: string): string {
    if (!uuidFilename || !uuidFilename.includes('.')) {
      return uuidFilename || 'unknown.txt'
    }

    const parts = uuidFilename.split('.')
    const extension = parts.length > 0 ? parts[parts.length - 1]!.toLowerCase() : 'txt'
    const namePart = parts.slice(0, -1).join('.')

    // Check if it has a language code suffix (e.g., "uuid_vi")
    if (namePart.includes('_')) {
      const lastPart = namePart.split('_').pop()
      if (lastPart && lastPart.length <= 3) {
        return `research_report_${lastPart}.${extension}`
      }
    }

    return `research_report.${extension}`
  }

  function handleResearchStatus(payload: ResearchStatusPayload) {
    overallStatus.value = payload.overall_status
    overallProgress.value = Math.round(payload.progress)
    if (payload.current_stage) {
      currentStage.value = payload.current_stage
    }
    agentsCompleted.value = payload.agents_completed
    agentsTotal.value = payload.agents_total

    // CRITICAL FIX: Clear stale error state when receiving real research status
    // This handles duplicated sessions where initial load showed "failed"
    // but research actually started successfully
    if (payload.overall_status === 'running' || payload.overall_status === 'initializing') {
      if (lastError.value && lastError.value.error_type === 'session_error') {
        console.log('✅ Clearing stale session error - received real research status')
        lastError.value = null
      }
    }

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
    researchSubject.value = ''
    agents.value.clear()
    events.value = []
    files.value = []
    overallProgress.value = 0
    overallStatus.value = 'initializing'
    currentStage.value = 'Idle'
    agentsCompleted.value = 0
    agentsTotal.value = 7
    lastError.value = null

    // CRITICAL FIX: Initialize all agents to pending state
    // This ensures the UI shows all agents in the pipeline from the start
    // WebSocket updates will override these as research progresses
    AGENT_PIPELINE_ORDER.forEach(agentName => {
      agents.value.set(agentName, {
        agent_id: agentName.toLowerCase(),
        agent_name: agentName,
        status: 'pending',
        progress: null,
        message: 'Waiting to start...'
      })
    })

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

      // Save session ID and subject
      localStorage.setItem('tk9_session_id', response.session_id)
      sessionId.value = response.session_id
      researchSubject.value = subject

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
      // Populate research subject from session state (title from research_sessions table)
      researchSubject.value = state.subject || state.title || ''

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

      // Re-populate historical logs from session.log file
      try {
        const logData = await api.getSessionLogEvents(sessionIdParam, 1000)
        if (logData.events && logData.events.length > 0) {
          events.value = logData.events
          console.log(`✅ Loaded ${logData.count} historical log events`)
        }
      } catch (error) {
        console.warn('Could not load historical logs:', error)
        // Not a critical error - continue without logs
      }

      // Set overall status based on CLI status
      if (state.status === 'completed') {
        overallStatus.value = 'completed'
        overallProgress.value = 100
        currentStage.value = 'Research completed'
        agentsCompleted.value = agentsTotal.value

        // Mark all agents as completed for historical sessions
        AGENT_PIPELINE_ORDER.forEach(agentName => {
          agents.value.set(agentName, {
            agent_id: agentName.toLowerCase(),
            agent_name: agentName,
            status: 'completed',
            progress: 100,
            message: 'Completed'
          })
        })
      } else if (state.status === 'running') {
        overallStatus.value = 'running'
        currentStage.value = 'Research in progress...'

        // CRITICAL FIX: Initialize all agents to pending state
        // This ensures they show in the UI even if they completed before WebSocket connected
        // WebSocket updates will override these states as they arrive
        AGENT_PIPELINE_ORDER.forEach(agentName => {
          agents.value.set(agentName, {
            agent_id: agentName.toLowerCase(),
            agent_name: agentName,
            status: 'pending',
            progress: null,
            message: 'Waiting to start...'
          })
        })
        console.log('✓ Initialized all agents to pending state - WebSocket will update them')
      } else if (state.status === 'failed') {
        overallStatus.value = 'failed'
        lastError.value = {
          error_type: 'session_error',
          message: state.error || 'Session failed',
          recoverable: false
        }
        // Mark all agents as error for failed sessions
        AGENT_PIPELINE_ORDER.forEach(agentName => {
          agents.value.set(agentName, {
            agent_id: agentName.toLowerCase(),
            agent_name: agentName,
            status: 'error',
            progress: null,
            message: 'Session failed'
          })
        })
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
    researchSubject,
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

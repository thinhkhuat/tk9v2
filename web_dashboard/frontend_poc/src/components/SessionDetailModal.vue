<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useSessionsStore, type ResearchSession } from '@/stores/sessionsStore'
import { useSessionStore } from '@/stores/sessionStore'
import { formatDate, formatAbsoluteDate, formatFileSize, getStatusColor } from '@/utils/formatters'
import WaitingExperience from './WaitingExperience/WaitingExperience.vue'
import FileList from './FileList.vue'
import FilePreviewModal from './FilePreviewModal.vue'
import LogViewer from './LogViewer.vue'
import ConfirmDialog, { type ConfirmVariant } from './ConfirmDialog.vue'
import type { ResearchStage } from './WaitingExperience/types'
import type { FileGeneratedPayload } from '@/types/events'
import { api, triggerFileDownload } from '@/services/api'

const props = defineProps<{
  session: ResearchSession
  isOpen: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'update'): void
}>()

const router = useRouter()
const store = useSessionsStore()
const sessionStore = useSessionStore()

// Tab state
type TabName = 'overview' | 'files' | 'logs' | 'metadata'
const activeTab = ref<TabName>('overview')

// Computed properties
const isArchived = computed(() => !!props.session.archived_at)
const parametersJson = computed(() =>
  props.session.parameters ? JSON.stringify(props.session.parameters, null, 2) : '{}'
)

// ============================================================================
// Waiting Experience Integration
// ============================================================================

/**
 * Determine if WaitingExperience should be shown
 * Show during active research execution
 */
const showWaitingExperience = computed(() => {
  const status = props.session.status
  return status === 'in_progress' || sessionStore.isResearchRunning
})

/**
 * Map string stage names to numeric stages (1-4) for WaitingExperience
 * TK9 workflow: Browser → Editor → Researcher → Writer → Publisher → Translator → Orchestrator
 *
 * Stage 1 (Initial Research): Browser agent
 * Stage 2 (Planning): Editor agent
 * Stage 3 (Parallel Research): Researcher + Writer + Publisher
 * Stage 4 (Writing): Translator + Orchestrator + finalization
 */
function mapStageNameToNumber(stageName: string): ResearchStage {
  const normalizedStage = stageName.toLowerCase()

  // Stage 1: Initial Research (Browser)
  if (normalizedStage.includes('browser') ||
      normalizedStage.includes('initial') ||
      normalizedStage.includes('searching')) {
    return 1
  }

  // Stage 2: Planning (Editor)
  if (normalizedStage.includes('editor') ||
      normalizedStage.includes('planning') ||
      normalizedStage.includes('organizing')) {
    return 2
  }

  // Stage 3: Parallel Research (Researcher, Writer, Publisher)
  if (normalizedStage.includes('researcher') ||
      normalizedStage.includes('writer') ||
      normalizedStage.includes('publisher') ||
      normalizedStage.includes('research') ||
      normalizedStage.includes('writing') ||
      normalizedStage.includes('parallel')) {
    return 3
  }

  // Stage 4: Finalization (Translator, Orchestrator)
  if (normalizedStage.includes('translator') ||
      normalizedStage.includes('orchestrator') ||
      normalizedStage.includes('finalizing') ||
      normalizedStage.includes('completing')) {
    return 4
  }

  // Default: Stage 1 if unknown
  return 1
}

/**
 * Get friendly stage name from numeric stage
 */
function getStageName(stage: ResearchStage): string {
  const stageNames: Record<ResearchStage, string> = {
    1: 'Initial Research',
    2: 'Planning',
    3: 'Parallel Research',
    4: 'Writing'
  }
  return stageNames[stage]
}

/**
 * Current research stage (1-4)
 */
const currentStage = computed<ResearchStage>(() => {
  if (!sessionStore.currentStage) return 1
  return mapStageNameToNumber(sessionStore.currentStage)
})

/**
 * Stage progress (0-100)
 * Uses overall progress from sessionStore
 */
const stageProgress = computed(() => {
  return sessionStore.overallProgress || 0
})

/**
 * Stage name for display
 */
const stageName = computed(() => {
  // Use actual stage name from store if available, otherwise derive from numeric stage
  if (sessionStore.currentStage && sessionStore.currentStage !== 'Idle') {
    return sessionStore.currentStage
  }
  return getStageName(currentStage.value)
})

/**
 * Active agent name
 */
const activeAgentName = computed(() => {
  return sessionStore.activeAgent?.agent_name || undefined
})

/**
 * Session status for WaitingExperience
 */
const sessionStatus = computed<'pending' | 'in_progress' | 'running' | 'completed' | 'failed' | 'cancelled'>(() => {
  if (sessionStore.isResearchCompleted) return 'completed'
  if (sessionStore.isResearchRunning) return 'running'
  if (sessionStore.hasErrors) return 'failed'
  return props.session.status
})

// ============================================================================
// Event Handlers
// ============================================================================

/**
 * Handle research completion from WaitingExperience
 */
function handleResearchComplete() {
  console.log('✅ Research completed via WaitingExperience')

  // Refresh session data
  emit('update')

  // Switch to files tab to show results
  activeTab.value = 'files'
}

/**
 * Handle research error from WaitingExperience
 */
function handleResearchError(error: Error) {
  console.error('❌ Research error:', error)

  // Refresh session data
  emit('update')

  // Switch to logs tab to show error details
  activeTab.value = 'logs'
}

/**
 * Handle "View Full Session" click
 * Reconstructs final state from historical session in the modal
 */
async function handleViewFullSession() {
  try {
    console.log(`📊 Reconstructing state for session ${props.session.id}...`)

    // Disconnect any existing WebSocket connection
    sessionStore.disconnect()

    // Rehydrate store with historical session state
    await sessionStore.rehydrate(props.session.id)

    console.log('✅ Session state reconstructed successfully')

    // Stay in modal - let WaitingExperience, FileList, LogViewer display the state
  } catch (error) {
    console.error('❌ Failed to reconstruct session state:', error)
    alert('Failed to load session details. Please try again.')
  }
}

// ============================================================================
// WebSocket Connection Management
// ============================================================================

/**
 * Connect to WebSocket when modal opens with active session
 */
watch(
  () => props.isOpen,
  (isOpen) => {
    if (isOpen && showWaitingExperience.value) {
      // Connect to WebSocket for real-time updates
      sessionStore.connect(props.session.id)
    } else if (isOpen && !showWaitingExperience.value) {
      // Historical/completed session: auto-rehydrate to load files list
      // Avoid requiring manual "View Full Session" click
      sessionStore.rehydrate(props.session.id)
    } else if (!isOpen) {
      // Disconnect when modal closes
      sessionStore.disconnect()
    }
  },
  { immediate: true }
)

/**
 * Cleanup on component unmount
 */
onUnmounted(() => {
  sessionStore.disconnect()
})

// Actions
async function handleDuplicate() {
  try {
    console.log(`🔄 Duplicating and auto-starting session ${props.session.id}...`)

    // Extract subject and language from current session
    const subject = props.session.title.replace(' (Copy)', '') // Remove " (Copy)" suffix if present
    const language = props.session.language || 'vi'

    // Submit new research (creates new session and auto-starts)
    const response = await api.submitResearch(subject, language)

    console.log(`✅ New research started: ${response.session_id}`)

    // Close modal
    emit('close')

    // Navigate to dashboard (home page) where user can see the new session starting
    router.push('/')
  } catch (error) {
    console.error('❌ Failed to duplicate and start research:', error)
    alert('Failed to start new research. Please try again.')
  }
}

async function handleArchive() {
  // Show confirmation dialog
  confirmDialogConfig.value = {
    title: 'Archive Session',
    message: `Are you sure you want to archive "${props.session.title}"? You can restore it later.`,
    confirmLabel: 'Archive',
    variant: 'warning',
    onConfirm: async () => {
      await store.archiveSession(props.session.id)
      emit('update')
      emit('close')
      showConfirmDialog.value = false
    }
  }
  showConfirmDialog.value = true
}

async function handleRestore() {
  await store.restoreSession(props.session.id)
  emit('update')
  emit('close')
}

async function handleDelete() {
  // Show confirmation dialog
  confirmDialogConfig.value = {
    title: 'Delete Session Permanently',
    message: `Are you sure you want to permanently delete "${props.session.title}"? This action cannot be undone!`,
    confirmLabel: 'Delete Permanently',
    variant: 'danger',
    onConfirm: async () => {
      await store.deleteSession(props.session.id)
      emit('update')
      emit('close')
      showConfirmDialog.value = false
    }
  }
  showConfirmDialog.value = true
}

function handleClose() {
  emit('close')
}

// Handle backdrop click
function handleBackdropClick(event: MouseEvent) {
  if (event.target === event.currentTarget) {
    handleClose()
  }
}

// Handle escape key
function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') {
    handleClose()
  }
}

// ============================================================================
// File Actions (Download & Preview)
// ============================================================================

// Preview modal state
const showPreviewModal = ref(false)
const fileToPreview = ref<FileGeneratedPayload | null>(null)

// ============================================================================
// Confirm Dialog State
// ============================================================================

const showConfirmDialog = ref(false)
const confirmDialogConfig = ref<{
  title: string
  message: string
  confirmLabel: string
  variant: ConfirmVariant
  onConfirm: () => void
}>({
  title: '',
  message: '',
  confirmLabel: 'Confirm',
  variant: 'warning',
  onConfirm: () => {}
})

// Download file handler (same as FileExplorer)
async function downloadFile(file: FileGeneratedPayload) {
  if (!props.session.id) return

  try {
    console.log(`Downloading ${file.filename}...`)

    const blob = await api.downloadFile(props.session.id, file.filename)

    // Save with backend-provided friendly name (with fallback)
    const downloadName = file.friendly_name || file.filename
    triggerFileDownload(blob, downloadName)
  } catch (error) {
    console.error('Download failed:', error)
    alert(`Failed to download ${file.filename}`)
  }
}

// Preview file handler (same as FileExplorer)
function previewFile(file: FileGeneratedPayload) {
  fileToPreview.value = file
  showPreviewModal.value = true
}

// Close preview modal
function closePreview() {
  showPreviewModal.value = false
  // Clear after animation
  setTimeout(() => {
    fileToPreview.value = null
  }, 300)
}

// ============================================================================
// Logs Tab - Download Functionality
// ============================================================================

// Check if logs are available
const hasLogs = computed(() => sessionStore.events.some(e => e.event_type === 'log'))

// Download logs file
async function downloadLogs() {
  try {
    console.log(`Downloading logs for session ${props.session.id}...`)

    const blob = await api.downloadSessionLogs(props.session.id)
    triggerFileDownload(blob, `${props.session.id}_session.log`)
  } catch (error) {
    console.error('Failed to download logs:', error)
    alert('Failed to download logs. The log file may not exist yet.')
  }
}
</script>

<template>
  <!-- Modal Backdrop -->
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="isOpen"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4"
        @click="handleBackdropClick"
        @keydown="handleKeydown"
      >
        <!-- Modal Container -->
        <div
          class="bg-white rounded-lg shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col"
          @click.stop
        >
          <!-- Header -->
          <div class="flex items-center justify-between p-6 border-b border-gray-200">
            <div class="flex-1 min-w-0 mr-4">
              <h2 class="text-2xl font-bold text-gray-900 truncate" :title="session.title">
                {{ session.title }}
              </h2>
              <div class="flex items-center gap-3 mt-2">
                <span
                  :class="getStatusColor(session.status)"
                  class="px-2 py-1 rounded text-xs font-medium capitalize"
                >
                  {{ session.status.replace('_', ' ') }}
                </span>
                <span v-if="isArchived" class="px-2 py-1 bg-gray-200 text-gray-700 text-xs font-semibold rounded">
                  Archived
                </span>
                <span v-if="session.language" class="px-2 py-1 bg-purple-100 text-purple-800 text-xs font-medium rounded uppercase">
                  {{ session.language }}
                </span>
              </div>
            </div>

            <!-- Close Button -->
            <button
              @click="handleClose"
              class="p-2 hover:bg-gray-100 rounded-full transition-colors flex-shrink-0"
              title="Close"
            >
              <svg class="w-6 h-6 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <!-- Tabs Navigation -->
          <div class="border-b border-gray-200">
            <nav class="flex -mb-px px-6" aria-label="Tabs">
              <button
                @click="activeTab = 'overview'"
                :class="[
                  activeTab === 'overview'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
                  'py-4 px-4 border-b-2 font-medium text-sm transition-colors'
                ]"
              >
                Overview
              </button>
              <button
                @click="activeTab = 'files'"
                :class="[
                  activeTab === 'files'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
                  'py-4 px-4 border-b-2 font-medium text-sm transition-colors'
                ]"
              >
                Files ({{ session.file_count || 0 }})
              </button>
              <button
                @click="activeTab = 'logs'"
                :class="[
                  activeTab === 'logs'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
                  'py-4 px-4 border-b-2 font-medium text-sm transition-colors'
                ]"
              >
                Logs
              </button>
              <button
                @click="activeTab = 'metadata'"
                :class="[
                  activeTab === 'metadata'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
                  'py-4 px-4 border-b-2 font-medium text-sm transition-colors'
                ]"
              >
                Metadata
              </button>
            </nav>
          </div>

          <!-- Tab Content (Scrollable) -->
          <div class="flex-1 overflow-y-auto p-6">
            <!-- Overview Tab -->
            <div v-if="activeTab === 'overview'" class="space-y-6">
              <!-- Waiting Experience Animation (During Active Research) -->
              <div v-if="showWaitingExperience" class="mb-8">
                <WaitingExperience
                  :session-id="session.id"
                  :current-stage="currentStage"
                  :stage-progress="stageProgress"
                  :stage-name="stageName"
                  :active-agent="activeAgentName"
                  :status="sessionStatus"
                  @complete="handleResearchComplete"
                  @error="handleResearchError"
                />
              </div>

              <!-- Session Information (Always Visible) -->
              <div class="bg-gray-50 rounded-lg p-4">
                <h3 class="text-lg font-semibold text-gray-900 mb-4">Session Information</h3>
                <dl class="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <dt class="text-sm font-medium text-gray-500">Session ID</dt>
                    <dd class="mt-1 text-sm text-gray-900 font-mono">{{ session.id }}</dd>
                  </div>
                  <div>
                    <dt class="text-sm font-medium text-gray-500">Status</dt>
                    <dd class="mt-1">
                      <span
                        :class="getStatusColor(session.status)"
                        class="px-2 py-1 rounded text-xs font-medium capitalize"
                      >
                        {{ session.status.replace('_', ' ') }}
                      </span>
                    </dd>
                  </div>
                  <div>
                    <dt class="text-sm font-medium text-gray-500">Created</dt>
                    <dd class="mt-1 text-sm text-gray-900">
                      {{ formatAbsoluteDate(session.created_at) }}
                      <span class="text-gray-500 ml-1">({{ formatDate(session.created_at) }})</span>
                    </dd>
                  </div>
                  <div>
                    <dt class="text-sm font-medium text-gray-500">Last Updated</dt>
                    <dd class="mt-1 text-sm text-gray-900">
                      {{ formatAbsoluteDate(session.updated_at) }}
                      <span class="text-gray-500 ml-1">({{ formatDate(session.updated_at) }})</span>
                    </dd>
                  </div>
                  <div v-if="session.archived_at">
                    <dt class="text-sm font-medium text-gray-500">Archived</dt>
                    <dd class="mt-1 text-sm text-gray-900">
                      {{ formatAbsoluteDate(session.archived_at) }}
                      <span class="text-gray-500 ml-1">({{ formatDate(session.archived_at) }})</span>
                    </dd>
                  </div>
                  <div>
                    <dt class="text-sm font-medium text-gray-500">Language</dt>
                    <dd class="mt-1 text-sm text-gray-900 uppercase">
                      {{ session.language || 'Not specified' }}
                    </dd>
                  </div>
                  <div>
                    <dt class="text-sm font-medium text-gray-500">File Count</dt>
                    <dd class="mt-1 text-sm text-gray-900">{{ session.file_count || 0 }} files</dd>
                  </div>
                  <div v-if="session.total_size_bytes">
                    <dt class="text-sm font-medium text-gray-500">Total Size</dt>
                    <dd class="mt-1 text-sm text-gray-900">{{ formatFileSize(session.total_size_bytes) }}</dd>
                  </div>
                </dl>
              </div>

              <!-- Research Parameters -->
              <div v-if="session.parameters" class="bg-gray-50 rounded-lg p-4">
                <h3 class="text-lg font-semibold text-gray-900 mb-4">Research Parameters</h3>
                <div class="space-y-2">
                  <div v-for="(value, key) in session.parameters" :key="key" class="flex items-start">
                    <dt class="text-sm font-medium text-gray-500 w-1/3">{{ key }}:</dt>
                    <dd class="text-sm text-gray-900 w-2/3">{{ value }}</dd>
                  </div>
                </div>
              </div>
            </div>

            <!-- Files Tab -->
            <div v-if="activeTab === 'files'">
              <div v-if="sessionStore.totalFilesGenerated > 0" class="space-y-4">
                <div class="flex justify-between items-center mb-4">
                  <h3 class="text-lg font-semibold text-gray-800">
                    Generated Files ({{ session.file_count || 0 }})
                  </h3>
                  <button
                    @click="handleViewFullSession"
                    class="text-sm text-blue-600 hover:text-blue-700 font-medium underline"
                  >
                    View Full Session →
                  </button>
                </div>

                <!-- DRY: Using shared FileList component with download/preview -->
                <div class="space-y-2 max-h-96 overflow-y-auto">
                  <FileList
                    :files="sessionStore.files"
                    variant="detailed"
                    :show-actions="true"
                    empty-message="No files generated yet"
                    @preview="previewFile"
                    @download="downloadFile"
                  />
                </div>

                <!-- Completion notice -->
                <div
                  v-if="sessionStore.isResearchCompleted"
                  class="bg-green-100 border border-green-400 text-green-800 p-3 rounded-lg mt-4"
                >
                  <p class="text-sm font-semibold">
                    ✅ Research completed! All {{ sessionStore.totalFilesGenerated }} files are ready.
                  </p>
                </div>
              </div>

              <!-- Empty state with custom SVG -->
              <div v-else class="text-center py-12">
                <svg class="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                </svg>
                <h3 class="text-lg font-semibold text-gray-700 mb-2">No Files Generated Yet</h3>
                <p class="text-gray-500">
                  Files will appear here in real-time as the research progresses
                </p>
              </div>
            </div>

            <!-- Logs Tab -->
            <div v-if="activeTab === 'logs'" class="space-y-4">
              <!-- Download Logs Button -->
              <div class="flex justify-between items-center">
                <h3 class="text-lg font-semibold text-gray-800">Execution Logs</h3>
                <button
                  @click="downloadLogs"
                  class="px-3 py-1.5 bg-blue-500 hover:bg-blue-600 text-white text-sm rounded flex items-center gap-2 transition-colors"
                  title="Download complete log file"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  Download Logs
                </button>
              </div>

              <!-- LogViewer Component -->
              <div v-if="hasLogs || showWaitingExperience" class="max-h-96 overflow-hidden">
                <LogViewer />
              </div>

              <!-- Empty State -->
              <div v-else class="text-center py-12">
                <svg class="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <h3 class="text-lg font-semibold text-gray-700 mb-2">No Logs Available</h3>
                <p class="text-gray-500">
                  Logs will appear here during active research sessions
                </p>
              </div>
            </div>

            <!-- Metadata Tab -->
            <div v-if="activeTab === 'metadata'">
              <div class="bg-gray-900 rounded-lg p-4 overflow-x-auto">
                <pre class="text-green-400 text-sm font-mono">{{ parametersJson }}</pre>
              </div>
              <div class="mt-4 text-sm text-gray-500">
                Full session metadata in JSON format
              </div>
            </div>
          </div>

          <!-- Footer Actions -->
          <div class="border-t border-gray-200 p-6 flex items-center justify-between bg-gray-50">
            <div class="flex items-center gap-2">
              <button
                @click="handleDuplicate"
                class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md font-medium transition-colors flex items-center gap-2"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
                Duplicate
              </button>

              <button
                v-if="!isArchived"
                @click="handleArchive"
                class="px-4 py-2 bg-yellow-500 hover:bg-yellow-600 text-white rounded-md font-medium transition-colors flex items-center gap-2"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
                </svg>
                Archive
              </button>

              <button
                v-else
                @click="handleRestore"
                class="px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-md font-medium transition-colors flex items-center gap-2"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Restore
              </button>

              <button
                @click="handleDelete"
                class="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-md font-medium transition-colors flex items-center gap-2"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                Delete
              </button>
            </div>

            <button
              @click="handleClose"
              class="px-6 py-2 bg-gray-200 hover:bg-gray-300 text-gray-800 rounded-md font-medium transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- File Preview Modal (same as FileExplorer) -->
    <FilePreviewModal
      :file="fileToPreview"
      :show="showPreviewModal"
      :session-id="session.id"
      @close="closePreview"
    />

    <!-- Confirm Dialog -->
    <ConfirmDialog
      :is-open="showConfirmDialog"
      :title="confirmDialogConfig.title"
      :message="confirmDialogConfig.message"
      :confirm-label="confirmDialogConfig.confirmLabel"
      :variant="confirmDialogConfig.variant"
      @confirm="confirmDialogConfig.onConfirm"
      @cancel="showConfirmDialog = false"
    />
  </Teleport>
</template>

<style scoped>
/* Modal transition animations */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .bg-white,
.modal-leave-active .bg-white {
  transition: transform 0.3s ease;
}

.modal-enter-from .bg-white,
.modal-leave-to .bg-white {
  transform: scale(0.95);
}
</style>

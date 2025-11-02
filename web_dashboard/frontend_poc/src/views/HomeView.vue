<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useSessionStore } from '../stores/sessionStore'
import { useAuthStore } from '../stores/authStore'
import { MIN_SUBJECT_LENGTH, MAX_SUBJECT_LENGTH } from '../config/validation'
import ProgressTracker from '../components/ProgressTracker.vue'
import LogViewer from '../components/LogViewer.vue'
import FileExplorer from '../components/FileExplorer.vue'
import AppSkeletonLoader from '../components/AppSkeletonLoader.vue'
import ErrorMessage from '../components/ErrorMessage.vue'
import AgentFlow from '../components/AgentFlow.vue'
import WaitingExperience from '../components/WaitingExperience/WaitingExperience.vue'
import type { ResearchStage } from '../components/WaitingExperience/types'

const route = useRoute()
const store = useSessionStore()
const authStore = useAuthStore()

// Form state
const researchSubject = ref('')
const researchLanguage = ref('vi')

// Initialize session on mount (auth already done by App.vue)
onMounted(async () => {
  try {
    // Wait for auth to be ready (should already be done by App.vue)
    if (authStore.isInitializing) {
      console.log('[HomeView] Waiting for auth to complete...')
      let attempts = 0
      while (authStore.isInitializing && attempts < 50) {
        await new Promise(resolve => setTimeout(resolve, 100))
        attempts++
      }
    }

    // Verify user is authenticated
    if (!authStore.isAuthenticated) {
      console.error('[HomeView] User not authenticated')
      store.appError = 'Authentication required. Please refresh the page.'
      return
    }

    console.log('[HomeView] Auth ready, user ID:', authStore.userId)

    // PRIORITY 1: Check for session ID in route params (from "View Full Details")
    const routeSessionId = route.params.id as string | undefined
    if (routeSessionId) {
      console.log(`[HomeView] Loading historical session from route: ${routeSessionId}`)
      store.rehydrate(routeSessionId)
      return
    }

    // PRIORITY 2: Check for existing research session in localStorage
    const savedSessionId = localStorage.getItem('tk9_session_id')
    if (savedSessionId) {
      console.log(`[HomeView] Re-hydrating research session: ${savedSessionId}`)
      store.rehydrate(savedSessionId)
    } else {
      // No session to rehydrate - initialize fresh
      console.log('[HomeView] No saved research session, initializing fresh')
      store.initializeNew()
    }
  } catch (err) {
    console.error('[HomeView] Initialization failed:', err)
    store.appError = 'Failed to initialize application. Please refresh the page.'
  }
})

// Character count (validation limits imported from config/validation.ts)
const subjectLength = computed(() => researchSubject.value.length)
const isSubjectValid = computed(() => {
  const length = researchSubject.value.trim().length
  return length >= MIN_SUBJECT_LENGTH && length <= MAX_SUBJECT_LENGTH
})

const subjectError = computed(() => {
  const length = researchSubject.value.trim().length
  if (length === 0) return null
  if (length < MIN_SUBJECT_LENGTH) {
    return `Minimum ${MIN_SUBJECT_LENGTH} characters required`
  }
  if (length > MAX_SUBJECT_LENGTH) {
    return `Maximum ${MAX_SUBJECT_LENGTH} characters allowed`
  }
  return null
})

async function submitResearch() {
  const trimmedSubject = researchSubject.value.trim()

  // Client-side validation
  if (!trimmedSubject) {
    store.appError = 'Please enter a research subject'
    return
  }

  if (trimmedSubject.length < MIN_SUBJECT_LENGTH) {
    store.appError = `Subject must be at least ${MIN_SUBJECT_LENGTH} characters`
    return
  }

  if (trimmedSubject.length > MAX_SUBJECT_LENGTH) {
    store.appError = `Subject must be at most ${MAX_SUBJECT_LENGTH} characters`
    return
  }

  // Call centralized store action
  await store.startNewSession(trimmedSubject, researchLanguage.value)

  // Clear form on success
  if (!store.appError) {
    researchSubject.value = ''
  }
}

function newResearch() {
  store.reset()
  localStorage.removeItem('tk9_session_id')
}

function handleRetry() {
  // Clear error and allow user to try again
  store.appError = null
}

// ============================================================================
// Waiting Experience Integration (Origami Animations + Quotes)
// ============================================================================

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
  if (!store.currentStage) return 1
  return mapStageNameToNumber(store.currentStage)
})

/**
 * Stage progress (0-100)
 */
const stageProgress = computed(() => {
  return store.overallProgress || 0
})

/**
 * Stage name for display
 */
const stageName = computed(() => {
  if (store.currentStage && store.currentStage !== 'Idle') {
    return store.currentStage
  }
  return getStageName(currentStage.value)
})

/**
 * Active agent name
 */
const activeAgentName = computed(() => {
  return store.activeAgent?.agent_name || undefined
})

/**
 * Session status for WaitingExperience
 */
const sessionStatus = computed<'pending' | 'in_progress' | 'running' | 'completed' | 'failed' | 'cancelled'>(() => {
  if (store.isResearchCompleted) return 'completed'
  if (store.isResearchRunning) return 'running'
  if (store.hasErrors) return 'failed'
  return 'in_progress'
})
</script>

<template>
  <div class="home-view">
    <!-- Show Skeleton Loader During Initial Load/Rehydration -->
    <div v-if="store.isLoading">
      <AppSkeletonLoader />
    </div>

    <!-- Show Error Message if Something Went Wrong -->
    <div v-else-if="store.appError">
      <ErrorMessage :message="store.appError" @retry="handleRetry" />
    </div>

    <!-- Show Main Application UI -->
    <div v-else>
      <!-- Research Form (shown when no active session) -->
      <div v-if="!store.sessionId" class="max-w-2xl mx-auto mb-8">
        <div class="bg-white rounded-lg shadow-md p-6">
          <h2 class="text-2xl font-bold mb-4">Start New Research</h2>

          <form @submit.prevent="submitResearch" class="space-y-4">
            <div>
              <div class="flex justify-between items-center mb-2">
                <label for="subject" class="block text-sm font-medium text-gray-700">
                  Research Subject
                </label>
                <span
                  :class="[
                    'text-xs font-medium',
                    subjectError ? 'text-red-600' :
                    subjectLength > 900 ? 'text-orange-600' : 'text-gray-500'
                  ]"
                >
                  {{ subjectLength }} / {{ MAX_SUBJECT_LENGTH }}
                </span>
              </div>
              <textarea
                id="subject"
                v-model="researchSubject"
                rows="3"
                :class="[
                  'w-full px-4 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                  subjectError ? 'border-red-500 focus:ring-red-500' : 'border-gray-300'
                ]"
                placeholder="Enter your research topic (3-1000 characters)..."
                :disabled="store.isSubmitting"
                :maxlength="MAX_SUBJECT_LENGTH + 100"
              />
              <p v-if="subjectError" class="mt-1 text-sm text-red-600">
                {{ subjectError }}
              </p>
              <p v-else class="mt-1 text-xs text-gray-500">
                Enter a detailed research question or topic (minimum 3 characters)
              </p>
            </div>

            <div>
              <label for="language" class="block text-sm font-medium text-gray-700 mb-2">
                Language
              </label>
              <select
                id="language"
                v-model="researchLanguage"
                class="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                :disabled="store.isSubmitting"
              >
                <option value="vi">Vietnamese</option>
                <option value="en">English</option>
                <option value="es">Spanish</option>
                <option value="fr">French</option>
              </select>
            </div>

            <button
              type="submit"
              class="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-md transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
              :disabled="store.isSubmitting || !isSubjectValid"
            >
              <span v-if="store.isSubmitting">Starting Research...</span>
              <span v-else-if="!isSubjectValid">Enter Valid Subject ({{ MIN_SUBJECT_LENGTH }}-{{ MAX_SUBJECT_LENGTH }} chars)</span>
              <span v-else>🚀 Start Research</span>
            </button>
          </form>
        </div>
      </div>

      <!-- Active Session Dashboard -->
      <div v-else class="space-y-3">
        <!-- Compact Session Header -->
        <div class="bg-white rounded shadow p-3 flex justify-between items-start">
          <div class="flex-1 min-w-0 pr-3">
            <h2 class="font-bold text-gray-800 whitespace-normal break-words session-title" :title="store.researchSubject || 'Research Session'">
              {{ store.researchSubject || 'Research Session' }}
            </h2>
            <p class="text-xs text-gray-600">{{ store.sessionId }}</p>
          </div>
          <button
            @click="newResearch"
            class="bg-red-500 hover:bg-red-600 text-white px-3 py-1.5 rounded text-sm font-semibold transition-colors flex-shrink-0 ml-3"
          >
            New Research
          </button>
        </div>

        <!-- Agent Flow & Waiting Experience Side-by-Side (Equal Width & Height) -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-3">
          <!-- Left Column - Agent Flow -->
          <div class="lg:col-span-1">
            <AgentFlow />
          </div>

          <!-- Right Column - Waiting Experience -->
          <div class="lg:col-span-1">
            <WaitingExperience
              v-if="store.overallStatus === 'initializing' || store.overallStatus === 'running' || store.isResearchRunning"
              :session-id="store.sessionId"
              :current-stage="currentStage"
              :stage-progress="stageProgress"
              :stage-name="stageName"
              :active-agent="activeAgentName"
              :status="sessionStatus"
            />
            <!-- Placeholder when not running -->
            <div
              v-else
              class="bg-white rounded-lg shadow p-3 h-full flex items-center justify-center text-gray-400"
            >
              <p class="text-sm">Waiting experience shown during research...</p>
            </div>
          </div>
        </div>

        <!-- Progress Tracker (Full Width) -->
        <ProgressTracker />

        <!-- Files and Logs Side-by-Side (Equal Width) -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-3">
          <!-- Left Column - Files -->
          <div class="lg:col-span-1">
            <FileExplorer />
          </div>

          <!-- Right Column - Logs -->
          <div class="lg:col-span-1">
            <LogViewer />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Responsive title sizing: reduces font size first, then wraps */
.session-title {
  /* clamp(minimum, preferred, maximum) */
  font-size: clamp(0.875rem, 2vw + 0.5rem, 1.125rem);
  /* 0.875rem = 14px minimum */
  /* 1.125rem = 18px maximum (text-lg) */
  line-height: 1.4;
}
</style>

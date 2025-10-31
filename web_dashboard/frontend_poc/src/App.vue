<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useSessionStore } from './stores/sessionStore'
import ProgressTracker from './components/ProgressTracker.vue'
import LogViewer from './components/LogViewer.vue'
import FileExplorer from './components/FileExplorer.vue'
import AppSkeletonLoader from './components/AppSkeletonLoader.vue'
import ErrorMessage from './components/ErrorMessage.vue'
import AgentFlow from './components/AgentFlow.vue' // Phase 4

const store = useSessionStore()

// Form state
const researchSubject = ref('')
const researchLanguage = ref('vi')

// Check for existing session on mount (Phase 3: Enhanced with proper loading)
onMounted(() => {
  const savedSessionId = localStorage.getItem('tk9_session_id')
  if (savedSessionId) {
    console.log(`Re-hydrating session: ${savedSessionId}`)
    store.rehydrate(savedSessionId)
  } else {
    // No session to rehydrate - initialize fresh
    store.initializeNew()
  }
})

async function submitResearch() {
  if (!researchSubject.value.trim()) {
    store.appError = 'Please enter a research subject'
    return
  }

  // Call centralized store action (Phase 3: refactored)
  await store.startNewSession(researchSubject.value, researchLanguage.value)

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
</script>

<template>
  <div class="app min-h-screen bg-gray-50">
    <!-- Header -->
    <header class="bg-gradient-to-r from-purple-600 to-blue-600 text-white shadow-lg">
      <div class="container mx-auto px-4 py-6">
        <h1 class="text-4xl font-bold">🎯 TK9 Deep Research Dashboard</h1>
        <p class="text-purple-100 mt-2">Real-time multi-agent research monitoring</p>
      </div>
    </header>

    <!-- Main Content -->
    <main class="container mx-auto px-4 py-8">
      <!-- PHASE 3: Conditional Rendering Based on Loading/Error State -->

      <!-- 1. Show Skeleton Loader During Initial Load/Rehydration -->
      <div v-if="store.isLoading">
        <AppSkeletonLoader />
      </div>

      <!-- 2. Show Error Message if Something Went Wrong -->
      <div v-else-if="store.appError">
        <ErrorMessage
          :message="store.appError"
          @retry="handleRetry"
        />
      </div>

      <!-- 3. Show Main Application UI -->
      <div v-else>
        <!-- Research Form (shown when no active session) -->
        <div v-if="!store.sessionId" class="max-w-2xl mx-auto mb-8">
          <div class="bg-white rounded-lg shadow-md p-6">
            <h2 class="text-2xl font-bold mb-4">Start New Research</h2>

            <form @submit.prevent="submitResearch" class="space-y-4">
              <div>
                <label for="subject" class="block text-sm font-medium text-gray-700 mb-2">
                  Research Subject
                </label>
                <input
                  id="subject"
                  v-model="researchSubject"
                  type="text"
                  class="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter your research topic..."
                  :disabled="store.isSubmitting"
                />
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
                :disabled="store.isSubmitting"
              >
                <span v-if="store.isSubmitting">Starting Research...</span>
                <span v-else>🚀 Start Research</span>
              </button>
            </form>
          </div>
        </div>

        <!-- Active Session Dashboard -->
        <div v-else class="space-y-6">
          <!-- Session Header -->
          <div class="bg-white rounded-lg shadow-md p-6 flex justify-between items-center">
            <div>
              <h2 class="text-2xl font-bold text-gray-800">Research Session</h2>
              <p class="text-sm text-gray-600 mt-1">Session ID: {{ store.sessionId }}</p>
            </div>
            <button
              @click="newResearch"
              class="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-md font-semibold transition-colors"
            >
              New Research
            </button>
          </div>

          <!-- PHASE 4: Agent Flow Visualization -->
          <AgentFlow />

          <!-- Dashboard Grid -->
          <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <!-- Left Column - Progress and Files -->
            <div class="lg:col-span-2 space-y-6">
              <ProgressTracker />
              <FileExplorer />
            </div>

            <!-- Right Column - Logs -->
            <div class="lg:col-span-1">
              <div class="sticky top-6">
                <LogViewer />
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- Footer -->
    <footer class="bg-gray-800 text-gray-300 mt-12">
      <div class="container mx-auto px-4 py-6 text-center">
        <p class="text-sm">
          TK9 Deep Research System | Powered by Multi-Agent AI | Version 2.0
        </p>
      </div>
    </footer>
  </div>
</template>

<style scoped>
/* Additional custom styles if needed */
</style>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useSessionStore } from './stores/sessionStore'
import { api } from './services/api'
import ProgressTracker from './components/ProgressTracker.vue'
import LogViewer from './components/LogViewer.vue'
import FileExplorer from './components/FileExplorer.vue'

const store = useSessionStore()

// Form state
const researchSubject = ref('')
const researchLanguage = ref('vi')
const isSubmitting = ref(false)

// Check for existing session on mount
onMounted(async () => {
  // Check localStorage for existing session
  const savedSessionId = localStorage.getItem('tk9_session_id')
  if (savedSessionId) {
    console.log(`Re-hydrating session: ${savedSessionId}`)
    try {
      await store.rehydrate(savedSessionId)
      console.log('✅ Session re-hydrated successfully')
    } catch (error) {
      console.error('Failed to re-hydrate session, starting fresh')
    }
  }
})

async function submitResearch() {
  if (!researchSubject.value.trim()) {
    alert('Please enter a research subject')
    return
  }

  isSubmitting.value = true

  try {
    const response = await api.submitResearch(researchSubject.value, researchLanguage.value)
    console.log('Research submitted:', response)

    // Save session ID to localStorage
    localStorage.setItem('tk9_session_id', response.session_id)

    // Connect to WebSocket for this session
    store.connect(response.session_id)

    // Clear form
    researchSubject.value = ''
  } catch (error) {
    console.error('Failed to submit research:', error)
    alert('Failed to submit research. Please try again.')
  } finally {
    isSubmitting.value = false
  }
}

function newResearch() {
  store.reset()
  localStorage.removeItem('tk9_session_id')
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
      <!-- Research Form -->
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
                :disabled="isSubmitting"
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
                :disabled="isSubmitting"
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
              :disabled="isSubmitting"
            >
              <span v-if="isSubmitting">Starting Research...</span>
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

        <!-- Dashboard Grid -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <!-- Left Column - Progress and Files -->
          <div class="lg:col-span-2 space-y-6">
            <!-- Progress Tracker -->
            <div class="bg-white rounded-lg shadow-md p-6">
              <ProgressTracker />
            </div>

            <!-- File Explorer -->
            <div class="bg-white rounded-lg shadow-md p-6">
              <FileExplorer />
            </div>
          </div>

          <!-- Right Column - Logs -->
          <div class="lg:col-span-1">
            <div class="bg-white rounded-lg shadow-md p-6 sticky top-6">
              <LogViewer />
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

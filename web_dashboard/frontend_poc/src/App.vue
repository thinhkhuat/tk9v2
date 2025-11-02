<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useAuthStore } from '@/stores/authStore'
import AnonymousSessionBadge from './components/auth/AnonymousSessionBadge.vue'

const authStore = useAuthStore()
const isAuthReady = ref(false)
const authError = ref<string | null>(null)

// Initialize authentication before rendering app
onMounted(async () => {
  try {
    console.log('[App] Initializing authentication...')
    await authStore.initializeAuth()
    isAuthReady.value = true
    console.log('[App] Authentication ready')
  } catch (error) {
    console.error('[App] Authentication initialization failed:', error)
    authError.value = error instanceof Error ? error.message : 'Authentication failed'
  }
})
</script>

<template>
  <div class="app min-h-screen bg-gray-50 flex flex-col">
    <!-- Loading Screen (while auth initializes) -->
    <div v-if="!isAuthReady && !authError" class="flex items-center justify-center min-h-screen">
      <div class="text-center">
        <svg class="animate-spin h-16 w-16 text-purple-600 mx-auto mb-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <p class="text-xl font-semibold text-gray-700">Initializing Authentication...</p>
        <p class="text-sm text-gray-500 mt-2">Please wait</p>
      </div>
    </div>

    <!-- Error Screen (if auth fails) -->
    <div v-else-if="authError" class="flex items-center justify-center min-h-screen">
      <div class="text-center max-w-md">
        <svg class="w-16 h-16 text-red-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <h2 class="text-2xl font-bold text-gray-900 mb-2">Authentication Failed</h2>
        <p class="text-gray-600 mb-6">{{ authError }}</p>
        <button
          @click="() => window.location.reload()"
          class="bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-md font-semibold transition-colors"
        >
          Retry
        </button>
      </div>
    </div>

    <!-- Main App (only after auth is ready) -->
    <template v-else>
      <!-- Header -->
      <header class="bg-gradient-to-r from-purple-600 to-blue-600 text-white shadow-lg">
        <div class="container mx-auto px-4 py-6">
          <div class="flex items-center justify-between">
            <div>
              <h1 class="text-4xl font-bold">🎯 TK9 Deep Research Dashboard</h1>
              <p class="text-purple-100 mt-2">Real-time multi-agent research monitoring</p>
            </div>
            <!-- Anonymous Session Badge -->
            <AnonymousSessionBadge />
          </div>

          <!-- Navigation -->
          <nav class="mt-4 flex gap-4">
            <router-link
              to="/"
              class="px-4 py-2 rounded-md transition-colors"
              :class="$route.path === '/' ? 'bg-white text-purple-600 font-semibold' : 'text-purple-100 hover:bg-purple-700'"
            >
              Dashboard
            </router-link>
            <router-link
              to="/sessions"
              class="px-4 py-2 rounded-md transition-colors"
              :class="$route.path === '/sessions' ? 'bg-white text-purple-600 font-semibold' : 'text-purple-100 hover:bg-purple-700'"
            >
              Sessions
            </router-link>
          </nav>
        </div>
      </header>

      <!-- Main Content -->
      <main class="container mx-auto px-4 py-8 flex-1">
        <router-view />
      </main>

      <!-- Footer -->
      <footer class="bg-gray-800 text-gray-300 mt-12">
        <div class="container mx-auto px-4 py-6 text-center">
          <p class="text-sm">
            TK9 Deep Research System | Powered by Multi-Agent AI | Version 2.0
          </p>
        </div>
      </footer>
    </template>
  </div>
</template>

<style scoped>
/* Additional custom styles if needed */
</style>

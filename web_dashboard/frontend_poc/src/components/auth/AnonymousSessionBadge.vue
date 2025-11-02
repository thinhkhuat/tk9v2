<script setup lang="ts">
import { computed } from 'vue'
import { useAuthStore } from '@/stores/authStore'

const authStore = useAuthStore()

// Emits
const emit = defineEmits<{
  (e: 'show-login'): void
  (e: 'show-registration'): void
  (e: 'sign-out'): void
}>()

const badgeText = computed(() => {
  if (!authStore.isAuthenticated) {
    return 'Not Authenticated'
  }
  return authStore.isAnonymous ? 'Anonymous Session' : 'Signed In'
})

const badgeColor = computed(() => {
  if (!authStore.isAuthenticated) {
    return 'bg-red-100 text-red-800'
  }
  return authStore.isAnonymous
    ? 'bg-yellow-100 text-yellow-800'
    : 'bg-green-100 text-green-800'
})

const tooltipText = computed(() => {
  if (!authStore.isAuthenticated) {
    return 'Authentication required. Please refresh the page.'
  }
  return authStore.isAnonymous
    ? 'You are using an anonymous session. Your research data is temporary and will be lost if you clear your browser data. Sign up to save your work permanently.'
    : 'You are signed in. Your research data is saved to your account.'
})

const handleSignOut = async () => {
  try {
    await authStore.signOut()
    emit('sign-out')
  } catch (err) {
    console.error('[AnonymousSessionBadge] Sign out failed:', err)
  }
}
</script>

<template>
  <div class="inline-flex items-center gap-2 relative">
    <!-- Badge -->
    <div
      :class="[
        'flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium transition-all group relative',
        badgeColor
      ]"
    >
      <!-- Icon -->
      <svg
        v-if="authStore.isAnonymous"
        xmlns="http://www.w3.org/2000/svg"
        class="h-4 w-4"
        viewBox="0 0 20 20"
        fill="currentColor"
      >
        <path
          fill-rule="evenodd"
          d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-6-3a2 2 0 11-4 0 2 2 0 014 0zm-2 4a5 5 0 00-4.546 2.916A5.986 5.986 0 0010 16a5.986 5.986 0 004.546-2.084A5 5 0 0010 11z"
          clip-rule="evenodd"
        />
      </svg>

      <svg
        v-else-if="authStore.isAuthenticated"
        xmlns="http://www.w3.org/2000/svg"
        class="h-4 w-4"
        viewBox="0 0 20 20"
        fill="currentColor"
      >
        <path
          fill-rule="evenodd"
          d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z"
          clip-rule="evenodd"
        />
      </svg>

      <svg
        v-else
        xmlns="http://www.w3.org/2000/svg"
        class="h-4 w-4"
        viewBox="0 0 20 20"
        fill="currentColor"
      >
        <path
          fill-rule="evenodd"
          d="M13.477 14.89A6 6 0 015.11 6.524l8.367 8.368zm1.414-1.414L6.524 5.11a6 6 0 018.367 8.367zM18 10a8 8 0 11-16 0 8 8 0 0116 0z"
          clip-rule="evenodd"
        />
      </svg>

      <!-- Text -->
      <span>{{ badgeText }}</span>

      <!-- Tooltip -->
      <div
        class="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg shadow-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none w-64 text-center z-50"
      >
        {{ tooltipText }}
        <!-- Tooltip arrow -->
        <div
          class="absolute top-full left-1/2 transform -translate-x-1/2 -mt-1 border-4 border-transparent border-t-gray-900"
        ></div>
      </div>
    </div>

    <!-- Action buttons -->
    <div class="flex items-center gap-2">
      <!-- Sign In button (for anonymous users only) -->
      <button
        v-if="authStore.isAnonymous"
        @click="emit('show-login')"
        class="px-3 py-1 text-sm font-medium text-indigo-600 bg-indigo-50 hover:bg-indigo-100 rounded-lg transition-colors"
      >
        Sign In
      </button>

      <!-- Sign Out button (for authenticated non-anonymous users) -->
      <button
        v-if="authStore.isAuthenticated && !authStore.isAnonymous"
        @click="handleSignOut"
        class="px-3 py-1 text-sm font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
      >
        Sign Out
      </button>
    </div>
  </div>
</template>

<style scoped>
/* Ensure tooltip doesn't cause layout shift */
.group {
  position: relative;
}
</style>

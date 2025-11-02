<template>
  <div
    v-if="shouldShowPrompt"
    class="fixed bottom-6 right-6 max-w-md bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-lg shadow-2xl p-6 animate-slide-up z-50"
  >
    <!-- Close button -->
    <button
      @click="dismissPrompt"
      class="absolute top-2 right-2 text-white/80 hover:text-white transition-colors"
      aria-label="Dismiss"
    >
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
      </svg>
    </button>

    <!-- Content -->
    <div class="pr-6">
      <div class="flex items-center mb-3">
        <svg class="w-8 h-8 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M5 13l4 4L19 7"
          />
        </svg>
        <h3 class="text-lg font-bold">Research Complete!</h3>
      </div>

      <p class="text-white/90 mb-4 leading-relaxed">
        Love what you discovered? Save your research history and access it from any device by
        creating a permanent account.
      </p>

      <button
        @click="openRegistrationModal"
        class="w-full bg-white text-indigo-600 font-semibold py-3 px-6 rounded-lg hover:bg-gray-50 transition-all transform hover:scale-105 shadow-lg"
      >
        Upgrade to Permanent Account
      </button>

      <p class="text-xs text-white/70 mt-3 text-center">
        Takes less than 30 seconds • No credit card required
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useAuthStore } from '@/stores/authStore'

const authStore = useAuthStore()

// Props
const props = defineProps<{
  researchCompleted: boolean
}>()

// Emits
const emit = defineEmits<{
  (e: 'open-registration'): void
}>()

// Local state
const isDismissed = ref(false)
const dismissCount = ref(0)

// Load dismissal state from localStorage
const DISMISS_COUNT_KEY = 'tk9_anonymous_prompt_dismiss_count'
const LAST_SHOWN_KEY = 'tk9_anonymous_prompt_last_shown'

// Initialize from localStorage
const loadDismissalState = () => {
  const stored = localStorage.getItem(DISMISS_COUNT_KEY)
  dismissCount.value = stored ? parseInt(stored, 10) : 0
}

loadDismissalState()

// Computed: Should show prompt
const shouldShowPrompt = computed(() => {
  // Don't show if dismissed in current session
  if (isDismissed.value) return false

  // Don't show if not anonymous
  if (!authStore.isAnonymous) return false

  // Don't show if research not completed
  if (!props.researchCompleted) return false

  // Show after being dismissed 3 times (remind after 3rd dismissal)
  // This means: show on 1st, 2nd, 3rd completion, then remind on 4th+
  if (dismissCount.value >= 3) {
    // Check if enough time passed since last shown (e.g., 24 hours)
    const lastShown = localStorage.getItem(LAST_SHOWN_KEY)
    if (lastShown) {
      const daysSinceLastShown = (Date.now() - parseInt(lastShown, 10)) / (1000 * 60 * 60 * 24)
      if (daysSinceLastShown < 1) {
        return false // Don't show if reminded within last 24 hours
      }
    }
  }

  return true
})

// Watch research completion to show prompt
watch(
  () => props.researchCompleted,
  (completed) => {
    if (completed && shouldShowPrompt.value) {
      // Reset dismissed state when new research completes
      isDismissed.value = false
    }
  }
)

// Actions
const dismissPrompt = () => {
  isDismissed.value = true
  dismissCount.value += 1
  localStorage.setItem(DISMISS_COUNT_KEY, dismissCount.value.toString())
  localStorage.setItem(LAST_SHOWN_KEY, Date.now().toString())
}

const openRegistrationModal = () => {
  emit('open-registration')
  isDismissed.value = true // Don't show again in current session
}
</script>

<style scoped>
@keyframes slide-up {
  from {
    transform: translateY(100%);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.animate-slide-up {
  animation: slide-up 0.4s ease-out;
}
</style>

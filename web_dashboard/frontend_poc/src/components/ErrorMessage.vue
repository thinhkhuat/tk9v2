<script setup lang="ts">
defineProps<{
  message: string
}>()

const emit = defineEmits<{
  retry: []
}>()
</script>

<template>
  <div class="max-w-2xl mx-auto">
    <div class="bg-red-50 border border-red-200 rounded-lg p-6 shadow-sm">
      <div class="flex items-start space-x-4">
        <!-- Error Icon -->
        <div class="flex-shrink-0">
          <svg class="h-6 w-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>

        <div class="flex-1">
          <!-- Error Title -->
          <h3 class="text-lg font-semibold text-red-900 mb-2">
            Something went wrong
          </h3>

          <!-- Error Message -->
          <p class="text-red-800 mb-4">
            {{ message }}
          </p>

          <!-- Actions -->
          <div class="flex space-x-3">
            <button
              @click="emit('retry')"
              class="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors font-medium"
            >
              Try Again
            </button>
            <button
              @click="$router.push('/')"
              class="px-4 py-2 bg-white text-red-600 border border-red-300 rounded-md hover:bg-red-50 transition-colors font-medium"
            >
              Go Home
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<!--
  ErrorMessage - User-friendly error display component
  Phase 3: Replaces browser alerts with styled error messages
-->

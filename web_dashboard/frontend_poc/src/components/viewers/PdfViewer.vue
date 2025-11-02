<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  blobUrl: string  // PDF Blob URL (string) - no reactivity issues!
  filename: string
}>()

const isLoading = ref(true)
const loadError = ref<string | null>(null)
const iframeKey = ref(0)

watch(() => props.blobUrl, (newUrl) => {
  console.log('[PdfViewer] Received Blob URL:', newUrl)
  isLoading.value = false
  // Force iframe reload
  iframeKey.value++
}, { immediate: true })
</script>

<template>
  <div class="relative h-full flex flex-col bg-gray-50">
    <!-- Toolbar -->
    <div class="px-4 py-2 bg-white border-b border-gray-200">
      <div class="flex items-center justify-between">
        <span class="text-sm font-medium text-gray-700">PDF Document Preview</span>
        <span class="text-sm text-gray-500 font-mono">{{ filename }}</span>
      </div>
    </div>

    <!-- Content Area -->
    <div class="flex-1 overflow-auto relative">
      <!-- Loading State -->
      <div v-if="isLoading" class="flex items-center justify-center h-full min-h-[400px]">
        <div class="text-center">
          <svg class="animate-spin h-12 w-12 text-blue-600 mx-auto mb-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <p class="text-gray-600">Loading PDF...</p>
        </div>
      </div>

      <!-- Error State -->
      <div v-else-if="loadError" class="flex items-center justify-center h-full min-h-[400px]">
        <div class="text-center max-w-md">
          <svg class="w-16 h-16 text-red-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h3 class="text-lg font-semibold text-gray-900 mb-2">PDF Loading Error</h3>
          <p class="text-gray-600">{{ loadError }}</p>
        </div>
      </div>

      <!-- PDF Content - iframe must have explicit height to be visible -->
      <iframe
        v-else
        :key="iframeKey"
        :src="blobUrl"
        class="w-full border-0"
        style="height: calc(90vh - 200px); min-height: 600px;"
        title="PDF Preview"
      />
    </div>
  </div>
</template>

<style scoped>
/* Ensure iframe fills container properly */
iframe {
  display: block;
}
</style>

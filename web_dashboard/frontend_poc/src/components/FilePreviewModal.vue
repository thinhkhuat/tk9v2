<script setup lang="ts">
import { ref, shallowRef, computed, watch, onMounted, onUnmounted } from 'vue'
import { onKeyStroke } from '@vueuse/core'
import type { FileGeneratedPayload } from '@/types/events'
import { extractFilePathFromDownloadUrl, detectFileExtension, getViewerType } from '@/utils/file-display-utils'
import TextFileViewer from './viewers/TextFileViewer.vue'
import CodeViewer from './viewers/CodeViewer.vue'
import DocxViewer from './viewers/DocxViewer.vue'
import ImageGalleryViewer from './viewers/ImageGalleryViewer.vue'
import PdfViewer from './viewers/PdfViewer.vue'

const props = defineProps<{
  file: FileGeneratedPayload | null
  show: boolean
  sessionId?: string | null  // Required for file path construction
}>()

const emit = defineEmits<{
  close: []
}>()

// State
const isLoading = ref(false)
const error = ref<string | null>(null)

// CRITICAL: Use shallowRef for binary content (Uint8Array for binary, string for text)
// Regular ref causes Vue's reactivity to wrap binary data in Proxies,
// which leads to detachment and data corruption
const fileContent = shallowRef<string | Uint8Array | null>(null)

// For PDF files, create a Blob URL to avoid binary data reactivity issues
const pdfBlobUrl = ref<string | null>(null)

// Calculate word count from content
const wordCount = computed(() => {
  if (!fileContent.value || typeof fileContent.value !== 'string') {
    return null
  }

  // Remove extra whitespace and count words
  const text = fileContent.value.trim()
  if (!text) return 0

  // Split by whitespace and filter out empty strings
  const words = text.split(/\s+/).filter(word => word.length > 0)
  return words.length
})

// DRY: Use shared file type detection utility (single source of truth)
const viewerType = computed(() => {
  if (!props.file) return null

  // Use centralized detection with fallback
  const ext = detectFileExtension(props.file.file_type, props.file.filename)

  console.log('[FilePreviewModal] File:', props.file.filename, 'file_type:', props.file.file_type, 'detected ext:', ext)

  // Use centralized viewer type mapping
  return getViewerType(ext)
})

// Fetch file content when file changes
watch(() => props.file, async (newFile) => {
  if (!newFile) {
    fileContent.value = null
    error.value = null

    // Clean up PDF blob URL
    if (pdfBlobUrl.value) {
      URL.revokeObjectURL(pdfBlobUrl.value)
      pdfBlobUrl.value = null
    }
    return
  }

  isLoading.value = true
  error.value = null

  try {
    // Fetch file content from API
    const { api } = await import('@/services/api')

    // DRY: Use centralized utility to extract filesystem path from download URL
    // Converts /download/{session_id}/{filename} → {session_id}/{filename}
    let filePath = extractFilePathFromDownloadUrl(newFile.path, newFile.filename)

    // Fallback: If path doesn't include session_id and we have it as prop, construct it
    if (props.sessionId && !filePath.includes('/')) {
      filePath = `${props.sessionId}/${newFile.filename}`
    }

    const content = await api.getFileContent(newFile.file_id, filePath)

    // CRITICAL: For binary content (ArrayBuffer), convert to Uint8Array immediately
    // This prevents detachment issues when ArrayBuffers are passed as props
    if (content instanceof ArrayBuffer) {
      console.log('[FilePreviewModal] Converting ArrayBuffer to Uint8Array, length:', content.byteLength)
      const uint8Array = new Uint8Array(content)
      console.log('[FilePreviewModal] Uint8Array created, length:', uint8Array.length, 'First bytes:', Array.from(uint8Array.slice(0, 10)))
      fileContent.value = uint8Array

      // For PDF files, create a Blob URL to bypass Vue reactivity issues
      if (viewerType.value === 'pdf') {
        // Clean up old blob URL if exists
        if (pdfBlobUrl.value) {
          URL.revokeObjectURL(pdfBlobUrl.value)
        }

        const blob = new Blob([uint8Array], { type: 'application/pdf' })
        pdfBlobUrl.value = URL.createObjectURL(blob)
        console.log('[FilePreviewModal] Created PDF Blob URL:', pdfBlobUrl.value)
      }
    } else {
      fileContent.value = content
    }
  } catch (err: any) {
    console.error('Failed to load file content:', err)
    error.value = err.message || 'Failed to load file preview'
  } finally {
    isLoading.value = false
  }
}, { immediate: true })

// Close on ESC key
onKeyStroke('Escape', () => {
  if (props.show) {
    emit('close')
  }
})

// Close on backdrop click
function handleBackdropClick(event: MouseEvent) {
  if (event.target === event.currentTarget) {
    emit('close')
  }
}

// Prevent body scroll when modal is open
watch(() => props.show, (isShown) => {
  if (isShown) {
    document.body.style.overflow = 'hidden'
  } else {
    document.body.style.overflow = ''
  }
})

// Cleanup on unmount
onUnmounted(() => {
  document.body.style.overflow = ''

  // Clean up PDF blob URL
  if (pdfBlobUrl.value) {
    URL.revokeObjectURL(pdfBlobUrl.value)
  }
})
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="show"
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-75 backdrop-blur-sm"
        @click="handleBackdropClick"
      >
        <div
          class="relative w-full max-w-6xl max-h-[90vh] bg-white rounded-lg shadow-2xl overflow-hidden flex flex-col"
          @click.stop
        >
          <!-- Header -->
          <div class="flex items-center justify-between px-6 py-4 border-b border-gray-200 bg-gray-50">
            <div class="flex-1 min-w-0">
              <h2 class="text-xl font-semibold text-gray-900 truncate">
                {{ file?.filename || 'File Preview' }}
              </h2>
              <p class="text-sm text-gray-500 mt-1">
                {{ file?.file_type?.toUpperCase() }} file
                <span v-if="file?.size_bytes" class="ml-2">
                  ({{ (file.size_bytes / 1024).toFixed(2) }} KB)
                </span>
                <span v-if="wordCount !== null" class="ml-2">
                  • {{ wordCount.toLocaleString() }} words
                </span>
              </p>
            </div>
            <button
              @click="emit('close')"
              class="ml-4 p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-200 rounded-full transition-colors"
              aria-label="Close preview"
            >
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <!-- Content Area -->
          <div class="flex-1 overflow-auto bg-white">
            <!-- Loading State -->
            <div v-if="isLoading" class="flex items-center justify-center h-full min-h-[400px]">
              <div class="text-center">
                <svg class="animate-spin h-12 w-12 text-blue-600 mx-auto mb-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <p class="text-gray-600">Loading preview...</p>
              </div>
            </div>

            <!-- Error State -->
            <div v-else-if="error" class="flex items-center justify-center h-full min-h-[400px]">
              <div class="text-center max-w-md">
                <svg class="w-16 h-16 text-red-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <h3 class="text-lg font-semibold text-gray-900 mb-2">Preview Error</h3>
                <p class="text-gray-600 mb-4">{{ error }}</p>
                <button
                  @click="emit('close')"
                  class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                >
                  Close
                </button>
              </div>
            </div>

            <!-- Unsupported Format -->
            <div v-else-if="!viewerType" class="flex items-center justify-center h-full min-h-[400px]">
              <div class="text-center max-w-md">
                <svg class="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <h3 class="text-lg font-semibold text-gray-900 mb-2">Preview Not Available</h3>
                <p class="text-gray-600 mb-4">
                  Preview is not supported for {{ file?.file_type?.toUpperCase() }} files.
                </p>
                <a
                  v-if="file?.path"
                  :href="file.path"
                  download
                  class="inline-block px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                >
                  Download File
                </a>
              </div>
            </div>

            <!-- Viewer Components -->
            <TextFileViewer
              v-else-if="viewerType === 'text' && fileContent"
              :content="fileContent as string"
              :file-type="file?.filename?.endsWith('.md') ? 'md' : (file?.file_type || 'txt')"
            />

            <CodeViewer
              v-else-if="viewerType === 'code' && fileContent"
              :content="fileContent as string"
              :language="file?.file_type || 'plaintext'"
              :filename="file?.filename || ''"
            />

            <DocxViewer
              v-else-if="viewerType === 'docx' && fileContent"
              :content="fileContent as Uint8Array"
              :filename="file?.filename || ''"
            />

            <ImageGalleryViewer
              v-else-if="viewerType === 'image' && file"
              :file="file"
            />

            <PdfViewer
              v-else-if="viewerType === 'pdf' && pdfBlobUrl"
              :blob-url="pdfBlobUrl"
              :filename="file?.filename || ''"
            />
          </div>

          <!-- Footer -->
          <div class="px-6 py-3 border-t border-gray-200 bg-gray-50 flex items-center justify-between">
            <div class="text-sm text-gray-500">
              Press <kbd class="px-2 py-1 bg-gray-200 rounded text-xs font-mono">ESC</kbd> to close
            </div>
            <div class="flex gap-2">
              <a
                v-if="file?.path"
                :href="file.path"
                download
                class="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors text-sm font-medium"
              >
                Download
              </a>
              <button
                @click="emit('close')"
                class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm font-medium"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
/* Modal transition animations */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-active .modal > div,
.modal-leave-active .modal > div {
  transition: transform 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from > div,
.modal-leave-to > div {
  transform: scale(0.95);
}

/* Keyboard hint styling */
kbd {
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}
</style>

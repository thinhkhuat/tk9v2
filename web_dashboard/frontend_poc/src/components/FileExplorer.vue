<script setup lang="ts">
import { useSessionStore } from '@/stores/sessionStore'
import { computed, ref } from 'vue'
import { api, triggerFileDownload } from '@/services/api'
import type { FileGeneratedPayload } from '@/types/events'
import FilePreviewModal from './FilePreviewModal.vue'
import {
  getFileTypeIcon,
  guessFileTypeFromFilename,
  normalizeFileData
} from '@/utils/file-display-utils'
import { formatFileSize } from '@/utils/formatters'

const store = useSessionStore()

// Preview modal state
const showPreviewModal = ref(false)
const fileToPreview = ref<FileGeneratedPayload | null>(null)

// Group files by type (backend provides file_type, fallback to guess if missing)
const filesByType = computed(() => {
  const groups: Record<string, FileGeneratedPayload[]> = {}

  store.files.forEach(file => {
    // Backend should provide file_type - use it directly
    let fileType = file.file_type

    // Fallback: guess from filename only if backend didn't provide it
    if (!fileType || fileType === 'undefined' || fileType === 'null') {
      fileType = guessFileTypeFromFilename(file.filename)
    }

    if (!groups[fileType]) {
      groups[fileType] = []
    }
    groups[fileType].push(file)
  })

  return groups
})

// Get friendly filename from backend metadata
function getFriendlyFilename(file: FileGeneratedPayload): string {
  // Backend should provide friendly_name in the event
  // If not available, fallback to a simple display format
  if (!file.filename || !file.filename.includes('.')) return file.filename

  const parts = file.filename.split('.')
  const extension = parts[parts.length - 1].toLowerCase()
  const namePart = parts.slice(0, -1).join('.')

  // Check if it has a language code suffix (e.g., "uuid_vi")
  if (namePart.includes('_')) {
    const lastPart = namePart.split('_').pop()
    if (lastPart && lastPart.length <= 3) {
      // Translated file
      return `research_report_${lastPart}.${extension}`
    }
  }

  // Original file
  return `research_report.${extension}`
}

// Download file handler
async function downloadFile(file: FileGeneratedPayload) {
  if (!store.sessionId) return

  try {
    // Use UUID filename for download (file.filename is already UUID now)
    console.log(`Downloading ${file.filename}...`)

    const blob = await api.downloadFile(store.sessionId, file.filename)

    // Save with friendly name for user
    const friendlyName = getFriendlyFilename(file.filename)
    triggerFileDownload(blob, friendlyName)
  } catch (error) {
    console.error('Download failed:', error)
    alert(`Failed to download ${file.filename}`)
  }
}

// Download all files as ZIP
async function downloadAllAsZip() {
  if (!store.sessionId) return

  try {
    console.log('Downloading all files as ZIP...')
    const blob = await api.downloadSessionZip(store.sessionId)
    triggerFileDownload(blob, `${store.sessionId}_all_files.zip`)
  } catch (error) {
    console.error('ZIP download failed:', error)
    alert('Failed to download files as ZIP')
  }
}

// NOTE: getLanguageColor() is available in @/utils/formatters.ts if needed

// Preview file handler
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
</script>

<template>
  <div class="file-explorer bg-white rounded shadow p-3 h-[450px] flex flex-col">
    <div class="header flex justify-between items-center mb-2">
      <h2 class="text-sm font-bold">
        Files <span class="text-xs text-gray-600">({{ store.totalFilesGenerated }})</span>
      </h2>

      <button
        v-if="store.totalFilesGenerated > 0"
        @click="downloadAllAsZip"
        class="bg-blue-500 hover:bg-blue-600 text-white px-2 py-1 rounded text-xs font-semibold flex items-center gap-1"
      >
        <span>📦</span>
        <span>ZIP</span>
      </button>
    </div>

    <!-- Empty state -->
    <div
      v-if="store.totalFilesGenerated === 0"
      class="empty-state bg-gray-50 border border-dashed border-gray-300 rounded p-4 text-center"
    >
      <div class="text-3xl mb-2">📁</div>
      <h3 class="text-sm font-semibold text-gray-700 mb-1">No files yet</h3>
      <p class="text-xs text-gray-600">
        Files appear as research progresses
      </p>
    </div>

    <!-- Files grouped by type (Compact List View) -->
    <div v-else class="file-groups space-y-2 overflow-y-auto flex-1">
      <div
        v-for="(files, fileType) in filesByType"
        :key="fileType"
        class="file-group"
      >
        <h3 class="text-[10px] font-semibold mb-1 flex items-center gap-1 text-gray-700 bg-gray-100 px-2 py-1 rounded">
          <span>{{ getFileTypeIcon(fileType) }}</span>
          <span>{{ fileType.toUpperCase() }} ({{ files.length }})</span>
        </h3>

        <div class="file-list space-y-1">
          <div
            v-for="file in files"
            :key="file.file_id"
            class="file-row flex items-center justify-between gap-2 px-2 py-1 hover:bg-gray-50 rounded text-[10px] border-b border-gray-100"
          >
            <!-- File info (left side) -->
            <div class="flex items-center gap-2 flex-1 min-w-0">
              <span class="text-sm">{{ getFileTypeIcon(file.file_type) }}</span>
              <span class="font-medium truncate" :title="getFriendlyFilename(file)">{{ getFriendlyFilename(file) }}</span>
              <span class="text-[9px] text-gray-500">{{ formatFileSize(file.size_bytes) }}</span>
            </div>

            <!-- Actions (right side) -->
            <div class="flex gap-1 flex-shrink-0">
              <button
                @click.stop="previewFile(file)"
                class="px-2 py-0.5 bg-gray-400 hover:bg-gray-500 text-white rounded text-[10px]"
                title="Preview"
              >
                👁️
              </button>
              <button
                @click.stop="downloadFile(file)"
                class="px-2 py-0.5 bg-blue-400 hover:bg-blue-500 text-white rounded text-[10px]"
                title="Download"
              >
                ⬇️
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Research completion notice -->
    <div
      v-if="store.isResearchCompleted && store.totalFilesGenerated > 0"
      class="completion-notice bg-green-100 border border-green-400 text-green-800 p-4 rounded-lg mt-6"
    >
      <h3 class="font-semibold mb-2">✅ Research Completed!</h3>
      <p class="text-sm">
        All {{ store.totalFilesGenerated }} files are ready for download.
        You can download them individually or as a ZIP archive.
      </p>
    </div>

    <!-- File Preview Modal -->
    <FilePreviewModal
      :file="fileToPreview"
      :show="showPreviewModal"
      @close="closePreview"
    />
  </div>
</template>

<style scoped>
.file-card {
  transition: all 0.2s ease;
}

.file-card:hover {
  transform: translateY(-2px);
  border-color: #3B82F6;
}

.file-card:active {
  transform: translateY(0);
}

.file-name {
  word-break: break-word;
}
</style>

<script setup lang="ts">
import { useSessionStore } from '@/stores/sessionStore'
import { computed, ref } from 'vue'
import { api, triggerFileDownload } from '@/services/api'
import type { FileGeneratedPayload } from '@/types/events'
import FilePreviewModal from './FilePreviewModal.vue'
import FileList from './FileList.vue'
import FileIcon from './icons/FileIcon.vue'
import ArchiveIcon from './icons/ArchiveIcon.vue'
import FolderIcon from './icons/FolderIcon.vue'

const store = useSessionStore()

// Preview modal state
const showPreviewModal = ref(false)
const fileToPreview = ref<FileGeneratedPayload | null>(null)

// Group files by type (backend provides file_type - trust it completely)
const filesByType = computed(() => {
  const groups: Record<string, FileGeneratedPayload[]> = {}

  store.files.forEach(file => {
    // Backend is source of truth - use file_type directly
    const fileType = file.file_type

    if (!groups[fileType]) {
      groups[fileType] = []
    }
    groups[fileType].push(file)
  })

  return groups
})

// Display name mapping for file types
function getFileTypeDisplayName(fileType: string): string {
  if (fileType === 'UNDEFINED' || !fileType) {
    return 'Other Files'
  }

  // Descriptive labels with file extensions
  const typeLabels: Record<string, string> = {
    'md': 'Markdown format (.md)',
    'docx': 'Word format (.docx)',
    'pdf': 'PDF format (.pdf)',
    'txt': 'Text format (.txt)',
    'json': 'JSON format (.json)',
    'html': 'HTML format (.html)',
    'csv': 'CSV format (.csv)',
    'xlsx': 'Excel format (.xlsx)',
    'pptx': 'PowerPoint format (.pptx)',
    'png': 'PNG Image (.png)',
    'jpg': 'JPEG Image (.jpg)',
    'jpeg': 'JPEG Image (.jpeg)',
    'gif': 'GIF Image (.gif)',
    'svg': 'SVG Image (.svg)'
  }

  const normalizedType = fileType.toLowerCase()
  return typeLabels[normalizedType] || fileType.toUpperCase()
}

// Get color class for file type (matches FileIcon colors)
function getFileTypeColor(fileType: string): string {
  const colors: Record<string, string> = {
    'pdf': 'text-red-500',
    'docx': 'text-blue-600',
    'doc': 'text-blue-600',
    'md': 'text-purple-600',
    'markdown': 'text-purple-600',
    'txt': 'text-gray-600',
    'json': 'text-yellow-600',
    'xml': 'text-orange-600',
    'html': 'text-orange-600',
    'csv': 'text-green-600',
    'xlsx': 'text-green-700',
    'pptx': 'text-orange-500',
    'png': 'text-indigo-500',
    'jpg': 'text-indigo-500',
    'jpeg': 'text-indigo-500',
    'gif': 'text-indigo-500',
    'svg': 'text-indigo-500'
  }

  const normalizedType = fileType.toLowerCase()
  return colors[normalizedType] || 'text-gray-500'
}

// Download file handler
async function downloadFile(file: FileGeneratedPayload) {
  if (!store.sessionId) return

  try {
    // Use UUID filename for download request
    console.log(`Downloading ${file.filename}...`)

    const blob = await api.downloadFile(store.sessionId, file.filename)

    // Save with backend-provided friendly name (with fallback for migration)
    const downloadName = file.friendly_name || file.filename
    triggerFileDownload(blob, downloadName)
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
  <div
    class="file-explorer bg-white rounded shadow p-3 h-[500px] flex flex-col transition-shadow duration-500"
    :class="{ 'files-present-glow': store.totalFilesGenerated > 0 }"
  >
    <div class="header flex justify-between items-center mb-2">
      <h2 class="text-sm font-bold">
        Files <span class="text-xs text-gray-600">({{ store.totalFilesGenerated }})</span>
      </h2>

      <button
        v-if="store.totalFilesGenerated > 0"
        @click="downloadAllAsZip"
        class="bg-blue-500 hover:bg-blue-600 text-white px-2 py-1 rounded text-xs font-semibold flex items-center gap-1"
      >
        <ArchiveIcon size="sm" />
        <span>ZIP</span>
      </button>
    </div>

    <!-- Empty state -->
    <div
      v-if="store.totalFilesGenerated === 0"
      class="empty-state bg-gray-50 border border-dashed border-gray-300 rounded p-4 text-center"
    >
      <div class="flex justify-center mb-2 text-gray-400">
        <FolderIcon size="xl" />
      </div>
      <h3 class="text-sm font-semibold text-gray-700 mb-1">No files yet</h3>
      <p class="text-xs text-gray-600">
        Files appear as research progresses
      </p>
    </div>

    <!-- Files grouped by type (Compact List View) -->
    <div v-else class="file-groups space-y-4 overflow-y-auto flex-1">
      <div
        v-for="(files, fileType) in filesByType"
        :key="fileType"
        class="file-group space-y-1"
      >
        <h3 class="text-sm font-semibold mb-2 flex items-center gap-2 bg-gray-100 px-3 py-2 rounded">
          <FileIcon :type="fileType" size="md" />
          <span :class="getFileTypeColor(fileType)">{{ getFileTypeDisplayName(fileType) }} ({{ files.length }})</span>
        </h3>

        <!-- DRY: Using shared FileList component -->
        <FileList
          :files="files"
          variant="compact"
          :show-actions="true"
          @preview="previewFile"
          @download="downloadFile"
        />
      </div>
    </div>

    <!-- Research completion notice -->
    <div
      v-if="store.isResearchCompleted && store.totalFilesGenerated > 0"
      class="completion-notice bg-green-100 border border-green-400 text-green-800 p-4 rounded-lg mt-6"
    >
      <h3 class="font-semibold mb-2">✅ Research Completed!</h3>
      <p class="text-sm">
        All {{ store.totalFilesGenerated }} files ({{ Math.floor(store.totalFilesGenerated / 2) }} English + {{ Math.floor(store.totalFilesGenerated / 2) }} translated) are ready for download.
        You can download them individually or as a ZIP archive.
      </p>
    </div>

    <!-- File Preview Modal -->
    <FilePreviewModal
      :file="fileToPreview"
      :show="showPreviewModal"
      :session-id="store.sessionId"
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

/* Subtle green glow when files are present */
.files-present-glow {
  box-shadow: 0 0 20px rgba(34, 197, 94, 0.3), 0 0 40px rgba(34, 197, 94, 0.15);
}
</style>

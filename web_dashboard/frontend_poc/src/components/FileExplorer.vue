<script setup lang="ts">
import { useSessionStore } from '@/stores/sessionStore'
import { computed } from 'vue'
import { api, triggerFileDownload, formatFileSize } from '@/services/api'
import type { FileGeneratedPayload } from '@/types/events'

const store = useSessionStore()

// Group files by type
const filesByType = computed(() => {
  const groups: Record<string, FileGeneratedPayload[]> = {}

  store.files.forEach(file => {
    if (!groups[file.file_type]) {
      groups[file.file_type] = []
    }
    groups[file.file_type].push(file)
  })

  return groups
})

// File type icons
function getFileIcon(fileType: string): string {
  const icons: Record<string, string> = {
    pdf: '📄',
    docx: '📝',
    md: '📋',
    txt: '📃',
    json: '{ }',
    xml: '</>',
    html: '🌐'
  }
  return icons[fileType.toLowerCase()] || '📎'
}

// Download file handler
async function downloadFile(file: FileGeneratedPayload) {
  if (!store.sessionId) return

  try {
    console.log(`Downloading ${file.filename}...`)
    const blob = await api.downloadFile(store.sessionId, file.filename)
    triggerFileDownload(blob, file.filename)
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

// File language badge color
function getLanguageBadgeColor(language: string): string {
  const colors: Record<string, string> = {
    vi: 'bg-blue-100 text-blue-800',
    en: 'bg-green-100 text-green-800',
    es: 'bg-yellow-100 text-yellow-800',
    fr: 'bg-purple-100 text-purple-800'
  }
  return colors[language.toLowerCase()] || 'bg-gray-100 text-gray-800'
}
</script>

<template>
  <div class="file-explorer">
    <div class="header flex justify-between items-center mb-4">
      <h2 class="text-2xl font-bold">
        Generated Files
        <span class="text-lg text-gray-600">({{ store.totalFilesGenerated }})</span>
      </h2>

      <button
        v-if="store.totalFilesGenerated > 0"
        @click="downloadAllAsZip"
        class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded font-semibold flex items-center gap-2"
      >
        <span>📦</span>
        <span>Download All (ZIP)</span>
      </button>
    </div>

    <!-- File stats -->
    <div v-if="store.totalFilesGenerated > 0" class="file-stats bg-gray-100 p-4 rounded-lg mb-4">
      <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
        <div class="stat">
          <div class="text-sm text-gray-600">Total Files</div>
          <div class="text-xl font-semibold">{{ store.totalFilesGenerated }}</div>
        </div>
        <div class="stat">
          <div class="text-sm text-gray-600">Total Size</div>
          <div class="text-xl font-semibold">{{ formatFileSize(store.totalFileSize) }}</div>
        </div>
        <div class="stat">
          <div class="text-sm text-gray-600">File Types</div>
          <div class="text-xl font-semibold">{{ Object.keys(filesByType).length }}</div>
        </div>
      </div>
    </div>

    <!-- Empty state -->
    <div
      v-if="store.totalFilesGenerated === 0"
      class="empty-state bg-gray-50 border-2 border-dashed border-gray-300 rounded-lg p-8 text-center"
    >
      <div class="text-6xl mb-4">📁</div>
      <h3 class="text-xl font-semibold text-gray-700 mb-2">No files generated yet</h3>
      <p class="text-gray-600">
        Files will appear here as the research progresses
      </p>
    </div>

    <!-- Files grouped by type -->
    <div v-else class="file-groups space-y-6">
      <div
        v-for="(files, fileType) in filesByType"
        :key="fileType"
        class="file-group"
      >
        <h3 class="text-lg font-semibold mb-3 flex items-center gap-2">
          <span>{{ getFileIcon(fileType) }}</span>
          <span>{{ fileType.toUpperCase() }} Files ({{ files.length }})</span>
        </h3>

        <div class="file-list grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          <div
            v-for="file in files"
            :key="file.file_id"
            class="file-card bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
            @click="downloadFile(file)"
          >
            <div class="flex items-start justify-between mb-2">
              <div class="file-icon text-3xl">{{ getFileIcon(file.file_type) }}</div>
              <span
                :class="getLanguageBadgeColor(file.language)"
                class="px-2 py-1 rounded text-xs font-semibold uppercase"
              >
                {{ file.language }}
              </span>
            </div>

            <div class="file-name font-medium text-sm mb-1 truncate" :title="file.filename">
              {{ file.filename }}
            </div>

            <div class="file-size text-xs text-gray-600">
              {{ formatFileSize(file.size_bytes) }}
            </div>

            <div class="file-actions mt-3">
              <button
                @click.stop="downloadFile(file)"
                class="w-full bg-blue-500 hover:bg-blue-600 text-white py-2 rounded text-sm font-semibold transition-colors"
              >
                Download
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

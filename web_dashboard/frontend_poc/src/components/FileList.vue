<!--
  FileList.vue - Reusable File Display Component

  Purpose: DRY-compliant component for displaying file lists
  Replaces duplicated logic in FileExplorer.vue and SessionDetailModal.vue

  Design: Hybrid props + scoped slots pattern (Gemini validated)
  Session: 54e39d73-0e9c-461a-b139-567b499f80df
-->

<script setup lang="ts">
import type { FileGeneratedPayload } from '@/types/events'
import { formatFileSize } from '@/utils/formatters'
import FileIcon from './icons/FileIcon.vue'
import DownloadIcon from './icons/DownloadIcon.vue'
import EyeIcon from './icons/EyeIcon.vue'

// Vue 3 Best Practice: Use withDefaults for props (unused in script, auto-exposed to template)
withDefaults(defineProps<{
  files: FileGeneratedPayload[]
  variant?: 'compact' | 'detailed'
  showActions?: boolean
  emptyMessage?: string
  loading?: boolean // Loading state for skeleton loader
}>(), {
  variant: 'detailed', // Default to the more descriptive variant
  showActions: false,
  emptyMessage: 'No files available.',
  loading: false
})

// Vue 3 Best Practice: Typed emits
const emit = defineEmits<{
  (e: 'preview', file: FileGeneratedPayload): void
  (e: 'download', file: FileGeneratedPayload): void
}>()

// Internal handlers (keeps template cleaner)
const handlePreview = (file: FileGeneratedPayload) => {
  emit('preview', file)
}

const handleDownload = (file: FileGeneratedPayload) => {
  emit('download', file)
}

// Language badge styling helper
const getLanguageBadgeClass = (language: string): string => {
  const lang = language.toLowerCase()
  if (lang === 'en') {
    return 'bg-blue-100 text-blue-800 border-blue-200'
  } else if (lang === 'vi') {
    return 'bg-amber-100 text-amber-800 border-amber-200'
  }
  // Default for other languages
  return 'bg-gray-100 text-gray-800 border-gray-200'
}
</script>

<template>
  <!-- Loading State: Skeleton Loader -->
  <div v-if="loading">
    <div v-for="i in 3" :key="i" class="p-3 bg-gray-50 rounded-lg mb-2 animate-pulse">
      <div class="flex items-center gap-3">
        <div class="w-8 h-8 bg-gray-200 rounded"></div>
        <div class="flex-1 space-y-2">
          <div class="h-4 bg-gray-200 rounded w-3/4"></div>
          <div class="h-3 bg-gray-200 rounded w-1/4"></div>
        </div>
      </div>
    </div>
  </div>

  <div v-else-if="files && files.length > 0">
    <!-- The v-for loop is the core responsibility of this component -->
    <div v-for="file in files" :key="file.file_id" class="file-list-item">
      <!--
        Vue 3 Best Practice: Scoped Slot for extensibility.
        The content *inside* the <slot> tag is the default template.
        A parent can override this by providing its own <template #item="{ file }">
      -->
      <slot name="item" :file="file">
        <!-- Default Template: Compact Variant (for FileExplorer) -->
        <div
          v-if="variant === 'compact'"
          @click="handlePreview(file)"
          class="flex items-center justify-between gap-2 px-2 py-2 hover:bg-gray-50 rounded text-xs border-b border-gray-100 min-h-[40px] cursor-pointer"
        >
          <div class="flex items-center gap-3 flex-1 min-w-0">
            <FileIcon :type="file.file_type" size="md" />
            <span class="font-medium truncate text-sm" :title="file.friendly_name || file.filename">
              {{ file.friendly_name || file.filename }}
            </span>
            <span
              v-if="file.language"
              class="px-2 py-0.5 text-[10px] font-bold rounded-full border flex-shrink-0"
              :class="getLanguageBadgeClass(file.language)"
            >
              {{ file.language.toUpperCase() }}
            </span>
            <span class="text-xs text-gray-500 whitespace-nowrap">{{ formatFileSize(file.size_bytes ?? 0) }}</span>
          </div>
          <div v-if="showActions" class="flex gap-2 flex-shrink-0">
            <button
              @click.stop="handlePreview(file)"
              class="px-3 py-1.5 bg-gray-400 hover:bg-gray-500 text-white rounded text-xs flex items-center transition-colors"
              title="Preview"
              aria-label="Preview file"
            >
              <EyeIcon size="md" />
            </button>
            <button
              @click.stop="handleDownload(file)"
              class="px-3 py-1.5 bg-blue-400 hover:bg-blue-500 text-white rounded text-xs flex items-center transition-colors"
              title="Download"
              aria-label="Download file"
            >
              <DownloadIcon size="md" />
            </button>
          </div>
        </div>

        <!-- Default Template: Detailed Variant (for SessionDetailModal) -->
        <div
          v-else-if="variant === 'detailed'"
          @click="handlePreview(file)"
          class="bg-gray-50 rounded-lg p-3 flex items-center justify-between hover:bg-gray-100 transition-colors cursor-pointer"
        >
          <div class="flex items-center gap-3 flex-1 min-w-0">
            <FileIcon :type="file.file_type" size="lg" />
            <div class="min-w-0 flex-1">
              <div class="font-medium text-sm truncate" :title="file.filename">
                {{ file.filename }}
              </div>
              <div class="text-xs text-gray-500">{{ formatFileSize(file.size_bytes ?? 0) }}</div>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <span
              v-if="file.language"
              class="px-2 py-1 text-xs font-bold rounded border"
              :class="getLanguageBadgeClass(file.language)"
            >
              {{ file.language.toUpperCase() }}
            </span>
            <div v-if="showActions" class="flex gap-1 flex-shrink-0">
              <button
                @click.stop="handlePreview(file)"
                class="px-2 py-1 bg-gray-400 hover:bg-gray-500 text-white rounded text-xs flex items-center"
                title="Preview"
                aria-label="Preview file"
              >
                <EyeIcon size="md" />
              </button>
              <button
                @click.stop="handleDownload(file)"
                class="px-2 py-1 bg-blue-400 hover:bg-blue-500 text-white rounded text-xs flex items-center"
                title="Download"
                aria-label="Download file"
              >
                <DownloadIcon size="md" />
              </button>
            </div>
          </div>
        </div>
      </slot>
    </div>
  </div>
  <!-- The component also handles the empty state, another core responsibility -->
  <div v-else class="text-center py-10 text-gray-500 text-sm">
    <slot name="empty">
      <p>{{ emptyMessage }}</p>
    </slot>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useSessionsStore, type ResearchSession } from '@/stores/sessionsStore'
import { formatDate, formatFileSize, getStatusColor } from '@/utils/formatters'

const props = defineProps<{
  session: ResearchSession
}>()

const emit = defineEmits<{
  (e: 'open-modal'): void
}>()

const router = useRouter()
const store = useSessionsStore()

const showActions = ref(false)
const isSelected = ref(store.selectedSessions.has(props.session.id))

// Toggle selection
function toggleSelect(event: Event) {
  event.stopPropagation()
  store.toggleSelection(props.session.id)
  isSelected.value = store.selectedSessions.has(props.session.id)
}

// Open quick view modal
function openQuickView() {
  emit('open-modal')
}

// View full session details (navigates to HomeView with session loaded)
function viewSession() {
  router.push(`/sessions/${props.session.id}`)
  showActions.value = false
}

// Duplicate session
async function duplicateSession(event: Event) {
  event.stopPropagation()
  const newSessionId = await store.duplicateSession(props.session.id)
  if (newSessionId) {
    router.push(`/sessions/${newSessionId}`)
  }
}

// Archive session
async function archiveSession(event: Event) {
  event.stopPropagation()
  if (confirm(`Archive session "${props.session.title}"?`)) {
    await store.archiveSession(props.session.id)
  }
}

// Restore session
async function restoreSession(event: Event) {
  event.stopPropagation()
  await store.restoreSession(props.session.id)
}

// Delete session
async function deleteSession(event: Event) {
  event.stopPropagation()
  if (confirm(`Permanently delete session "${props.session.title}"? This cannot be undone!`)) {
    await store.deleteSession(props.session.id)
  }
}
</script>

<template>
  <div
    class="session-card bg-white rounded-lg shadow-sm border border-gray-200 p-5 hover:shadow-md transition-all cursor-pointer relative"
    :class="{ 'ring-2 ring-blue-500': isSelected }"
    @click="openQuickView"
  >
    <!-- Selection Checkbox -->
    <div class="absolute top-4 left-4">
      <input
        type="checkbox"
        :checked="isSelected"
        @change="toggleSelect"
        @click.stop
        class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
      />
    </div>

    <!-- Archived Badge -->
    <div v-if="session.archived_at" class="absolute top-4 right-4">
      <span class="px-2 py-1 bg-gray-200 text-gray-700 text-xs font-semibold rounded">
        Archived
      </span>
    </div>

    <!-- Session Title -->
    <div class="ml-8 mr-4 mb-3">
      <h3 class="font-semibold text-gray-800 whitespace-normal break-words session-card-title" :title="session.title">
        {{ session.title }}
      </h3>
    </div>

    <!-- Session Info -->
    <div class="space-y-2 text-sm text-gray-600">
      <!-- Status Badge -->
      <div class="flex items-center gap-2">
        <span class="text-xs text-gray-500">Status:</span>
        <span
          :class="getStatusColor(session.status)"
          class="px-2 py-0.5 rounded text-xs font-medium capitalize"
        >
          {{ session.status.replace('_', ' ') }}
        </span>
      </div>

      <!-- Created Date -->
      <div class="flex items-center gap-2">
        <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
        <span>{{ formatDate(session.created_at) }}</span>
      </div>

      <!-- File Count -->
      <div class="flex items-center gap-2">
        <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
        </svg>
        <span>{{ session.file_count || 0 }} files</span>
        <span v-if="session.total_size_bytes" class="text-gray-400">
          ({{ formatFileSize(session.total_size_bytes) }})
        </span>
      </div>

      <!-- Language -->
      <div v-if="session.language" class="flex items-center gap-2">
        <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
        </svg>
        <span class="uppercase">{{ session.language }}</span>
      </div>
    </div>

    <!-- Actions -->
    <div class="mt-4 pt-4 border-t border-gray-200 flex items-center justify-between">
      <button
        @click.stop="openQuickView"
        class="text-sm text-blue-600 hover:text-blue-700 font-medium"
      >
        Quick View →
      </button>

      <!-- Action Menu -->
      <div class="relative">
        <button
          @click.stop="showActions = !showActions"
          class="p-2 hover:bg-gray-100 rounded transition-colors"
        >
          <svg class="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
          </svg>
        </button>

        <!-- Dropdown Menu -->
        <div
          v-if="showActions"
          @click.stop
          class="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 z-10"
        >
          <button
            @click="viewSession"
            class="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
            Full Details
          </button>

          <button
            @click="duplicateSession"
            class="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
            Duplicate
          </button>

          <button
            v-if="!session.archived_at"
            @click="archiveSession"
            class="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
            </svg>
            Archive
          </button>

          <button
            v-else
            @click="restoreSession"
            class="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Restore
          </button>

          <button
            @click="deleteSession"
            class="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 flex items-center gap-2 border-t border-gray-100"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
            Delete
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.session-card {
  min-height: 200px;
}

/* Responsive title sizing: reduces font size first, then wraps */
.session-card-title {
  /* clamp(minimum, preferred, maximum) */
  font-size: clamp(0.875rem, 2vw + 0.5rem, 1.125rem);
  /* 0.875rem = 14px minimum */
  /* 1.125rem = 18px maximum (text-lg) */
  line-height: 1.4;
}
</style>

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
function viewSession(event: Event) {
  event.stopPropagation()
  router.push(`/sessions/${props.session.id}`)
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
  <tr
    class="hover:bg-gray-50 cursor-pointer transition-colors"
    :class="{ 'bg-blue-50': isSelected }"
    @click="openQuickView"
  >
    <!-- Checkbox -->
    <td class="px-4 py-4">
      <input
        type="checkbox"
        :checked="isSelected"
        @change="toggleSelect"
        @click.stop
        class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
      />
    </td>

    <!-- Title -->
    <td class="px-6 py-4">
      <div class="flex items-start gap-2">
        <span class="font-medium text-gray-900 whitespace-normal break-words session-row-title" :title="session.title">
          {{ session.title }}
        </span>
        <span v-if="session.archived_at" class="px-2 py-0.5 bg-gray-200 text-gray-700 text-xs font-semibold rounded flex-shrink-0">
          Archived
        </span>
      </div>
    </td>

    <!-- Status -->
    <td class="px-6 py-4">
      <span
        :class="getStatusColor(session.status)"
        class="px-2 py-1 rounded text-xs font-medium capitalize inline-block"
      >
        {{ session.status.replace('_', ' ') }}
      </span>
    </td>

    <!-- Created Date -->
    <td class="px-6 py-4 text-sm text-gray-600">
      {{ formatDate(session.created_at) }}
    </td>

    <!-- Files -->
    <td class="px-6 py-4 text-sm text-gray-600">
      <div class="flex items-center gap-1">
        <span>{{ session.file_count || 0 }}</span>
        <span v-if="session.total_size_bytes" class="text-gray-400">
          ({{ formatFileSize(session.total_size_bytes) }})
        </span>
      </div>
    </td>

    <!-- Actions -->
    <td class="px-6 py-4 text-right">
      <div class="flex items-center justify-end gap-2" @click.stop>
        <!-- Duplicate Button -->
        <button
          @click="duplicateSession"
          class="p-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
          title="Duplicate"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
        </button>

        <!-- Archive/Restore Button -->
        <button
          v-if="!session.archived_at"
          @click="archiveSession"
          class="p-2 text-gray-600 hover:text-yellow-600 hover:bg-yellow-50 rounded transition-colors"
          title="Archive"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
          </svg>
        </button>
        <button
          v-else
          @click="restoreSession"
          class="p-2 text-gray-600 hover:text-green-600 hover:bg-green-50 rounded transition-colors"
          title="Restore"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>

        <!-- Delete Button -->
        <button
          @click="deleteSession"
          class="p-2 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
          title="Delete"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
        </button>

        <!-- View Button -->
        <button
          @click="viewSession"
          class="p-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
          title="View Details"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
          </svg>
        </button>
      </div>
    </td>
  </tr>
</template>

<style scoped>
/* Responsive title sizing: reduces font size first, then wraps */
.session-row-title {
  /* clamp(minimum, preferred, maximum) */
  font-size: clamp(0.8125rem, 1.5vw + 0.5rem, 1rem);
  /* 0.8125rem = 13px minimum */
  /* 1rem = 16px maximum (default) */
  line-height: 1.4;
}
</style>

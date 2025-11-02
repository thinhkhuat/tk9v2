<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useSessionsStore, type ResearchSession } from '@/stores/sessionsStore'
import { useAuthStore } from '@/stores/authStore'
import SessionCard from '@/components/SessionCard.vue'
import SessionListRow from '@/components/SessionListRow.vue'
import SessionDetailModal from '@/components/SessionDetailModal.vue'

const store = useSessionsStore()
const authStore = useAuthStore()

// Modal state
const isModalOpen = ref(false)
const selectedSessionForModal = ref<ResearchSession | null>(null)

// Fetch sessions only after authentication is ready
onMounted(async () => {
  // Wait for auth to be ready (should already be done by App.vue, but double-check)
  if (authStore.isInitializing) {
    console.log('[SessionsDashboard] Waiting for auth...')
    // Poll until ready (max 5 seconds)
    let attempts = 0
    while (authStore.isInitializing && attempts < 50) {
      await new Promise(resolve => setTimeout(resolve, 100))
      attempts++
    }
  }

  // Only fetch if authenticated
  if (authStore.isAuthenticated) {
    console.log('[SessionsDashboard] Auth ready, fetching sessions')
    store.fetchSessions()
  } else {
    console.error('[SessionsDashboard] User not authenticated, cannot fetch sessions')
  }
})

// Modal handlers
function openModal(session: ResearchSession) {
  selectedSessionForModal.value = session
  isModalOpen.value = true
}

function closeModal() {
  isModalOpen.value = false
  selectedSessionForModal.value = null
}

function handleModalUpdate() {
  // Refresh sessions list after modal actions
  store.fetchSessions()
}

// Toggle view mode
function toggleView() {
  store.toggleViewMode()
}

// Pagination handlers
function nextPage() {
  store.nextPage()
}

function previousPage() {
  store.previousPage()
}

// Bulk operations
function handleBulkArchive() {
  if (confirm(`Archive ${store.selectedCount} selected sessions?`)) {
    store.archiveSelected()
  }
}

function handleBulkDelete() {
  if (confirm(`Permanently delete ${store.selectedCount} selected sessions? This cannot be undone!`)) {
    store.deleteSelected()
  }
}

// Filter handlers
function toggleArchived() {
  store.setFilters({ includeArchived: !store.includeArchived })
}

function setStatusFilter(status: string | null) {
  store.setFilters({ status })
}
</script>

<template>
  <div class="sessions-dashboard">
    <!-- Header -->
    <div class="mb-6 flex items-center justify-between">
      <div>
        <h1 class="text-3xl font-bold text-gray-800">Session Management</h1>
        <p class="text-gray-600 mt-1">
          Manage your research sessions ({{ store.sessionCount.total }} total,
          {{ store.sessionCount.active }} active, {{ store.sessionCount.archived }} archived)
        </p>
      </div>

      <!-- View Toggle -->
      <div class="flex gap-2">
        <button
          @click="toggleView"
          class="px-4 py-2 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors flex items-center gap-2"
        >
          <svg v-if="store.viewMode === 'grid'" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h16M4 18h16" />
          </svg>
          <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
          </svg>
          <span>{{ store.viewMode === 'grid' ? 'List View' : 'Grid View' }}</span>
        </button>
      </div>
    </div>

    <!-- Filters and Controls -->
    <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
      <div class="flex items-center justify-between flex-wrap gap-4">
        <!-- Filter Controls -->
        <div class="flex items-center gap-3">
          <!-- Include Archived Toggle -->
          <label class="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              :checked="store.includeArchived"
              @change="toggleArchived"
              class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span class="text-sm font-medium text-gray-700">Show Archived</span>
          </label>

          <!-- Status Filter -->
          <select
            :value="store.statusFilter || ''"
            @change="setStatusFilter(($event.target as HTMLSelectElement).value || null)"
            class="px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">All Statuses</option>
            <option value="in_progress">In Progress</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
          </select>

          <!-- Reset Filters -->
          <button
            @click="store.resetFilters()"
            class="text-sm text-blue-600 hover:text-blue-700 font-medium"
          >
            Reset Filters
          </button>
        </div>

        <!-- Bulk Actions (shown when selections exist) -->
        <div v-if="store.hasSelection" class="flex items-center gap-2">
          <span class="text-sm text-gray-600">{{ store.selectedCount }} selected</span>
          <button
            @click="handleBulkArchive"
            class="px-3 py-1.5 text-sm bg-yellow-500 hover:bg-yellow-600 text-white rounded-md font-medium transition-colors"
          >
            Archive Selected
          </button>
          <button
            @click="handleBulkDelete"
            class="px-3 py-1.5 text-sm bg-red-500 hover:bg-red-600 text-white rounded-md font-medium transition-colors"
          >
            Delete Selected
          </button>
          <button
            @click="store.clearSelection()"
            class="px-3 py-1.5 text-sm bg-gray-500 hover:bg-gray-600 text-white rounded-md font-medium transition-colors"
          >
            Clear
          </button>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="store.isLoading" class="text-center py-12">
      <svg class="animate-spin h-12 w-12 text-blue-600 mx-auto mb-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      <p class="text-gray-600">Loading sessions...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="store.error" class="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
      <svg class="w-12 h-12 text-red-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <h3 class="text-lg font-semibold text-gray-900 mb-2">Failed to Load Sessions</h3>
      <p class="text-gray-600 mb-4">{{ store.error }}</p>
      <button
        @click="store.fetchSessions()"
        class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md font-semibold transition-colors"
      >
        Retry
      </button>
    </div>

    <!-- Empty State -->
    <div v-else-if="store.sessions.length === 0" class="bg-gray-50 border-2 border-dashed border-gray-300 rounded-lg p-12 text-center">
      <div class="text-6xl mb-4">📁</div>
      <h3 class="text-xl font-semibold text-gray-700 mb-2">No Sessions Found</h3>
      <p class="text-gray-600 mb-6">
        {{ store.includeArchived ? 'You have no research sessions yet.' : 'You have no active research sessions.' }}
      </p>
      <router-link
        to="/"
        class="inline-block bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-md font-semibold transition-colors"
      >
        Start New Research
      </router-link>
    </div>

    <!-- Sessions List/Grid -->
    <div v-else>
      <!-- Grid View -->
      <div v-if="store.viewMode === 'grid'" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        <SessionCard
          v-for="session in store.sessions"
          :key="session.id"
          :session="session"
          @open-modal="openModal(session)"
        />
      </div>

      <!-- List View -->
      <div v-else class="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden mb-6">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-4 py-3 text-left">
                <input
                  type="checkbox"
                  @change="($event.target as HTMLInputElement).checked ? store.selectAll() : store.clearSelection()"
                  class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Title</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Files</th>
              <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <SessionListRow
              v-for="session in store.sessions"
              :key="session.id"
              :session="session"
              @open-modal="openModal(session)"
            />
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div class="flex items-center justify-between bg-white rounded-lg shadow-sm border border-gray-200 px-6 py-4">
        <div class="text-sm text-gray-600">
          Showing {{ (store.currentPage - 1) * store.pageSize + 1 }}-{{ Math.min(store.currentPage * store.pageSize, store.totalCount) }}
          of {{ store.totalCount }} sessions
        </div>

        <div class="flex items-center gap-2">
          <button
            @click="previousPage"
            :disabled="store.currentPage === 1"
            class="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Previous
          </button>
          <span class="text-sm text-gray-600">
            Page {{ store.currentPage }} of {{ Math.ceil(store.totalCount / store.pageSize) }}
          </span>
          <button
            @click="nextPage"
            :disabled="!store.hasMore"
            class="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Next
          </button>
        </div>
      </div>
    </div>

    <!-- Session Detail Modal -->
    <SessionDetailModal
      v-if="selectedSessionForModal"
      :session="selectedSessionForModal"
      :is-open="isModalOpen"
      @close="closeModal"
      @update="handleModalUpdate"
    />
  </div>
</template>

<style scoped>
/* Additional custom styles if needed */
</style>

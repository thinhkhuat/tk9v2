/**
 * Pinia store for session management (list of all sessions).
 * Handles CRUD operations for research sessions.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useToast } from 'vue-toastification'
import { api } from '@/services/api'

const toast = useToast()

export interface ResearchSession {
  id: string
  user_id: string
  title: string
  status: 'in_progress' | 'completed' | 'failed'
  language?: string
  parameters?: Record<string, any>
  archived_at?: string | null
  file_count?: number
  total_size_bytes?: number
  created_at: string
  updated_at: string
}

export type ViewMode = 'grid' | 'list'

export const useSessionsStore = defineStore('sessions', () => {
  // ============================================================================
  // State
  // ============================================================================

  const sessions = ref<ResearchSession[]>([])
  const selectedSessions = ref<Set<string>>(new Set())
  const viewMode = ref<ViewMode>('list')
  const includeArchived = ref(false)
  const statusFilter = ref<string | null>(null)
  const languageFilter = ref<string | null>(null)

  // Pagination
  const currentPage = ref(1)
  const pageSize = ref(20)
  const totalCount = ref(0)

  // Loading states
  const isLoading = ref(false)
  const isOperating = ref(false)

  // Error state
  const error = ref<string | null>(null)

  // ============================================================================
  // Computed Properties
  // ============================================================================

  const activeSessions = computed(() => {
    return sessions.value.filter(s => !s.archived_at)
  })

  const archivedSessions = computed(() => {
    return sessions.value.filter(s => s.archived_at)
  })

  const sessionCount = computed(() => {
    return {
      total: totalCount.value,
      active: activeSessions.value.length,
      archived: archivedSessions.value.length
    }
  })

  const hasMore = computed(() => {
    return (currentPage.value * pageSize.value) < totalCount.value
  })

  const selectedCount = computed(() => {
    return selectedSessions.value.size
  })

  const hasSelection = computed(() => {
    return selectedSessions.value.size > 0
  })

  // ============================================================================
  // Actions
  // ============================================================================

  /**
   * Fetch sessions from the API with current filters and pagination
   */
  async function fetchSessions(resetPage = false) {
    if (resetPage) {
      currentPage.value = 1
    }

    isLoading.value = true
    error.value = null

    try {
      const params = {
        include_archived: includeArchived.value,
        status: statusFilter.value,
        language: languageFilter.value,
        limit: pageSize.value,
        offset: (currentPage.value - 1) * pageSize.value
      }

      const response = await api.getSessions(params)

      sessions.value = response.sessions
      totalCount.value = response.total_count

      console.log(`[SessionsStore] Fetched ${sessions.value.length} sessions (total: ${totalCount.value})`)
    } catch (err: any) {
      console.error('[SessionsStore] Failed to fetch sessions:', err)
      error.value = err.message || 'Failed to load sessions'
      toast.error('Failed to load sessions')
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Archive a session (soft delete)
   */
  async function archiveSession(sessionId: string) {
    isOperating.value = true
    error.value = null

    try {
      await api.archiveSession(sessionId)

      // Update local state
      const session = sessions.value.find(s => s.id === sessionId)
      if (session) {
        session.archived_at = new Date().toISOString()
      }

      toast.success('Session archived successfully')

      // Refresh if we're not showing archived sessions
      if (!includeArchived.value) {
        await fetchSessions()
      }
    } catch (err: any) {
      console.error('[SessionsStore] Failed to archive session:', err)
      error.value = err.message || 'Failed to archive session'
      toast.error('Failed to archive session')
      throw err
    } finally {
      isOperating.value = false
    }
  }

  /**
   * Restore an archived session
   */
  async function restoreSession(sessionId: string) {
    isOperating.value = true
    error.value = null

    try {
      await api.restoreSession(sessionId)

      // Update local state
      const session = sessions.value.find(s => s.id === sessionId)
      if (session) {
        session.archived_at = null
      }

      toast.success('Session restored successfully')
      await fetchSessions()
    } catch (err: any) {
      console.error('[SessionsStore] Failed to restore session:', err)
      error.value = err.message || 'Failed to restore session'
      toast.error('Failed to restore session')
      throw err
    } finally {
      isOperating.value = false
    }
  }

  /**
   * Permanently delete a session
   */
  async function deleteSession(sessionId: string) {
    isOperating.value = true
    error.value = null

    try {
      await api.deleteSession(sessionId)

      // Remove from local state
      sessions.value = sessions.value.filter(s => s.id !== sessionId)
      totalCount.value = Math.max(0, totalCount.value - 1)

      // Remove from selection if selected
      selectedSessions.value.delete(sessionId)

      toast.success('Session deleted permanently')
    } catch (err: any) {
      console.error('[SessionsStore] Failed to delete session:', err)
      error.value = err.message || 'Failed to delete session'
      toast.error('Failed to delete session')
      throw err
    } finally {
      isOperating.value = false
    }
  }

  /**
   * Duplicate a session
   */
  async function duplicateSession(sessionId: string): Promise<string | null> {
    isOperating.value = true
    error.value = null

    try {
      const response = await api.duplicateSession(sessionId)

      toast.success('Session duplicated successfully')

      // Refresh the list to show new session
      await fetchSessions()

      return response.new_session_id
    } catch (err: any) {
      console.error('[SessionsStore] Failed to duplicate session:', err)
      error.value = err.message || 'Failed to duplicate session'
      toast.error('Failed to duplicate session')
      return null
    } finally {
      isOperating.value = false
    }
  }

  /**
   * Bulk archive selected sessions
   */
  async function archiveSelected() {
    if (selectedSessions.value.size === 0) return

    isOperating.value = true
    const sessionIds = Array.from(selectedSessions.value)

    try {
      await Promise.all(sessionIds.map(id => archiveSession(id)))
      toast.success(`Archived ${sessionIds.length} sessions`)
      clearSelection()
    } catch (err) {
      toast.error('Failed to archive some sessions')
    } finally {
      isOperating.value = false
    }
  }

  /**
   * Bulk delete selected sessions
   */
  async function deleteSelected() {
    if (selectedSessions.value.size === 0) return

    isOperating.value = true
    const sessionIds = Array.from(selectedSessions.value)

    try {
      await Promise.all(sessionIds.map(id => deleteSession(id)))
      toast.success(`Deleted ${sessionIds.length} sessions`)
      clearSelection()
    } catch (err) {
      toast.error('Failed to delete some sessions')
    } finally {
      isOperating.value = false
    }
  }

  /**
   * Toggle session selection
   */
  function toggleSelection(sessionId: string) {
    if (selectedSessions.value.has(sessionId)) {
      selectedSessions.value.delete(sessionId)
    } else {
      selectedSessions.value.add(sessionId)
    }
  }

  /**
   * Select all visible sessions
   */
  function selectAll() {
    sessions.value.forEach(session => {
      selectedSessions.value.add(session.id)
    })
  }

  /**
   * Clear all selections
   */
  function clearSelection() {
    selectedSessions.value.clear()
  }

  /**
   * Toggle view mode (grid/list)
   */
  function toggleViewMode() {
    viewMode.value = viewMode.value === 'grid' ? 'list' : 'grid'
  }

  /**
   * Set filters and refresh
   */
  function setFilters(filters: {
    includeArchived?: boolean
    status?: string | null
    language?: string | null
  }) {
    if (filters.includeArchived !== undefined) {
      includeArchived.value = filters.includeArchived
    }
    if (filters.status !== undefined) {
      statusFilter.value = filters.status
    }
    if (filters.language !== undefined) {
      languageFilter.value = filters.language
    }

    // Reset to first page when filters change
    fetchSessions(true)
  }

  /**
   * Go to next page
   */
  function nextPage() {
    if (hasMore.value) {
      currentPage.value++
      fetchSessions()
    }
  }

  /**
   * Go to previous page
   */
  function previousPage() {
    if (currentPage.value > 1) {
      currentPage.value--
      fetchSessions()
    }
  }

  /**
   * Reset all filters
   */
  function resetFilters() {
    includeArchived.value = false
    statusFilter.value = null
    languageFilter.value = null
    currentPage.value = 1
    fetchSessions()
  }

  // ============================================================================
  // Return Public API
  // ============================================================================

  return {
    // State
    sessions,
    selectedSessions,
    viewMode,
    includeArchived,
    statusFilter,
    languageFilter,
    currentPage,
    pageSize,
    totalCount,
    isLoading,
    isOperating,
    error,

    // Computed
    activeSessions,
    archivedSessions,
    sessionCount,
    hasMore,
    selectedCount,
    hasSelection,

    // Actions
    fetchSessions,
    archiveSession,
    restoreSession,
    deleteSession,
    duplicateSession,
    archiveSelected,
    deleteSelected,
    toggleSelection,
    selectAll,
    clearSelection,
    toggleViewMode,
    setFilters,
    nextPage,
    previousPage,
    resetFilters
  }
})

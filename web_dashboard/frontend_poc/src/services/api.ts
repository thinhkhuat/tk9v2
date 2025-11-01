/**
 * API client for HTTP requests to the TK9 Deep Research backend.
 * Handles research submissions, session management, and file downloads.
 */

import axios, { type AxiosInstance, type AxiosError } from 'axios'
import { MIN_SUBJECT_LENGTH, MAX_SUBJECT_LENGTH } from '@/config/validation'
import { API_BASE_URL, API_TIMEOUT, FILE_DOWNLOAD_TIMEOUT } from '@/config/api'
import { guessFileTypeFromFilename, isBinaryFileType } from '@/utils/file-display-utils'

// Response Types
export interface ResearchResponse {
  session_id: string
  status: string
  message: string
  websocket_url: string
}

export interface SessionStatus {
  session_id: string
  status: 'running' | 'completed' | 'failed' | 'unknown'
  progress: number
  files: FileInfo[]
  error_message?: string
}

export interface FileInfo {
  file_id: string
  filename: string
  file_type: string
  language: string
  size_bytes: number
  download_url: string
}

export interface ResearchSession {
  session_id: string
  subject: string
  language: string
  status: string
  created_at: string
  file_count: number
}

export interface HealthStatus {
  status: string
  active_sessions: number
  websocket_connections: number
}

export interface SessionStatistics {
  session_id: string
  total_files: number
  total_size_bytes: number
  file_types: Record<string, number>
  languages: string[]
  created_at?: string
}

export interface SearchResults {
  query: string
  results: FileInfo[]
  count: number
}

// Create axios instance with default configuration
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json'
  },
  // CRITICAL: Send cookies with every request (required for JWT authentication)
  withCredentials: true
})

// Request interceptor for logging and debugging + JWT authentication
apiClient.interceptors.request.use(
  (config) => {
    const method = config.method?.toUpperCase()
    const url = config.url
    console.log(`→ ${method} ${url}`)

    // Add timestamp to request
    config.metadata = { startTime: Date.now() }

    // Add JWT token from Supabase session to Authorization header
    // Supabase stores session in localStorage with key format: sb-{project-ref}-auth-token
    // Extract project ref from Supabase URL for dynamic key construction
    const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || ''
    const projectRef = supabaseUrl.match(/https:\/\/([^.]+)\.supabase\.co/)?.[1]

    if (projectRef) {
      const supabaseSessionKey = `sb-${projectRef}-auth-token`
      const supabaseSession = localStorage.getItem(supabaseSessionKey)

      if (supabaseSession) {
        try {
          const session = JSON.parse(supabaseSession)
          const accessToken = session?.access_token
          if (accessToken) {
            config.headers.Authorization = `Bearer ${accessToken}`
            console.log('[API] Added JWT to request from', supabaseSessionKey)
          } else {
            console.warn('[API] Session found but no access_token:', session)
          }
        } catch (e) {
          console.error('[API] Failed to parse Supabase session:', e)
        }
      } else {
        console.warn('[API] No Supabase session found at key:', supabaseSessionKey)
      }
    } else {
      console.error('[API] Could not extract project ref from Supabase URL:', supabaseUrl)
    }

    return config
  },
  (error) => {
    console.error('Request error:', error)
    return Promise.reject(error)
  }
)

/**
 * Parse FastAPI/Pydantic validation errors into user-friendly messages
 */
function parseValidationError(error: AxiosError): string {
  const data = error.response?.data as any

  // Check if it's a FastAPI validation error (422)
  if (error.response?.status === 422 && data?.detail && Array.isArray(data.detail)) {
    const errors = data.detail.map((err: any) => {
      const field = err.loc?.[err.loc.length - 1] || 'field'
      const message = err.msg || 'Invalid value'

      // Enhanced messages for specific error types
      if (err.type === 'string_too_long') {
        const maxLength = err.ctx?.max_length || 'unknown'
        return `${field}: Maximum ${maxLength} characters allowed`
      } else if (err.type === 'string_too_short') {
        const minLength = err.ctx?.min_length || 'unknown'
        return `${field}: Minimum ${minLength} characters required`
      } else if (err.type === 'value_error') {
        return `${field}: ${message}`
      } else {
        return `${field}: ${message}`
      }
    })

    return errors.join('; ')
  }

  // Check for other error formats
  if (data?.message) {
    return data.message
  }

  if (data?.detail && typeof data.detail === 'string') {
    return data.detail
  }

  // Fallback to status-based messages
  if (error.response?.status === 401) {
    return 'Authentication required. Please sign in.'
  } else if (error.response?.status === 403) {
    return 'You do not have permission to perform this action.'
  } else if (error.response?.status === 404) {
    return 'The requested resource was not found.'
  } else if (error.response?.status === 500) {
    return 'Server error. Please try again later.'
  }

  return 'An unexpected error occurred. Please try again.'
}

// Response interceptor for logging and error handling
apiClient.interceptors.response.use(
  (response) => {
    const duration = Date.now() - (response.config.metadata?.startTime || Date.now())
    console.log(`← ${response.status} ${response.config.url} (${duration}ms)`)
    return response
  },
  (error: AxiosError) => {
    // Enhanced error logging
    if (error.response) {
      // Server responded with error status
      console.error(`API Error ${error.response.status}:`, {
        url: error.config?.url,
        method: error.config?.method,
        status: error.response.status,
        data: error.response.data
      })
    } else if (error.request) {
      // Request made but no response received
      console.error('Network error - no response received:', {
        url: error.config?.url,
        method: error.config?.method
      })
    } else {
      // Request setup error
      console.error('Request setup error:', error.message)
    }

    // Attach parsed user-friendly message to error
    error.message = parseValidationError(error)

    return Promise.reject(error)
  }
)

// ============================================================================
// API Methods
// ============================================================================

export const api = {
  /**
   * Submit a new research request
   */
  async submitResearch(subject: string, language: string = 'vi'): Promise<ResearchResponse> {
    const trimmedSubject = subject.trim()

    // Client-side validation (constraints from config/validation.ts)
    if (!trimmedSubject) {
      throw new Error('Research subject is required')
    }

    if (trimmedSubject.length < MIN_SUBJECT_LENGTH) {
      throw new Error(`Research subject must be at least ${MIN_SUBJECT_LENGTH} characters long`)
    }

    if (trimmedSubject.length > MAX_SUBJECT_LENGTH) {
      throw new Error(`Research subject must be at most ${MAX_SUBJECT_LENGTH} characters long`)
    }

    try {
      const response = await apiClient.post<ResearchResponse>('/api/research', {
        subject: trimmedSubject,
        language,
        save_files: true // Backend expects this field
      })
      return response.data
    } catch (error) {
      console.error('Failed to submit research:', error)
      throw error
    }
  },

  /**
   * Get status of a specific research session
   */
  async getSessionStatus(sessionId: string): Promise<SessionStatus> {
    try {
      const response = await apiClient.get<SessionStatus>(`/api/session/${sessionId}`)
      return response.data
    } catch (error) {
      console.error(`Failed to get session status for ${sessionId}:`, error)
      throw error
    }
  },

  /**
   * Get complete session state for re-hydration
   */
  async getSessionState(sessionId: string): Promise<any> {
    try {
      const response = await apiClient.get(`/api/session/${sessionId}/state`)
      return response.data
    } catch (error) {
      console.error(`Failed to get session state for ${sessionId}:`, error)
      throw error
    }
  },

  /**
   * Get all research sessions
   */
  async getAllSessions(): Promise<ResearchSession[]> {
    try {
      const response = await apiClient.get<ResearchSession[]>('/api/sessions')
      return response.data
    } catch (error) {
      console.error('Failed to get all sessions:', error)
      throw error
    }
  },

  /**
   * Download a specific file
   */
  async downloadFile(sessionId: string, filename: string): Promise<Blob> {
    try {
      const response = await apiClient.get(`/download/${sessionId}/${filename}`, {
        responseType: 'blob'
      })
      return response.data
    } catch (error) {
      console.error(`Failed to download file ${filename}:`, error)
      throw error
    }
  },

  /**
   * Download all files from a session as ZIP
   */
  async downloadSessionZip(sessionId: string): Promise<Blob> {
    try {
      const response = await apiClient.get(`/api/session/${sessionId}/zip`, {
        responseType: 'blob',
        timeout: FILE_DOWNLOAD_TIMEOUT
      })
      return response.data
    } catch (error) {
      console.error(`Failed to download session ZIP for ${sessionId}:`, error)
      throw error
    }
  },

  /**
   * Get file preview
   */
  async getFilePreview(sessionId: string, filename: string, lines: number = 50): Promise<any> {
    try {
      const response = await apiClient.get(
        `/api/session/${sessionId}/file/${filename}/preview`,
        { params: { lines } }
      )
      return response.data
    } catch (error) {
      console.error(`Failed to get file preview for ${filename}:`, error)
      throw error
    }
  },

  /**
   * Get file metadata
   */
  async getFileMetadata(sessionId: string, filename: string): Promise<any> {
    try {
      const response = await apiClient.get(
        `/api/session/${sessionId}/file/${filename}/metadata`
      )
      return response.data
    } catch (error) {
      console.error(`Failed to get file metadata for ${filename}:`, error)
      throw error
    }
  },

  /**
   * Get session statistics
   */
  async getSessionStatistics(sessionId: string): Promise<SessionStatistics> {
    try {
      const response = await apiClient.get<SessionStatistics>(
        `/api/session/${sessionId}/statistics`
      )
      return response.data
    } catch (error) {
      console.error(`Failed to get session statistics for ${sessionId}:`, error)
      throw error
    }
  },

  /**
   * Search for files across sessions
   */
  async searchFiles(query: string, sessionId?: string): Promise<SearchResults> {
    try {
      const response = await apiClient.get<SearchResults>('/api/search/files', {
        params: {
          q: query,
          session_id: sessionId
        }
      })
      return response.data
    } catch (error) {
      console.error(`Failed to search files for "${query}":`, error)
      throw error
    }
  },

  /**
   * Get download history
   */
  async getDownloadHistory(limit: number = 10): Promise<any> {
    try {
      const response = await apiClient.get('/api/downloads/history', {
        params: { limit }
      })
      return response.data
    } catch (error) {
      console.error('Failed to get download history:', error)
      throw error
    }
  },

  /**
   * Health check
   */
  async healthCheck(): Promise<HealthStatus> {
    try {
      const response = await apiClient.get<HealthStatus>('/api/health')
      return response.data
    } catch (error) {
      console.error('Health check failed:', error)
      throw error
    }
  },

  /**
   * Get file content for preview
   * Returns file content as string for text files or ArrayBuffer for binary files
   */
  async getFileContent(fileId: string, filePath: string): Promise<string | ArrayBuffer> {
    try {
      // PRE-REQUEST: Guess file type from filename to determine response format
      // This is a legitimate use case - we need to tell axios the responseType BEFORE the request
      const fileType = guessFileTypeFromFilename(filePath)
      const isBinary = isBinaryFileType(fileType)

      const response = await apiClient.get(`/api/files/content`, {
        params: { file_id: fileId, file_path: filePath },
        responseType: isBinary ? 'arraybuffer' : 'text',
        timeout: FILE_DOWNLOAD_TIMEOUT
      })

      return response.data
    } catch (error) {
      console.error(`Failed to get file content for ${filePath}:`, error)
      throw error
    }
  },

  // ============================================================================
  // Session Management APIs
  // ============================================================================

  /**
   * Get sessions list with filters and pagination
   */
  async getSessions(params: {
    include_archived?: boolean
    status?: string | null
    language?: string | null
    limit?: number
    offset?: number
  }): Promise<{
    sessions: any[]
    total_count: number
    limit: number
    offset: number
    has_more: boolean
  }> {
    try {
      const response = await apiClient.get('/api/sessions/list', { params })
      return response.data
    } catch (error) {
      console.error('Failed to get sessions:', error)
      throw error
    }
  },

  /**
   * Archive a session (soft delete)
   */
  async archiveSession(sessionId: string): Promise<void> {
    try {
      await apiClient.post(`/api/sessions/${sessionId}/archive`)
    } catch (error) {
      console.error(`Failed to archive session ${sessionId}:`, error)
      throw error
    }
  },

  /**
   * Restore an archived session
   */
  async restoreSession(sessionId: string): Promise<void> {
    try {
      await apiClient.post(`/api/sessions/${sessionId}/restore`)
    } catch (error) {
      console.error(`Failed to restore session ${sessionId}:`, error)
      throw error
    }
  },

  /**
   * Permanently delete a session
   */
  async deleteSession(sessionId: string): Promise<void> {
    try {
      await apiClient.delete(`/api/sessions/${sessionId}`)
    } catch (error) {
      console.error(`Failed to delete session ${sessionId}:`, error)
      throw error
    }
  },

  /**
   * Duplicate a session
   */
  async duplicateSession(sessionId: string): Promise<{
    message: string
    original_session_id: string
    new_session_id: string
  }> {
    try {
      const response = await apiClient.post(`/api/sessions/${sessionId}/duplicate`)
      return response.data
    } catch (error) {
      console.error(`Failed to duplicate session ${sessionId}:`, error)
      throw error
    }
  },

  /**
   * Compare multiple sessions
   */
  async compareSessions(sessionIds: string[]): Promise<{
    sessions: any[]
    count: number
  }> {
    try {
      const response = await apiClient.post('/api/sessions/compare', sessionIds)
      return response.data
    } catch (error) {
      console.error('Failed to compare sessions:', error)
      throw error
    }
  }
}

/**
 * Helper function to trigger file download in browser
 */
export function triggerFileDownload(blob: Blob, filename: string) {
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}

// NOTE: formatFileSize() moved to @/utils/file-display-utils.ts to follow DRY principle
// Import from there instead of duplicating here

// Extend AxiosRequestConfig to include metadata
declare module 'axios' {
  export interface AxiosRequestConfig {
    metadata?: {
      startTime: number
    }
  }
}

export default api

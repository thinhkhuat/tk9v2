/**
 * API client for HTTP requests to the TK9 Deep Research backend.
 * Handles research submissions, session management, and file downloads.
 */

import axios, { type AxiosInstance, type AxiosError } from 'axios'

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:12656'
const API_TIMEOUT = 30000 // 30 seconds

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
  }
})

// Request interceptor for logging and debugging
apiClient.interceptors.request.use(
  (config) => {
    const method = config.method?.toUpperCase()
    const url = config.url
    console.log(`→ ${method} ${url}`)

    // Add timestamp to request
    config.metadata = { startTime: Date.now() }

    return config
  },
  (error) => {
    console.error('Request error:', error)
    return Promise.reject(error)
  }
)

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
    try {
      const response = await apiClient.post<ResearchResponse>('/api/research', {
        subject,
        language
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
        timeout: 60000 // 60 seconds for large ZIPs
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

/**
 * Format bytes to human-readable size
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes'

  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

// Extend AxiosRequestConfig to include metadata
declare module 'axios' {
  export interface AxiosRequestConfig {
    metadata?: {
      startTime: number
    }
  }
}

export default api

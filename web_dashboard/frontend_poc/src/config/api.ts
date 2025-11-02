/**
 * API and Timing Configuration
 *
 * Centralized configuration for API timeouts and WebSocket settings.
 * All values are configurable via environment variables with sensible fallbacks.
 */

/**
 * Helper function to safely parse integer environment variables.
 * Handles edge cases: undefined, null, empty strings, non-numeric strings, and 0.
 *
 * @param envVar - The environment variable value (string | undefined)
 * @param defaultValue - The fallback value if parsing fails
 * @returns The parsed integer or default value
 */
function envToInt(envVar: string | undefined, defaultValue: number): number {
  if (envVar === undefined || envVar === null || envVar.trim() === '') {
    return defaultValue
  }
  const parsed = parseInt(envVar, 10)
  return isNaN(parsed) ? defaultValue : parsed
}

/**
 * API timeout for standard requests (milliseconds)
 * Default: 30 seconds
 */
export const API_TIMEOUT = envToInt(import.meta.env.VITE_API_TIMEOUT, 30000)

/**
 * Extended timeout for file download operations (milliseconds)
 * Default: 60 seconds (for large files)
 */
export const FILE_DOWNLOAD_TIMEOUT = envToInt(import.meta.env.VITE_FILE_DOWNLOAD_TIMEOUT, 60000)

/**
 * WebSocket reconnection delay (milliseconds)
 * Default: 3 seconds
 */
export const WS_RECONNECT_DELAY = envToInt(import.meta.env.VITE_WS_RECONNECT_DELAY, 3000)

/**
 * API base URL
 * Default: http://localhost:12656
 * Uses nullish coalescing (??) to only check for null/undefined, not empty strings
 */
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:12656'

/**
 * WebSocket base URL
 * Default: ws://localhost:12656
 */
export const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL ?? 'ws://localhost:12656'

/**
 * Configuration object for API settings
 */
export const API_CONFIG = {
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  fileDownloadTimeout: FILE_DOWNLOAD_TIMEOUT,
  wsBaseURL: WS_BASE_URL,
  wsReconnectDelay: WS_RECONNECT_DELAY,
} as const

export default API_CONFIG

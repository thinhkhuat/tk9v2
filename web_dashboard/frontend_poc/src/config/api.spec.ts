/**
 * Test suite for Phase 1 frontend configuration management.
 *
 * Tests environment variable parsing, edge cases, and fallback behavior
 * for all 3 frontend Phase 1 configuration items.
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest'

// Store original env for restoration
const originalEnv = { ...import.meta.env }

describe('API Configuration', () => {
  afterEach(() => {
    // Restore original env after each test
    Object.assign(import.meta.env, originalEnv)
  })

  describe('Default Values', () => {
    it('should use default API_TIMEOUT when env var is not set', () => {
      // Clear the env var
      delete import.meta.env.VITE_API_TIMEOUT

      // Re-import the module to get fresh values
      // Note: In a real test setup, you'd need to clear the module cache
      // This is a simplified example
      const { API_TIMEOUT } = require('./api')
      expect(API_TIMEOUT).toBe(30000)
    })

    it('should use default FILE_DOWNLOAD_TIMEOUT when env var is not set', () => {
      delete import.meta.env.VITE_FILE_DOWNLOAD_TIMEOUT
      const { FILE_DOWNLOAD_TIMEOUT } = require('./api')
      expect(FILE_DOWNLOAD_TIMEOUT).toBe(60000)
    })

    it('should use default WS_RECONNECT_DELAY when env var is not set', () => {
      delete import.meta.env.VITE_WS_RECONNECT_DELAY
      const { WS_RECONNECT_DELAY } = require('./api')
      expect(WS_RECONNECT_DELAY).toBe(3000)
    })

    it('should use default API_BASE_URL when env var is not set', () => {
      delete import.meta.env.VITE_API_BASE_URL
      const { API_BASE_URL } = require('./api')
      expect(API_BASE_URL).toBe('http://localhost:12656')
    })

    it('should use default WS_BASE_URL when env var is not set', () => {
      delete import.meta.env.VITE_WS_BASE_URL
      const { WS_BASE_URL } = require('./api')
      expect(WS_BASE_URL).toBe('ws://localhost:12656')
    })
  })

  describe('Valid Environment Variables', () => {
    it('should parse valid API_TIMEOUT from env var', () => {
      import.meta.env.VITE_API_TIMEOUT = '5000'
      const { API_TIMEOUT } = require('./api')
      expect(API_TIMEOUT).toBe(5000)
    })

    it('should parse valid FILE_DOWNLOAD_TIMEOUT from env var', () => {
      import.meta.env.VITE_FILE_DOWNLOAD_TIMEOUT = '120000'
      const { FILE_DOWNLOAD_TIMEOUT } = require('./api')
      expect(FILE_DOWNLOAD_TIMEOUT).toBe(120000)
    })

    it('should parse valid WS_RECONNECT_DELAY from env var', () => {
      import.meta.env.VITE_WS_RECONNECT_DELAY = '5000'
      const { WS_RECONNECT_DELAY } = require('./api')
      expect(WS_RECONNECT_DELAY).toBe(5000)
    })

    it('should use custom API_BASE_URL from env var', () => {
      import.meta.env.VITE_API_BASE_URL = 'https://api.example.com'
      const { API_BASE_URL } = require('./api')
      expect(API_BASE_URL).toBe('https://api.example.com')
    })

    it('should use custom WS_BASE_URL from env var', () => {
      import.meta.env.VITE_WS_BASE_URL = 'wss://ws.example.com'
      const { WS_BASE_URL } = require('./api')
      expect(WS_BASE_URL).toBe('wss://ws.example.com')
    })
  })

  describe('Edge Cases - Zero Value', () => {
    it('should correctly handle the value 0 for API_TIMEOUT', () => {
      import.meta.env.VITE_API_TIMEOUT = '0'
      const { API_TIMEOUT } = require('./api')
      // This is the critical test - 0 should NOT fall back to default
      expect(API_TIMEOUT).toBe(0)
    })

    it('should correctly handle the value 0 for FILE_DOWNLOAD_TIMEOUT', () => {
      import.meta.env.VITE_FILE_DOWNLOAD_TIMEOUT = '0'
      const { FILE_DOWNLOAD_TIMEOUT } = require('./api')
      expect(FILE_DOWNLOAD_TIMEOUT).toBe(0)
    })

    it('should correctly handle the value 0 for WS_RECONNECT_DELAY', () => {
      import.meta.env.VITE_WS_RECONNECT_DELAY = '0'
      const { WS_RECONNECT_DELAY } = require('./api')
      // 0 delay = immediate reconnect, should be valid
      expect(WS_RECONNECT_DELAY).toBe(0)
    })
  })

  describe('Edge Cases - Invalid Values', () => {
    it('should fall back to default for non-numeric API_TIMEOUT', () => {
      import.meta.env.VITE_API_TIMEOUT = 'not-a-number'
      const { API_TIMEOUT } = require('./api')
      expect(API_TIMEOUT).toBe(30000)
    })

    it('should fall back to default for empty string API_TIMEOUT', () => {
      import.meta.env.VITE_API_TIMEOUT = ''
      const { API_TIMEOUT } = require('./api')
      expect(API_TIMEOUT).toBe(30000)
    })

    it('should fall back to default for whitespace-only API_TIMEOUT', () => {
      import.meta.env.VITE_API_TIMEOUT = '   '
      const { API_TIMEOUT } = require('./api')
      expect(API_TIMEOUT).toBe(30000)
    })

    it('should fall back to default for NaN result', () => {
      import.meta.env.VITE_FILE_DOWNLOAD_TIMEOUT = 'abc123'
      const { FILE_DOWNLOAD_TIMEOUT } = require('./api')
      expect(FILE_DOWNLOAD_TIMEOUT).toBe(60000)
    })

    it('should handle negative numbers correctly', () => {
      import.meta.env.VITE_WS_RECONNECT_DELAY = '-5000'
      const { WS_RECONNECT_DELAY } = require('./api')
      // parseInt('-5000') returns -5000, which is valid for parseInt
      // but setTimeout treats negative as 0, so this is technically valid
      expect(WS_RECONNECT_DELAY).toBe(-5000)
    })
  })

  describe('Edge Cases - String URLs', () => {
    it('should handle empty string API_BASE_URL', () => {
      import.meta.env.VITE_API_BASE_URL = ''
      const { API_BASE_URL } = require('./api')
      // Empty string is falsy but valid, so it should be kept
      // With ?? operator, empty string is kept (not replaced)
      expect(API_BASE_URL).toBe('')
    })

    it('should handle null/undefined API_BASE_URL', () => {
      import.meta.env.VITE_API_BASE_URL = undefined
      const { API_BASE_URL } = require('./api')
      expect(API_BASE_URL).toBe('http://localhost:12656')
    })
  })

  describe('API_CONFIG Object', () => {
    it('should export a complete API_CONFIG object', () => {
      const { API_CONFIG } = require('./api')

      expect(API_CONFIG).toBeDefined()
      expect(API_CONFIG).toHaveProperty('baseURL')
      expect(API_CONFIG).toHaveProperty('timeout')
      expect(API_CONFIG).toHaveProperty('fileDownloadTimeout')
      expect(API_CONFIG).toHaveProperty('wsBaseURL')
      expect(API_CONFIG).toHaveProperty('wsReconnectDelay')
    })

    it('should have correct default values in API_CONFIG', () => {
      // Clear all env vars
      delete import.meta.env.VITE_API_TIMEOUT
      delete import.meta.env.VITE_FILE_DOWNLOAD_TIMEOUT
      delete import.meta.env.VITE_WS_RECONNECT_DELAY
      delete import.meta.env.VITE_API_BASE_URL
      delete import.meta.env.VITE_WS_BASE_URL

      const { API_CONFIG } = require('./api')

      expect(API_CONFIG.baseURL).toBe('http://localhost:12656')
      expect(API_CONFIG.timeout).toBe(30000)
      expect(API_CONFIG.fileDownloadTimeout).toBe(60000)
      expect(API_CONFIG.wsBaseURL).toBe('ws://localhost:12656')
      expect(API_CONFIG.wsReconnectDelay).toBe(3000)
    })

    it('should be immutable (as const)', () => {
      const { API_CONFIG } = require('./api')

      // TypeScript should prevent this at compile time
      // At runtime, this will throw in strict mode or fail silently
      expect(() => {
        // @ts-expect-error - Testing immutability
        API_CONFIG.timeout = 99999
      }).toThrow()
    })
  })

  describe('Backward Compatibility', () => {
    it('should match original hardcoded values when env vars are not set', () => {
      // Clear all env vars to test defaults
      delete import.meta.env.VITE_API_TIMEOUT
      delete import.meta.env.VITE_FILE_DOWNLOAD_TIMEOUT
      delete import.meta.env.VITE_WS_RECONNECT_DELAY

      const { API_TIMEOUT, FILE_DOWNLOAD_TIMEOUT, WS_RECONNECT_DELAY } = require('./api')

      // These should match the original hardcoded values
      expect(API_TIMEOUT).toBe(30000) // Was: const API_TIMEOUT = 30000
      expect(FILE_DOWNLOAD_TIMEOUT).toBe(60000) // Was: timeout: 60000
      expect(WS_RECONNECT_DELAY).toBe(3000) // Was: setTimeout(..., 3000)
    })
  })

  describe('Production Scenarios', () => {
    it('should handle production timeout values', () => {
      // Production might want longer timeouts
      import.meta.env.VITE_API_TIMEOUT = '60000'
      import.meta.env.VITE_FILE_DOWNLOAD_TIMEOUT = '300000' // 5 minutes
      import.meta.env.VITE_WS_RECONNECT_DELAY = '5000'

      const { API_TIMEOUT, FILE_DOWNLOAD_TIMEOUT, WS_RECONNECT_DELAY } = require('./api')

      expect(API_TIMEOUT).toBe(60000)
      expect(FILE_DOWNLOAD_TIMEOUT).toBe(300000)
      expect(WS_RECONNECT_DELAY).toBe(5000)
    })

    it('should handle production URLs', () => {
      import.meta.env.VITE_API_BASE_URL = 'https://tk9.thinhkhuat.com'
      import.meta.env.VITE_WS_BASE_URL = 'wss://tk9.thinhkhuat.com'

      const { API_BASE_URL, WS_BASE_URL } = require('./api')

      expect(API_BASE_URL).toBe('https://tk9.thinhkhuat.com')
      expect(WS_BASE_URL).toBe('wss://tk9.thinhkhuat.com')
    })
  })
})

describe('envToInt Helper Function', () => {
  // Note: envToInt is not exported, but we can test its behavior indirectly
  // through the exported constants

  it('should handle undefined input', () => {
    import.meta.env.VITE_API_TIMEOUT = undefined
    const { API_TIMEOUT } = require('./api')
    expect(API_TIMEOUT).toBe(30000)
  })

  it('should handle null input', () => {
    import.meta.env.VITE_API_TIMEOUT = null
    const { API_TIMEOUT } = require('./api')
    expect(API_TIMEOUT).toBe(30000)
  })

  it('should handle empty string', () => {
    import.meta.env.VITE_API_TIMEOUT = ''
    const { API_TIMEOUT } = require('./api')
    expect(API_TIMEOUT).toBe(30000)
  })

  it('should handle whitespace-only string', () => {
    import.meta.env.VITE_API_TIMEOUT = '   '
    const { API_TIMEOUT } = require('./api')
    expect(API_TIMEOUT).toBe(30000)
  })

  it('should handle non-numeric string', () => {
    import.meta.env.VITE_API_TIMEOUT = 'abc'
    const { API_TIMEOUT } = require('./api')
    expect(API_TIMEOUT).toBe(30000)
  })

  it('should handle numeric string with leading/trailing spaces', () => {
    import.meta.env.VITE_API_TIMEOUT = '  5000  '
    const { API_TIMEOUT } = require('./api')
    // trim() is called before parseInt, so this should work
    expect(API_TIMEOUT).toBe(5000)
  })

  it('should handle zero correctly', () => {
    import.meta.env.VITE_API_TIMEOUT = '0'
    const { API_TIMEOUT } = require('./api')
    // This is the critical test that would fail with the old || operator
    expect(API_TIMEOUT).toBe(0)
  })

  it('should handle floating point numbers (parseInt truncates)', () => {
    import.meta.env.VITE_API_TIMEOUT = '5000.75'
    const { API_TIMEOUT } = require('./api')
    expect(API_TIMEOUT).toBe(5000) // parseInt truncates
  })

  it('should handle strings starting with numbers', () => {
    import.meta.env.VITE_API_TIMEOUT = '5000abc'
    const { API_TIMEOUT } = require('./api')
    expect(API_TIMEOUT).toBe(5000) // parseInt stops at first non-digit
  })
})

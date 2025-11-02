/**
 * Validation Configuration
 *
 * Centralized validation rules that must match backend constraints.
 * Values are read from environment variables with sensible fallbacks.
 *
 * IMPORTANT: Keep in sync with backend validation in:
 * - web_dashboard/models.py (ResearchRequest Pydantic model)
 * - web_dashboard/.env.example
 */

export const VALIDATION_CONFIG = {
  /**
   * Research subject validation constraints
   */
  subject: {
    minLength: parseInt(import.meta.env.VITE_MIN_SUBJECT_LENGTH) || 3,
    maxLength: parseInt(import.meta.env.VITE_MAX_SUBJECT_LENGTH) || 1000,
  },

  /**
   * Helper method to validate subject string
   */
  validateSubject(subject: string): { valid: boolean; error?: string } {
    const trimmed = subject.trim()

    if (!trimmed) {
      return { valid: false, error: 'Research subject is required' }
    }

    if (trimmed.length < this.subject.minLength) {
      return {
        valid: false,
        error: `Subject must be at least ${this.subject.minLength} characters`,
      }
    }

    if (trimmed.length > this.subject.maxLength) {
      return {
        valid: false,
        error: `Subject must be at most ${this.subject.maxLength} characters`,
      }
    }

    return { valid: true }
  },
}

/**
 * Export individual constants for convenience
 */
export const MIN_SUBJECT_LENGTH = VALIDATION_CONFIG.subject.minLength
export const MAX_SUBJECT_LENGTH = VALIDATION_CONFIG.subject.maxLength

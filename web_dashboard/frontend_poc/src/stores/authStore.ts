/**
 * Authentication store for managing Supabase anonymous authentication.
 * Handles automatic sign-in, session persistence, and user state.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { supabase } from '@/utils/supabase'
import type { User, Session } from '@supabase/supabase-js'
import { useToast } from 'vue-toastification'

const toast = useToast()

export const useAuthStore = defineStore('auth', () => {
  // ============================================================================
  // State
  // ============================================================================

  const user = ref<User | null>(null)
  const session = ref<Session | null>(null)
  const isInitializing = ref(false)
  const error = ref<string | null>(null)

  // ============================================================================
  // Computed Properties
  // ============================================================================

  const isAuthenticated = computed(() => !!user.value)
  const isAnonymous = computed(() => user.value?.is_anonymous ?? false)
  const userId = computed(() => user.value?.id ?? null)

  // ============================================================================
  // Actions
  // ============================================================================

  /**
   * Sign in anonymously using Supabase Auth.
   * Creates a new anonymous user session automatically.
   */
  async function signInAnonymously() {
    try {
      isInitializing.value = true
      error.value = null

      console.log('[AuthStore] Initiating anonymous sign-in...')

      const { data, error: signInError } = await supabase.auth.signInAnonymously()

      if (signInError) {
        throw signInError
      }

      if (!data.user || !data.session) {
        throw new Error('No user or session returned from anonymous sign-in')
      }

      user.value = data.user
      session.value = data.session

      console.log('[AuthStore] Anonymous sign-in successful:', {
        userId: data.user.id,
        isAnonymous: data.user.is_anonymous
      })

      return data
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to sign in anonymously'
      error.value = errorMessage
      console.error('[AuthStore] Anonymous sign-in failed:', err)

      toast.error('Authentication failed. Please refresh the page.')
      throw err
    } finally {
      isInitializing.value = false
    }
  }

  /**
   * Restore existing session from Supabase storage.
   * Checks for existing valid session on app mount.
   */
  async function restoreSession() {
    try {
      isInitializing.value = true
      error.value = null

      console.log('[AuthStore] Checking for existing session...')

      const { data: { session: existingSession }, error: sessionError } =
        await supabase.auth.getSession()

      if (sessionError) {
        throw sessionError
      }

      if (existingSession) {
        session.value = existingSession
        user.value = existingSession.user

        console.log('[AuthStore] Session restored:', {
          userId: existingSession.user.id,
          isAnonymous: existingSession.user.is_anonymous
        })

        return true
      }

      console.log('[AuthStore] No existing session found')
      return false
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to restore session'
      error.value = errorMessage
      console.error('[AuthStore] Session restoration failed:', err)

      // Don't show toast for restoration failures - will auto sign-in instead
      return false
    } finally {
      isInitializing.value = false
    }
  }

  /**
   * Initialize authentication on app mount.
   * Restores existing session or creates new anonymous session.
   */
  async function initializeAuth() {
    try {
      // First, try to restore existing session
      const hasSession = await restoreSession()

      // If no session exists, create a new anonymous session
      if (!hasSession) {
        console.log('[AuthStore] No session found, creating anonymous session...')
        await signInAnonymously()
      }

      // Setup auth state change listener
      supabase.auth.onAuthStateChange((event, newSession) => {
        console.log('[AuthStore] Auth state changed:', event)

        if (newSession) {
          session.value = newSession
          user.value = newSession.user
        } else {
          session.value = null
          user.value = null
        }
      })
    } catch (err) {
      console.error('[AuthStore] Auth initialization failed:', err)
      // Let the error bubble up so App.vue can handle it
      throw err
    }
  }

  /**
   * Sign out the current user.
   * Clears session and user state.
   */
  async function signOut() {
    try {
      const { error: signOutError } = await supabase.auth.signOut()

      if (signOutError) {
        throw signOutError
      }

      user.value = null
      session.value = null

      console.log('[AuthStore] Signed out successfully')
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to sign out'
      error.value = errorMessage
      console.error('[AuthStore] Sign out failed:', err)

      toast.error('Failed to sign out. Please try again.')
      throw err
    }
  }

  /**
   * Register a new user with email and password (upgrade from anonymous).
   * Transfers anonymous research sessions to the new permanent account.
   */
  async function registerWithEmail(email: string, password: string) {
    try {
      isInitializing.value = true
      error.value = null

      console.log('[AuthStore] Starting email registration...')

      // Store old user ID for session transfer
      const oldUserId = user.value?.id

      // Sign up with Supabase
      const { data, error: signUpError } = await supabase.auth.signUp({
        email,
        password
      })

      if (signUpError) {
        throw signUpError
      }

      if (!data.user || !data.session) {
        throw new Error('No user or session returned from sign up')
      }

      // Update local state
      user.value = data.user
      session.value = data.session

      console.log('[AuthStore] Email registration successful:', {
        userId: data.user.id,
        email: data.user.email
      })

      // Transfer anonymous sessions if user was previously anonymous
      if (oldUserId && oldUserId !== data.user.id) {
        try {
          const transferredCount = await transferAnonymousSessions(oldUserId, data.user.id)
          console.log(`[AuthStore] Transferred ${transferredCount} research sessions`)
        } catch (transferErr) {
          console.error('[AuthStore] Session transfer failed:', transferErr)
          // Don't fail registration if transfer fails - user account is still created
          toast.warning('Account created, but failed to transfer some research sessions.')
        }
      }

      toast.success('Account created! Check your email for verification.')
      return data
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to register'
      error.value = errorMessage
      console.error('[AuthStore] Email registration failed:', err)

      // Parse specific error types for better UX
      if (errorMessage.includes('already registered') || errorMessage.includes('User already registered')) {
        toast.error('This email is already registered. Try signing in instead.')
      } else {
        toast.error('Registration failed. Please try again.')
      }
      throw err
    } finally {
      isInitializing.value = false
    }
  }

  /**
   * Sign in with email and password.
   * For users with permanent accounts.
   */
  async function signInWithEmail(email: string, password: string) {
    try {
      isInitializing.value = true
      error.value = null

      console.log('[AuthStore] Starting email sign-in...')

      const { data, error: signInError } = await supabase.auth.signInWithPassword({
        email,
        password
      })

      if (signInError) {
        throw signInError
      }

      if (!data.user || !data.session) {
        throw new Error('No user or session returned from sign in')
      }

      user.value = data.user
      session.value = data.session

      console.log('[AuthStore] Email sign-in successful:', {
        userId: data.user.id,
        email: data.user.email
      })

      toast.success('Welcome back!')
      return data
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to sign in'
      error.value = errorMessage
      console.error('[AuthStore] Email sign-in failed:', err)

      // Parse specific error types
      if (errorMessage.includes('Invalid login credentials')) {
        toast.error('Invalid email or password.')
      } else if (errorMessage.includes('Email not confirmed')) {
        toast.error('Please verify your email before signing in.')
      } else {
        toast.error('Sign in failed. Please try again.')
      }
      throw err
    } finally {
      isInitializing.value = false
    }
  }

  /**
   * Reset password for a user by email.
   * Sends password reset link to the user's email.
   */
  async function resetPassword(email: string) {
    try {
      error.value = null

      console.log('[AuthStore] Sending password reset email...')

      const { error: resetError } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/auth/reset-password`
      })

      if (resetError) {
        throw resetError
      }

      console.log('[AuthStore] Password reset email sent successfully')
      toast.success('Password reset link sent! Check your email.')
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to send reset email'
      error.value = errorMessage
      console.error('[AuthStore] Password reset failed:', err)

      toast.error('Failed to send reset email. Please try again.')
      throw err
    }
  }

  /**
   * Transfer anonymous research sessions to permanent account.
   * Called after successful registration.
   */
  async function transferAnonymousSessions(oldUserId: string, newUserId: string): Promise<number> {
    try {
      console.log('[AuthStore] Transferring sessions:', { oldUserId, newUserId })

      // Call backend API endpoint (to be implemented in Task 4)
      const response = await fetch('/api/auth/transfer-sessions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include', // Include cookies for JWT auth
        body: JSON.stringify({
          old_user_id: oldUserId,
          new_user_id: newUserId
        })
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.error?.message || 'Session transfer failed')
      }

      const data = await response.json()
      return data.transferred_count || 0
    } catch (err) {
      console.error('[AuthStore] Session transfer error:', err)
      throw err
    }
  }

  // ============================================================================
  // Return Public API
  // ============================================================================

  return {
    // State
    user,
    session,
    isInitializing,
    error,

    // Computed
    isAuthenticated,
    isAnonymous,
    userId,

    // Actions
    signInAnonymously,
    restoreSession,
    initializeAuth,
    signOut,
    registerWithEmail,
    signInWithEmail,
    resetPassword
  }
})

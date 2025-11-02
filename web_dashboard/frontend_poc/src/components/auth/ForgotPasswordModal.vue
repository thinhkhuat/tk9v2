<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="show"
        class="fixed inset-0 z-50 overflow-y-auto"
        @click.self="closeModal"
      >
        <!-- Backdrop -->
        <div class="fixed inset-0 bg-black/50 backdrop-blur-sm transition-opacity"></div>

        <!-- Modal container -->
        <div class="flex min-h-screen items-center justify-center p-4">
          <div
            class="relative w-full max-w-md transform rounded-xl bg-white shadow-2xl transition-all"
            @click.stop
          >
            <!-- Close button -->
            <button
              @click="closeModal"
              class="absolute right-4 top-4 text-gray-400 hover:text-gray-600 transition-colors"
              aria-label="Close"
            >
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>

            <!-- Header -->
            <div class="border-b border-gray-200 px-6 py-5">
              <h2 class="text-2xl font-bold text-gray-900">Reset Password</h2>
              <p class="mt-1 text-sm text-gray-600">
                Enter your email and we'll send you a reset link
              </p>
            </div>

            <!-- Form -->
            <form @submit.prevent="handleSubmit" class="px-6 py-6 space-y-5">
              <!-- Email field -->
              <div>
                <label for="reset-email" class="block text-sm font-medium text-gray-700 mb-1">
                  Email Address
                </label>
                <input
                  id="reset-email"
                  v-model="email"
                  type="email"
                  required
                  autocomplete="email"
                  class="w-full px-4 py-2.5 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors"
                  :class="{
                    'border-red-300 focus:ring-red-500 focus:border-red-500': emailError
                  }"
                  placeholder="you@example.com"
                  @blur="validateEmail"
                  @input="emailError = ''"
                />
                <p v-if="emailError" class="mt-1 text-sm text-red-600">{{ emailError }}</p>
              </div>

              <!-- Error message -->
              <div v-if="errorMessage" class="rounded-lg bg-red-50 p-4">
                <div class="flex">
                  <svg class="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
                  </svg>
                  <p class="ml-3 text-sm text-red-800">{{ errorMessage }}</p>
                </div>
              </div>

              <!-- Success message -->
              <div v-if="successMessage" class="rounded-lg bg-green-50 p-4">
                <div class="flex">
                  <svg class="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                  </svg>
                  <p class="ml-3 text-sm text-green-800">{{ successMessage }}</p>
                </div>
              </div>

              <!-- Submit button -->
              <button
                type="submit"
                :disabled="isLoading || !email || !!successMessage"
                class="w-full bg-indigo-600 text-white font-semibold py-3 px-6 rounded-lg hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              >
                <span v-if="!isLoading">Send Reset Link</span>
                <span v-else class="flex items-center justify-center">
                  <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Sending...
                </span>
              </button>
            </form>

            <!-- Footer -->
            <div class="border-t border-gray-200 px-6 py-4 bg-gray-50 rounded-b-xl">
              <p class="text-xs text-gray-600 text-center">
                Remember your password?
                <button
                  @click="$emit('show-login')"
                  class="text-indigo-600 hover:text-indigo-500 font-medium"
                >
                  Sign In
                </button>
              </p>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useAuthStore } from '@/stores/authStore'

const authStore = useAuthStore()

// Props
const props = defineProps<{
  show: boolean
}>()

// Emits
const emit = defineEmits<{
  (e: 'close'): void
  (e: 'show-login'): void
}>()

// Form state
const email = ref('')
const isLoading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const emailError = ref('')

// RFC 5322 Email validation regex
const EMAIL_REGEX = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/

// Validation
const validateEmail = () => {
  if (!email.value) {
    emailError.value = 'Email is required'
    return false
  }
  if (!EMAIL_REGEX.test(email.value)) {
    emailError.value = 'Please enter a valid email address'
    return false
  }
  emailError.value = ''
  return true
}

// Actions
const closeModal = () => {
  if (!isLoading.value) {
    resetForm()
    emit('close')
  }
}

const resetForm = () => {
  email.value = ''
  errorMessage.value = ''
  successMessage.value = ''
  emailError.value = ''
}

const handleSubmit = async () => {
  // Clear previous messages
  errorMessage.value = ''
  successMessage.value = ''

  // Validate email
  if (!validateEmail()) {
    return
  }

  isLoading.value = true

  try {
    // Call authStore password reset method
    await authStore.resetPassword(email.value)

    // Success
    successMessage.value = 'Password reset link sent to your email!'

    // Auto-close after delay
    setTimeout(() => {
      closeModal()
    }, 3000)
  } catch (err: any) {
    console.error('[ForgotPasswordModal] Password reset failed:', err)
    errorMessage.value = 'Failed to send reset email. Please try again.'
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
/* Modal transition */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .transform,
.modal-leave-active .transform {
  transition: transform 0.3s ease;
}

.modal-enter-from .transform,
.modal-leave-to .transform {
  transform: scale(0.95);
}
</style>

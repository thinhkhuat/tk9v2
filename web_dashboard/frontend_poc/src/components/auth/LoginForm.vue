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
              <h2 class="text-2xl font-bold text-gray-900">Welcome Back</h2>
              <p class="mt-1 text-sm text-gray-600">
                Sign in to access your research history
              </p>
            </div>

            <!-- Form -->
            <form @submit.prevent="handleSubmit" class="px-6 py-6 space-y-5">
              <!-- Email field -->
              <div>
                <label for="login-email" class="block text-sm font-medium text-gray-700 mb-1">
                  Email Address
                </label>
                <input
                  id="login-email"
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

              <!-- Password field -->
              <div>
                <div class="flex items-center justify-between mb-1">
                  <label for="login-password" class="block text-sm font-medium text-gray-700">
                    Password
                  </label>
                  <button
                    type="button"
                    @click="$emit('show-forgot-password')"
                    class="text-sm text-indigo-600 hover:text-indigo-500 font-medium"
                  >
                    Forgot Password?
                  </button>
                </div>
                <div class="relative">
                  <input
                    id="login-password"
                    v-model="password"
                    :type="showPassword ? 'text' : 'password'"
                    required
                    autocomplete="current-password"
                    class="w-full px-4 py-2.5 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors pr-10"
                    placeholder="Enter your password"
                    @input="errorMessage = ''"
                  />
                  <button
                    type="button"
                    @click="showPassword = !showPassword"
                    class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                    aria-label="Toggle password visibility"
                  >
                    <svg v-if="!showPassword" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                    <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                    </svg>
                  </button>
                </div>
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

              <!-- Submit button -->
              <button
                type="submit"
                :disabled="isLoading || !email || !password"
                class="w-full bg-indigo-600 text-white font-semibold py-3 px-6 rounded-lg hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              >
                <span v-if="!isLoading">Sign In</span>
                <span v-else class="flex items-center justify-center">
                  <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Signing in...
                </span>
              </button>
            </form>

            <!-- Footer -->
            <div class="border-t border-gray-200 px-6 py-4 bg-gray-50 rounded-b-xl">
              <p class="text-xs text-gray-600 text-center">
                Don't have an account?
                <button
                  @click="$emit('show-registration')"
                  class="text-indigo-600 hover:text-indigo-500 font-medium"
                >
                  Create Account
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
  (e: 'show-registration'): void
  (e: 'show-forgot-password'): void
  (e: 'login-success'): void
}>()

// Form state
const email = ref('')
const password = ref('')
const showPassword = ref(false)
const isLoading = ref(false)
const errorMessage = ref('')
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
  password.value = ''
  showPassword.value = false
  errorMessage.value = ''
  emailError.value = ''
}

const handleSubmit = async () => {
  // Clear previous messages
  errorMessage.value = ''

  // Validate email
  if (!validateEmail()) {
    return
  }

  if (!password.value) {
    errorMessage.value = 'Please enter your password'
    return
  }

  isLoading.value = true

  try {
    // Call authStore login method
    await authStore.signInWithEmail(email.value, password.value)

    // Success - emit event and redirect
    emit('login-success')
    closeModal()

    // Redirect to dashboard (or stay on current page)
    // router.push('/') // Uncomment when routes are set up
  } catch (err: any) {
    console.error('[LoginForm] Login failed:', err)
    // Error already handled by authStore with toast
    // Just show inline error message
    errorMessage.value = 'Login failed. Please check your credentials.'
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

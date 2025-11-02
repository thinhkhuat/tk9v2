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
              <h2 class="text-2xl font-bold text-gray-900">Create Your Account</h2>
              <p class="mt-1 text-sm text-gray-600">
                Preserve your research history and access it from anywhere
              </p>
            </div>

            <!-- Form -->
            <form @submit.prevent="handleSubmit" class="px-6 py-6 space-y-5">
              <!-- Email field -->
              <div>
                <label for="email" class="block text-sm font-medium text-gray-700 mb-1">
                  Email Address
                </label>
                <input
                  id="email"
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
                <label for="password" class="block text-sm font-medium text-gray-700 mb-1">
                  Password
                </label>
                <div class="relative">
                  <input
                    id="password"
                    v-model="password"
                    :type="showPassword ? 'text' : 'password'"
                    required
                    autocomplete="new-password"
                    class="w-full px-4 py-2.5 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors pr-10"
                    :class="{
                      'border-red-300 focus:ring-red-500 focus:border-red-500': passwordError
                    }"
                    placeholder="Minimum 8 characters"
                    @blur="validatePassword"
                    @input="passwordError = ''"
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
                <p v-if="passwordError" class="mt-1 text-sm text-red-600">{{ passwordError }}</p>

                <!-- Password requirements -->
                <ul class="mt-2 text-xs space-y-1">
                  <li :class="password.length >= 8 ? 'text-green-600' : 'text-gray-500'">
                    <span class="mr-1">{{ password.length >= 8 ? '✓' : '○' }}</span>
                    At least 8 characters
                  </li>
                  <li :class="/[A-Z]/.test(password) ? 'text-green-600' : 'text-gray-500'">
                    <span class="mr-1">{{ /[A-Z]/.test(password) ? '✓' : '○' }}</span>
                    One uppercase letter
                  </li>
                  <li :class="/[a-z]/.test(password) ? 'text-green-600' : 'text-gray-500'">
                    <span class="mr-1">{{ /[a-z]/.test(password) ? '✓' : '○' }}</span>
                    One lowercase letter
                  </li>
                  <li :class="/[0-9]/.test(password) ? 'text-green-600' : 'text-gray-500'">
                    <span class="mr-1">{{ /[0-9]/.test(password) ? '✓' : '○' }}</span>
                    One number
                  </li>
                </ul>
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
                :disabled="isLoading || !isFormValid"
                class="w-full bg-indigo-600 text-white font-semibold py-3 px-6 rounded-lg hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              >
                <span v-if="!isLoading">Create Account</span>
                <span v-else class="flex items-center justify-center">
                  <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Creating account...
                </span>
              </button>
            </form>

            <!-- Footer -->
            <div class="border-t border-gray-200 px-6 py-4 bg-gray-50 rounded-b-xl">
              <p class="text-xs text-gray-600 text-center">
                Already have an account?
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
import { ref, computed } from 'vue'
import { useAuthStore } from '@/stores/authStore'
import { useToast } from 'vue-toastification'

const toast = useToast()
const authStore = useAuthStore()

// Props (unused in script, but exposed to template automatically)
defineProps<{
  show: boolean
}>()

// Emits
const emit = defineEmits<{
  (e: 'close'): void
  (e: 'show-login'): void
  (e: 'registration-success'): void
}>()

// Form state
const email = ref('')
const password = ref('')
const showPassword = ref(false)
const isLoading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const emailError = ref('')
const passwordError = ref('')

// RFC 5322 Email validation regex (simplified but compliant)
const EMAIL_REGEX = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/

// Password validation: min 8 chars, 1 uppercase, 1 lowercase, 1 number
const PASSWORD_REGEX = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/

// Validation functions
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

const validatePassword = () => {
  if (!password.value) {
    passwordError.value = 'Password is required'
    return false
  }
  if (password.value.length < 8) {
    passwordError.value = 'Password must be at least 8 characters'
    return false
  }
  if (!/[A-Z]/.test(password.value)) {
    passwordError.value = 'Password must contain at least one uppercase letter'
    return false
  }
  if (!/[a-z]/.test(password.value)) {
    passwordError.value = 'Password must contain at least one lowercase letter'
    return false
  }
  if (!/[0-9]/.test(password.value)) {
    passwordError.value = 'Password must contain at least one number'
    return false
  }
  passwordError.value = ''
  return true
}

// Computed: Is form valid
const isFormValid = computed(() => {
  return (
    email.value &&
    password.value &&
    EMAIL_REGEX.test(email.value) &&
    PASSWORD_REGEX.test(password.value) &&
    !emailError.value &&
    !passwordError.value
  )
})

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
  successMessage.value = ''
  emailError.value = ''
  passwordError.value = ''
}

const handleSubmit = async () => {
  // Clear previous messages
  errorMessage.value = ''
  successMessage.value = ''

  // Validate fields
  const isEmailValid = validateEmail()
  const isPasswordValid = validatePassword()

  if (!isEmailValid || !isPasswordValid) {
    return
  }

  isLoading.value = true

  try {
    // Call authStore registration method (to be implemented in Task 3)
    await authStore.registerWithEmail(email.value, password.value)

    // Success
    successMessage.value = 'Account created! Check your email for verification.'
    toast.success('Account created successfully! Check your email for verification.')

    // Emit success event
    emit('registration-success')

    // Close modal after short delay
    setTimeout(() => {
      closeModal()
    }, 2000)
  } catch (err: any) {
    // Handle errors
    console.error('[RegistrationModal] Registration failed:', err)

    // Parse error message
    if (err.message?.includes('already registered') || err.message?.includes('already exists')) {
      errorMessage.value = 'This email is already registered. Try signing in instead.'
    } else if (err.message?.includes('network') || err.message?.includes('fetch')) {
      errorMessage.value = 'Network error. Please check your connection and try again.'
    } else {
      errorMessage.value = err.message || 'Registration failed. Please try again.'
    }

    toast.error(errorMessage.value)
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

<!--
  ConfirmDialog.vue - Reusable confirmation dialog component
  Replaces browser confirm() with proper UI component
-->

<script setup lang="ts">
import { computed } from 'vue'

export type ConfirmVariant = 'warning' | 'danger' | 'info'

const props = withDefaults(defineProps<{
  isOpen: boolean
  title: string
  message: string
  confirmLabel?: string
  cancelLabel?: string
  variant?: ConfirmVariant
}>(), {
  confirmLabel: 'Confirm',
  cancelLabel: 'Cancel',
  variant: 'warning'
})

const emit = defineEmits<{
  (e: 'confirm'): void
  (e: 'cancel'): void
}>()

// Variant-specific button colors
const confirmButtonClass = computed(() => {
  const variants = {
    warning: 'bg-yellow-500 hover:bg-yellow-600 text-white',
    danger: 'bg-red-500 hover:bg-red-600 text-white',
    info: 'bg-blue-500 hover:bg-blue-600 text-white'
  }
  return variants[props.variant]
})

// Variant-specific icon colors
const iconColorClass = computed(() => {
  const variants = {
    warning: 'text-yellow-500',
    danger: 'text-red-500',
    info: 'text-blue-500'
  }
  return variants[props.variant]
})

function handleConfirm() {
  emit('confirm')
}

function handleCancel() {
  emit('cancel')
}

// Handle backdrop click
function handleBackdropClick(event: MouseEvent) {
  if (event.target === event.currentTarget) {
    handleCancel()
  }
}

// Handle escape key
function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') {
    handleCancel()
  }
}
</script>

<template>
  <!-- Modal Backdrop -->
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="isOpen"
        class="fixed inset-0 z-[60] flex items-center justify-center bg-black bg-opacity-50 p-4"
        @click="handleBackdropClick"
        @keydown="handleKeydown"
      >
        <!-- Dialog Container -->
        <div
          class="bg-white rounded-lg shadow-2xl w-full max-w-md"
          @click.stop
        >
          <!-- Icon and Content -->
          <div class="p-6">
            <div class="flex items-start gap-4">
              <!-- Warning/Danger Icon -->
              <div class="flex-shrink-0">
                <svg
                  :class="iconColorClass"
                  class="w-8 h-8"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    v-if="variant === 'danger' || variant === 'warning'"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                  />
                  <path
                    v-else
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>

              <!-- Text Content -->
              <div class="flex-1">
                <h3 class="text-lg font-semibold text-gray-900 mb-2">
                  {{ title }}
                </h3>
                <p class="text-sm text-gray-600">
                  {{ message }}
                </p>
              </div>
            </div>
          </div>

          <!-- Actions -->
          <div class="bg-gray-50 px-6 py-4 flex items-center justify-end gap-3 rounded-b-lg">
            <button
              @click="handleCancel"
              class="px-4 py-2 bg-white hover:bg-gray-100 text-gray-700 border border-gray-300 rounded-md font-medium transition-colors"
            >
              {{ cancelLabel }}
            </button>
            <button
              @click="handleConfirm"
              :class="confirmButtonClass"
              class="px-4 py-2 rounded-md font-medium transition-colors"
            >
              {{ confirmLabel }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
/* Modal transition animations */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .bg-white,
.modal-leave-active .bg-white {
  transition: transform 0.3s ease;
}

.modal-enter-from .bg-white,
.modal-leave-to .bg-white {
  transform: scale(0.95);
}
</style>

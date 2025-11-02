<template>
  <div class="tk9-waiting-experience">
    <!-- Main content container -->
    <div class="tk9-waiting-content">
      <!-- Origami Animation (Left Side) -->
      <div class="tk9-animation-side">
        <OrigamiAnimation
          :shape-index="state.currentShapeIndex"
          :palette-index="state.currentPaletteIndex"
          :animation-speed="effectiveAnimationSpeed"
          :stage-progress="stageProgress"
        />
      </div>

      <!-- Text Content (Right Side) -->
      <div class="tk9-text-content">
        <!-- Quote Display -->
        <QuoteDisplay
          :stage="currentStage"
          @quote-changed="handleQuoteChanged"
        />
      </div>
    </div>

    <!-- Completion/Error States (Basic for Phase 1, enhanced in Task 10) -->
    <div v-if="isCompleted" class="tk9-completion-state">
      <p class="tk9-completion-message">
        Research Complete! 
      </p>
    </div>

    <div v-if="error" class="tk9-error-state">
      <p class="tk9-error-message">
        {{ error.message }}
      </p>
      <button
        v-if="error.retryable"
        class="tk9-retry-button"
        @click="handleRetry"
      >
        Retry Research
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, reactive, watch } from 'vue'
import type { WaitingExperienceProps, ResearchStage, Quote, ResearchError } from './types'
import { STAGE_SPEEDS, getAdjustedSpeed, shuffleArray } from './types'
import { TOTAL_SHAPES } from './origami-shapes'
import { TOTAL_PALETTES } from './color-palettes'
import OrigamiAnimation from './OrigamiAnimation.vue'
import QuoteDisplay from './QuoteDisplay.vue'

// ============================================================================
// Props
// ============================================================================

const props = withDefaults(defineProps<WaitingExperienceProps>(), {
  activeAgent: undefined,
  status: 'in_progress',
  onComplete: undefined,
  onError: undefined
})

// ============================================================================
// Emits
// ============================================================================

const emit = defineEmits<{
  'stage-changed': [stage: ResearchStage]
  'progress-updated': [progress: number]
  'quote-changed': [quote: Quote]
  'complete': []
  'error': [error: Error]
}>()

// ============================================================================
// State Management
// ============================================================================

interface WaitingExperienceState {
  currentShapeIndex: number
  currentPaletteIndex: number
  currentQuoteIndex: number
  shapeRotationInterval: ReturnType<typeof setInterval> | null
  paletteRotationInterval: ReturnType<typeof setInterval> | null
  isCompleted: boolean
  error: ResearchError | null
  shuffledShapeIndices: number[]
  shuffledPaletteIndices: number[]
}

const state = reactive<WaitingExperienceState>({
  currentShapeIndex: 0,
  currentPaletteIndex: 0,
  currentQuoteIndex: 0,
  shapeRotationInterval: null,
  paletteRotationInterval: null,
  isCompleted: false,
  error: null,
  shuffledShapeIndices: [],
  shuffledPaletteIndices: []
})

/**
 * Determine if research is completed
 */
const isCompleted = computed(() => props.status === 'completed' || state.isCompleted)

/**
 * Extract error state
 */
const error = computed(() => state.error)

// ============================================================================
// Computed Properties
// ============================================================================

/**
 * Calculate effective animation speed based on stage and progress
 * Uses getAdjustedSpeed utility from types.ts
 */
const effectiveAnimationSpeed = computed(() => {
  return getAdjustedSpeed(props.currentStage, props.stageProgress)
})

/**
 * Get base speed for current stage (for interval calculations)
 * Currently unused - reserved for future interval timing features
 */
// const baseStageSpeed = computed(() => {
//   return STAGE_SPEEDS[props.currentStage]
// })

// ============================================================================
// Methods
// ============================================================================

/**
 * Initialize shuffled indices for shapes and palettes
 * Uses Fisher-Yates shuffle from types.ts
 */
function initializeShuffledIndices(): void {
  // Create arrays of indices
  const shapeIndices = Array.from({ length: TOTAL_SHAPES }, (_, i) => i)
  const paletteIndices = Array.from({ length: TOTAL_PALETTES }, (_, i) => i)

  // Shuffle them
  state.shuffledShapeIndices = shuffleArray(shapeIndices)
  state.shuffledPaletteIndices = shuffleArray(paletteIndices)

  // Start at first shuffled indices
  state.currentShapeIndex = state.shuffledShapeIndices[0]!
  state.currentPaletteIndex = state.shuffledPaletteIndices[0]!
}

/**
 * Advance to next shape (following shuffle order)
 */
function advanceToNextShape(): void {
  const currentPosition = state.shuffledShapeIndices.indexOf(state.currentShapeIndex)
  const nextPosition = (currentPosition + 1) % state.shuffledShapeIndices.length

  state.currentShapeIndex = state.shuffledShapeIndices[nextPosition]!

  // Re-shuffle when reaching end
  if (nextPosition === 0) {
    state.shuffledShapeIndices = shuffleArray([...state.shuffledShapeIndices])
  }
}

/**
 * Advance to next palette (following shuffle order)
 */
function advanceToNextPalette(): void {
  const currentPosition = state.shuffledPaletteIndices.indexOf(state.currentPaletteIndex)
  const nextPosition = (currentPosition + 1) % state.shuffledPaletteIndices.length

  state.currentPaletteIndex = state.shuffledPaletteIndices[nextPosition]!

  // Re-shuffle when reaching end
  if (nextPosition === 0) {
    state.shuffledPaletteIndices = shuffleArray([...state.shuffledPaletteIndices])
  }
}

/**
 * Start shape rotation timer based on current stage speed
 */
function startShapeRotation(): void {
  // Clear existing interval
  if (state.shapeRotationInterval) {
    clearInterval(state.shapeRotationInterval)
  }

  // Use effective animation speed (with progress acceleration)
  const speed = effectiveAnimationSpeed.value

  state.shapeRotationInterval = setInterval(() => {
    advanceToNextShape()
  }, speed)
}

/**
 * Start palette rotation timer (slower than shapes)
 * Palettes change every 3 shape cycles
 */
function startPaletteRotation(): void {
  // Clear existing interval
  if (state.paletteRotationInterval) {
    clearInterval(state.paletteRotationInterval)
  }

  // Palettes rotate 3x slower than shapes
  const speed = effectiveAnimationSpeed.value * 3

  state.paletteRotationInterval = setInterval(() => {
    advanceToNextPalette()
  }, speed)
}

/**
 * Stop all rotation timers
 */
function stopRotation(): void {
  if (state.shapeRotationInterval) {
    clearInterval(state.shapeRotationInterval)
    state.shapeRotationInterval = null
  }

  if (state.paletteRotationInterval) {
    clearInterval(state.paletteRotationInterval)
    state.paletteRotationInterval = null
  }
}

/**
 * Restart rotation timers when stage or speed changes
 */
function restartRotation(): void {
  stopRotation()
  startShapeRotation()
  startPaletteRotation()
}

/**
 * Handle quote change event from QuoteDisplay
 */
function handleQuoteChanged(quote: Quote): void {
  emit('quote-changed', quote)
}

/**
 * Handle retry button click
 */
function handleRetry(): void {
  state.error = null
  state.isCompleted = false

  // Emit retry event (parent will restart research)
  emit('error', new Error('User requested retry'))
}

/**
 * Mark research as completed
 */
function handleComplete(): void {
  state.isCompleted = true
  stopRotation()

  if (props.onComplete) {
    props.onComplete()
  }

  emit('complete')
}

/**
 * Handle research error
 */
function handleError(errorMessage: string, retryable = true): void {
  state.error = {
    code: 'unknown',
    message: errorMessage,
    retryable
  }

  stopRotation()

  const error = new Error(errorMessage)

  if (props.onError) {
    props.onError(error)
  }

  emit('error', error)
}

// ============================================================================
// Watchers
// ============================================================================

/**
 * Watch for stage changes and restart timers
 */
watch(
  () => props.currentStage,
  (newStage, oldStage) => {
    if (newStage !== oldStage) {
      restartRotation()
      emit('stage-changed', newStage)
    }
  }
)

/**
 * Watch for progress changes (for acceleration)
 */
watch(
  () => props.stageProgress,
  (newProgress) => {
    emit('progress-updated', newProgress)

    // Restart timers when crossing acceleration thresholds (25%, 50%, 75%, 95%)
    const thresholds = [25, 50, 75, 95]
    const crossedThreshold = thresholds.some(threshold =>
      Math.abs(newProgress - threshold) < 1
    )

    if (crossedThreshold) {
      restartRotation()
    }
  }
)

/**
 * Watch for status changes (completion, errors)
 */
watch(
  () => props.status,
  (newStatus) => {
    if (newStatus === 'completed') {
      handleComplete()
    } else if (newStatus === 'failed') {
      handleError('Research execution failed. Please try again.')
    }
  }
)

// ============================================================================
// Lifecycle Hooks
// ============================================================================

onMounted(() => {
  // Initialize shuffled indices
  initializeShuffledIndices()

  // Start rotation timers
  startShapeRotation()
  startPaletteRotation()
})

onUnmounted(() => {
  // Clean up timers
  stopRotation()
})
</script>

<style scoped>
/* ============================================================================
   Main Container
   ============================================================================ */

.tk9-waiting-experience {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 90px;
  height: 100%;
  padding: 0.25rem;
  background: linear-gradient(135deg, #fafbfc 0%, #f5f7fa 100%);
  border-radius: 8px;
  box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1);
}

.tk9-waiting-content {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  max-width: 100%;
  width: 100%;
}

/* ============================================================================
   Layout Sides
   ============================================================================ */

.tk9-animation-side {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.tk9-text-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  min-width: 0; /* Allow text to wrap */
}

/* ============================================================================
   Completion State
   ============================================================================ */

.tk9-completion-state {
  text-align: center;
  padding: 2rem;
}

.tk9-completion-message {
  font-size: 24px;
  font-weight: 600;
  color: #67c23a;
  margin: 0;
}

/* ============================================================================
   Error State
   ============================================================================ */

.tk9-error-state {
  text-align: center;
  padding: 2rem;
}

.tk9-error-message {
  font-size: 16px;
  font-weight: 500;
  color: #f56c6c;
  margin: 0 0 1rem 0;
}

.tk9-retry-button {
  padding: 0.75rem 1.5rem;
  font-size: 16px;
  font-weight: 600;
  color: white;
  background: #409eff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s ease, transform 0.1s ease;
}

.tk9-retry-button:hover {
  background: #337ecc;
}

.tk9-retry-button:active {
  transform: scale(0.98);
}

.tk9-retry-button:focus-visible {
  outline: 2px solid #409eff;
  outline-offset: 2px;
}

/* ============================================================================
   Responsive Design
   ============================================================================ */

/**
 * Mobile devices (< 768px)
 * Stack vertically on small screens
 */
@media (max-width: 767px) {
  .tk9-waiting-experience {
    padding: 0.75rem 0.5rem;
    min-height: 150px;
  }

  .tk9-waiting-content {
    flex-direction: column;
    gap: 0.75rem;
  }

  .tk9-text-content {
    width: 100%;
  }

  .tk9-quote {
    text-align: center !important;
  }

  .tk9-quote-display-wrapper {
    align-items: center !important;
  }

  .tk9-completion-message {
    font-size: 18px;
  }

  .tk9-error-message {
    font-size: 13px;
  }

  .tk9-retry-button {
    padding: 0.5rem 1rem;
    font-size: 13px;
  }
}

/**
 * Tablet devices (768px - 991px)
 */
@media (min-width: 768px) and (max-width: 991px) {
  .tk9-waiting-content {
    gap: 1.75rem;
  }
}

/* ============================================================================
   Accessibility
   ============================================================================ */

/**
 * Reduced motion support
 */
@media (prefers-reduced-motion: reduce) {
  .tk9-retry-button {
    transition: none;
  }
}

/**
 * High contrast mode
 */
@media (prefers-contrast: high) {
  .tk9-waiting-experience {
    background: white;
    border: 2px solid #000000;
  }
}

/* ============================================================================
   Print Styles
   ============================================================================ */

@media print {
  .tk9-waiting-experience {
    background: white;
    border: 1px solid #ccc;
  }

  .tk9-retry-button {
    display: none;
  }
}
</style>

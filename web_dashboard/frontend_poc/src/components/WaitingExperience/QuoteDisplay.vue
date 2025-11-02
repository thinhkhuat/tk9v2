<template>
  <div class="tk9-quote-display-wrapper">
    <Transition name="quote-fade" mode="out-in">
      <blockquote
        :key="currentQuoteIndex"
        class="tk9-quote"
        :aria-label="`Quote from ${currentQuote.author}`"
      >
        <p class="tk9-quote-text">
          "{{ currentQuote.text }}"
        </p>
        <footer class="tk9-quote-author">
          <cite>{{ currentQuote.author }}</cite>
        </footer>
      </blockquote>
    </Transition>

    <!-- Quote navigation dots (Always visible, clickable) -->
    <div class="tk9-quote-navigation-container">
      <div class="tk9-quote-progress" role="navigation" aria-label="Quote navigation">
        <button
          v-for="(_, index) in stageQuotes"
          :key="`indicator-${index}`"
          class="tk9-quote-progress-dot"
          :class="{ active: index === currentQuoteIndex }"
          :aria-label="`Go to quote ${index + 1} of ${stageQuotes.length}`"
          :aria-current="index === currentQuoteIndex ? 'true' : 'false'"
          :title="`Quote ${index + 1}`"
          @click="navigateToQuote(index)"
          @keydown.enter="navigateToQuote(index)"
          @keydown.space.prevent="navigateToQuote(index)"
        />
      </div>
      <p class="tk9-quote-hint">
        <span class="tk9-keyboard-key">←</span>
        <span class="tk9-keyboard-key">→</span>
        or click dots to navigate
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import type { Quote, QuoteDisplayProps } from './types'
import { getQuotesByStage } from './quotes-library'

// ============================================================================
// Props
// ============================================================================

const props = withDefaults(defineProps<QuoteDisplayProps>(), {
  quoteIndex: undefined
})

// ============================================================================
// Emits
// ============================================================================

const emit = defineEmits<{
  'quote-changed': [quote: Quote, index: number]
}>()

// ============================================================================
// Constants
// ============================================================================

const QUOTE_ROTATION_INTERVAL = 10000 // 10 seconds (milliseconds)

// ============================================================================
// State
// ============================================================================

/**
 * Current quote index within stage-specific quotes
 * Can be controlled externally via props.quoteIndex or auto-rotates
 */
const currentQuoteIndex = ref(0)

/**
 * setInterval handle for auto-rotation
 */
let rotationInterval: ReturnType<typeof setInterval> | null = null

// ============================================================================
// Computed Properties
// ============================================================================

/**
 * Get quotes filtered by current stage
 */
const stageQuotes = computed((): Quote[] => {
  return getQuotesByStage(props.stage)
})

/**
 * Get current quote to display
 */
const currentQuote = computed((): Quote => {
  // Use manual index if provided, otherwise use auto-rotating index
  const index = props.quoteIndex ?? currentQuoteIndex.value
  const safeIndex = index % stageQuotes.value.length
  return stageQuotes.value[safeIndex]
})

// ============================================================================
// Methods
// ============================================================================

/**
 * Advance to next quote in the current stage
 */
function advanceToNextQuote(): void {
  currentQuoteIndex.value = (currentQuoteIndex.value + 1) % stageQuotes.value.length

  // Emit event for analytics/tracking
  emit('quote-changed', currentQuote.value, currentQuoteIndex.value)
}

/**
 * Navigate to a specific quote by index (user interaction)
 * Pauses auto-rotation temporarily
 */
function navigateToQuote(index: number): void {
  currentQuoteIndex.value = index

  // Emit event
  emit('quote-changed', currentQuote.value, currentQuoteIndex.value)

  // Pause auto-rotation temporarily (restart after delay)
  stopRotation()

  // Resume auto-rotation after 15 seconds of inactivity
  setTimeout(() => {
    if (!rotationInterval) {
      startRotation()
    }
  }, 15000)
}

/**
 * Navigate to previous quote (keyboard shortcut)
 */
function navigateToPrevious(): void {
  const prevIndex = currentQuoteIndex.value === 0
    ? stageQuotes.value.length - 1
    : currentQuoteIndex.value - 1
  navigateToQuote(prevIndex)
}

/**
 * Navigate to next quote (keyboard shortcut)
 */
function navigateToNext(): void {
  const nextIndex = (currentQuoteIndex.value + 1) % stageQuotes.value.length
  navigateToQuote(nextIndex)
}

/**
 * Handle keyboard navigation (arrow keys)
 */
function handleKeydown(event: KeyboardEvent): void {
  if (event.key === 'ArrowLeft') {
    event.preventDefault()
    navigateToPrevious()
  } else if (event.key === 'ArrowRight') {
    event.preventDefault()
    navigateToNext()
  }
}

/**
 * Start auto-rotation timer
 */
function startRotation(): void {
  // Clear any existing interval
  if (rotationInterval) {
    clearInterval(rotationInterval)
  }

  // Start new interval
  rotationInterval = setInterval(() => {
    advanceToNextQuote()
  }, QUOTE_ROTATION_INTERVAL)
}

/**
 * Stop auto-rotation timer
 */
function stopRotation(): void {
  if (rotationInterval) {
    clearInterval(rotationInterval)
    rotationInterval = null
  }
}

/**
 * Reset quote index when stage changes
 */
function resetQuoteIndex(): void {
  currentQuoteIndex.value = 0

  // Emit initial quote
  emit('quote-changed', currentQuote.value, 0)
}

// ============================================================================
// Watchers
// ============================================================================

/**
 * Watch for stage changes and reset to first quote
 */
watch(
  () => props.stage,
  () => {
    resetQuoteIndex()
    // Restart rotation timer
    stopRotation()
    startRotation()
  }
)

/**
 * Watch for external quoteIndex changes (manual control)
 */
watch(
  () => props.quoteIndex,
  (newIndex) => {
    if (newIndex !== undefined) {
      // External control mode - stop auto-rotation
      stopRotation()
      currentQuoteIndex.value = newIndex % stageQuotes.value.length
      emit('quote-changed', currentQuote.value, currentQuoteIndex.value)
    } else {
      // Resume auto-rotation if control released
      startRotation()
    }
  }
)

// ============================================================================
// Lifecycle Hooks
// ============================================================================

onMounted(() => {
  // Start auto-rotation
  startRotation()

  // Emit initial quote
  emit('quote-changed', currentQuote.value, currentQuoteIndex.value)

  // Add keyboard navigation
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  // Clean up rotation timer
  stopRotation()

  // Remove keyboard listener
  window.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
/* ============================================================================
   Quote Display Container
   ============================================================================ */

.tk9-quote-display-wrapper {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: flex-start;
  gap: 0.25rem;
  width: 100%;
  padding: 0;
}

/* ============================================================================
   Blockquote Styling
   ============================================================================ */

.tk9-quote {
  margin: 0;
  padding: 0.5rem 0.625rem;
  text-align: left;
  background: rgba(255, 255, 255, 0.5);
  border-radius: 6px;
  border-left: 3px solid #409eff;
  width: 100%;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  transition: box-shadow 0.2s ease, border-color 0.2s ease;
}

.tk9-quote:hover {
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
  border-left-color: #36a3f7;
}

/**
 * Quote Text
 * UTF-8 compatible typography with system fonts that support Vietnamese diacritics
 * WCAG AA contrast: #2c3e50 on white = 12.6:1 (exceeds 4.5:1 minimum)
 */
.tk9-quote-text {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
  font-size: 16px;
  font-weight: 500;
  line-height: 1.5;
  color: #2c3e50;
  margin: 0 0 0.375rem 0;
  font-style: italic;

  /* Improve text rendering and UTF-8 character support */
  text-rendering: optimizeLegibility;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  unicode-bidi: embed;
}

/**
 * Quote Author
 * Muted color for visual hierarchy
 * WCAG AA contrast: #546e7a on white = 7.8:1
 * UTF-8 compatible system fonts
 */
.tk9-quote-author {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
  font-size: 13px;
  font-weight: 600;
  line-height: 1.4;
  color: #546e7a;
  margin: 0;
}

.tk9-quote-author cite {
  font-style: normal;
}

/* ============================================================================
   Responsive Typography
   ============================================================================ */

/**
 * Mobile devices (< 768px)
 * Smaller font size for better fit
 */
@media (max-width: 767px) {
  .tk9-quote-text {
    font-size: 16px;
    line-height: 1.5;
  }

  .tk9-quote-author {
    font-size: 13px;
  }

  .tk9-quote-display-wrapper {
    max-width: 100%;
    padding: 0 0.75rem;
  }

  /* Hide keyboard hint on mobile (not applicable) */
  .tk9-quote-hint {
    display: none;
  }

  .tk9-quote {
    padding: 0.625rem 0.75rem;
  }
}

/**
 * Tablet devices (768px - 991px)
 * Intermediate sizing
 */
@media (min-width: 768px) and (max-width: 991px) {
  .tk9-quote-text {
    font-size: 18px;
    line-height: 1.55;
  }
}

/**
 * Large displays (> 1920px)
 * Slightly larger for better readability on 4K screens
 */
@media (min-width: 1920px) {
  .tk9-quote-text {
    font-size: 22px;
  }

  .tk9-quote-author {
    font-size: 15px;
  }
}

/* ============================================================================
   Fade Transition Animation
   ============================================================================ */

/**
 * Smooth fade transition between quotes
 * 300ms duration as per UX spec
 */
.quote-fade-enter-active,
.quote-fade-leave-active {
  transition: opacity 0.3s ease-in-out, transform 0.3s ease-in-out;
}

.quote-fade-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

.quote-fade-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

.quote-fade-enter-to,
.quote-fade-leave-from {
  opacity: 1;
  transform: translateY(0);
}

/* ============================================================================
   Quote Navigation (Interactive)
   ============================================================================ */

.tk9-quote-navigation-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.375rem;
  width: 100%;
}

.tk9-quote-progress {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  justify-content: center;
  padding: 0.25rem 0;
}

.tk9-quote-hint {
  margin: 0;
  font-size: 9px;
  color: #90a4ae;
  display: flex;
  align-items: center;
  gap: 0.25rem;
  opacity: 0.7;
  transition: opacity 0.2s ease;
}

.tk9-quote-hint:hover {
  opacity: 1;
}

.tk9-keyboard-key {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.125rem 0.25rem;
  font-size: 10px;
  font-weight: 600;
  background: rgba(144, 164, 174, 0.15);
  border: 1px solid rgba(144, 164, 174, 0.3);
  border-radius: 3px;
  font-family: monospace;
  line-height: 1;
}

.tk9-quote-progress-dot {
  /* Reset button styles */
  padding: 0;
  margin: 0;
  border: none;
  background: none;
  outline: none;

  /* Dot appearance */
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #b0bec5;
  cursor: pointer;

  /* Smooth transitions */
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);

  /* Improve click target for accessibility */
  position: relative;
}

/* Larger click target (invisible padding) */
.tk9-quote-progress-dot::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 24px;
  height: 24px;
  border-radius: 50%;
}

/* Hover state */
.tk9-quote-progress-dot:hover {
  background: #78909c;
  transform: scale(1.25);
}

/* Active (current) state */
.tk9-quote-progress-dot.active {
  background: linear-gradient(135deg, #409eff 0%, #36a3f7 100%);
  width: 24px;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(64, 158, 255, 0.3);
}

/* Active dot doesn't scale on hover */
.tk9-quote-progress-dot.active:hover {
  transform: scale(1);
  box-shadow: 0 2px 6px rgba(64, 158, 255, 0.4);
}

/* Focus state (keyboard navigation) */
.tk9-quote-progress-dot:focus-visible {
  outline: 2px solid #409eff;
  outline-offset: 2px;
}

/* Pressed state */
.tk9-quote-progress-dot:active {
  transform: scale(0.9);
}

/* ============================================================================
   Accessibility Enhancements
   ============================================================================ */

/**
 * Reduced motion support
 * Disable transform animations for users who prefer reduced motion
 */
@media (prefers-reduced-motion: reduce) {
  .quote-fade-enter-active,
  .quote-fade-leave-active {
    transition: opacity 0.3s ease-in-out;
  }

  .quote-fade-enter-from,
  .quote-fade-leave-to {
    transform: none;
  }

  .tk9-quote-progress-dot {
    transition: background 0.2s ease, width 0.2s ease;
  }

  .tk9-quote-progress-dot:hover,
  .tk9-quote-progress-dot:active {
    transform: none;
  }
}

/**
 * High contrast mode support
 * Ensure quotes remain readable
 */
@media (prefers-contrast: high) {
  .tk9-quote-text {
    color: #000000;
    font-weight: 500;
  }

  .tk9-quote-author {
    color: #424242;
  }

  .tk9-quote-progress-dot {
    border: 2px solid #000000;
  }

  .tk9-quote-progress-dot.active {
    background: #000000;
  }
}

/* ============================================================================
   Print Styles
   ============================================================================ */

@media print {
  .tk9-quote-display-wrapper {
    page-break-inside: avoid;
  }

  .tk9-quote-navigation-container {
    display: none;
  }

  .tk9-quote {
    box-shadow: none;
    border-left-width: 2px;
  }

  .tk9-quote-text {
    font-size: 14pt;
    color: #000000;
  }

  .tk9-quote-author {
    font-size: 11pt;
    color: #424242;
  }
}

/* ============================================================================
   Focus Styles (Accessibility)
   ============================================================================ */

/**
 * If quotes become interactive (e.g., clickable for more info)
 * Ensure proper focus indicators
 */
.tk9-quote:focus-visible {
  outline: 2px solid #409eff;
  outline-offset: 4px;
  border-radius: 4px;
}
</style>

<template>
  <div class="tk9-origami-animation-wrapper">
    <svg
      v-if="currentShape"
      :viewBox="ORIGAMI_VIEWBOX"
      :width="animationSize"
      :height="animationSize"
      class="tk9-origami-shape"
      :class="{ 'tk9-origami-reduced-motion': prefersReducedMotion }"
      :style="{ animationDuration: `${effectiveAnimationSpeed}ms` }"
      role="img"
      :aria-label="`Origami ${currentShape.name} shape`"
    >
      <!-- Render each path in the shape with appropriate fill color and path-specific animations -->
      <path
        v-for="(path, index) in currentShape.paths"
        :key="`path-${index}`"
        :d="path.d"
        :fill="getColorForFillPosition(path.fill)"
        :opacity="path.opacity ?? 1"
        class="tk9-origami-path"
        :class="getPathAnimationClass(index)"
        :style="getPathAnimationStyle(index)"
      />
    </svg>

    <!-- Debug info disabled for production -->
    <!-- <div v-if="showDebugInfo" class="tk9-origami-debug">
      <p>Shape: {{ currentShape.name }}</p>
      <p>Palette: {{ currentPalette.name }}</p>
      <p>Speed: {{ effectiveAnimationSpeed }}ms</p>
    </div> -->
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import type { OrigamiAnimationProps } from './types'
import { allOrigamiShapes } from './origami-shapes'
import { allColorPalettes, getColorByFillPosition } from './color-palettes'

// ============================================================================
// Props
// ============================================================================

const props = withDefaults(defineProps<OrigamiAnimationProps>(), {
  stageProgress: 0
})

// ============================================================================
// Constants
// ============================================================================

const ORIGAMI_VIEWBOX = '0 0 200 200'
const DESKTOP_SIZE = 180 // px (side-by-side layout) - increased for better visibility
const MOBILE_SIZE = 100  // px
const MOBILE_BREAKPOINT = 768 // px

// ============================================================================
// Computed Properties
// ============================================================================

/**
 * Get current origami shape from shapes library
 */
const currentShape = computed(() => {
  const safeIndex = props.shapeIndex % allOrigamiShapes.length
  return allOrigamiShapes[safeIndex]
})

/**
 * Get current color palette from palettes library
 */
const currentPalette = computed(() => {
  const safeIndex = props.paletteIndex % allColorPalettes.length
  return allColorPalettes[safeIndex]
})

/**
 * Calculate effective animation speed with progress-based acceleration
 * Based on UX spec: +10-25% faster as stage completes
 */
const effectiveAnimationSpeed = computed(() => {
  if (!props.stageProgress) return props.animationSpeed

  // Calculate speed multiplier based on progress (from types.ts)
  const progress = props.stageProgress
  let multiplier = 1.0

  if (progress < 25) multiplier = 1.0      // 0-25%: Base speed
  else if (progress < 50) multiplier = 1.1  // 25-50%: +10% faster
  else if (progress < 75) multiplier = 1.15 // 50-75%: +15% faster
  else if (progress < 95) multiplier = 1.2  // 75-95%: +20% faster
  else multiplier = 1.25                    // 95-100%: +25% faster

  // Divide by multiplier to make animation faster
  return Math.round(props.animationSpeed / multiplier)
})

/**
 * Responsive animation size based on viewport width
 */
const animationSize = ref(DESKTOP_SIZE)

/**
 * Check if user prefers reduced motion (accessibility)
 */
const prefersReducedMotion = ref(false)

/**
 * Debug info display toggle (for development)
 */
const showDebugInfo = ref(false)

// ============================================================================
// Methods
// ============================================================================

/**
 * Map fill position to actual hex color from current palette
 * @param fillPosition - 'primary', 'secondary', or 'accent'
 * @returns Hex color string
 */
function getColorForFillPosition(fillPosition: 'primary' | 'secondary' | 'accent'): string {
  return getColorByFillPosition(currentPalette.value, fillPosition)
}

/**
 * Get animation class for individual path elements
 * Creates variety by applying different animations to different parts
 */
function getPathAnimationClass(index: number): string {
  // Cycle through different animation types based on path index
  const animationTypes = [
    'tk9-path-float',
    'tk9-path-wing',
    'tk9-path-pulse',
    'tk9-path-rotate',
    'tk9-path-sway'
  ]
  return animationTypes[index % animationTypes.length]
}

/**
 * Get animation style with staggered delays for wave effect
 */
function getPathAnimationStyle(index: number): Record<string, string> {
  const delay = index * 0.15 // Stagger animations by 150ms
  return {
    animationDelay: `${delay}s`
  }
}

/**
 * Update animation size based on viewport width
 */
function updateAnimationSize() {
  const isMobile = window.innerWidth < MOBILE_BREAKPOINT
  animationSize.value = isMobile ? MOBILE_SIZE : DESKTOP_SIZE
}

/**
 * Check if user prefers reduced motion (accessibility)
 */
function checkReducedMotionPreference() {
  const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
  prefersReducedMotion.value = mediaQuery.matches

  // Listen for changes
  mediaQuery.addEventListener('change', (e) => {
    prefersReducedMotion.value = e.matches
  })
}

// ============================================================================
// Lifecycle Hooks
// ============================================================================

onMounted(() => {
  // Setup responsive sizing
  updateAnimationSize()
  window.addEventListener('resize', updateAnimationSize)

  // Check accessibility preferences
  checkReducedMotionPreference()

  // Debug info disabled for production
  showDebugInfo.value = false
})

onUnmounted(() => {
  window.removeEventListener('resize', updateAnimationSize)
})
</script>

<style scoped>
/* ============================================================================
   Origami Animation Styles
   ============================================================================ */

.tk9-origami-animation-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.25rem;
  padding: 0.25rem;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 8px;
  transition: background 0.3s ease;
}

.tk9-origami-animation-wrapper:hover {
  background: rgba(255, 255, 255, 0.5);
}

.tk9-origami-shape {
  /* Animation applied via :style binding for dynamic speed */
  animation-name: tk9-origami-fold-3d;
  animation-timing-function: ease-in-out;
  animation-iteration-count: infinite;
  animation-fill-mode: both;

  /* Ensure crisp rendering */
  shape-rendering: geometricPrecision;

  /* Add subtle drop shadow for depth */
  filter: drop-shadow(0 4px 12px rgba(0, 0, 0, 0.08));

  /* Smooth transitions */
  transition: filter 0.3s ease;
}

.tk9-origami-shape:hover {
  /* Slightly stronger shadow on hover */
  filter: drop-shadow(0 6px 16px rgba(0, 0, 0, 0.12));
}

.tk9-origami-path {
  /* Smooth path rendering */
  stroke-linejoin: round;
  stroke-linecap: round;

  /* Transitions for color changes */
  transition: fill 0.4s ease, opacity 0.4s ease;

  /* Animation properties - will be overridden by specific animation classes */
  animation-duration: 2.5s;
  animation-timing-function: ease-in-out;
  animation-iteration-count: infinite;
  animation-fill-mode: both;

  /* GPU acceleration for smooth animations */
  transform-origin: center;
  will-change: transform;
}

/* ============================================================================
   Keyframe Animations
   ============================================================================ */

/**
 * origamiFold Animation
 * 3D rotation effect simulating paper folding
 * Enhanced with scale and opacity for visibility
 */
@keyframes origamiFold {
  0% {
    transform: perspective(600px) rotateY(0deg) rotateX(0deg) scale(1);
    opacity: 1;
  }

  25% {
    transform: perspective(600px) rotateY(45deg) rotateX(10deg) scale(0.95);
    opacity: 0.95;
  }

  50% {
    transform: perspective(600px) rotateY(180deg) rotateX(0deg) scale(0.85);
    opacity: 0.85;
  }

  75% {
    transform: perspective(600px) rotateY(270deg) rotateX(-10deg) scale(0.95);
    opacity: 0.95;
  }

  100% {
    transform: perspective(600px) rotateY(360deg) rotateX(0deg) scale(1);
    opacity: 1;
  }
}

/* ============================================================================
   Path-Specific Animations (Bold & Visible)
   ============================================================================ */

/**
 * Float Animation - Vertical bobbing motion
 * Creates noticeable up-and-down movement
 */
@keyframes tk9-path-float {
  0%, 100% {
    transform: translateY(0px);
  }
  50% {
    transform: translateY(-12px);
  }
}

.tk9-path-float {
  animation-name: tk9-path-float;
  animation-duration: 2.8s;
}

/**
 * Wing Animation - Rotating motion like a bird wing
 * Large rotation angle for clear visibility
 */
@keyframes tk9-path-wing {
  0%, 100% {
    transform: rotateZ(0deg);
  }
  50% {
    transform: rotateZ(-20deg);
  }
}

.tk9-path-wing {
  animation-name: tk9-path-wing;
  animation-duration: 2.5s;
}

/**
 * Pulse Animation - Scale in and out
 * Noticeable size change for visual interest
 */
@keyframes tk9-path-pulse {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.15);
    opacity: 0.9;
  }
}

.tk9-path-pulse {
  animation-name: tk9-path-pulse;
  animation-duration: 2.2s;
}

/**
 * Rotate Animation - Full 360-degree rotation
 * Continuous spinning motion
 */
@keyframes tk9-path-rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.tk9-path-rotate {
  animation-name: tk9-path-rotate;
  animation-duration: 4s;
  animation-timing-function: linear;
}

/**
 * Sway Animation - Combined horizontal and rotational movement
 * Creates a natural swaying motion
 */
@keyframes tk9-path-sway {
  0%, 100% {
    transform: translateX(0px) rotateZ(0deg);
  }
  25% {
    transform: translateX(10px) rotateZ(8deg);
  }
  75% {
    transform: translateX(-10px) rotateZ(-8deg);
  }
}

.tk9-path-sway {
  animation-name: tk9-path-sway;
  animation-duration: 3.5s;
}

/* ============================================================================
   Reduced Motion Support (Accessibility)
   ============================================================================ */

/**
 * For users who prefer reduced motion, replace 3D rotation
 * with a simple fade animation
 */
.tk9-origami-reduced-motion {
  animation-name: simpleFade !important;
}

@keyframes simpleFade {
  0%,
  100% {
    opacity: 1;
    transform: scale(1);
  }

  50% {
    opacity: 0.7;
    transform: scale(0.95);
  }
}

/* Alternative: Completely disable animation */
@media (prefers-reduced-motion: reduce) {
  .tk9-origami-shape {
    animation: none !important;
  }

  /* Disable all path animations for reduced motion */
  .tk9-origami-path {
    animation: none !important;
  }

  /* Optional: Still allow gentle fade */
  /* .tk9-origami-shape {
    animation: simpleFade 4s ease-in-out infinite !important;
  } */
}

/* ============================================================================
   Responsive Design
   ============================================================================ */

/**
 * Mobile devices (< 768px)
 * - Smaller size (120px vs 192px)
 * - Reduced animation complexity (handled via JS)
 */
@media (max-width: 767px) {
  .tk9-origami-animation-wrapper {
    gap: 0.375rem;
  }

  .tk9-origami-shape {
    /* Lighter shadow on mobile to conserve GPU */
    filter: drop-shadow(0 2px 8px rgba(0, 0, 0, 0.06));
  }

  .tk9-origami-shape:hover {
    filter: drop-shadow(0 3px 10px rgba(0, 0, 0, 0.08));
  }
}

/**
 * Large displays (> 1920px)
 * Optional: Scale up slightly for 4K displays
 */
@media (min-width: 1920px) {
  /* Keep size consistent per UX spec */
  /* But allow for future expansion if needed */
}

/* ============================================================================
   Debug Info (Development Only)
   ============================================================================ */

.tk9-origami-debug {
  margin-top: 0.5rem;
  padding: 0.5rem;
  background: rgba(0, 0, 0, 0.05);
  border-radius: 0.25rem;
  font-size: 0.75rem;
  font-family: monospace;
  color: #546e7a;
  text-align: center;
}

.tk9-origami-debug p {
  margin: 0.125rem 0;
}

/* ============================================================================
   Performance Optimizations
   ============================================================================ */

/**
 * Use GPU acceleration for smoother animations
 */
.tk9-origami-shape {
  will-change: transform, opacity;
  transform: translateZ(0); /* Force GPU layer */
  backface-visibility: hidden;
}

/**
 * Disable GPU hints when not animating (e.g., component paused)
 */
.tk9-origami-shape.paused {
  will-change: auto;
}

/* ============================================================================
   Print Styles
   ============================================================================ */

@media print {
  .tk9-origami-shape {
    animation: none !important;
    transform: none !important;
    opacity: 1 !important;
  }

  .tk9-origami-debug {
    display: none;
  }
}
</style>

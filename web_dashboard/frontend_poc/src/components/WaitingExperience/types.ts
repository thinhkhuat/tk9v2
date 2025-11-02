/**
 * TypeScript Type Definitions for TK9 Waiting Experience
 *
 * This file contains all TypeScript interfaces and types used across
 * the WaitingExperience component system.
 *
 * Reference: docs/ux-design-specification.md Section 6.1-6.3
 */

// ============================================================================
// Research Stage Types
// ============================================================================

/**
 * Research stages in TK9 multi-agent workflow
 * 1 = Initial Research, 2 = Planning, 3 = Parallel Research, 4 = Writing
 */
export type ResearchStage = 1 | 2 | 3 | 4

/**
 * Stage names mapping
 */
export const STAGE_NAMES: Record<ResearchStage, string> = {
  1: 'Initial Research',
  2: 'Planning',
  3: 'Parallel Research',
  4: 'Writing'
}

/**
 * Stage-specific animation speeds (milliseconds)
 * ~5 second duration for contemplative experience
 */
export const STAGE_SPEEDS: Record<ResearchStage, number> = {
  1: 4500,  // Initial Research: Fast (4.5s)
  2: 5000,  // Planning: Moderate (5s)
  3: 4800,  // Parallel Research: Balanced (4.8s)
  4: 5500   // Writing: Slow, thoughtful (5.5s)
}

// ============================================================================
// Quote System Types
// ============================================================================

/**
 * Famous quote with author attribution
 */
export interface Quote {
  text: string
  author: string
  stage: ResearchStage
}

/**
 * Props for QuoteDisplay component
 */
export interface QuoteDisplayProps {
  stage: ResearchStage
  quoteIndex?: number  // Optional: for manual control
}

// ============================================================================
// Origami Animation Types
// ============================================================================

/**
 * Origami shape definition with SVG paths
 */
export interface OrigamiShape {
  name: string
  category: 'traditional' | 'modern' | 'research'
  paths: OrigamiShapePath[]
}

/**
 * SVG path data for origami shape
 */
export interface OrigamiShapePath {
  d: string           // SVG path data
  fill: 'primary' | 'secondary' | 'accent'
  opacity?: number    // Optional opacity (0-1)
}

/**
 * Color palette for origami shapes
 */
export interface ColorPalette {
  name: string
  colors: [string, string, string]  // [primary, secondary, accent] hex colors
}

/**
 * Props for OrigamiAnimation component
 */
export interface OrigamiAnimationProps {
  shapeIndex: number        // 0-9 (Phase 1: 10 shapes)
  paletteIndex: number      // 0-19
  animationSpeed: number    // Milliseconds (3000-6000)
  stageProgress?: number    // 0-100 (for progress-based acceleration)
}

// ============================================================================
// Stage Progress Types
// ============================================================================

/**
 * Agent status in the research workflow
 */
export type AgentStatus = 'queued' | 'active' | 'completed' | 'error'

/**
 * Stage progress information
 */
export interface StageInfo {
  stage: ResearchStage
  name: string
  agent: string
  status: AgentStatus
  progress?: number  // 0-100
}

/**
 * Props for StageProgress component
 */
export interface StageProgressProps {
  stages: StageInfo[]
  currentStage: ResearchStage
}

// ============================================================================
// Main Waiting Experience Types
// ============================================================================

/**
 * Session status from backend
 */
export type SessionStatus =
  | 'pending'
  | 'in_progress'
  | 'running'
  | 'completed'
  | 'failed'
  | 'cancelled'

/**
 * Props for WaitingExperience orchestrator component
 */
export interface WaitingExperienceProps {
  sessionId: string
  currentStage: ResearchStage
  stageProgress: number           // 0-100
  stageName: string               // "Initial Research", "Planning", etc.
  activeAgent?: string
  status?: SessionStatus
  onComplete?: () => void
  onError?: (error: Error) => void
}

/**
 * Internal state for WaitingExperience component
 */
export interface WaitingExperienceState {
  currentShapeIndex: number
  currentPaletteIndex: number
  currentQuoteIndex: number
  animationSpeed: number
  isCompleted: boolean
  error: Error | null
}

// ============================================================================
// Completion & Error Types
// ============================================================================

/**
 * Research completion result
 */
export interface ResearchCompletionResult {
  sessionId: string
  filesGenerated: number
  fileNames: string[]
  duration: number  // milliseconds
}

/**
 * Research error information
 */
export interface ResearchError {
  code: string
  message: string
  retryable: boolean
  details?: Record<string, unknown>
}

/**
 * Error type codes
 */
export type ErrorCode =
  | 'network_timeout'
  | 'api_error'
  | 'invalid_query'
  | 'rate_limit'
  | 'unknown'

/**
 * Error messages mapping
 */
export const ERROR_MESSAGES: Record<ErrorCode, string> = {
  network_timeout: 'Connection lost. Please check your internet and retry.',
  api_error: 'Research service unavailable. Please try again later.',
  invalid_query: 'Query format error. Please refine your research topic.',
  rate_limit: 'Too many requests. Please wait 1 minute and retry.',
  unknown: 'An unexpected error occurred. Our team has been notified.'
}

// ============================================================================
// Utility Types
// ============================================================================

/**
 * Progress acceleration calculation
 * Returns speed multiplier based on stage progress (0-100)
 */
export function calculateSpeedMultiplier(progress: number): number {
  if (progress < 25) return 1.0      // 0-25%: Base speed
  if (progress < 50) return 1.1      // 25-50%: +10% faster
  if (progress < 75) return 1.15     // 50-75%: +15% faster
  if (progress < 95) return 1.2      // 75-95%: +20% faster
  return 1.25                        // 95-100%: +25% faster
}

/**
 * Get adjusted animation speed based on stage and progress
 */
export function getAdjustedSpeed(
  stage: ResearchStage,
  progress: number
): number {
  const baseSpeed = STAGE_SPEEDS[stage]
  const multiplier = calculateSpeedMultiplier(progress)
  return Math.round(baseSpeed / multiplier)
}

/**
 * Fisher-Yates shuffle algorithm for randomizing arrays
 */
export function shuffleArray<T>(array: T[]): T[] {
  const shuffled = [...array]
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j]!, shuffled[i]!]
  }
  return shuffled
}

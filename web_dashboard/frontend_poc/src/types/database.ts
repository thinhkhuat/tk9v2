/**
 * Database TypeScript Interfaces
 * Story 1.3: User and Session Database Schema
 *
 * These types match the database schema and Pydantic models in web_dashboard/models.py
 */

// ============================================================
// Enums (as const objects for erasableSyntaxOnly compliance)
// ============================================================

export const SessionStatus = {
  IN_PROGRESS: 'in_progress',
  COMPLETED: 'completed',
  FAILED: 'failed',
} as const

export type SessionStatus = (typeof SessionStatus)[keyof typeof SessionStatus]

export const ResearchStage = {
  INITIAL_RESEARCH: '1_initial_research',
  PLANNING: '2_planning',
  PARALLEL_RESEARCH: '3_parallel_research',
  WRITING: '4_writing',
} as const

export type ResearchStage = (typeof ResearchStage)[keyof typeof ResearchStage]

// ============================================================
// Database Tables
// ============================================================

export interface User {
  /** User UUID (primary key) */
  id: string
  /** User email (nullable for anonymous users) */
  email: string | null
  /** Whether user is anonymous */
  is_anonymous: boolean
  /** User creation timestamp */
  created_at: string
  /** Last update timestamp */
  updated_at: string
}

export interface ResearchSession {
  /** Session UUID (primary key) */
  id: string
  /** Foreign key to users.id */
  user_id: string
  /** Research session title/subject */
  title: string
  /** Session status */
  status: SessionStatus
  /** Session creation timestamp */
  created_at: string
  /** Last update timestamp */
  updated_at: string
}

export interface DraftFile {
  /** Draft file UUID (primary key) */
  id: string
  /** Foreign key to research_sessions.id */
  session_id: string
  /** Research stage */
  stage: ResearchStage
  /** Path to draft file */
  file_path: string
  /** File detection timestamp */
  detected_at: string
}

// ============================================================
// API Request/Response Types
// ============================================================

export interface TransferSessionsRequest {
  /** Anonymous user UUID */
  old_user_id: string
  /** Permanent account UUID */
  new_user_id: string
}

export interface TransferSessionsResponse {
  /** Number of sessions transferred */
  transferred_count: number
  /** Success message */
  message: string
}

// ============================================================
// Helper Types
// ============================================================

export type SessionStatusType = `${SessionStatus}`
export type ResearchStageType = `${ResearchStage}`

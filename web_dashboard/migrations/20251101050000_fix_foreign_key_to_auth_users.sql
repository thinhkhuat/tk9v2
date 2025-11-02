-- ============================================================
-- Migration: Fix Foreign Key to Reference auth.users
-- Created: 2025-11-01
-- Story: 1.3 - User and Session Database Schema (CORRECTIVE)
-- Description: Drop and recreate tables to fix foreign key reference
--              from public.users(id) to auth.users(id)
-- ============================================================
--
-- SAFETY: This migration drops and recreates research_sessions and draft_files.
-- Current state verified: research_sessions has 0 rows (safe to drop)
--
-- Before: research_sessions.user_id → public.users(id) ❌
-- After:  research_sessions.user_id → auth.users(id) ✅
-- ============================================================

-- ============================================================
-- STEP 1: Drop existing tables with wrong foreign keys
-- ============================================================

-- Drop draft_files first (has FK to research_sessions)
DROP TABLE IF EXISTS draft_files CASCADE;

-- Drop research_sessions (has FK to public.users - WRONG!)
DROP TABLE IF EXISTS research_sessions CASCADE;

-- Drop ENUMs (will recreate)
DROP TYPE IF EXISTS research_stage CASCADE;
DROP TYPE IF EXISTS session_status CASCADE;

-- Drop trigger function (will recreate)
DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;

-- ============================================================
-- STEP 2: Recreate with correct foreign keys
-- ============================================================

-- Create session_status enum
CREATE TYPE session_status AS ENUM ('in_progress', 'completed', 'failed');

-- Create research_stage enum
CREATE TYPE research_stage AS ENUM (
  '1_initial_research',
  '2_planning',
  '3_parallel_research',
  '4_writing'
);

-- Create research_sessions table with CORRECT foreign key
CREATE TABLE research_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  -- ✅ CORRECT: Reference auth.users instead of public.users
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  status session_status NOT NULL DEFAULT 'in_progress',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Create indexes on research_sessions
CREATE INDEX idx_research_sessions_user_id ON research_sessions(user_id);
CREATE INDEX idx_research_sessions_created_at ON research_sessions(created_at DESC);

-- Create draft_files table
CREATE TABLE draft_files (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL REFERENCES research_sessions(id) ON DELETE CASCADE,
  stage research_stage NOT NULL,
  file_path TEXT NOT NULL,
  detected_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Create index on draft_files
CREATE INDEX idx_draft_files_session_id ON draft_files(session_id);

-- Create trigger function for automatic updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for research_sessions table
CREATE TRIGGER update_research_sessions_updated_at
  BEFORE UPDATE ON research_sessions
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- VERIFICATION
-- ============================================================

-- Verify foreign key now points to auth.users
DO $$
DECLARE
  fk_record RECORD;
BEGIN
  SELECT
      ccu.table_schema AS foreign_table_schema,
      ccu.table_name AS foreign_table_name
  INTO fk_record
  FROM information_schema.table_constraints AS tc
  JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
  JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
  WHERE tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_name = 'research_sessions'
    AND kcu.column_name = 'user_id';

  IF fk_record.foreign_table_schema = 'auth' AND fk_record.foreign_table_name = 'users' THEN
    RAISE NOTICE '✅ SUCCESS: research_sessions.user_id → auth.users(id)';
  ELSE
    RAISE EXCEPTION '❌ FAILED: Foreign key points to %.% instead of auth.users',
      fk_record.foreign_table_schema, fk_record.foreign_table_name;
  END IF;
END $$;

-- ============================================================
-- NOTES
-- ============================================================

-- 1. The public.users table is left untouched (used by other projects)
-- 2. All new sessions will reference auth.users(id) directly
-- 3. This aligns with Supabase Auth best practices
-- 4. CASCADE deletes will work correctly when auth users are deleted

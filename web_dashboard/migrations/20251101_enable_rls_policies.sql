-- Migration: Enable Row-Level Security (RLS) Policies
-- Story: 1.4 - Row-Level Security (RLS) Policies Implementation
-- Date: 2025-11-01
-- Description: Implement RLS policies on research_sessions and draft_files tables
--              to enforce complete data isolation between users at the database level.
--
-- NOTE: Per Story 1.3 architecture, we use auth.users (not public.users).
--       The auth.users table is managed by Supabase Auth and already has RLS.
--       We only need to add RLS policies to OUR tables (research_sessions, draft_files).

-- ============================================================================
-- SECTION 1: Enable Row-Level Security on Tables
-- ============================================================================

-- Enable RLS on research_sessions table
ALTER TABLE research_sessions ENABLE ROW LEVEL SECURITY;

-- Enable RLS on draft_files table
ALTER TABLE draft_files ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- SECTION 3: Research Sessions Table RLS Policies
-- ============================================================================

-- Policy: Users can view only their own sessions
-- Description: Restricts SELECT operations to sessions owned by the authenticated user
CREATE POLICY "Users view own sessions"
ON research_sessions
FOR SELECT
USING (user_id = auth.uid());

-- Policy: Users can insert sessions only for themselves
-- Description: Prevents users from creating sessions with a different user_id
--              WITH CHECK validates data before insertion
CREATE POLICY "Users insert own sessions"
ON research_sessions
FOR INSERT
WITH CHECK (user_id = auth.uid());

-- Policy: Users can update only their own sessions
-- Description: Restricts UPDATE operations to sessions owned by the authenticated user
CREATE POLICY "Users update own sessions"
ON research_sessions
FOR UPDATE
USING (user_id = auth.uid());

-- ============================================================================
-- SECTION 4: Draft Files Table RLS Policies
-- ============================================================================

-- Policy: Users can view drafts only from their own sessions
-- Description: Uses a subquery to check session ownership before allowing access to draft files
--              This ensures users cannot access draft files from other users' sessions
CREATE POLICY "Users view own drafts"
ON draft_files
FOR SELECT
USING (
  session_id IN (
    SELECT id FROM research_sessions WHERE user_id = auth.uid()
  )
);

-- ============================================================================
-- VERIFICATION QUERIES (Run after migration to verify)
-- ============================================================================

-- Verify RLS is enabled on all tables:
-- SELECT schemaname, tablename, rowsecurity
-- FROM pg_tables
-- WHERE tablename IN ('research_sessions', 'draft_files');

-- View all created policies:
-- SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual, with_check
-- FROM pg_policies
-- WHERE tablename IN ('research_sessions', 'draft_files')
-- ORDER BY tablename, policyname;

-- ============================================================================
-- ROLLBACK SECTION (Use to undo this migration if needed)
-- ============================================================================

-- DROP POLICIES (in reverse order of creation)
-- DROP POLICY IF EXISTS "Users view own drafts" ON draft_files;
-- DROP POLICY IF EXISTS "Users update own sessions" ON research_sessions;
-- DROP POLICY IF EXISTS "Users insert own sessions" ON research_sessions;
-- DROP POLICY IF EXISTS "Users view own sessions" ON research_sessions;

-- DISABLE RLS
-- ALTER TABLE draft_files DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE research_sessions DISABLE ROW LEVEL SECURITY;

-- ============================================================================
-- NOTES
-- ============================================================================

-- 1. auth.uid() returns the authenticated user's UUID from the JWT token's 'sub' claim
-- 2. If auth.uid() returns NULL (unauthenticated request), all policies will filter out rows
--    This results in empty result sets rather than permission errors
-- 3. Service role key bypasses RLS - use only for admin operations, never expose to frontend
-- 4. Supabase client automatically respects RLS policies based on the authenticated user context
-- 5. DELETE policies not included in this migration (no user-facing delete functionality in MVP)
-- 6. draft_files INSERT/UPDATE policies not needed (only backend file detection service writes drafts)

-- ============================================================
-- Migration: Cleanup Duplicate RLS Policies
-- Created: 2025-11-01
-- Story: 1.4 - Row-Level Security (RLS) Policies Implementation
-- Description: Remove duplicate RLS policies that were created
--              outside of the official migration workflow
-- ============================================================
--
-- Context: Database audit revealed duplicate policies on research_sessions:
-- - 2 SELECT policies (should be 1)
-- - 2 INSERT policies (should be 1)
-- - 2 UPDATE policies (should be 1)
-- - 1 DELETE policy (unexpected, but keeping it)
--
-- This migration removes the duplicates, keeping only the policies
-- from the official migration: 20251101_enable_rls_policies.sql
-- ============================================================

-- ============================================================
-- UP MIGRATION
-- ============================================================

-- Drop duplicate SELECT policy (keep "Users view own sessions")
DROP POLICY IF EXISTS "Users can view their own research sessions" ON research_sessions;

-- Drop duplicate INSERT policy (keep "Users insert own sessions")
DROP POLICY IF EXISTS "Users can insert their own research sessions" ON research_sessions;

-- Drop duplicate UPDATE policy (keep "Users update own sessions")
DROP POLICY IF EXISTS "Users can update their own research sessions" ON research_sessions;

-- NOTE: Keeping "Users can delete their own research sessions" DELETE policy
-- This was added manually and provides useful functionality

-- ============================================================
-- VERIFICATION
-- ============================================================

-- After applying this migration, verify with:
--
-- SELECT tablename, policyname, cmd
-- FROM pg_policies
-- WHERE tablename = 'research_sessions'
-- ORDER BY cmd, policyname;
--
-- Expected result (4 policies):
-- research_sessions | Users can delete their own research sessions | DELETE
-- research_sessions | Users insert own sessions                    | INSERT
-- research_sessions | Users view own sessions                      | SELECT
-- research_sessions | Users update own sessions                    | UPDATE

-- ============================================================
-- DOWN MIGRATION (ROLLBACK)
-- ============================================================

-- To rollback this migration, recreate the duplicate policies:

-- CREATE POLICY "Users can view their own research sessions"
-- ON research_sessions
-- FOR SELECT
-- USING (auth.uid() = user_id);
--
-- CREATE POLICY "Users can insert their own research sessions"
-- ON research_sessions
-- FOR INSERT
-- WITH CHECK (auth.uid() = user_id);
--
-- CREATE POLICY "Users can update their own research sessions"
-- ON research_sessions
-- FOR UPDATE
-- USING (auth.uid() = user_id)
-- WITH CHECK (auth.uid() = user_id);

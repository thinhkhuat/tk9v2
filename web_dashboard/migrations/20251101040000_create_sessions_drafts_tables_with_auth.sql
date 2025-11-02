-- ============================================================
-- Migration: Create research_sessions and draft_files tables
-- Created: 2025-11-01
-- Story: 1.3 - User and Session Database Schema (CORRECTED)
-- Description: Database schema for research session management
--              Uses Supabase Auth's built-in auth.users table
-- ============================================================
--
-- IMPORTANT: This migration does NOT create a public.users table.
-- Instead, it references auth.users (managed by Supabase Auth).
--
-- Why we use auth.users:
-- 1. Single source of truth for user authentication
-- 2. Avoid synchronization issues with separate users table
-- 3. JWT and RLS built around auth.users
-- 4. No conflicts with existing tables in shared instances
-- ============================================================

-- ============================================================
-- UP MIGRATION
-- ============================================================

-- Create session_status enum if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'session_status') THEN
        CREATE TYPE session_status AS ENUM ('in_progress', 'completed', 'failed');
    END IF;
END
$$;

-- Create research_stage enum if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'research_stage') THEN
        CREATE TYPE research_stage AS ENUM (
          '1_initial_research',
          '2_planning',
          '3_parallel_research',
          '4_writing'
        );
    END IF;
END
$$;

-- Create research_sessions table
-- CRITICAL: References auth.users(id) instead of public.users(id)
CREATE TABLE IF NOT EXISTS research_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  -- Reference Supabase Auth's user table directly
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  status session_status NOT NULL DEFAULT 'in_progress',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Create indexes on research_sessions
CREATE INDEX IF NOT EXISTS idx_research_sessions_user_id ON research_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_research_sessions_created_at ON research_sessions(created_at DESC);

-- Create draft_files table
CREATE TABLE IF NOT EXISTS draft_files (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL REFERENCES research_sessions(id) ON DELETE CASCADE,
  stage research_stage NOT NULL,
  file_path TEXT NOT NULL,
  detected_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Create index on draft_files
CREATE INDEX IF NOT EXISTS idx_draft_files_session_id ON draft_files(session_id);

-- Create trigger function for automatic updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for research_sessions table (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'update_research_sessions_updated_at'
    ) THEN
        CREATE TRIGGER update_research_sessions_updated_at
          BEFORE UPDATE ON research_sessions
          FOR EACH ROW
          EXECUTE FUNCTION update_updated_at_column();
    END IF;
END
$$;

-- ============================================================
-- DOWN MIGRATION (ROLLBACK)
-- ============================================================

-- To rollback this migration, run the following:

-- DROP TRIGGER IF EXISTS update_research_sessions_updated_at ON research_sessions;
-- DROP FUNCTION IF EXISTS update_updated_at_column();
-- DROP INDEX IF EXISTS idx_draft_files_session_id;
-- DROP TABLE IF EXISTS draft_files;
-- DROP TYPE IF EXISTS research_stage;
-- DROP INDEX IF EXISTS idx_research_sessions_created_at;
-- DROP INDEX IF EXISTS idx_research_sessions_user_id;
-- DROP TABLE IF EXISTS research_sessions;
-- DROP TYPE IF EXISTS session_status;

-- ============================================================
-- VERIFICATION QUERIES
-- ============================================================

-- After applying this migration, verify with:

-- 1. List all tables:
--    SELECT tablename FROM pg_tables WHERE schemaname = 'public';
--
-- 2. List all indexes:
--    SELECT indexname, tablename FROM pg_indexes WHERE schemaname = 'public';
--
-- 3. Verify foreign key to auth.users:
--    SELECT
--      tc.table_name,
--      kcu.column_name,
--      ccu.table_schema AS foreign_table_schema,
--      ccu.table_name AS foreign_table_name,
--      ccu.column_name AS foreign_column_name
--    FROM information_schema.table_constraints AS tc
--    JOIN information_schema.key_column_usage AS kcu
--      ON tc.constraint_name = kcu.constraint_name
--      AND tc.table_schema = kcu.table_schema
--    JOIN information_schema.constraint_column_usage AS ccu
--      ON ccu.constraint_name = tc.constraint_name
--      AND ccu.table_schema = tc.table_schema
--    WHERE tc.constraint_type = 'FOREIGN KEY'
--      AND tc.table_name = 'research_sessions';
--    -- Should show: research_sessions.user_id → auth.users.id
--
-- 4. Test with an existing auth user:
--    -- Get an existing user ID from auth.users
--    SELECT id, email FROM auth.users LIMIT 1;
--
--    -- Create a test session (replace USER_ID with actual user ID)
--    INSERT INTO research_sessions (user_id, title, status)
--    VALUES ('USER_ID', 'Test Session', 'in_progress')
--    RETURNING *;
--
--    -- Verify the session was created
--    SELECT * FROM research_sessions WHERE title = 'Test Session';
--
-- 5. Test CASCADE delete (optional - use with caution):
--    -- Create a test user in auth.users first (via Supabase Auth signup)
--    -- Then create a session for that user
--    -- Delete the auth user and verify the session is deleted too
--
-- 6. Test trigger:
--    -- Update a session's title
--    UPDATE research_sessions SET title = 'Updated Title'
--    WHERE title = 'Test Session';
--
--    -- Verify updated_at changed
--    SELECT title, created_at, updated_at FROM research_sessions
--    WHERE title = 'Updated Title';
--    -- updated_at should be different from created_at

-- ============================================================
-- NOTES FOR DEVELOPERS
-- ============================================================

-- 1. DO NOT create a public.users table - use auth.users directly
--
-- 2. To get the current user ID in RLS policies (Story 1.4):
--    auth.uid() -- Returns the user ID from the JWT token
--
-- 3. To check if a user exists before creating a session:
--    SELECT id FROM auth.users WHERE id = 'user-uuid';
--
-- 4. For anonymous users:
--    Supabase Auth supports anonymous users automatically.
--    Check: SELECT * FROM auth.users WHERE is_anonymous = true;
--
-- 5. For storing additional user profile data:
--    Create a separate public.profiles table with:
--    CREATE TABLE public.profiles (
--      id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
--      -- your custom fields here
--    );
--
-- 6. The auth.users table contains:
--    - id (uuid) - Primary key
--    - email (text) - User email
--    - encrypted_password (text) - Password hash
--    - email_confirmed_at (timestamptz) - Email verification timestamp
--    - is_anonymous (boolean) - Whether user is anonymous
--    - created_at (timestamptz) - Account creation timestamp
--    - updated_at (timestamptz) - Last update timestamp
--    - And many other auth-related fields
--
-- 7. Foreign key constraint behavior:
--    ON DELETE CASCADE means when a user is deleted from auth.users,
--    all their research_sessions will be automatically deleted,
--    and subsequently all draft_files for those sessions will be deleted.

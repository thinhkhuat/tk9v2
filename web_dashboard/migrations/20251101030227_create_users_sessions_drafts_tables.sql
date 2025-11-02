-- Migration: Create users, research_sessions, and draft_files tables
-- Created: 2025-11-01
-- Story: 1.3 - User and Session Database Schema
-- Description: Initial database schema for authentication and research session management

-- ============================================================
-- UP MIGRATION
-- ============================================================

-- Create users table
CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE,  -- NULLABLE for anonymous users
  is_anonymous BOOLEAN NOT NULL DEFAULT false,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Create index on email for fast lookups
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Create session_status enum
CREATE TYPE session_status AS ENUM ('in_progress', 'completed', 'failed');

-- Create research_sessions table
CREATE TABLE IF NOT EXISTS research_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  status session_status NOT NULL DEFAULT 'in_progress',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Create indexes on research_sessions
CREATE INDEX IF NOT EXISTS idx_research_sessions_user_id ON research_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_research_sessions_created_at ON research_sessions(created_at DESC);

-- Create research_stage enum
CREATE TYPE research_stage AS ENUM (
  '1_initial_research',
  '2_planning',
  '3_parallel_research',
  '4_writing'
);

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

-- Create triggers for users table
CREATE TRIGGER update_users_updated_at
  BEFORE UPDATE ON users
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- Create triggers for research_sessions table
CREATE TRIGGER update_research_sessions_updated_at
  BEFORE UPDATE ON research_sessions
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- DOWN MIGRATION (ROLLBACK)
-- ============================================================

-- To rollback this migration, run the following:

-- DROP TRIGGER IF EXISTS update_research_sessions_updated_at ON research_sessions;
-- DROP TRIGGER IF EXISTS update_users_updated_at ON users;
-- DROP FUNCTION IF EXISTS update_updated_at_column();
-- DROP INDEX IF EXISTS idx_draft_files_session_id;
-- DROP TABLE IF EXISTS draft_files;
-- DROP TYPE IF EXISTS research_stage;
-- DROP INDEX IF EXISTS idx_research_sessions_created_at;
-- DROP INDEX IF EXISTS idx_research_sessions_user_id;
-- DROP TABLE IF EXISTS research_sessions;
-- DROP TYPE IF EXISTS session_status;
-- DROP INDEX IF EXISTS idx_users_email;
-- DROP TABLE IF EXISTS users;

-- ============================================================
-- VERIFICATION QUERIES
-- ============================================================

-- After applying this migration, verify with:
-- 1. List all tables:
--    SELECT tablename FROM pg_tables WHERE schemaname = 'public';
--
-- 2. List all indexes:
--    \di
--
-- 3. Test trigger:
--    INSERT INTO users (email, is_anonymous) VALUES ('test@example.com', false);
--    UPDATE users SET email = 'test2@example.com' WHERE email = 'test@example.com';
--    SELECT email, created_at, updated_at FROM users WHERE email = 'test2@example.com';
--    -- updated_at should be different from created_at
--
-- 4. Test foreign key cascade:
--    DELETE FROM users WHERE email = 'test2@example.com';
--    -- All related research_sessions should be deleted automatically

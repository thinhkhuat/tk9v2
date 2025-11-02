-- ============================================================
-- MIGRATION AUDIT LOG
-- ============================================================
-- Story: 1.3 - User and Session Database Schema
-- Migration File: 20251101030227_create_users_sessions_drafts_tables.sql
-- Created: 2025-11-01 03:02:27
-- Applied: [TO BE FILLED BY DBA]
-- Applied By: [TO BE FILLED BY DBA]
-- Database: Supabase PostgreSQL 15.8.1.073
-- Project: yurbnrqgsipdlijeyyuw (Supabase github-auth)
-- Region: ap-southeast-1
--
-- Purpose: Initial database schema for TK9 Web Dashboard
--   - User authentication and session management
--   - Research session tracking with status
--   - Draft file detection and organization
--
-- Dependencies: None (initial schema)
-- Rollback Script: See "DOWN MIGRATION" section at end of file
-- ============================================================

-- ============================================================
-- PRE-MIGRATION VERIFICATION
-- ============================================================

-- Check for existing tables (should be empty)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = 'users') THEN
        RAISE NOTICE 'WARNING: users table already exists';
    END IF;
    IF EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = 'research_sessions') THEN
        RAISE NOTICE 'WARNING: research_sessions table already exists';
    END IF;
    IF EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = 'draft_files') THEN
        RAISE NOTICE 'WARNING: draft_files table already exists';
    END IF;
END $$;

-- ============================================================
-- MIGRATION: CREATE TABLES
-- ============================================================

-- -------------------------------------------------------------
-- Table: users
-- Purpose: Store user profiles (both anonymous and registered)
-- Acceptance Criteria: AC#1
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE,  -- NULLABLE for anonymous users
  is_anonymous BOOLEAN NOT NULL DEFAULT false,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE users IS 'User profiles for TK9 Deep Research system';
COMMENT ON COLUMN users.id IS 'User UUID (primary key)';
COMMENT ON COLUMN users.email IS 'User email address (nullable for anonymous users, unique constraint)';
COMMENT ON COLUMN users.is_anonymous IS 'Flag indicating if user is anonymous (no email)';
COMMENT ON COLUMN users.created_at IS 'User account creation timestamp';
COMMENT ON COLUMN users.updated_at IS 'Last update timestamp (auto-updated by trigger)';

-- Index for fast email lookups (Acceptance Criteria: AC#4)
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- -------------------------------------------------------------
-- Enum: session_status
-- Purpose: Constrained values for research session states
-- Acceptance Criteria: AC#2
-- -------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'session_status') THEN
        CREATE TYPE session_status AS ENUM ('in_progress', 'completed', 'failed');
    END IF;
END $$;

COMMENT ON TYPE session_status IS 'Research session status: in_progress, completed, failed';

-- -------------------------------------------------------------
-- Table: research_sessions
-- Purpose: Track research sessions and their completion status
-- Acceptance Criteria: AC#2
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS research_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  status session_status NOT NULL DEFAULT 'in_progress',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE research_sessions IS 'Research sessions created by users';
COMMENT ON COLUMN research_sessions.id IS 'Session UUID (primary key)';
COMMENT ON COLUMN research_sessions.user_id IS 'Foreign key to users.id (CASCADE delete)';
COMMENT ON COLUMN research_sessions.title IS 'Research subject/query title';
COMMENT ON COLUMN research_sessions.status IS 'Session status (enum: in_progress, completed, failed)';
COMMENT ON COLUMN research_sessions.created_at IS 'Session start timestamp';
COMMENT ON COLUMN research_sessions.updated_at IS 'Last update timestamp (auto-updated by trigger)';

-- Indexes for fast queries (Acceptance Criteria: AC#4)
CREATE INDEX IF NOT EXISTS idx_research_sessions_user_id ON research_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_research_sessions_created_at ON research_sessions(created_at DESC);

-- -------------------------------------------------------------
-- Enum: research_stage
-- Purpose: Constrained values for research pipeline stages
-- Acceptance Criteria: AC#3
-- -------------------------------------------------------------
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
END $$;

COMMENT ON TYPE research_stage IS 'Research pipeline stages: 1_initial_research, 2_planning, 3_parallel_research, 4_writing';

-- -------------------------------------------------------------
-- Table: draft_files
-- Purpose: Track draft files generated during research stages
-- Acceptance Criteria: AC#3
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS draft_files (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL REFERENCES research_sessions(id) ON DELETE CASCADE,
  stage research_stage NOT NULL,
  file_path TEXT NOT NULL,
  detected_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE draft_files IS 'Draft files generated during research sessions';
COMMENT ON COLUMN draft_files.id IS 'Draft file UUID (primary key)';
COMMENT ON COLUMN draft_files.session_id IS 'Foreign key to research_sessions.id (CASCADE delete)';
COMMENT ON COLUMN draft_files.stage IS 'Research stage when file was generated (enum)';
COMMENT ON COLUMN draft_files.file_path IS 'File system path to draft file';
COMMENT ON COLUMN draft_files.detected_at IS 'Timestamp when file was detected';

-- Index for fast session file lookups (Acceptance Criteria: AC#4)
CREATE INDEX IF NOT EXISTS idx_draft_files_session_id ON draft_files(session_id);

-- ============================================================
-- TRIGGERS: Automatic Timestamp Updates
-- Acceptance Criteria: AC#5
-- ============================================================

-- -------------------------------------------------------------
-- Trigger Function: update_updated_at_column()
-- Purpose: Automatically update updated_at timestamp on row updates
-- -------------------------------------------------------------
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION update_updated_at_column() IS 'Trigger function to auto-update updated_at timestamp';

-- -------------------------------------------------------------
-- Trigger: update_users_updated_at
-- Applied to: users table
-- -------------------------------------------------------------
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
  BEFORE UPDATE ON users
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- -------------------------------------------------------------
-- Trigger: update_research_sessions_updated_at
-- Applied to: research_sessions table
-- -------------------------------------------------------------
DROP TRIGGER IF EXISTS update_research_sessions_updated_at ON research_sessions;
CREATE TRIGGER update_research_sessions_updated_at
  BEFORE UPDATE ON research_sessions
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- POST-MIGRATION VERIFICATION
-- ============================================================

-- Verify all tables exist
DO $$
DECLARE
    table_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count
    FROM pg_tables
    WHERE schemaname = 'public'
    AND tablename IN ('users', 'research_sessions', 'draft_files');

    IF table_count != 3 THEN
        RAISE EXCEPTION 'MIGRATION FAILED: Expected 3 tables, found %', table_count;
    ELSE
        RAISE NOTICE 'SUCCESS: All 3 tables created';
    END IF;
END $$;

-- Verify all indexes exist
DO $$
DECLARE
    index_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO index_count
    FROM pg_indexes
    WHERE schemaname = 'public'
    AND indexname IN (
        'idx_users_email',
        'idx_research_sessions_user_id',
        'idx_research_sessions_created_at',
        'idx_draft_files_session_id'
    );

    IF index_count != 4 THEN
        RAISE EXCEPTION 'MIGRATION FAILED: Expected 4 indexes, found %', index_count;
    ELSE
        RAISE NOTICE 'SUCCESS: All 4 indexes created';
    END IF;
END $$;

-- Verify all triggers exist
DO $$
DECLARE
    trigger_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO trigger_count
    FROM pg_trigger
    WHERE tgname IN (
        'update_users_updated_at',
        'update_research_sessions_updated_at'
    );

    IF trigger_count != 2 THEN
        RAISE EXCEPTION 'MIGRATION FAILED: Expected 2 triggers, found %', trigger_count;
    ELSE
        RAISE NOTICE 'SUCCESS: All 2 triggers created';
    END IF;
END $$;

-- ============================================================
-- POST-MIGRATION TESTING
-- ============================================================

-- Test 1: Insert test user (AC#1)
DO $$
DECLARE
    test_user_id UUID;
BEGIN
    INSERT INTO users (email, is_anonymous)
    VALUES ('migration_test@example.com', false)
    RETURNING id INTO test_user_id;

    RAISE NOTICE 'TEST 1 PASSED: User inserted with ID %', test_user_id;

    -- Cleanup
    DELETE FROM users WHERE id = test_user_id;
    RAISE NOTICE 'TEST 1 CLEANUP: Test user deleted';
END $$;

-- Test 2: Insert test session with foreign key (AC#2)
DO $$
DECLARE
    test_user_id UUID;
    test_session_id UUID;
BEGIN
    -- Create test user
    INSERT INTO users (email, is_anonymous)
    VALUES ('migration_test_fk@example.com', false)
    RETURNING id INTO test_user_id;

    -- Create test session
    INSERT INTO research_sessions (user_id, title, status)
    VALUES (test_user_id, 'Test Session', 'in_progress')
    RETURNING id INTO test_session_id;

    RAISE NOTICE 'TEST 2 PASSED: Session inserted with ID %', test_session_id;

    -- Cleanup (CASCADE should delete session)
    DELETE FROM users WHERE id = test_user_id;

    -- Verify CASCADE delete worked
    IF EXISTS (SELECT 1 FROM research_sessions WHERE id = test_session_id) THEN
        RAISE EXCEPTION 'TEST 2 FAILED: CASCADE delete did not work';
    ELSE
        RAISE NOTICE 'TEST 2 CLEANUP: CASCADE delete verified';
    END IF;
END $$;

-- Test 3: Test updated_at trigger (AC#5)
DO $$
DECLARE
    test_user_id UUID;
    initial_updated_at TIMESTAMPTZ;
    new_updated_at TIMESTAMPTZ;
BEGIN
    -- Insert test user
    INSERT INTO users (email, is_anonymous)
    VALUES ('migration_test_trigger@example.com', false)
    RETURNING id, updated_at INTO test_user_id, initial_updated_at;

    -- Wait briefly
    PERFORM pg_sleep(0.1);

    -- Update user
    UPDATE users SET is_anonymous = true WHERE id = test_user_id
    RETURNING updated_at INTO new_updated_at;

    -- Verify trigger updated timestamp
    IF new_updated_at > initial_updated_at THEN
        RAISE NOTICE 'TEST 3 PASSED: updated_at trigger working';
    ELSE
        RAISE EXCEPTION 'TEST 3 FAILED: updated_at trigger did not update timestamp';
    END IF;

    -- Cleanup
    DELETE FROM users WHERE id = test_user_id;
    RAISE NOTICE 'TEST 3 CLEANUP: Test user deleted';
END $$;

-- ============================================================
-- MIGRATION SUMMARY
-- ============================================================

-- Display final schema summary
SELECT
    'MIGRATION COMPLETE' as status,
    (SELECT COUNT(*) FROM pg_tables WHERE schemaname = 'public' AND tablename IN ('users', 'research_sessions', 'draft_files')) as tables_created,
    (SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public' AND indexname LIKE 'idx_%') as indexes_created,
    (SELECT COUNT(*) FROM pg_trigger WHERE tgname LIKE 'update_%') as triggers_created;

-- List all tables with row counts
SELECT
    tablename as table_name,
    (SELECT COUNT(*) FROM users) as users_count,
    (SELECT COUNT(*) FROM research_sessions) as sessions_count,
    (SELECT COUNT(*) FROM draft_files) as files_count
FROM pg_tables
WHERE schemaname = 'public'
AND tablename = 'users'
LIMIT 1;

-- ============================================================
-- DOWN MIGRATION (ROLLBACK)
-- ============================================================
-- To rollback this migration, execute the following in order:
--
-- DROP TRIGGER IF EXISTS update_research_sessions_updated_at ON research_sessions;
-- DROP TRIGGER IF EXISTS update_users_updated_at ON users;
-- DROP FUNCTION IF EXISTS update_updated_at_column();
-- DROP INDEX IF EXISTS idx_draft_files_session_id;
-- DROP TABLE IF EXISTS draft_files CASCADE;
-- DROP TYPE IF EXISTS research_stage;
-- DROP INDEX IF EXISTS idx_research_sessions_created_at;
-- DROP INDEX IF EXISTS idx_research_sessions_user_id;
-- DROP TABLE IF EXISTS research_sessions CASCADE;
-- DROP TYPE IF EXISTS session_status;
-- DROP INDEX IF EXISTS idx_users_email;
-- DROP TABLE IF EXISTS users CASCADE;
--
-- WARNING: This will permanently delete all user data, research sessions, and draft files!
-- ============================================================

-- ============================================================
-- AUDIT METADATA
-- ============================================================
-- [TO BE FILLED AFTER EXECUTION]
--
-- Execution Date: _______________
-- Executed By: _______________
-- Execution Time: _______________ ms
-- Database Version: PostgreSQL 15.8.1.073
-- Supabase Project: yurbnrqgsipdlijeyyuw
--
-- Verification Checklist:
-- [ ] All 3 tables created successfully
-- [ ] All 4 indexes created successfully
-- [ ] All 2 triggers created successfully
-- [ ] All 3 test cases passed
-- [ ] No errors in Supabase logs
-- [ ] Foreign key constraints working
-- [ ] CASCADE deletes working
-- [ ] updated_at triggers working
-- [ ] Email unique constraint working
--
-- Sign-off: _______________
-- ============================================================

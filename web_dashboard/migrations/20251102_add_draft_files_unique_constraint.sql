-- Migration: Add unique constraint to draft_files for upsert support
-- Created: 2025-11-02
-- Description: Adds unique constraint on (session_id, file_path) to prevent duplicates
--              and enable upsert operations when files are re-detected

-- Add unique constraint on (session_id, file_path)
-- This ensures one entry per file per session
ALTER TABLE public.draft_files
ADD CONSTRAINT draft_files_session_file_unique
UNIQUE (session_id, file_path);

-- Add comment for documentation
COMMENT ON CONSTRAINT draft_files_session_file_unique ON public.draft_files
IS 'Ensures one entry per file per session, enables upsert for re-detection';

-- Migration validation
DO $$
BEGIN
  -- Check if constraint was added successfully
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.table_constraints
    WHERE table_schema = 'public'
    AND table_name = 'draft_files'
    AND constraint_name = 'draft_files_session_file_unique'
  ) THEN
    RAISE EXCEPTION 'Migration failed: unique constraint not added';
  END IF;

  RAISE NOTICE 'Migration completed successfully: Added unique constraint to draft_files';
END $$;

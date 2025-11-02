-- Migration: Fix file stats trigger to use file_size_bytes column
-- Created: 2025-11-02
-- Description: Updates trigger to use file_size_bytes instead of pg_stat_file()
--              for DRY compliance and to work with relative file paths

-- Drop old function
DROP FUNCTION IF EXISTS update_session_file_stats() CASCADE;

-- Create corrected function that uses file_size_bytes column
CREATE OR REPLACE FUNCTION update_session_file_stats()
RETURNS TRIGGER AS $$
DECLARE
  affected_session_id UUID;
BEGIN
  -- Determine which session_id to update (NEW for INSERT/UPDATE, OLD for DELETE)
  IF TG_OP = 'DELETE' THEN
    affected_session_id := OLD.session_id;
  ELSE
    affected_session_id := NEW.session_id;
  END IF;

  -- Update file count and total size for the session
  -- DRY: Uses file_size_bytes column instead of reading filesystem
  UPDATE public.research_sessions
  SET
    file_count = (
      SELECT COUNT(*)
      FROM public.draft_files
      WHERE session_id = affected_session_id
    ),
    total_size_bytes = (
      SELECT COALESCE(SUM(file_size_bytes), 0)
      FROM public.draft_files
      WHERE session_id = affected_session_id
    ),
    updated_at = NOW()
  WHERE id = affected_session_id;

  -- Return appropriate record for trigger
  IF TG_OP = 'DELETE' THEN
    RETURN OLD;
  ELSE
    RETURN NEW;
  END IF;
END;
$$ LANGUAGE plpgsql;

-- Recreate trigger with fixed function
DROP TRIGGER IF EXISTS trigger_update_session_file_stats ON public.draft_files;
CREATE TRIGGER trigger_update_session_file_stats
AFTER INSERT OR UPDATE OR DELETE ON public.draft_files
FOR EACH ROW
EXECUTE FUNCTION update_session_file_stats();

-- Add comment for documentation
COMMENT ON FUNCTION update_session_file_stats() IS
'Auto-updates research_sessions.file_count and total_size_bytes when draft_files changes. Uses file_size_bytes column for DRY compliance.';

-- Migration validation
DO $$
BEGIN
  -- Check if function was created successfully
  IF NOT EXISTS (
    SELECT 1 FROM pg_proc
    WHERE proname = 'update_session_file_stats'
  ) THEN
    RAISE EXCEPTION 'Migration failed: update_session_file_stats function not created';
  END IF;

  -- Check if trigger exists
  IF NOT EXISTS (
    SELECT 1 FROM pg_trigger
    WHERE tgname = 'trigger_update_session_file_stats'
  ) THEN
    RAISE EXCEPTION 'Migration failed: trigger_update_session_file_stats not created';
  END IF;

  RAISE NOTICE 'Migration completed successfully: Fixed file stats trigger to use file_size_bytes';
END $$;

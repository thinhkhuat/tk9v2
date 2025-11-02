-- Migration: Add session metadata columns for advanced session management
-- Created: 2025-11-02
-- Description: Adds language, parameters, archive status, and file statistics to research_sessions table

-- Add new columns to research_sessions table
ALTER TABLE public.research_sessions
ADD COLUMN IF NOT EXISTS language VARCHAR(10) DEFAULT 'vi' NOT NULL,
ADD COLUMN IF NOT EXISTS parameters JSONB DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS archived_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS file_count INTEGER DEFAULT 0 NOT NULL,
ADD COLUMN IF NOT EXISTS total_size_bytes BIGINT DEFAULT 0 NOT NULL;

-- Add comments for documentation
COMMENT ON COLUMN public.research_sessions.language IS 'Research output language (ISO 639-1 code)';
COMMENT ON COLUMN public.research_sessions.parameters IS 'Research parameters (tone, depth, format options, etc.) as JSON';
COMMENT ON COLUMN public.research_sessions.archived_at IS 'Timestamp when session was archived (NULL = not archived)';
COMMENT ON COLUMN public.research_sessions.file_count IS 'Number of files generated in this session';
COMMENT ON COLUMN public.research_sessions.total_size_bytes IS 'Total size of all files in bytes';

-- Create indexes for efficient filtering and sorting
CREATE INDEX IF NOT EXISTS idx_research_sessions_archived_at
ON public.research_sessions(archived_at);

CREATE INDEX IF NOT EXISTS idx_research_sessions_language
ON public.research_sessions(language);

CREATE INDEX IF NOT EXISTS idx_research_sessions_status
ON public.research_sessions(status);

CREATE INDEX IF NOT EXISTS idx_research_sessions_user_created
ON public.research_sessions(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_research_sessions_user_archived
ON public.research_sessions(user_id, archived_at)
WHERE archived_at IS NOT NULL;

-- Create partial index for active (non-archived) sessions
CREATE INDEX IF NOT EXISTS idx_research_sessions_active
ON public.research_sessions(user_id, created_at DESC)
WHERE archived_at IS NULL;

-- Function to automatically update file statistics
CREATE OR REPLACE FUNCTION update_session_file_stats()
RETURNS TRIGGER AS $$
BEGIN
  -- Update file count and total size for the session
  UPDATE public.research_sessions
  SET
    file_count = (
      SELECT COUNT(*)
      FROM public.draft_files
      WHERE session_id = NEW.session_id
    ),
    total_size_bytes = (
      SELECT COALESCE(SUM(
        (SELECT pg_stat_file(file_path, true)).size
      ), 0)
      FROM public.draft_files
      WHERE session_id = NEW.session_id
    ),
    updated_at = NOW()
  WHERE id = NEW.session_id;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to auto-update file stats when files are added/removed
DROP TRIGGER IF EXISTS trigger_update_session_file_stats ON public.draft_files;
CREATE TRIGGER trigger_update_session_file_stats
AFTER INSERT OR DELETE ON public.draft_files
FOR EACH ROW
EXECUTE FUNCTION update_session_file_stats();

-- Update RLS policies to include archived sessions
-- Drop existing policies if they exist
DROP POLICY IF EXISTS "Users can view their own research sessions" ON public.research_sessions;
DROP POLICY IF EXISTS "Users can insert their own research sessions" ON public.research_sessions;
DROP POLICY IF EXISTS "Users can update their own research sessions" ON public.research_sessions;
DROP POLICY IF EXISTS "Users can delete their own research sessions" ON public.research_sessions;

-- Create updated RLS policies
-- Policy: Users can view all their own sessions (including archived)
CREATE POLICY "Users can view their own research sessions"
ON public.research_sessions
FOR SELECT
USING (auth.uid() = user_id);

-- Policy: Users can insert their own sessions
CREATE POLICY "Users can insert their own research sessions"
ON public.research_sessions
FOR INSERT
WITH CHECK (auth.uid() = user_id);

-- Policy: Users can update their own sessions (including archive/restore)
CREATE POLICY "Users can update their own research sessions"
ON public.research_sessions
FOR UPDATE
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

-- Policy: Users can delete their own sessions (permanent delete after archive)
CREATE POLICY "Users can delete their own research sessions"
ON public.research_sessions
FOR DELETE
USING (auth.uid() = user_id);

-- Ensure RLS is enabled on research_sessions table
ALTER TABLE public.research_sessions ENABLE ROW LEVEL SECURITY;

-- Grant necessary permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON public.research_sessions TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.research_sessions TO anon;

-- Migration validation
DO $$
BEGIN
  -- Check if all columns were added successfully
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public'
    AND table_name = 'research_sessions'
    AND column_name IN ('language', 'parameters', 'archived_at', 'file_count', 'total_size_bytes')
    GROUP BY table_name
    HAVING COUNT(*) = 5
  ) THEN
    RAISE EXCEPTION 'Migration failed: Not all columns were added';
  END IF;

  RAISE NOTICE 'Migration completed successfully: Added session metadata columns and indexes';
END $$;

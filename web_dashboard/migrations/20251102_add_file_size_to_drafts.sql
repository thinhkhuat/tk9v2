-- Migration: Add file_size_bytes column to draft_files table
-- Created: 2025-11-02
-- Description: Adds file_size_bytes column to draft_files for DRY compliance
--              This allows accurate calculation of total_size_bytes without filesystem access

-- Add file_size_bytes column to draft_files table
ALTER TABLE public.draft_files
ADD COLUMN IF NOT EXISTS file_size_bytes BIGINT DEFAULT 0 NOT NULL;

-- Add comment for documentation
COMMENT ON COLUMN public.draft_files.file_size_bytes IS 'File size in bytes (populated when file is detected)';

-- Create index for efficient aggregation queries
CREATE INDEX IF NOT EXISTS idx_draft_files_session_size
ON public.draft_files(session_id, file_size_bytes);

-- Update existing rows to set file_size_bytes to 0 (will be populated by application)
UPDATE public.draft_files
SET file_size_bytes = 0
WHERE file_size_bytes IS NULL;

-- Migration validation
DO $$
BEGIN
  -- Check if column was added successfully
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public'
    AND table_name = 'draft_files'
    AND column_name = 'file_size_bytes'
  ) THEN
    RAISE EXCEPTION 'Migration failed: file_size_bytes column not added';
  END IF;

  RAISE NOTICE 'Migration completed successfully: Added file_size_bytes to draft_files';
END $$;

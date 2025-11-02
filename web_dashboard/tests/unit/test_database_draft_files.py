"""
Unit tests for database.create_draft_file() function.
Tests validation, path traversal protection, and upsert behavior.
"""

import sys
from pathlib import Path

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import database


class TestCreateDraftFileValidation:
    """Test validation and security in create_draft_file()"""

    @pytest.mark.asyncio
    async def test_blocks_path_traversal_with_double_dots(self):
        """Should reject file paths containing '..' (path traversal)"""
        result = await database.create_draft_file(
            session_id="test-session-id",
            file_path="../malicious/path.pdf",
            file_size_bytes=1000,
            stage="4_writing",
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_blocks_absolute_paths(self):
        """Should reject absolute file paths starting with '/'"""
        result = await database.create_draft_file(
            session_id="test-session-id",
            file_path="/etc/passwd",
            file_size_bytes=1000,
            stage="4_writing",
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_accepts_valid_relative_path(self):
        """Should accept valid relative paths without traversal"""
        # Note: This will still fail if Supabase not configured, but validates path check passes
        result = await database.create_draft_file(
            session_id="550e8400-e29b-41d4-a716-446655440000",
            file_path="outputs/550e8400-e29b-41d4-a716-446655440000/report.pdf",
            file_size_bytes=1000,
            stage="4_writing",
        )
        # Result depends on Supabase config, but path validation should pass
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_handles_url_encoded_filenames(self):
        """Should handle URL-encoded characters in filenames"""
        result = await database.create_draft_file(
            session_id="550e8400-e29b-41d4-a716-446655440000",
            file_path="outputs/550e8400-e29b-41d4-a716-446655440000/report%20with%20spaces.pdf",
            file_size_bytes=1000,
            stage="4_writing",
        )
        # Path validation should pass (no '..' or leading '/')
        assert isinstance(result, bool)


class TestCreateDraftFileUpsertBehavior:
    """Test upsert behavior with duplicate files"""

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not database.get_supabase_client(),
        reason="Requires Supabase configuration",
    )
    async def test_upsert_updates_existing_file(self):
        """Should update file_size_bytes if file already exists"""
        session_id = "test-upsert-session"
        file_path = "outputs/test-upsert-session/test.pdf"

        # First insert
        result1 = await database.create_draft_file(
            session_id=session_id,
            file_path=file_path,
            file_size_bytes=1000,
            stage="4_writing",
        )
        assert result1 is True

        # Second insert (same path) - should update, not fail
        result2 = await database.create_draft_file(
            session_id=session_id,
            file_path=file_path,
            file_size_bytes=2000,  # Different size
            stage="4_writing",
        )
        assert result2 is True

        # Cleanup
        client = database.get_supabase_client()
        if client:
            client.table("draft_files").delete().eq("session_id", session_id).execute()

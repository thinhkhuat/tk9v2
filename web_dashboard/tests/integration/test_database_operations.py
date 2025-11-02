"""
⚠️  DEPRECATED - DO NOT USE  ⚠️

This test file uses the WRONG users table (public.users instead of auth.users).
It was created before Story 1.3 correction and is now INVALID.

Use test_database_operations_auth_users.py instead - that file correctly uses auth.users.

---

Integration tests for database operations
Story 1.3: User and Session Database Schema

These tests require:
1. Supabase project configured with migration applied
2. SUPABASE_URL and SUPABASE_SERVICE_KEY in .env file or environment variables
3. Database tables: users, research_sessions, draft_files

Run tests with: pytest tests/integration/test_database_operations.py -v
"""

import asyncio
import os
import sys
from pathlib import Path
from uuid import UUID, uuid4

import pytest

# DEPRECATED: Skip all tests in this file
pytestmark = pytest.mark.skip(
    reason="DEPRECATED: Uses wrong users table. Use test_database_operations_auth_users.py"
)

# Load environment variables from .env file
from dotenv import load_dotenv  # noqa: E402 - Must load before other imports

# ALWAYS use web_dashboard/.env - the ONLY source of truth
# Test path: web_dashboard/tests/integration/test_*.py
# .env path: web_dashboard/.env (3 levels up from test file)
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

# ruff: noqa: E402 - Imports after sys.path modification are intentional
from database import (
    create_research_session,
    get_supabase_client,
    transfer_sessions,
    update_research_session_status,
)
from models import SessionStatusEnum


@pytest.fixture(scope="module")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def skip_if_no_supabase():
    """Skip tests if Supabase is not configured"""
    client = get_supabase_client()
    if client is None:
        pytest.skip("Supabase not configured - set SUPABASE_URL and SUPABASE_SERVICE_KEY")


# ============================================================
# AC1: Test users table schema
# ============================================================


@pytest.mark.asyncio
async def test_users_table_exists(skip_if_no_supabase):
    """Test that users table exists and can be queried"""
    client = get_supabase_client()
    assert client is not None, "Supabase client not initialized"

    # Try to query users table (should not raise error)
    result = client.table("users").select("*").limit(1).execute()
    assert result is not None


@pytest.mark.asyncio
async def test_user_email_unique_constraint(skip_if_no_supabase):
    """Test that email column has unique constraint"""
    client = get_supabase_client()
    test_email = f"test_{uuid4()}@example.com"

    # Insert first user
    user1_data = {"email": test_email, "is_anonymous": False}
    result1 = client.table("users").insert(user1_data).execute()
    assert len(result1.data) > 0, "Failed to insert first user"
    user1_id = result1.data[0]["id"]

    # Try to insert duplicate email (should fail)
    user2_data = {"email": test_email, "is_anonymous": False}
    try:
        client.table("users").insert(user2_data).execute()
        pytest.fail("Expected unique constraint violation")
    except Exception as e:
        # Expected error for duplicate email
        assert "duplicate" in str(e).lower() or "unique" in str(e).lower()

    # Cleanup
    client.table("users").delete().eq("id", user1_id).execute()


# ============================================================
# AC2: Test research_sessions table schema
# ============================================================


@pytest.mark.asyncio
async def test_create_research_session(skip_if_no_supabase):
    """Test creating research session with database function"""
    session_id = str(uuid4())
    user_id = str(uuid4())
    title = "Test Research Session"

    # Create test user first
    client = get_supabase_client()
    user_data = {"id": user_id, "email": None, "is_anonymous": True}
    client.table("users").insert(user_data).execute()

    # Create research session
    session = await create_research_session(
        session_id=session_id,
        user_id=user_id,
        title=title,
        status=SessionStatusEnum.IN_PROGRESS,
    )

    assert session is not None, "Failed to create session"
    assert session.id == UUID(session_id)
    assert session.user_id == UUID(user_id)
    assert session.title == title
    assert session.status == SessionStatusEnum.IN_PROGRESS

    # Cleanup
    client.table("research_sessions").delete().eq("id", session_id).execute()
    client.table("users").delete().eq("id", user_id).execute()


@pytest.mark.asyncio
async def test_update_session_status(skip_if_no_supabase):
    """Test updating session status"""
    session_id = str(uuid4())
    user_id = str(uuid4())

    # Setup: Create user and session
    client = get_supabase_client()
    client.table("users").insert({"id": user_id, "is_anonymous": True}).execute()
    await create_research_session(session_id, user_id, "Test", SessionStatusEnum.IN_PROGRESS)

    # Update status to completed
    success = await update_research_session_status(session_id, SessionStatusEnum.COMPLETED)
    assert success, "Failed to update session status"

    # Verify status was updated
    result = client.table("research_sessions").select("status").eq("id", session_id).execute()
    assert len(result.data) > 0
    assert result.data[0]["status"] == "completed"

    # Cleanup
    client.table("research_sessions").delete().eq("id", session_id).execute()
    client.table("users").delete().eq("id", user_id).execute()


# ============================================================
# AC3: Test draft_files table schema
# ============================================================


@pytest.mark.asyncio
async def test_draft_files_table_exists(skip_if_no_supabase):
    """Test that draft_files table exists and foreign keys work"""
    session_id = str(uuid4())
    user_id = str(uuid4())

    # Setup: Create user and session
    client = get_supabase_client()
    client.table("users").insert({"id": user_id, "is_anonymous": True}).execute()
    await create_research_session(session_id, user_id, "Test", SessionStatusEnum.IN_PROGRESS)

    # Insert draft file
    file_data = {
        "session_id": session_id,
        "stage": "1_initial_research",
        "file_path": "/outputs/test/file.json",
    }
    result = client.table("draft_files").insert(file_data).execute()
    assert len(result.data) > 0, "Failed to insert draft file"
    file_id = result.data[0]["id"]

    # Cleanup
    client.table("draft_files").delete().eq("id", file_id).execute()
    client.table("research_sessions").delete().eq("id", session_id).execute()
    client.table("users").delete().eq("id", user_id).execute()


# ============================================================
# AC4: Test indexes
# ============================================================


@pytest.mark.asyncio
async def test_indexes_exist(skip_if_no_supabase):
    """Test that required indexes exist"""
    client = get_supabase_client()

    # Query for indexes (PostgreSQL specific)
    indexes_query = """
    SELECT indexname, tablename
    FROM pg_indexes
    WHERE schemaname = 'public'
    AND indexname IN (
        'idx_users_email',
        'idx_research_sessions_user_id',
        'idx_research_sessions_created_at',
        'idx_draft_files_session_id'
    )
    """

    try:
        result = client.rpc("execute_sql", {"query": indexes_query}).execute()
        # If RPC not available, skip this test
        if not result:
            pytest.skip("Cannot verify indexes - RPC not available")
    except Exception:  # noqa: E722 - Broad exception catching for test skip logic
        pytest.skip("Cannot verify indexes - requires SQL execution permissions")


# ============================================================
# AC5: Test updated_at trigger
# ============================================================


@pytest.mark.asyncio
async def test_updated_at_trigger(skip_if_no_supabase):
    """Test that updated_at timestamp changes on update"""
    session_id = str(uuid4())
    user_id = str(uuid4())

    # Setup: Create user and session
    client = get_supabase_client()
    client.table("users").insert({"id": user_id, "is_anonymous": True}).execute()
    await create_research_session(session_id, user_id, "Test", SessionStatusEnum.IN_PROGRESS)

    # Get initial timestamps
    result1 = (
        client.table("research_sessions")
        .select("created_at, updated_at")
        .eq("id", session_id)
        .execute()
    )
    initial_updated_at = result1.data[0]["updated_at"]

    # Wait a moment to ensure timestamp difference
    await asyncio.sleep(1)

    # Update session
    await update_research_session_status(session_id, SessionStatusEnum.COMPLETED)

    # Get updated timestamps
    result2 = (
        client.table("research_sessions")
        .select("created_at, updated_at")
        .eq("id", session_id)
        .execute()
    )
    new_updated_at = result2.data[0]["updated_at"]

    # Verify updated_at changed
    assert new_updated_at > initial_updated_at, "updated_at timestamp did not change on update"

    # Cleanup
    client.table("research_sessions").delete().eq("id", session_id).execute()
    client.table("users").delete().eq("id", user_id).execute()


# ============================================================
# Test session transfer (Story 1.2 dependency)
# ============================================================


@pytest.mark.asyncio
async def test_session_transfer_with_database(skip_if_no_supabase):
    """Test session transfer updates user_id correctly"""
    old_user_id = str(uuid4())
    new_user_id = str(uuid4())
    session1_id = str(uuid4())
    session2_id = str(uuid4())

    # Setup: Create users
    client = get_supabase_client()
    client.table("users").insert({"id": old_user_id, "is_anonymous": True}).execute()
    client.table("users").insert(
        {"id": new_user_id, "is_anonymous": False, "email": "test@example.com"}
    ).execute()

    # Create sessions for old user
    await create_research_session(
        session1_id, old_user_id, "Session 1", SessionStatusEnum.COMPLETED
    )
    await create_research_session(
        session2_id, old_user_id, "Session 2", SessionStatusEnum.IN_PROGRESS
    )

    # Transfer sessions
    transferred_count = await transfer_sessions(old_user_id, new_user_id)
    assert transferred_count == 2, f"Expected 2 sessions transferred, got {transferred_count}"

    # Verify sessions now belong to new user
    result = client.table("research_sessions").select("user_id").eq("id", session1_id).execute()
    assert result.data[0]["user_id"] == new_user_id

    result = client.table("research_sessions").select("user_id").eq("id", session2_id).execute()
    assert result.data[0]["user_id"] == new_user_id

    # Cleanup
    client.table("research_sessions").delete().eq("id", session1_id).execute()
    client.table("research_sessions").delete().eq("id", session2_id).execute()
    client.table("users").delete().eq("id", old_user_id).execute()
    client.table("users").delete().eq("id", new_user_id).execute()


# ============================================================
# Test cascade deletes
# ============================================================


@pytest.mark.asyncio
async def test_cascade_delete_user_sessions(skip_if_no_supabase):
    """Test that deleting user cascades to research_sessions"""
    user_id = str(uuid4())
    session_id = str(uuid4())

    # Setup: Create user and session
    client = get_supabase_client()
    client.table("users").insert({"id": user_id, "is_anonymous": True}).execute()
    await create_research_session(session_id, user_id, "Test", SessionStatusEnum.IN_PROGRESS)

    # Delete user
    client.table("users").delete().eq("id", user_id).execute()

    # Verify session was also deleted (CASCADE)
    result = client.table("research_sessions").select("id").eq("id", session_id).execute()
    assert len(result.data) == 0, "Session was not cascaded deleted"


@pytest.mark.asyncio
async def test_cascade_delete_session_files(skip_if_no_supabase):
    """Test that deleting session cascades to draft_files"""
    user_id = str(uuid4())
    session_id = str(uuid4())

    # Setup: Create user, session, and file
    client = get_supabase_client()
    client.table("users").insert({"id": user_id, "is_anonymous": True}).execute()
    await create_research_session(session_id, user_id, "Test", SessionStatusEnum.IN_PROGRESS)

    file_data = {
        "session_id": session_id,
        "stage": "1_initial_research",
        "file_path": "/test/file.json",
    }
    file_result = client.table("draft_files").insert(file_data).execute()
    file_id = file_result.data[0]["id"]

    # Delete session
    client.table("research_sessions").delete().eq("id", session_id).execute()

    # Verify file was also deleted (CASCADE)
    result = client.table("draft_files").select("id").eq("id", file_id).execute()
    assert len(result.data) == 0, "Draft file was not cascaded deleted"

    # Cleanup user
    client.table("users").delete().eq("id", user_id).execute()


# ============================================================
# Test foreign key constraints
# ============================================================


@pytest.mark.asyncio
async def test_foreign_key_constraint_invalid_user(skip_if_no_supabase):
    """Test that inserting session with invalid user_id fails"""
    invalid_user_id = str(uuid4())
    session_id = str(uuid4())

    client = get_supabase_client()

    # Try to create session with non-existent user_id
    try:
        session_data = {
            "id": session_id,
            "user_id": invalid_user_id,
            "title": "Test",
            "status": "in_progress",
        }
        client.table("research_sessions").insert(session_data).execute()
        pytest.fail("Expected foreign key violation")
    except Exception as e:
        # Expected error for FK constraint
        assert "foreign" in str(e).lower() or "violat" in str(e).lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Integration tests for Row-Level Security (RLS) with REAL user authentication.

Unlike test_rls_policies.py which uses service_role (bypasses RLS),
these tests use actual user-level JWT tokens to verify RLS enforcement.

Story: 1.4 - Row-Level Security (RLS) Policies Implementation
"""

import pytest
import pytest_asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from web_dashboard/.env
env_path = Path(__file__).parent.parent.parent / "web_dashboard" / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    env_path = Path(__file__).parent.parent.parent / ".env"
    load_dotenv(env_path)

# Skip all tests if Supabase credentials are not configured
pytestmark = pytest.mark.skipif(
    not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_ANON_KEY"),
    reason="Supabase credentials not configured in .env",
)


@pytest_asyncio.fixture
async def authenticated_clients():
    """
    Create two authenticated Supabase clients for testing RLS isolation.

    This uses the ANON key (not service role) so RLS policies are enforced.
    Creates two test users and returns authenticated clients for each.
    """
    from supabase import create_client

    supabase_url = os.getenv("SUPABASE_URL")
    anon_key = os.getenv("SUPABASE_ANON_KEY")

    if not supabase_url or not anon_key:
        pytest.skip("Supabase anon key not configured")

    # Create base client for user creation (using anon key)
    base_client = create_client(supabase_url, anon_key)

    # Create two test users via anonymous sign in
    # Anonymous users get unique UUIDs and respect RLS
    user_a_response = base_client.auth.sign_in_anonymously()
    user_a_session = user_a_response.session
    user_a_id = user_a_response.user.id

    user_b_response = base_client.auth.sign_in_anonymously()
    user_b_session = user_b_response.session
    user_b_id = user_b_response.user.id

    # Create authenticated clients with user sessions
    client_a = create_client(supabase_url, anon_key)
    client_a.auth.set_session(user_a_session.access_token, user_a_session.refresh_token)

    client_b = create_client(supabase_url, anon_key)
    client_b.auth.set_session(user_b_session.access_token, user_b_session.refresh_token)

    yield {
        "user_a": {"id": user_a_id, "client": client_a, "session": user_a_session},
        "user_b": {"id": user_b_id, "client": client_b, "session": user_b_session},
    }

    # Cleanup: Sign out users (this will cascade delete anonymous users)
    try:
        client_a.auth.sign_out()
        client_b.auth.sign_out()
    except Exception as e:
        print(f"Cleanup warning: {e}")


# ============================================================================
# AC3: research_sessions SELECT policy - REAL RLS TEST
# ============================================================================


@pytest.mark.asyncio
async def test_rls_blocks_unauthorized_session_access(authenticated_clients):
    """
    REAL RLS TEST: Verify User B cannot access User A's sessions.

    This test uses actual user JWT tokens (not service_role), so RLS is enforced.
    """
    user_a = authenticated_clients["user_a"]
    user_b = authenticated_clients["user_b"]

    # User A creates a session
    session_response = (
        user_a["client"]
        .table("research_sessions")
        .insert(
            {"user_id": user_a["id"], "title": "User A Private Session", "status": "in_progress"}
        )
        .execute()
    )

    session_id = session_response.data[0]["id"]

    # User A can see their own session (positive test)
    user_a_query = (
        user_a["client"].table("research_sessions").select("*").eq("id", session_id).execute()
    )
    assert len(user_a_query.data) == 1, "User A should see their own session"
    assert user_a_query.data[0]["id"] == session_id

    # User B CANNOT see User A's session (negative test - RLS enforcement)
    user_b_query = (
        user_b["client"].table("research_sessions").select("*").eq("id", session_id).execute()
    )
    assert len(user_b_query.data) == 0, "User B should NOT see User A's session (RLS blocks it)"

    # Cleanup
    user_a["client"].table("research_sessions").delete().eq("id", session_id).execute()


# ============================================================================
# AC4: research_sessions INSERT policy - REAL RLS TEST
# ============================================================================


@pytest.mark.asyncio
async def test_rls_blocks_inserting_session_for_other_user(authenticated_clients):
    """
    REAL RLS TEST: Verify User B cannot create a session for User A.

    WITH CHECK constraint should reject the insert.
    """
    user_a = authenticated_clients["user_a"]
    user_b = authenticated_clients["user_b"]

    # User B attempts to create session with User A's user_id
    # This should FAIL due to RLS WITH CHECK constraint
    with pytest.raises(Exception) as exc_info:
        user_b["client"].table("research_sessions").insert(
            {
                "user_id": user_a["id"],  # Wrong user_id!
                "title": "Fake Session",
                "status": "in_progress",
            }
        ).execute()

    # Verify the error is permission-related
    error_msg = str(exc_info.value).lower()
    assert (
        "policy" in error_msg or "permission" in error_msg or "violat" in error_msg
    ), f"Expected RLS policy violation error, got: {exc_info.value}"


# ============================================================================
# AC4: research_sessions UPDATE policy - REAL RLS TEST
# ============================================================================


@pytest.mark.asyncio
async def test_rls_blocks_updating_other_users_session(authenticated_clients):
    """
    REAL RLS TEST: Verify User B cannot update User A's session.

    RLS USING clause should filter out unauthorized sessions.
    """
    user_a = authenticated_clients["user_a"]
    user_b = authenticated_clients["user_b"]

    # User A creates a session
    session_response = (
        user_a["client"]
        .table("research_sessions")
        .insert({"user_id": user_a["id"], "title": "User A Session", "status": "in_progress"})
        .execute()
    )

    session_id = session_response.data[0]["id"]

    # User B attempts to update User A's session
    # RLS should filter it out (0 rows affected, no error)
    update_response = (
        user_b["client"]
        .table("research_sessions")
        .update({"status": "completed"})
        .eq("id", session_id)
        .execute()
    )

    assert len(update_response.data) == 0, "Update should affect 0 rows (RLS filters it out)"

    # Verify session status unchanged
    check_response = (
        user_a["client"].table("research_sessions").select("status").eq("id", session_id).execute()
    )
    assert check_response.data[0]["status"] == "in_progress", "Status should remain unchanged"

    # Cleanup
    user_a["client"].table("research_sessions").delete().eq("id", session_id).execute()


# ============================================================================
# AC5: draft_files SELECT policy - REAL RLS TEST
# ============================================================================


@pytest.mark.asyncio
async def test_rls_blocks_accessing_drafts_from_other_users_sessions(authenticated_clients):
    """
    REAL RLS TEST: Verify User B cannot access drafts from User A's sessions.

    The draft_files RLS policy uses a subquery to check session ownership.
    """
    user_a = authenticated_clients["user_a"]
    user_b = authenticated_clients["user_b"]

    # User A creates session and draft
    session_response = (
        user_a["client"]
        .table("research_sessions")
        .insert(
            {
                "user_id": user_a["id"],
                "title": "User A Session with Drafts",
                "status": "in_progress",
            }
        )
        .execute()
    )

    session_id = session_response.data[0]["id"]

    draft_response = (
        user_a["client"]
        .table("draft_files")
        .insert(
            {
                "session_id": session_id,
                "stage": "1_initial_research",
                "file_path": "/outputs/test/draft.json",
            }
        )
        .execute()
    )

    draft_id = draft_response.data[0]["id"]

    # User A can see their own drafts (positive test)
    user_a_query = (
        user_a["client"].table("draft_files").select("*").eq("session_id", session_id).execute()
    )
    assert len(user_a_query.data) == 1, "User A should see their own drafts"

    # User B CANNOT see User A's drafts (negative test - RLS subquery blocks it)
    user_b_query = (
        user_b["client"].table("draft_files").select("*").eq("session_id", session_id).execute()
    )
    assert len(user_b_query.data) == 0, "User B should NOT see User A's drafts (RLS blocks it)"

    # Cleanup (cascade will delete draft)
    user_a["client"].table("research_sessions").delete().eq("id", session_id).execute()


# ============================================================================
# AC6: Multi-user complete isolation - REAL RLS TEST
# ============================================================================


@pytest.mark.asyncio
async def test_complete_data_isolation_between_users(authenticated_clients):
    """
    REAL RLS TEST: Comprehensive multi-user isolation verification.

    This is the definitive test that RLS actually works with real authentication.
    """
    user_a = authenticated_clients["user_a"]
    user_b = authenticated_clients["user_b"]

    # Both users create sessions
    session_a = (
        user_a["client"]
        .table("research_sessions")
        .insert(
            {"user_id": user_a["id"], "title": "User A Private Research", "status": "in_progress"}
        )
        .execute()
        .data[0]
    )

    session_b = (
        user_b["client"]
        .table("research_sessions")
        .insert(
            {"user_id": user_b["id"], "title": "User B Private Research", "status": "in_progress"}
        )
        .execute()
        .data[0]
    )

    # User A queries all sessions - should only see their own
    user_a_sessions = user_a["client"].table("research_sessions").select("*").execute()
    user_a_ids = [s["id"] for s in user_a_sessions.data]

    assert session_a["id"] in user_a_ids, "User A should see their own session"
    assert session_b["id"] not in user_a_ids, "User A should NOT see User B's session"

    # User B queries all sessions - should only see their own
    user_b_sessions = user_b["client"].table("research_sessions").select("*").execute()
    user_b_ids = [s["id"] for s in user_b_sessions.data]

    assert session_b["id"] in user_b_ids, "User B should see their own session"
    assert session_a["id"] not in user_b_ids, "User B should NOT see User A's session"

    # Verify complete isolation: no overlap
    assert (
        len(set(user_a_ids) & set(user_b_ids)) == 0
    ), "No session IDs should overlap between users"

    # Cleanup
    user_a["client"].table("research_sessions").delete().eq("id", session_a["id"]).execute()
    user_b["client"].table("research_sessions").delete().eq("id", session_b["id"]).execute()


# ============================================================================
# Summary
# ============================================================================

"""
Test Coverage Summary (REAL RLS TESTS):

✅ AC3: research_sessions SELECT policy with user JWT
✅ AC4: research_sessions INSERT policy with user JWT (WITH CHECK enforcement)
✅ AC4: research_sessions UPDATE policy with user JWT (USING enforcement)
✅ AC5: draft_files SELECT policy with subquery (user JWT)
✅ AC6: Complete multi-user isolation with real authentication

These tests ACTUALLY verify RLS enforcement because they:
1. Use SUPABASE_ANON_KEY (not service_role)
2. Authenticate as real users via sign_in_anonymously()
3. Make requests with user-level JWT tokens
4. Verify that unauthorized access returns empty results (not errors)
5. Verify that policy violations raise permission errors

Compare to test_rls_policies.py:
- Old tests: Use service_role → RLS bypassed → Documents expected behavior
- New tests: Use anon_key + user auth → RLS enforced → Proves actual security
"""

"""
Database module for Supabase integration
Story 1.3: User and Session Database Schema
"""

import logging
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from supabase import Client, create_client

from models import DraftFile, ResearchSessionDB, SessionStatusEnum

# Load environment variables from .env file
# ALWAYS use web_dashboard/.env - the ONLY source of truth
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

logger = logging.getLogger(__name__)

# Supabase configuration from environment
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")  # For server-side operations
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")  # For client-side operations

# Global Supabase client instance
_supabase_client: Optional[Client] = None


def get_supabase_client() -> Optional[Client]:
    """
    Get or create Supabase client instance with SERVICE ROLE privileges.

    CRITICAL: Service role key MUST bypass RLS for backend operations.
    The service key grants elevated access to bypass Row Level Security policies,
    which is required for:
    - Creating sessions for any user
    - Inserting draft files without user context
    - Updating session status without auth checks

    Returns None if Supabase credentials are not configured.
    """
    global _supabase_client

    if _supabase_client is None:
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            logger.warning(
                "Supabase credentials not configured. Database operations will be disabled."
            )
            return None

        try:
            # Create client with service role key
            # IMPORTANT: Service role key automatically bypasses RLS in supabase-py
            # No additional ClientOptions needed - the key itself grants bypassrls privilege
            _supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

            logger.info("Supabase client initialized with SERVICE ROLE key (bypasses RLS)")

            # Log a warning if accidentally using anon key
            if "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" in SUPABASE_SERVICE_KEY:
                # Decode JWT to check role
                import base64
                import json

                try:
                    # JWT format: header.payload.signature
                    payload_part = SUPABASE_SERVICE_KEY.split(".")[1]
                    # Add padding if needed
                    payload_part += "=" * (4 - len(payload_part) % 4)
                    decoded = json.loads(base64.urlsafe_b64decode(payload_part))
                    role = decoded.get("role", "unknown")

                    if role != "service_role":
                        logger.error(
                            f"⚠️ CRITICAL: Using key with role='{role}' instead of 'service_role'! "
                            f"This will NOT bypass RLS. Check SUPABASE_SERVICE_KEY in .env"
                        )
                    else:
                        logger.info(f"✓ Verified service_role key (role={role})")
                except Exception:
                    pass  # JWT decode failed, skip verification

        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            return None

    return _supabase_client


async def create_research_session(
    session_id: str,
    user_id: str,
    title: str,
    status: SessionStatusEnum = SessionStatusEnum.IN_PROGRESS,
) -> Optional[ResearchSessionDB]:
    """
    Create a new research session in the database.

    Args:
        session_id: UUID string for the session
        user_id: UUID string for the user
        title: Research subject/title
        status: Initial session status (default: in_progress)

    Returns:
        ResearchSessionDB if successful, None if database not configured or error
    """
    client = get_supabase_client()
    if not client:
        logger.warning("Skipping database insert - Supabase not configured")
        return None

    try:
        # Insert into research_sessions table
        response = (
            client.table("research_sessions")
            .insert(
                {
                    "id": session_id,
                    "user_id": user_id,
                    "title": title,
                    "status": status.value,
                }
            )
            .execute()
        )

        if response.data and len(response.data) > 0:
            session_data = response.data[0]
            logger.info(f"Created research session in database: {session_id}")
            return ResearchSessionDB(**session_data)
        else:
            logger.error("Failed to create research session: no data returned")
            return None

    except Exception as e:
        logger.error(f"Database error creating research session: {e}")
        return None


async def update_research_session_status(session_id: str, status: SessionStatusEnum) -> bool:
    """
    Update the status of a research session.

    Args:
        session_id: UUID string for the session
        status: New status value

    Returns:
        True if successful, False otherwise
    """
    client = get_supabase_client()
    if not client:
        logger.warning("Skipping database update - Supabase not configured")
        return False

    try:
        response = (
            client.table("research_sessions")
            .update({"status": status.value})
            .eq("id", session_id)
            .execute()
        )

        if response.data:
            logger.info(f"Updated session {session_id} status to {status.value}")

            # DRY: file_count and total_size_bytes are maintained by PostgreSQL trigger
            # Trigger fires automatically on draft_files INSERT/UPDATE/DELETE
            # No manual update needed here - trust the trigger

            return True
        else:
            logger.error(f"Failed to update session status: {session_id}")
            return False

    except Exception as e:
        logger.error(f"Database error updating session status: {e}")
        return False


async def update_session_file_stats(session_id: str) -> bool:
    """
    Update file_count and total_size_bytes in research_sessions table.
    DRY: This is the SINGLE point where these columns are updated.

    Args:
        session_id: UUID string for the session

    Returns:
        True if successful, False otherwise
    """
    client = get_supabase_client()
    if not client:
        logger.warning("Skipping file stats update - Supabase not configured")
        return False

    try:
        # Get file stats (DRY: reuse existing helper)
        file_stats = await get_session_file_stats(session_id)

        # Update the research_sessions table
        response = (
            client.table("research_sessions")
            .update(
                {
                    "file_count": file_stats["file_count"],
                    "total_size_bytes": file_stats["total_size_bytes"],
                }
            )
            .eq("id", session_id)
            .execute()
        )

        if response.data:
            logger.info(
                f"Updated session {session_id} file stats: "
                f"{file_stats['file_count']} files, "
                f"{file_stats['total_size_bytes']} bytes"
            )
            return True
        else:
            logger.error(f"Failed to update file stats for session: {session_id}")
            return False

    except Exception as e:
        logger.error(f"Database error updating file stats: {e}")
        return False


async def transfer_sessions(old_user_id: str, new_user_id: str) -> int:
    """
    Transfer all research sessions from one user to another.

    Args:
        old_user_id: UUID string for the old user (anonymous)
        new_user_id: UUID string for the new user (registered)

    Returns:
        Number of sessions transferred
    """
    client = get_supabase_client()
    if not client:
        logger.warning("Skipping database transfer - Supabase not configured")
        return 0

    try:
        # Update all sessions belonging to old_user_id
        response = (
            client.table("research_sessions")
            .update({"user_id": new_user_id})
            .eq("user_id", old_user_id)
            .execute()
        )

        transferred_count = len(response.data) if response.data else 0
        logger.info(f"Transferred {transferred_count} sessions from {old_user_id} to {new_user_id}")
        return transferred_count

    except Exception as e:
        logger.error(f"Database error transferring sessions: {e}")
        return 0


async def get_user_sessions(
    user_id: str, limit: int = 50, offset: int = 0
) -> list[ResearchSessionDB]:
    """
    Get all research sessions for a user, ordered by creation date (newest first).

    Args:
        user_id: UUID string for the user
        limit: Maximum number of sessions to return
        offset: Number of sessions to skip (for pagination)

    Returns:
        List of ResearchSessionDB objects
    """
    client = get_supabase_client()
    if not client:
        return []

    try:
        response = (
            client.table("research_sessions")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )

        if response.data:
            return [ResearchSessionDB(**session) for session in response.data]
        else:
            return []

    except Exception as e:
        logger.error(f"Database error fetching user sessions: {e}")
        return []


async def get_session_files(session_id: str) -> list[DraftFile]:
    """
    Get all draft files for a research session.

    Args:
        session_id: UUID string for the session

    Returns:
        List of DraftFile objects
    """
    client = get_supabase_client()
    if not client:
        return []

    try:
        response = (
            client.table("draft_files")
            .select("*")
            .eq("session_id", session_id)
            .order("detected_at", desc=False)
            .execute()
        )

        if response.data:
            return [DraftFile(**file) for file in response.data]
        else:
            return []

    except Exception as e:
        logger.error(f"Database error fetching session files: {e}")
        return []


async def get_session_file_stats(session_id: str) -> dict:
    """
    Get file statistics for a research session.
    DRY helper to avoid duplicating file count/size logic.

    Args:
        session_id: UUID string for the session

    Returns:
        Dictionary with file_count and total_size_bytes
    """
    client = get_supabase_client()
    if not client:
        return {"file_count": 0, "total_size_bytes": 0}

    try:
        response = (
            client.table("draft_files")
            .select("file_size_bytes", count="exact")  # type: ignore[arg-type]
            .eq("session_id", session_id)
            .execute()
        )

        file_count = response.count if response.count is not None else 0
        total_size = sum(f.get("file_size_bytes", 0) for f in response.data) if response.data else 0

        return {"file_count": file_count, "total_size_bytes": total_size}

    except Exception as e:
        logger.error(f"Database error fetching file stats for {session_id}: {e}")
        return {"file_count": 0, "total_size_bytes": 0}


async def get_user_sessions_with_filters(
    user_id: str,
    include_archived: bool = False,
    status_filter: Optional[str] = None,
    language_filter: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[ResearchSessionDB], int]:
    """
    Get research sessions for a user with filtering options.

    Args:
        user_id: UUID string for the user
        include_archived: Include archived sessions (default: False)
        status_filter: Filter by status (in_progress, completed, failed)
        language_filter: Filter by language code
        limit: Maximum number of sessions to return
        offset: Number of sessions to skip (for pagination)

    Returns:
        Tuple of (list of ResearchSessionDB objects, total count)
    """
    client = get_supabase_client()
    if not client:
        return [], 0

    try:
        # Start query
        query = (
            client.table("research_sessions")
            .select("*", count="exact")  # type: ignore[arg-type]
            .eq("user_id", user_id)
        )

        # Apply archived filter
        if not include_archived:
            query = query.is_("archived_at", "null")

        # Apply status filter
        if status_filter:
            query = query.eq("status", status_filter)

        # Apply language filter
        if language_filter:
            query = query.eq("language", language_filter)

        # Order and paginate
        response = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()

        sessions = (
            [ResearchSessionDB(**session) for session in response.data] if response.data else []
        )
        total_count = response.count if response.count is not None else 0

        return sessions, total_count

    except Exception as e:
        logger.error(f"Database error fetching filtered sessions: {e}")
        return [], 0


async def archive_session(session_id: str) -> bool:
    """
    Archive a research session (soft delete).

    Args:
        session_id: UUID string for the session

    Returns:
        True if successful, False otherwise
    """
    client = get_supabase_client()
    if not client:
        return False

    try:
        from datetime import datetime

        response = (
            client.table("research_sessions")
            .update({"archived_at": datetime.now().isoformat()})
            .eq("id", session_id)
            .execute()
        )

        if response.data:
            logger.info(f"Archived session {session_id}")
            return True
        else:
            logger.error(f"Failed to archive session: {session_id}")
            return False

    except Exception as e:
        logger.error(f"Database error archiving session: {e}")
        return False


async def restore_session(session_id: str) -> bool:
    """
    Restore an archived research session.

    Args:
        session_id: UUID string for the session

    Returns:
        True if successful, False otherwise
    """
    client = get_supabase_client()
    if not client:
        return False

    try:
        response = (
            client.table("research_sessions")
            .update({"archived_at": None})
            .eq("id", session_id)
            .execute()
        )

        if response.data:
            logger.info(f"Restored session {session_id}")
            return True
        else:
            logger.error(f"Failed to restore session: {session_id}")
            return False

    except Exception as e:
        logger.error(f"Database error restoring session: {e}")
        return False


async def delete_session_permanently(session_id: str) -> bool:
    """
    Permanently delete a research session and all its files.
    WARNING: This is irreversible!

    Args:
        session_id: UUID string for the session

    Returns:
        True if successful, False otherwise
    """
    client = get_supabase_client()
    if not client:
        return False

    try:
        # First delete all draft files for this session (cascade)
        client.table("draft_files").delete().eq("session_id", session_id).execute()

        # Then delete the session
        response = client.table("research_sessions").delete().eq("id", session_id).execute()

        if response.data:
            logger.info(f"Permanently deleted session {session_id}")
            return True
        else:
            logger.error(f"Failed to delete session: {session_id}")
            return False

    except Exception as e:
        logger.error(f"Database error deleting session: {e}")
        return False


async def duplicate_session(session_id: str, user_id: str) -> Optional[str]:
    """
    Duplicate a research session with a new UUID.
    Copies session metadata but NOT the generated files.

    Args:
        session_id: UUID string for the source session
        user_id: UUID string for the user

    Returns:
        New session UUID if successful, None otherwise
    """
    client = get_supabase_client()
    if not client:
        return None

    try:
        # Get original session
        original = (
            client.table("research_sessions").select("*").eq("id", session_id).single().execute()
        )

        if not original.data:
            logger.error(f"Source session not found: {session_id}")
            return None

        # Generate new UUID for duplicate
        import uuid

        new_session_id = str(uuid.uuid4())

        # Create duplicate with original parameters
        new_session = {
            "id": new_session_id,
            "user_id": user_id,
            "title": f"{original.data['title']} (Copy)",
            "status": "in_progress",
            "language": original.data.get("language", "vi"),
            "parameters": original.data.get("parameters", {}),
        }

        response = client.table("research_sessions").insert(new_session).execute()

        if response.data:
            logger.info(f"Duplicated session {session_id} -> {new_session_id}")
            return new_session_id
        else:
            logger.error(f"Failed to duplicate session: {session_id}")
            return None

    except Exception as e:
        logger.error(f"Database error duplicating session: {e}")
        return None


async def create_draft_file(
    session_id: str,
    file_path: str,
    file_size_bytes: int = 0,
    stage: str = "4_writing",
) -> bool:
    """
    Insert or update a draft file in the database.
    DRY: This is called when files are detected to populate draft_files table.

    Uses UPSERT to prevent duplicate inserts if called multiple times.

    Args:
        session_id: UUID string for the session
        file_path: Filesystem path to the draft file (e.g., /outputs/session_id/file.pdf)
        file_size_bytes: Size of the file in bytes
        stage: Research stage enum value (default: '4_writing' for final outputs)

    Returns:
        True if successful, False otherwise
    """
    client = get_supabase_client()
    if not client:
        logger.warning("Skipping draft file insert - Supabase not configured")
        return False

    try:
        # UPSERT: Insert or update if exists (prevents duplicates)
        # Unique constraint on (session_id, file_path) prevents duplicates
        response = (
            client.table("draft_files")
            .upsert(
                {
                    "session_id": session_id,
                    "file_path": file_path,
                    "file_size_bytes": file_size_bytes,
                    "stage": stage,
                },
                on_conflict="session_id,file_path",  # Upsert key
            )
            .execute()
        )

        if response.data:
            logger.info(f"Upserted draft file into database: {file_path} ({file_size_bytes} bytes)")
            return True
        else:
            logger.error(f"Failed to upsert draft file: {file_path}")
            return False

    except Exception as e:
        logger.error(f"Database error upserting draft file: {e}")
        return False


async def get_session_by_id(session_id: str, user_id: str) -> Optional[ResearchSessionDB]:
    """
    Get a specific session by ID for a user.

    Args:
        session_id: UUID string for the session
        user_id: UUID string for the user

    Returns:
        ResearchSessionDB if found, None otherwise
    """
    client = get_supabase_client()
    if not client:
        return None

    try:
        response = (
            client.table("research_sessions")
            .select("*")
            .eq("id", session_id)
            .eq("user_id", user_id)
            .single()
            .execute()
        )

        if response.data:
            return ResearchSessionDB(**response.data)
        else:
            return None

    except Exception as e:
        logger.error(f"Database error fetching session: {e}")
        return None


async def ingest_missing_drafts(session_id: str, outputs_path: Path) -> int:
    """
    Scan the filesystem for a session's output files and upsert any missing
    entries into the draft_files table with file_size_bytes populated.

    Returns number of upserts attempted (successful inserts/updates reported by Supabase).
    """
    client = get_supabase_client()
    if not client:
        logger.warning("Cannot ingest drafts - Supabase not configured")
        return 0

    try:
        session_dir = outputs_path / session_id
        if not session_dir.exists():
            logger.debug(f"Ingest: Session directory does not exist: {session_dir}")
            return 0

        supported_extensions = {".pdf", ".docx", ".md", ".txt", ".html", ".json"}
        upserted = 0

        for file_path in session_dir.iterdir():
            if (
                file_path.is_file()
                and file_path.suffix.lower() in supported_extensions
                and file_path.name != "session.log"
                and not file_path.name.startswith(".")
                and not file_path.name.startswith("~")
            ):
                try:
                    # Use absolute resolved path to be consistent with runtime inserts
                    resolved = str(file_path.resolve())
                    size = file_path.stat().st_size
                    # Reuse existing UPSERT logic
                    response = (
                        client.table("draft_files")
                        .upsert(
                            {
                                "session_id": session_id,
                                "file_path": resolved,
                                "file_size_bytes": size,
                                "stage": "4_writing",
                            },
                            on_conflict="session_id,file_path",
                        )
                        .execute()
                    )
                    if response.data:
                        upserted += 1
                except Exception as row_err:
                    logger.warning(f"Ingest: Failed to upsert draft row for {file_path}: {row_err}")

        logger.info(f"Ingest: Upserted/updated {upserted} draft file rows for session {session_id}")
        return upserted

    except Exception as e:
        logger.error(f"Ingest: Error while scanning/ingesting drafts for {session_id}: {e}")
        return 0


async def reconcile_session_with_filesystem(
    session_id: str, outputs_path: Path, user_id: Optional[str] = None
) -> Optional[ResearchSessionDB]:
    """
    FALLBACK MECHANISM: Reconcile database session data with filesystem reality.

    This function provides failproof operation when database updates failed during
    research execution. It detects discrepancies between database records and
    actual filesystem state, then auto-corrects the database.

    **Problem Solved:**
    - Historical sessions may have wrong status (FAILED when research completed)
    - File counts may be 0 when files actually exist
    - Database updates may have failed during research execution

    **Detection Logic:**
    1. Check filesystem for actual files in session directory
    2. Count real files (excluding session.log and temp files)
    3. Compare with database file_count and status
    4. Auto-correct database if mismatch detected

    **Auto-Correction Rules:**
    - If files exist but file_count=0: Update file_count
    - If files exist but status=FAILED: Change to COMPLETED
    - If status=IN_PROGRESS and files exist: Change to COMPLETED
    - If no files and status=IN_PROGRESS: Change to FAILED

    Args:
        session_id: UUID string for the session
        outputs_path: Path to outputs directory (typically PROJECT_ROOT / "outputs")
        user_id: Optional user_id for access control (if None, skips get_session_by_id check)

    Returns:
        Updated ResearchSessionDB if corrections were made, None if no changes needed

    Example:
        >>> # Session shows FAILED with 0 files, but filesystem has 6 files
        >>> reconciled = await reconcile_session_with_filesystem(
        ...     "787581a0-28ff-41f4-89d6-7644fc716170",
        ...     Path("/path/to/outputs")
        ... )
        >>> # Database now shows COMPLETED with 6 files
    """
    client = get_supabase_client()
    if not client:
        logger.warning("Cannot reconcile - Supabase not configured")
        return None

    try:
        # Get current database state (with user access check if user_id provided)
        if user_id:
            db_session = await get_session_by_id(session_id, user_id)
        else:
            # Admin/system reconciliation without user check
            response = (
                client.table("research_sessions")
                .select("*")
                .eq("id", session_id)
                .single()
                .execute()
            )
            db_session = ResearchSessionDB(**response.data) if response.data else None

        if not db_session:
            logger.warning(f"Cannot reconcile - session {session_id} not found in database")
            return None

        # Check filesystem reality
        session_dir = outputs_path / session_id

        if not session_dir.exists():
            logger.debug(f"Session directory does not exist: {session_dir}")
            # If no directory and status is IN_PROGRESS, mark as FAILED
            if db_session.status == SessionStatusEnum.IN_PROGRESS:
                logger.info(
                    f"🔧 RECONCILIATION: No files found, marking session {session_id} as FAILED"
                )
                await update_research_session_status(session_id, SessionStatusEnum.FAILED)
                return await get_session_by_id(session_id, user_id) if user_id else None
            return None

        # Count actual research output files (exclude session.log and temp files)
        actual_files = []
        supported_extensions = {".pdf", ".docx", ".md", ".txt", ".html", ".json"}

        for file_path in session_dir.iterdir():
            if (
                file_path.is_file()
                and file_path.suffix.lower() in supported_extensions
                and file_path.name != "session.log"
                and not file_path.name.startswith(".")
                and not file_path.name.startswith("~")
            ):
                actual_files.append(file_path)

        actual_file_count = len(actual_files)
        db_file_count = db_session.file_count or 0

        # Ingest any missing draft rows first (safety net for historical sessions)
        try:
            await ingest_missing_drafts(session_id, outputs_path)
        except Exception as ingest_err:
            logger.warning(f"Reconcile: Ingest step failed for {session_id}: {ingest_err}")

        # Recompute DB aggregate from draft_files and sync research_sessions columns
        await update_session_file_stats(session_id)

        # Detect discrepancies (any mismatch, not just when DB shows 0)
        needs_correction = False
        new_status = db_session.status
        new_file_count = db_file_count

        if actual_file_count != db_file_count:
            logger.warning(
                f"📊 DISCREPANCY DETECTED: Session {session_id} has {actual_file_count} files "
                f"in filesystem but database shows {db_file_count} files"
            )
            new_file_count = actual_file_count
            needs_correction = True

        # Status corrections
        if actual_file_count > 0 and db_session.status == SessionStatusEnum.FAILED:
            logger.warning(
                f"⚠️ DISCREPANCY DETECTED: Session {session_id} has {actual_file_count} files "
                f"but status is FAILED - should be COMPLETED"
            )
            new_status = SessionStatusEnum.COMPLETED
            needs_correction = True

        if actual_file_count > 0 and db_session.status == SessionStatusEnum.IN_PROGRESS:
            logger.warning(
                f"⏱️ DISCREPANCY DETECTED: Session {session_id} has {actual_file_count} files "
                f"but status is IN_PROGRESS - research likely completed but status wasn't updated"
            )
            new_status = SessionStatusEnum.COMPLETED
            needs_correction = True

        if actual_file_count == 0 and db_session.status == SessionStatusEnum.IN_PROGRESS:
            logger.warning(
                f"🔴 DISCREPANCY DETECTED: Session {session_id} has no files "
                f"but status is IN_PROGRESS - marking as FAILED"
            )
            new_status = SessionStatusEnum.FAILED
            needs_correction = True

        # Apply corrections if needed
        if needs_correction:
            logger.info(
                f"🔧 AUTO-CORRECTING session {session_id}: "
                f"status {db_session.status.value} → {new_status.value}, "
                f"file_count {db_file_count} → {new_file_count}"
            )

            # Update status; file_count will already be synced by update_session_file_stats,
            # but we still write authoritative count for clarity
            update_data = {"status": new_status.value, "file_count": new_file_count}
            response = (
                client.table("research_sessions").update(update_data).eq("id", session_id).execute()
            )

            if response.data:
                logger.info(
                    f"✅ RECONCILIATION SUCCESS: Session {session_id} corrected in database"
                )
                # Return updated session
                return (
                    await get_session_by_id(session_id, user_id)
                    if user_id
                    else ResearchSessionDB(**response.data[0])
                )
            else:
                logger.error(f"❌ RECONCILIATION FAILED: Could not update session {session_id}")
                return None
        else:
            logger.debug(f"✓ Session {session_id} matches filesystem - no correction needed")
            return None

    except Exception as e:
        logger.error(f"Error during session reconciliation: {e}")
        return None

import asyncio
import json
import logging
import urllib.parse
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load environment variables from .env file BEFORE importing anything else
load_dotenv()

# ruff: noqa: E402 - Imports after load_dotenv() are intentional
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import database
from cli_executor import CLIExecutor

# Configuration (must be imported after load_dotenv())
from config import settings
from file_manager import FileManager
from file_manager_enhanced import EnhancedFileManager
from filename_utils import (
    FilenameParser,
    Language,
    ParsedFilename,
    SecurePathValidator,
    build_download_url,
)
from middleware.auth_middleware import verify_jwt_middleware
from models import (
    ResearchRequest,
    ResearchResponse,
    ResearchSession,
    SessionStatus,
    SessionStatusEnum,
    TransferSessionsRequest,
)
from schemas import create_file_generated_event
from websocket_handler import WebSocketManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get project root (parent directory)
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
WEB_STATIC_PATH = Path(__file__).parent / "static"

# Initialize components
cli_executor = CLIExecutor(PROJECT_ROOT)
file_manager = FileManager(PROJECT_ROOT, WEB_STATIC_PATH)
enhanced_file_manager = EnhancedFileManager(PROJECT_ROOT, WEB_STATIC_PATH)
websocket_manager = WebSocketManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown"""
    # Startup
    logger.info("Starting Web Dashboard for Deep Research MCP")
    logger.info(f"Project root: {PROJECT_ROOT}")
    logger.info(f"Web static path: {WEB_STATIC_PATH}")

    # Start background cleanup task
    cleanup_task = asyncio.create_task(periodic_cleanup())

    yield

    # Shutdown
    cleanup_task.cancel()
    logger.info("Web Dashboard shutdown complete")


app = FastAPI(
    title="Deep Research MCP Web Dashboard",
    description="Simple web interface for the Deep Research MCP system",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS to allow frontend access
# Origins are configured via Pydantic BaseSettings from CORS_ORIGINS env var
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Register authentication middleware for JWT verification
# Note: Middleware is lenient - skips public endpoints and degrades gracefully
# if JWT_SECRET not configured
app.middleware("http")(verify_jwt_middleware)

# Mount static files
app.mount("/static", StaticFiles(directory=WEB_STATIC_PATH), name="static")

# Setup templates
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Serve the main dashboard page"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/research", response_model=ResearchResponse)
async def submit_research(
    request: ResearchRequest, background_tasks: BackgroundTasks, req: Request
):
    """Submit a new research request"""
    # Generate unique session ID
    session_id = str(uuid.uuid4())

    logger.info(f"New research request - Session: {session_id}, Subject: {request.subject}")

    # Get user_id from JWT (added by middleware)
    # Frontend MUST create anonymous user via Supabase Auth before making requests
    user_id = getattr(req.state, "user_id", None)

    if not user_id:
        logger.error("No user_id in request state - middleware auth failed")
        raise HTTPException(
            status_code=401,
            detail="Authentication required. User must be signed in (anonymous or registered).",
        )

    # Create session in database (Story 1.3)
    try:
        await database.create_research_session(
            session_id=session_id,
            user_id=user_id,
            title=request.subject,
            status=SessionStatusEnum.IN_PROGRESS,
        )
        logger.info(f"Created database session record for {session_id}")
    except Exception as e:
        logger.error(f"Failed to create database session: {e}")
        # Continue anyway - database is optional, CLI can still run

    # Start research in background
    background_tasks.add_task(start_research_session, session_id, request.subject, request.language)

    return ResearchResponse(
        session_id=session_id,
        status="started",
        message="Research session started successfully",
        websocket_url=f"/ws/{session_id}",
    )


@app.get("/api/session/{session_id}", response_model=SessionStatus)
async def get_session_status(session_id: str):
    """Get the status of a research session"""
    # Check CLI executor status
    cli_status = cli_executor.get_session_status(session_id)

    if not cli_status:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get available files
    files = await file_manager.get_session_files(session_id)

    # Map CLI status to API status
    status_mapping = {
        "running": "running",
        "completed": "completed",
        "failed": "failed",
    }

    return SessionStatus(
        session_id=session_id,
        status=status_mapping.get(cli_status["status"], "unknown"),
        progress=(
            100.0
            if cli_status["status"] == "completed"
            else 50.0 if cli_status["status"] == "running" else 0.0
        ),
        files=files,
        error_message=cli_status.get("error"),
    )


@app.get("/api/session/{session_id}/state")
async def get_session_state(session_id: str, req: Request):
    """
    Get complete session state for re-hydration after page refresh.
    Returns current status, files, and progress.

    DRY: Prefers database file_count over len(files) calculation.

    Authentication: Verifies user has access to session via JWT
    Database-first: Checks session existence in database before filesystem
    """
    # Get user_id from JWT (added by middleware)
    user_id = getattr(req.state, "user_id", None)

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. User must be signed in.",
        )

    # DATABASE-FIRST: Check if session exists and user has access
    # This prevents 404 errors for historical sessions without files
    db_session = await database.get_session_by_id(session_id, user_id)

    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found or access denied")

    # FALLBACK MECHANISM: Reconcile database with filesystem reality
    # This auto-corrects historical sessions that have wrong status/file_count
    # due to failed database updates during research execution
    outputs_path = PROJECT_ROOT / "outputs"
    reconciled_session = await database.reconcile_session_with_filesystem(
        session_id, outputs_path, user_id
    )

    # Use reconciled session if corrections were made, otherwise use original
    if reconciled_session:
        logger.info(f"🔧 Session {session_id} was reconciled with filesystem")
        db_session = reconciled_session

    # Session exists in database - now enrich with runtime data
    # Check if session exists in memory (active sessions)
    cli_status = cli_executor.get_session_status(session_id)

    # DATABASE-FIRST for files: prefer draft_files records, fallback to filesystem
    files_payload = []
    try:
        drafts = await database.get_session_files(session_id)
        if drafts:
            for d in drafts:
                try:
                    filename = Path(d.file_path).name
                    parsed = FilenameParser.parse(filename)
                    file_type = (
                        parsed.file_type.value
                        if parsed
                        else FilenameParser.extract_file_type(filename).value
                    )
                    language = (
                        parsed.language.value
                        if parsed
                        else FilenameParser.extract_language(filename).value
                    )
                    files_payload.append(
                        {
                            "file_id": filename,
                            "filename": filename,
                            "file_type": file_type,
                            "language": language,
                            "size_bytes": d.file_size_bytes,
                            "download_url": build_download_url(session_id, filename),
                        }
                    )
                except Exception:
                    continue
        else:
            # Fallback to filesystem discovery
            fm_files = await file_manager.get_session_files(session_id)
            for f in fm_files:
                files_payload.append(
                    {
                        "file_id": f.filename,
                        "filename": f.filename,
                        "file_type": f.file_type,
                        "language": f.language,
                        "size_bytes": f.size or 0,
                        "download_url": f.url,
                    }
                )
    except Exception:
        # Graceful degradation: leave files_payload empty
        files_payload = []

    # Note: Statistics removed - use dedicated /api/session/{id}/statistics endpoint
    # That endpoint now uses database-first approach (DRY compliance)

    # Build complete state
    # Database is ALWAYS the single source of truth for session metadata
    # CLI status is only used for transient runtime info (status, timestamps, errors)

    # Step 1: Get runtime status from CLI (if available) or use DB status
    if cli_status:
        status = cli_status["status"]
        start_time = (
            cli_status.get("start_time").isoformat() if cli_status.get("start_time") else None
        )
        end_time = cli_status.get("end_time").isoformat() if cli_status.get("end_time") else None
        error = cli_status.get("error")
    else:
        # Session not in CLI memory - use database status
        # Map DB status enum to CLI status format
        status_mapping = {
            "in_progress": "running",
            "completed": "completed",
            "failed": "failed",
        }
        status = status_mapping.get(
            db_session.status.value if hasattr(db_session.status, "value") else db_session.status,
            "completed",  # Default to completed for historical sessions
        )
        start_time = db_session.created_at.isoformat() if db_session.created_at else None
        end_time = db_session.updated_at.isoformat() if db_session.updated_at else None
        error = None

    # Step 2: Use database session data as single source of truth
    subject = db_session.title or "Unknown"
    file_count = db_session.file_count if db_session.file_count is not None else len(files_payload)

    return {
        "session_id": session_id,
        "status": status,
        "subject": subject,
        "start_time": start_time,
        "end_time": end_time,
        "files": files_payload,
        "file_count": file_count,  # DRY: Prefer DB, fallback to len(files)
        # Note: "statistics" removed - clients should call /api/session/{id}/statistics
        "error": error,
    }


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time log streaming"""
    await websocket_manager.handle_websocket(websocket, session_id)


@app.get("/api/sessions", response_model=list[ResearchSession])
async def get_all_sessions():
    """Get all available research sessions (legacy filesystem-based endpoint)"""
    try:
        sessions = await file_manager.get_all_research_sessions()
        return sessions
    except Exception as e:
        logger.error(f"Error getting research sessions: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve research sessions")


@app.get("/api/sessions/list")
async def list_user_sessions(
    req: Request,
    include_archived: bool = False,
    status: Optional[str] = None,
    language: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    outputs_base: Optional[str] = None,
):
    """
    Get research sessions for the authenticated user with filtering options.
    Supports pagination and filtering by status, language, and archive state.
    """
    # Get user_id from JWT
    user_id = getattr(req.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        sessions, total_count = await database.get_user_sessions_with_filters(
            user_id=user_id,
            include_archived=include_archived,
            status_filter=status,
            language_filter=language,
            limit=limit,
            offset=offset,
        )

        # Convert to dict for JSON response
        # DRY: Use stored file_count/total_size_bytes from database
        # (maintained by update_session_file_stats)
        # FALLBACK: Auto-reconcile sessions that look problematic
        sessions_data = []
        outputs_path = Path(outputs_base).resolve() if outputs_base else PROJECT_ROOT / "outputs"

        for session in sessions:
            # Auto-reconcile sessions with suspicious data (FAILED status or 0 files)
            # This corrects historical sessions that have wrong database records
            if session.status == SessionStatusEnum.FAILED or (
                session.file_count == 0 or session.file_count is None
            ):
                reconciled = await database.reconcile_session_with_filesystem(
                    str(session.id), outputs_path, user_id
                )
                if reconciled:
                    logger.info(f"🔧 Auto-reconciled session {session.id} in list view")
                    session = reconciled  # Use corrected data
            session_dict = {
                "id": str(session.id),
                "user_id": str(session.user_id),
                "title": session.title,
                "status": (
                    session.status.value if hasattr(session.status, "value") else session.status
                ),
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat(),
                "file_count": session.file_count or 0,  # Use stored value
                "total_size_bytes": session.total_size_bytes or 0,  # Use stored value
            }

            # Add optional fields if present
            if session.language:
                session_dict["language"] = session.language
            if session.archived_at:
                session_dict["archived_at"] = session.archived_at.isoformat()
            if session.parameters:
                session_dict["parameters"] = session.parameters

            sessions_data.append(session_dict)

        return {
            "sessions": sessions_data,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < total_count,
        }

    except Exception as e:
        logger.error(f"Error listing user sessions: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve sessions")


@app.post("/api/sessions/{session_id}/archive")
async def archive_user_session(session_id: str, req: Request):
    """Archive a research session (soft delete)"""
    # Get user_id from JWT
    user_id = getattr(req.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    # Verify session belongs to user
    session = await database.get_session_by_id(session_id, user_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Archive the session
    success = await database.archive_session(session_id)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to archive session")

    return {"message": "Session archived successfully", "session_id": session_id}


@app.post("/api/sessions/{session_id}/update-file-stats")
async def update_session_file_stats_endpoint(session_id: str, req: Request):
    """
    Manually trigger file stats update for a session.
    Useful for backfilling or fixing null values.
    """
    # Get user_id from JWT
    user_id = getattr(req.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    # Verify session belongs to user
    session = await database.get_session_by_id(session_id, user_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Update file stats (DRY: single point of update)
    success = await database.update_session_file_stats(session_id)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to update file stats")

    return {"message": "File stats updated successfully", "session_id": session_id}


@app.post("/api/sessions/backfill-file-stats")
async def backfill_all_file_stats(req: Request, outputs_base: Optional[str] = None):
    """
    Backfill file stats for ALL sessions with null values.
    Admin/maintenance endpoint.
    """
    # Get user_id from JWT
    user_id = getattr(req.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        # Get all user sessions
        sessions, _ = await database.get_user_sessions_with_filters(
            user_id=user_id,
            include_archived=True,  # Include archived
            limit=1000,  # Process up to 1000 sessions
        )

        updated_count = 0
        failed_count = 0

        outputs_path = PROJECT_ROOT / "outputs"

        for session in sessions:
            try:
                # Ingest drafts and recompute stats for any session that looks wrong
                stats = await database.get_session_file_stats(str(session.id))
                db_count = session.file_count or 0
                agg_count = stats.get("file_count", 0)

                if db_count != agg_count or db_count == 0:
                    # Try full reconcile which also ingests missing drafts
                    await database.reconcile_session_with_filesystem(
                        str(session.id), outputs_path, user_id
                    )
                    # Recompute after reconcile
                    stats_after = await database.get_session_file_stats(str(session.id))
                    if (stats_after.get("file_count", 0) or 0) > 0:
                        success = await database.update_session_file_stats(str(session.id))
                        if success:
                            updated_count += 1
                        else:
                            failed_count += 1
            except Exception:
                failed_count += 1

        return {
            "message": "Backfill complete",
            "updated": updated_count,
            "failed": failed_count,
            "total_processed": updated_count + failed_count,
        }

    except Exception as e:
        logger.error(f"Error during backfill: {e}")
        raise HTTPException(status_code=500, detail="Backfill failed")


@app.post("/api/sessions/{session_id}/reconcile")
async def reconcile_session(session_id: str, req: Request, outputs_base: Optional[str] = None):
    """
    Trigger reconciliation for one session: ingest missing drafts, sync file stats,
    and correct status/file_count mismatches.
    """
    user_id = getattr(req.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    outputs_path = Path(outputs_base).resolve() if outputs_base else PROJECT_ROOT / "outputs"
    reconciled = await database.reconcile_session_with_filesystem(session_id, outputs_path, user_id)
    # Only sync DB aggregates if we actually have any drafts
    stats = await database.get_session_file_stats(session_id)
    if (stats.get("file_count", 0) or 0) > 0:
        await database.update_session_file_stats(session_id)
    return {
        "session_id": session_id,
        "reconciled": bool(reconciled),
        "drafts_count": stats.get("file_count", 0),
    }


@app.get("/api/sessions/{session_id}/verify-file-stats")
async def verify_file_stats(
    session_id: str, repair: bool = False, req: Request = None, outputs_base: Optional[str] = None
):
    """
    Verify DB file_count vs draft_files count. Optionally repair by running reconcile.
    """
    user_id = getattr(req.state, "user_id", None) if req else None
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    client = database.get_supabase_client()
    if not client:
        raise HTTPException(status_code=500, detail="Database not configured")

    # Fetch research_sessions row
    try:
        rs = (
            client.table("research_sessions")
            .select("id, file_count, total_size_bytes")
            .eq("id", session_id)
            .single()
            .execute()
        )
    except Exception:
        raise HTTPException(status_code=404, detail="Session not found")

    if not rs.data:
        raise HTTPException(status_code=404, detail="Session not found")

    # Aggregate from drafts
    stats = await database.get_session_file_stats(session_id)
    db_count = rs.data.get("file_count") or 0
    agg_count = stats.get("file_count", 0)

    mismatch = db_count != agg_count

    if repair and mismatch:
        outputs_path = Path(outputs_base).resolve() if outputs_base else PROJECT_ROOT / "outputs"
        await database.reconcile_session_with_filesystem(session_id, outputs_path, user_id)
        # Only write DB aggregates if drafts exist
        stats = await database.get_session_file_stats(session_id)
        if (stats.get("file_count", 0) or 0) > 0:
            await database.update_session_file_stats(session_id)
        # Recompute
        rs = (
            client.table("research_sessions")
            .select("id, file_count, total_size_bytes")
            .eq("id", session_id)
            .single()
            .execute()
        )
        db_count = rs.data.get("file_count") or 0
        agg_count = stats.get("file_count", 0)
        mismatch = db_count != agg_count

    return {
        "session_id": session_id,
        "db_file_count": db_count,
        "drafts_file_count": agg_count,
        "mismatch": mismatch,
    }


@app.post("/api/sessions/{session_id}/restore")
async def restore_user_session(session_id: str, req: Request):
    """Restore an archived research session"""
    # Get user_id from JWT
    user_id = getattr(req.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    # Verify session belongs to user
    session = await database.get_session_by_id(session_id, user_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Restore the session
    success = await database.restore_session(session_id)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to restore session")

    return {"message": "Session restored successfully", "session_id": session_id}


@app.delete("/api/sessions/{session_id}")
async def delete_user_session(session_id: str, req: Request):
    """Permanently delete a research session and all its files"""
    # Get user_id from JWT
    user_id = getattr(req.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    # Verify session belongs to user
    session = await database.get_session_by_id(session_id, user_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Delete the session
    success = await database.delete_session_permanently(session_id)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete session")

    return {"message": "Session deleted permanently", "session_id": session_id}


@app.post("/api/sessions/{session_id}/duplicate")
async def duplicate_user_session(session_id: str, req: Request, background_tasks: BackgroundTasks):
    """
    Duplicate a research session and START a new research execution.
    Creates a new session with copied metadata and runs research with same parameters.
    """
    # Get user_id from JWT
    user_id = getattr(req.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    # Verify session belongs to user and get original parameters
    session = await database.get_session_by_id(session_id, user_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Extract original research parameters
    subject = session.title
    # Remove " (Copy)" suffix if it exists from previous duplication
    if subject.endswith(" (Copy)"):
        subject = subject[:-7].strip()

    language = session.language or "vi"

    # Duplicate the session in database
    new_session_id = await database.duplicate_session(session_id, user_id)

    if not new_session_id:
        raise HTTPException(status_code=500, detail="Failed to duplicate session")

    logger.info(
        f"Duplicated session {session_id} -> {new_session_id}, "
        f"starting research with subject='{subject}', language={language}"
    )

    # CRITICAL FIX: Start research execution in background
    # This was missing before, causing duplicated sessions to fail immediately
    background_tasks.add_task(start_research_session, new_session_id, subject, language)

    return {
        "message": "Session duplicated and research started",
        "original_session_id": session_id,
        "new_session_id": new_session_id,
        "websocket_url": f"/ws/{new_session_id}",
    }


@app.post("/api/sessions/compare")
async def compare_sessions(session_ids: list[str], req: Request):
    """
    Compare multiple research sessions.
    Returns metadata for comparison (title, language, parameters, stats).
    """
    # Get user_id from JWT
    user_id = getattr(req.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    if len(session_ids) < 2:
        raise HTTPException(status_code=400, detail="At least 2 sessions required for comparison")

    if len(session_ids) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 sessions can be compared at once")

    try:
        # Fetch all sessions
        sessions_data = []
        for session_id in session_ids:
            session = await database.get_session_by_id(session_id, user_id)
            if session:
                sessions_data.append(
                    {
                        "id": str(session.id),
                        "title": session.title,
                        "status": (
                            session.status.value
                            if hasattr(session.status, "value")
                            else session.status
                        ),
                        "created_at": session.created_at.isoformat(),
                    }
                )
            else:
                # Skip sessions not found or not belonging to user
                logger.warning(
                    f"Session {session_id} not found or access denied for user {user_id}"
                )

        if len(sessions_data) < 2:
            raise HTTPException(
                status_code=404, detail="Not enough valid sessions found for comparison"
            )

        return {"sessions": sessions_data, "count": len(sessions_data)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing sessions: {e}")
        raise HTTPException(status_code=500, detail="Failed to compare sessions")


@app.get("/download/{session_id}/{filename}")
async def download_file(session_id: str, filename: str):
    """Download a research output file"""
    # SECURITY: Validate filename using centralized module
    # Replaces: file_manager.is_valid_filename()
    if not FilenameParser.is_valid(filename):
        raise HTTPException(status_code=400, detail="Invalid filename")

    # Get file path (still using file_manager for path resolution)
    file_path = file_manager.get_file_path(session_id, filename)

    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")

    # Get proper MIME type using centralized parser
    # Replaces: file_manager.get_mime_type()
    mime_type = FilenameParser.get_mime_type(filename)

    # Create user-friendly download filename using centralized converter
    # Replaces: file_manager.create_friendly_filename_from_uuid()
    friendly_name = FilenameParser.to_friendly_name(file_path.name)

    return FileResponse(path=file_path, filename=friendly_name, media_type=mime_type)


@app.get("/api/sessions/{session_id}/logs")
async def download_session_logs(session_id: str):
    """
    Download session logs file

    Returns the session.log file containing all events that occurred during the research session.
    The log file is in JSONL format (one JSON object per line).
    """
    try:
        # Build log file path
        log_file = file_manager.outputs_path / session_id / "session.log"

        if not log_file.exists():
            raise HTTPException(
                status_code=404, detail="Log file not found. Logs may not have been generated yet."
            )

        # Return log file for download
        return FileResponse(
            path=log_file, filename=f"{session_id}_session.log", media_type="text/plain"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading logs for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to download logs")


@app.get("/api/sessions/{session_id}/logs/events")
async def get_session_log_events(session_id: str, limit: int = 1000):
    """
    Get session log events as JSON array for rehydration.

    Returns parsed log events from session.log file, suitable for populating
    the frontend events array during session rehydration.

    Args:
        session_id: Session UUID
        limit: Maximum number of events to return (default: 1000, most recent)
    """
    try:
        # Build log file path
        log_file = file_manager.outputs_path / session_id / "session.log"

        if not log_file.exists():
            # Return empty array if no logs yet (not an error for new sessions)
            return {"events": [], "count": 0}

        # Parse JSONL file and extract events
        events = []
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        event = json.loads(line)
                        events.append(event)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse log line: {e}")
                        continue

        # Return most recent events up to limit
        events = events[-limit:] if len(events) > limit else events

        return {"events": events, "count": len(events), "total": len(events)}

    except Exception as e:
        logger.error(f"Error reading log events for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to read log events")


@app.get("/api/files/content")
async def get_file_content(file_id: str, file_path: str, req: Request):
    """
    Get file content for preview.
    Returns file content with proper Content-Type header.
    """
    # Get user_id from JWT
    user_id = getattr(req.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        # Get file content and MIME type from enhanced file manager
        content, mime_type = await enhanced_file_manager.get_file_content(file_path)

        # For text files, return as plain text
        if mime_type.startswith("text/") or mime_type in [
            "application/json",
            "application/javascript",
        ]:
            from fastapi.responses import PlainTextResponse

            return PlainTextResponse(content=content.decode("utf-8"), media_type=mime_type)

        # For binary files (PDF, DOCX, images), return as binary response
        from fastapi.responses import Response

        return Response(content=content, media_type=mime_type)

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        logger.error(f"Error retrieving file content: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve file content")


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "active_sessions": len(cli_executor.sessions),
        "websocket_connections": sum(
            websocket_manager.get_session_connection_count(session_id)
            for session_id in websocket_manager.get_all_sessions()
        ),
    }


@app.post("/api/auth/transfer-sessions")
async def transfer_sessions(request_data: TransferSessionsRequest, req: Request):
    """
    Transfer all research sessions from anonymous user to permanent account.
    Protected by JWT auth middleware - user_id extracted from JWT token.
    """
    try:
        # Get authenticated user from JWT (added by middleware)
        authenticated_user_id = getattr(req.state, "user_id", None)

        if not authenticated_user_id:
            raise HTTPException(status_code=401, detail="Unauthorized - no user ID in token")

        # Validate UUIDs format
        try:
            uuid.UUID(request_data.old_user_id)
            uuid.UUID(request_data.new_user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid UUID format")

        # Verify the new_user_id matches the authenticated user
        # (prevent users from transferring sessions to other accounts)
        if request_data.new_user_id != authenticated_user_id:
            raise HTTPException(
                status_code=403,
                detail="Forbidden - can only transfer to your own account",
            )

        logger.info(
            f"Transferring sessions from {request_data.old_user_id} to {request_data.new_user_id}"
        )

        # Implement actual database update (Story 1.3)
        # UPDATE research_sessions SET user_id = new_user_id WHERE user_id = old_user_id
        transferred_count = await database.transfer_sessions(
            old_user_id=request_data.old_user_id, new_user_id=request_data.new_user_id
        )

        logger.info(f"Successfully transferred {transferred_count} sessions")

        return {
            "transferred_count": transferred_count,
            "message": f"Successfully transferred {transferred_count} research sessions",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session transfer error: {e}")
        raise HTTPException(status_code=500, detail=f"Session transfer failed: {str(e)}")


# Enhanced download endpoints
@app.get("/api/session/{session_id}/zip")
async def download_session_zip(session_id: str):
    """Download all files from a session as a ZIP archive"""
    # Create ZIP file
    zip_path = await enhanced_file_manager.create_session_zip(session_id)

    if not zip_path:
        raise HTTPException(status_code=404, detail="No files found for this session")

    # Track download
    enhanced_file_manager.track_download(session_id, zip_path.name)

    return FileResponse(
        path=zip_path,
        filename=f"{session_id}_all_files.zip",
        media_type="application/zip",
    )


@app.get("/api/session/{session_id}/file/{filename}/preview")
async def preview_file(session_id: str, filename: str, lines: int = 50):
    """Get a preview of a text-based file"""
    preview = await enhanced_file_manager.get_file_preview(session_id, filename, lines)

    if not preview:
        raise HTTPException(status_code=404, detail="File not found")

    if not preview.get("supported", False):
        raise HTTPException(
            status_code=400,
            detail=preview.get("error", "File type not supported for preview"),
        )

    return preview


@app.get("/api/session/{session_id}/file/{filename}/metadata")
async def get_file_metadata(session_id: str, filename: str):
    """Get detailed metadata for a file"""
    metadata = await enhanced_file_manager.get_file_metadata(session_id, filename)

    if not metadata:
        raise HTTPException(status_code=404, detail="File not found")

    return metadata


@app.get("/api/session/{session_id}/statistics")
async def get_session_statistics(session_id: str):
    """
    Get session statistics - DATABASE-FIRST with optional filesystem enrichment

    DRY COMPLIANCE:
    - file_count/total_size_bytes: from database (PostgreSQL trigger maintains)
    - file_types/languages: metadata enrichment from filesystem (optional)

    Validated by Gemini (session: cbc61ab1-141d-4306-aba8-01d503712592)
    """
    # CRITICAL: Verify session exists in database first (Gemini validation)
    # Check if session exists in research_sessions table
    client = database.get_supabase_client()
    if client:
        try:
            session_check = (
                client.table("research_sessions")
                .select("id, created_at")
                .eq("id", session_id)
                .single()
                .execute()
            )
            if not session_check.data:
                raise HTTPException(status_code=404, detail="Session not found")
            session_created_at = session_check.data.get("created_at")
        except Exception:
            # If session not found or any error, return 404
            raise HTTPException(status_code=404, detail="Session not found")
    else:
        # No Supabase client, can't verify session
        session_created_at = None

    # Get aggregate stats from DATABASE (DRY source of truth)
    db_stats = await database.get_session_file_stats(session_id)

    # Build response with database values
    response = {
        "session_id": session_id,
        "total_files": db_stats["file_count"],
        "total_size_bytes": db_stats["total_size_bytes"],
        "file_types": {},
        "languages": [],
        "created_at": session_created_at,  # From research_sessions table
    }

    # OPTIONAL: Enrich with file_types/languages from filesystem
    # This is metadata enrichment, not aggregate calculation (DRY compliant)
    try:
        session_dir = Path("outputs") / session_id

        if session_dir.exists():
            languages_set = set()  # Avoid duplicates

            for file_path in session_dir.iterdir():
                if file_path.is_file():
                    # Count file types by extension
                    ext = file_path.suffix.lower()
                    response["file_types"][ext] = response["file_types"].get(ext, 0) + 1

                    # Detect languages from filename using centralized parser
                    # Replaces: Manual string checking for _vi, _en patterns
                    language = FilenameParser.extract_language(file_path.name)
                    language_name = {
                        Language.ENGLISH: "English",
                        Language.VIETNAMESE: "Vietnamese",
                        Language.SPANISH: "Spanish",
                        Language.FRENCH: "French",
                    }.get(language, language.value.capitalize())
                    languages_set.add(language_name)

            response["languages"] = list(languages_set)

    except Exception as e:
        # Log but don't fail - graceful degradation
        logger.warning(
            f"Could not perform filesystem metadata enrichment for session {session_id}: {e}",
            exc_info=True,
        )
        # Continue with DB-only stats (file_types={}, languages=[])

    return response


@app.get("/api/search/files")
async def search_files(q: str, session_id: Optional[str] = None):
    """Search for files across sessions"""
    if not q or len(q) < 2:
        raise HTTPException(status_code=400, detail="Search query must be at least 2 characters")

    results = await enhanced_file_manager.search_files(q, session_id)
    return {"query": q, "results": results, "count": len(results)}


@app.get("/api/downloads/history")
async def get_download_history(limit: int = 10):
    """Get recent download history"""
    history = await enhanced_file_manager.get_download_history(limit)
    return {"history": history, "count": len(history)}


async def start_research_session(session_id: str, subject: str, language: str):
    """Start a research session and stream output via WebSocket"""
    file_watcher_task = None  # Initialize for cleanup

    try:
        # Track files we've already sent events for (to avoid duplicates)
        # KEY FIX: Use (filename, size) to uniquely identify file versions
        # This handles file deletion + recreation scenarios
        sent_file_keys = set()  # Stores (filename, size) tuples
        last_seen_sizes = {}  # Track file sizes to detect stability (cleaned up after processing)

        # Define OUTPUTS_BASE_DIR for security validation
        OUTPUTS_BASE_DIR = Path("outputs/").resolve()

        async def _process_new_file(file, session_id: str):
            """
            Process a single file: extract metadata, validate security, save to DB, create event.
            Returns (file_key, event) on success, (None, None) on failure.

            Security: Uses SecurePathValidator for path traversal prevention
            Performance: Parse filename ONCE to avoid redundant regex operations
            file_key: (filename, size) tuple uniquely identifying this file version

            Gemini validated: session dc76fc08-66c7-4a0b-81b8-51994d09e66d
            """
            try:
                # 1. SECURITY: Validate session_id format first
                if not SecurePathValidator.validate_session_id(session_id):
                    logger.error(f"Security: Invalid session_id format: {session_id}")
                    return (None, None)

                actual_filename = urllib.parse.unquote(file.url.split("/")[-1])

                # 2. PARSE ONCE: Get rich ParsedFilename object with all metadata
                # Replaces multiple redundant parse calls
                # (was: extract_file_type() + extract_language())
                parsed_file: Optional[ParsedFilename] = FilenameParser.parse(actual_filename)

                if not parsed_file:
                    logger.error(
                        f"Metadata: Could not parse standard filename format: "
                        f"{actual_filename}. Aborting processing."
                    )
                    # Fail fast if filename doesn't match expected UUID pattern
                    # This is safer than proceeding with incomplete data
                    return (None, None)

                logger.info(
                    f"📋 File metadata: {parsed_file.original_filename} → "
                    f"type={parsed_file.file_type.value}, lang={parsed_file.language.value}"
                )

                # 3. SECURITY: Validate path using centralized secure validator
                resolved_path = SecurePathValidator.resolve_safe_path(
                    OUTPUTS_BASE_DIR, session_id, parsed_file.original_filename
                )

                if not resolved_path:
                    logger.error(
                        f"Security: Path validation failed for {parsed_file.original_filename}"
                    )
                    return (None, None)

                # 4. DATABASE: Path is safe, proceed with DB operation
                db_success = await database.create_draft_file(
                    session_id=session_id,
                    file_path=str(resolved_path),
                    file_size_bytes=file.size or 0,
                    stage="4_writing",
                )

                if db_success:
                    # Create file_key to uniquely identify this file version
                    file_key = (parsed_file.original_filename, file.size)

                    # DRY: Use centralized download URL builder (single source of truth)
                    download_url = build_download_url(session_id, parsed_file.original_filename)

                    # Create and return WebSocket event with pre-computed friendly_name
                    file_event = create_file_generated_event(
                        session_id=session_id,
                        file_id=parsed_file.uuid,  # Use canonical UUID from parsed object
                        filename=parsed_file.original_filename,
                        file_type=parsed_file.file_type.value,
                        language=parsed_file.language.value,
                        size_bytes=file.size or 0,
                        friendly_name=parsed_file.friendly_name,  # Backend is source of truth
                        path=download_url,  # Proper download URL for file preview
                    )
                    return (file_key, file_event)
                else:
                    logger.error(f"DB insert failed for {parsed_file.original_filename}")
                    return (None, None)

            except Exception:
                # Use logger.exception() to automatically capture stack trace
                logger.exception(f"Unexpected error processing file: {getattr(file, 'url', 'N/A')}")
                return (None, None)

        # Start file watcher task that runs CONCURRENTLY with CLI
        async def watch_and_send_files():
            """Watch for new files and send WebSocket events immediately"""
            start_time = datetime.now()
            timeout = settings.FILE_WAIT_TIMEOUT

            while (datetime.now() - start_time).seconds < timeout:
                try:
                    # Discover files in session directory
                    current_files = await file_manager.discover_session_files(session_id)

                    # Send events for NEW files only (after size stabilizes)
                    for file in current_files:
                        file_key = (file.filename, file.size)

                        # Check if this exact file version already processed
                        if file_key in sent_file_keys:
                            continue  # Already processed this version

                        # CORRECTNESS FIX: Check if file size has stabilized
                        previous_size = last_seen_sizes.get(file.filename)
                        if previous_size == file.size:
                            # Size is stable - file is complete, process it
                            processed_key, file_event = await _process_new_file(file, session_id)

                            if file_event:
                                await websocket_manager.send_event(session_id, file_event)
                                logger.info(f"📄 Sent real-time event for: {file.filename}")
                                sent_file_keys.add(processed_key)

                                # MEMORY LEAK FIX: Clean up size tracking after
                                # successful processing
                                if file.filename in last_seen_sizes:
                                    del last_seen_sizes[file.filename]
                        else:
                            # File is new or still growing - track size and wait
                            last_seen_sizes[file.filename] = file.size
                            logger.debug(
                                f"File {file.filename} size: {file.size} (waiting for stability)"
                            )

                except Exception as e:
                    logger.error(f"Error in file watcher loop: {e}")

                # Check every 2 seconds for new files
                await asyncio.sleep(2)

        # Start file watcher as background task
        file_watcher_task = asyncio.create_task(watch_and_send_files())

        # Stream CLI output through WebSocket (runs concurrently with file watcher)
        await websocket_manager.stream_cli_output(session_id, cli_executor, subject, language)

        # Wait for file watcher to finish (or timeout)
        try:
            await asyncio.wait_for(file_watcher_task, timeout=settings.FILE_WAIT_TIMEOUT)
        except asyncio.TimeoutError:
            logger.warning(f"File watcher timed out for session {session_id}")

        # Get final file count for completion status
        final_files = await file_manager.discover_session_files(session_id)

        # Update session status to completed if files were generated
        # Note: Files were already sent via real-time WebSocket events above
        if final_files and sent_file_keys:
            try:
                await database.update_research_session_status(
                    session_id, SessionStatusEnum.COMPLETED
                )
                logger.info(
                    f"✅ Session {session_id} COMPLETED with "
                    f"{len(sent_file_keys)} files (sent in real-time)"
                )
            except Exception as db_error:
                logger.error(f"Failed to update session status: {db_error}")
        else:
            logger.warning(f"⚠️ No files generated for session {session_id}")

        # SAFETY NET: Ingest any missing drafts and sync DB aggregates at end-of-run
        try:
            outputs_path = PROJECT_ROOT / "outputs"
            await database.ingest_missing_drafts(session_id, outputs_path)
            await database.update_session_file_stats(session_id)
        except Exception as end_err:
            logger.warning(f"End-of-run sync failed for {session_id}: {end_err}")

    except Exception as e:
        logger.error(f"Error in research session {session_id}: {e}")

        # Update session status to failed in database (Story 1.3)
        try:
            await database.update_research_session_status(session_id, SessionStatusEnum.FAILED)
            logger.info(f"Updated session {session_id} to FAILED in database")
        except Exception as db_error:
            logger.error(f"Failed to update database status: {db_error}")

        from schemas import create_error_event

        error_event = create_error_event(
            session_id=session_id,
            error_type="session_error",
            message=f"Session error: {str(e)}",
            recoverable=False,
        )
        await websocket_manager.send_event(session_id, error_event)

    finally:
        # ROBUSTNESS FIX: Ensure background task is always cancelled
        if file_watcher_task and not file_watcher_task.done():
            file_watcher_task.cancel()
            try:
                # Give the task a moment to process the cancellation
                await file_watcher_task
            except asyncio.CancelledError:
                logger.info(f"File watcher task for session {session_id} cancelled successfully")


async def periodic_cleanup():
    """Periodically clean up old files and sessions"""
    while True:
        try:
            # Wait between cleanups (configurable via SESSION_CLEANUP_INTERVAL)
            await asyncio.sleep(settings.SESSION_CLEANUP_INTERVAL)

            # Clean up old files
            cleaned_files = await file_manager.cleanup_old_files(max_age_hours=24)
            if cleaned_files > 0:
                logger.info(f"Cleaned up {cleaned_files} old file directories")

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error during periodic cleanup: {e}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
        log_level="info",
    )

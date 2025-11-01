import asyncio
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

from fastapi import (
    BackgroundTasks,
    FastAPI,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
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
from middleware.auth_middleware import verify_jwt_middleware
from models import (
    ResearchRequest,
    ResearchResponse,
    ResearchSession,
    SessionStatus,
    SessionStatusEnum,
    TransferSessionsRequest,
)
from schemas import WebSocketEvent, create_file_generated_event
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
# Note: Middleware is lenient - skips public endpoints and degrades gracefully if JWT_SECRET not configured
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

    logger.info(
        f"New research request - Session: {session_id}, Subject: {request.subject}"
    )

    # Get user_id from JWT (added by middleware)
    # Frontend MUST create anonymous user via Supabase Auth before making requests
    user_id = getattr(req.state, "user_id", None)

    if not user_id:
        logger.error(f"No user_id in request state - middleware auth failed")
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
    background_tasks.add_task(
        start_research_session, session_id, request.subject, request.language
    )

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
async def get_session_state(session_id: str):
    """
    Get complete session state for re-hydration after page refresh.
    Returns current status, files, and progress.

    DRY: Prefers database file_count over len(files) calculation.
    """
    # Check if session exists in memory (active sessions)
    cli_status = cli_executor.get_session_status(session_id)

    # Get files from filesystem (works for both active and completed sessions)
    files = await file_manager.get_session_files(session_id)

    # If session is not active AND no files exist, it's truly not found
    if not cli_status and not files:
        raise HTTPException(status_code=404, detail="Session not found")

    # Note: Statistics removed - use dedicated /api/session/{id}/statistics endpoint
    # That endpoint now uses database-first approach (DRY compliance)

    # Build complete state
    # For completed sessions not in memory, infer status from files
    if cli_status:
        status = cli_status["status"]
        subject = cli_status.get("subject", "Unknown")
        start_time = (
            cli_status.get("start_time").isoformat()
            if cli_status.get("start_time")
            else None
        )
        end_time = (
            cli_status.get("end_time").isoformat()
            if cli_status.get("end_time")
            else None
        )
        error = cli_status.get("error")
    else:
        # Session completed and no longer in memory, but files exist
        status = "completed"
        subject = "Unknown"  # Can't retrieve subject from completed sessions
        start_time = None
        end_time = None
        error = None

    # DRY: Try to get file_count from database first
    # Fallback to len(files) only for non-database sessions
    file_count = len(files)  # Fallback
    try:
        from database import get_supabase_client
        client = get_supabase_client()
        if client:
            db_session = client.table("research_sessions").select("file_count").eq("id", session_id).single().execute()
            if db_session.data and db_session.data.get("file_count") is not None:
                file_count = db_session.data["file_count"]  # DRY: Use DB value
    except Exception as e:
        logger.debug(f"Could not get file_count from DB for session {session_id}: {e}")
        # Keep using len(files) fallback

    return {
        "session_id": session_id,
        "status": status,
        "subject": subject,
        "start_time": start_time,
        "end_time": end_time,
        "files": [file.dict() for file in files],
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
        raise HTTPException(
            status_code=500, detail="Failed to retrieve research sessions"
        )


@app.get("/api/sessions/list")
async def list_user_sessions(
    req: Request,
    include_archived: bool = False,
    status: Optional[str] = None,
    language: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
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
        # DRY: Use stored file_count/total_size_bytes from database (maintained by update_session_file_stats)
        sessions_data = []
        for session in sessions:
            session_dict = {
                "id": str(session.id),
                "user_id": str(session.user_id),
                "title": session.title,
                "status": (
                    session.status.value
                    if hasattr(session.status, "value")
                    else session.status
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

    return {
        "message": "File stats updated successfully",
        "session_id": session_id
    }


@app.post("/api/sessions/backfill-file-stats")
async def backfill_all_file_stats(req: Request):
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

        for session in sessions:
            # Only update if file_count is null or 0
            if session.file_count is None or session.file_count == 0:
                success = await database.update_session_file_stats(str(session.id))
                if success:
                    updated_count += 1
                else:
                    failed_count += 1

        return {
            "message": f"Backfill complete",
            "updated": updated_count,
            "failed": failed_count,
            "total_processed": updated_count + failed_count
        }

    except Exception as e:
        logger.error(f"Error during backfill: {e}")
        raise HTTPException(status_code=500, detail="Backfill failed")


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
async def duplicate_user_session(session_id: str, req: Request):
    """
    Duplicate a research session with same parameters.
    Creates a new session with copied metadata but NOT files.
    """
    # Get user_id from JWT
    user_id = getattr(req.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    # Verify session belongs to user
    session = await database.get_session_by_id(session_id, user_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Duplicate the session
    new_session_id = await database.duplicate_session(session_id, user_id)

    if not new_session_id:
        raise HTTPException(status_code=500, detail="Failed to duplicate session")

    return {
        "message": "Session duplicated successfully",
        "original_session_id": session_id,
        "new_session_id": new_session_id,
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
        raise HTTPException(
            status_code=400, detail="At least 2 sessions required for comparison"
        )

    if len(session_ids) > 5:
        raise HTTPException(
            status_code=400, detail="Maximum 5 sessions can be compared at once"
        )

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
    # Validate filename
    if not file_manager.is_valid_filename(filename):
        raise HTTPException(status_code=400, detail="Invalid filename")

    # Get file path
    file_path = file_manager.get_file_path(session_id, filename)

    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")

    # Get proper MIME type
    mime_type = file_manager.get_mime_type(filename)

    # Create a user-friendly download filename from UUID-based filename
    friendly_name = file_manager.create_friendly_filename_from_uuid(file_path.name)

    return FileResponse(path=file_path, filename=friendly_name, media_type=mime_type)


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

            return PlainTextResponse(
                content=content.decode("utf-8"), media_type=mime_type
            )

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
            raise HTTPException(
                status_code=401, detail="Unauthorized - no user ID in token"
            )

        # Validate UUIDs format
        import uuid

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
        raise HTTPException(
            status_code=500, detail=f"Session transfer failed: {str(e)}"
        )


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
        except Exception as e:
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
        "created_at": session_created_at  # From research_sessions table
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

                    # Detect languages from filename
                    if "_vi" in file_path.name:
                        languages_set.add("Vietnamese")
                    elif "_en" in file_path.name:
                        languages_set.add("English")

            response["languages"] = list(languages_set)

    except Exception as e:
        # Log but don't fail - graceful degradation
        logger.warning(
            f"Could not perform filesystem metadata enrichment for session {session_id}: {e}",
            exc_info=True
        )
        # Continue with DB-only stats (file_types={}, languages=[])

    return response


@app.get("/api/search/files")
async def search_files(q: str, session_id: Optional[str] = None):
    """Search for files across sessions"""
    if not q or len(q) < 2:
        raise HTTPException(
            status_code=400, detail="Search query must be at least 2 characters"
        )

    results = await enhanced_file_manager.search_files(q, session_id)
    return {"query": q, "results": results, "count": len(results)}


@app.get("/api/downloads/history")
async def get_download_history(limit: int = 10):
    """Get recent download history"""
    history = await enhanced_file_manager.get_download_history(limit)
    return {"history": history, "count": len(history)}


async def start_research_session(session_id: str, subject: str, language: str):
    """Start a research session and stream output via WebSocket"""
    try:
        # Track files we've already sent events for (to avoid duplicates)
        sent_files = set()

        # Start file watcher task that runs CONCURRENTLY with CLI
        async def watch_and_send_files():
            """Watch for new files and send WebSocket events immediately"""
            start_time = datetime.now()
            timeout = settings.FILE_WAIT_TIMEOUT

            while (datetime.now() - start_time).seconds < timeout:
                try:
                    # Discover files in session directory
                    current_files = await file_manager.discover_session_files(session_id)

                    # Send events for NEW files only
                    for file in current_files:
                        file_key = (file.filename, file.size)  # Unique identifier
                        if file_key not in sent_files:
                            sent_files.add(file_key)

                            # Extract file metadata
                            file_extension = (
                                file.filename.rsplit(".", 1)[-1]
                                if "." in file.filename
                                else "unknown"
                            )
                            filename_parts = file.filename.rsplit(".", 1)[0].split("_")
                            lang = (
                                filename_parts[-1]
                                if len(filename_parts) > 2 and len(filename_parts[-1]) <= 3
                                else "en"
                            )
                            file_id = file.filename.rsplit(".", 1)[0]

                            # Insert into database
                            actual_filename = urllib.parse.unquote(file.url.split('/')[-1])
                            filesystem_path = f"outputs/{session_id}/{actual_filename}"

                            # Security validation
                            if '..' in filesystem_path or filesystem_path.startswith('/'):
                                logger.error(f"Security: Invalid file path: {filesystem_path}")
                                continue

                            # Insert into database
                            db_success = await database.create_draft_file(
                                session_id=session_id,
                                file_path=filesystem_path,
                                file_size_bytes=file.size or 0,
                                stage="4_writing",
                            )

                            if db_success:
                                # Send WebSocket event IMMEDIATELY
                                file_event = create_file_generated_event(
                                    session_id=session_id,
                                    file_id=file_id,
                                    filename=file.filename,
                                    file_type=file_extension,
                                    language=lang,
                                    size_bytes=file.size or 0,
                                    path=file.url,
                                )
                                await websocket_manager.send_event(session_id, file_event)
                                logger.info(f"📄 Sent real-time event for: {file.filename}")
                            else:
                                logger.error(f"DB insert failed for {file.filename}")

                except Exception as e:
                    logger.error(f"Error in file watcher: {e}")

                # Check every 2 seconds for new files
                await asyncio.sleep(2)

        # Start file watcher as background task
        file_watcher_task = asyncio.create_task(watch_and_send_files())

        # Stream CLI output through WebSocket (runs concurrently with file watcher)
        await websocket_manager.stream_cli_output(
            session_id, cli_executor, subject, language
        )

        # Wait for file watcher to finish (or timeout)
        try:
            await asyncio.wait_for(file_watcher_task, timeout=settings.FILE_WAIT_TIMEOUT)
        except asyncio.TimeoutError:
            logger.warning(f"File watcher timed out for session {session_id}")

        # Get final file count for completion status
        final_files = await file_manager.discover_session_files(session_id)

        # Update session status to completed if files were generated
        # Note: Files were already sent via real-time WebSocket events above
        if final_files and len(sent_files) > 0:
            try:
                await database.update_research_session_status(
                    session_id, SessionStatusEnum.COMPLETED
                )
                logger.info(f"✅ Session {session_id} COMPLETED with {len(sent_files)} files (sent in real-time)")
            except Exception as db_error:
                logger.error(f"Failed to update session status: {db_error}")
        else:
            logger.warning(f"⚠️ No files generated for session {session_id}")

    except Exception as e:
        logger.error(f"Error in research session {session_id}: {e}")

        # Update session status to failed in database (Story 1.3)
        try:
            await database.update_research_session_status(
                session_id, SessionStatusEnum.FAILED
            )
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

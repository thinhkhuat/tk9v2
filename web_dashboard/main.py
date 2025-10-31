import asyncio
import logging
import uuid
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from models import ResearchRequest, ResearchResponse, SessionStatus, ResearchSession
from cli_executor import CLIExecutor
from file_manager import FileManager
from file_manager_enhanced import EnhancedFileManager
from websocket_handler import WebSocketManager
from schemas import create_file_generated_event, WebSocketEvent

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
    lifespan=lifespan
)

# Configure CORS to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://localhost:12656",
        "http://127.0.0.1:12656",
        "http://192.168.2.22:12656",
        "http://192.168.2.22:5173",
        "http://tk9.thinhkhuat.com",
        "https://tk9.thinhkhuat.com",
        "http://tk9v2.thinhkhuat.com",
        "https://tk9v2.thinhkhuat.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Mount static files
app.mount("/static", StaticFiles(directory=WEB_STATIC_PATH), name="static")

# Setup templates
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Serve the main dashboard page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/research", response_model=ResearchResponse)
async def submit_research(request: ResearchRequest, background_tasks: BackgroundTasks):
    """Submit a new research request"""
    # Generate unique session ID
    session_id = str(uuid.uuid4())
    
    logger.info(f"New research request - Session: {session_id}, Subject: {request.subject}")
    
    # Start research in background
    background_tasks.add_task(
        start_research_session, 
        session_id, 
        request.subject, 
        request.language
    )
    
    return ResearchResponse(
        session_id=session_id,
        status="started",
        message="Research session started successfully",
        websocket_url=f"/ws/{session_id}"
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
        'running': 'running',
        'completed': 'completed',
        'failed': 'failed'
    }

    return SessionStatus(
        session_id=session_id,
        status=status_mapping.get(cli_status['status'], 'unknown'),
        progress=100.0 if cli_status['status'] == 'completed' else 50.0 if cli_status['status'] == 'running' else 0.0,
        files=files,
        error_message=cli_status.get('error')
    )

@app.get("/api/session/{session_id}/state")
async def get_session_state(session_id: str):
    """
    Get complete session state for re-hydration after page refresh.
    Returns current status, files, and progress.
    """
    # Check if session exists
    cli_status = cli_executor.get_session_status(session_id)

    if not cli_status:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get files
    files = await file_manager.get_session_files(session_id)

    # Get session statistics if available
    try:
        stats = await enhanced_file_manager.get_session_statistics(session_id)
    except:
        stats = None

    # Build complete state
    return {
        "session_id": session_id,
        "status": cli_status['status'],
        "subject": cli_status.get('subject', 'Unknown'),
        "start_time": cli_status.get('start_time').isoformat() if cli_status.get('start_time') else None,
        "end_time": cli_status.get('end_time').isoformat() if cli_status.get('end_time') else None,
        "files": [file.dict() for file in files],
        "file_count": len(files),
        "statistics": stats,
        "error": cli_status.get('error')
    }

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time log streaming"""
    await websocket_manager.handle_websocket(websocket, session_id)

@app.get("/api/sessions", response_model=list[ResearchSession])
async def get_all_sessions():
    """Get all available research sessions"""
    try:
        sessions = await file_manager.get_all_research_sessions()
        return sessions
    except Exception as e:
        logger.error(f"Error getting research sessions: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve research sessions")

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
    
    return FileResponse(
        path=file_path,
        filename=friendly_name,
        media_type=mime_type
    )

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "active_sessions": len(cli_executor.sessions),
        "websocket_connections": sum(
            websocket_manager.get_session_connection_count(session_id)
            for session_id in websocket_manager.get_all_sessions()
        )
    }

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
        media_type="application/zip"
    )

@app.get("/api/session/{session_id}/file/{filename}/preview")
async def preview_file(session_id: str, filename: str, lines: int = 50):
    """Get a preview of a text-based file"""
    preview = await enhanced_file_manager.get_file_preview(session_id, filename, lines)

    if not preview:
        raise HTTPException(status_code=404, detail="File not found")

    if not preview.get("supported", False):
        raise HTTPException(status_code=400, detail=preview.get("error", "File type not supported for preview"))

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
    """Get statistics about a research session"""
    stats = await enhanced_file_manager.get_session_statistics(session_id)

    if not stats:
        raise HTTPException(status_code=404, detail="Session not found")

    return stats

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
    try:
        # Stream CLI output through WebSocket
        await websocket_manager.stream_cli_output(
            session_id, cli_executor, subject, language
        )
        
        # Wait for files to be generated
        files = await file_manager.wait_for_files(session_id, subject, timeout=30)

        if files:
            # Notify clients that files are available using structured events
            for file in files:
                # Extract file extension for file_type
                file_extension = file.filename.rsplit('.', 1)[-1] if '.' in file.filename else 'unknown'

                # Extract language from filename (e.g., "research_report_vi.pdf" -> "vi")
                # If no language code, default to "en"
                filename_parts = file.filename.rsplit('.', 1)[0].split('_')
                language = filename_parts[-1] if len(filename_parts) > 2 and len(filename_parts[-1]) <= 3 else "en"

                # Generate file_id from filename (use filename without extension as unique ID)
                file_id = file.filename.rsplit('.', 1)[0]

                file_event = create_file_generated_event(
                    session_id=session_id,
                    file_id=file_id,
                    filename=file.filename,
                    file_type=file_extension,
                    language=language,
                    size_bytes=file.size or 0,  # Use 0 if size is None
                    path=file.url
                )
                await websocket_manager.send_event(session_id, file_event)
        else:
            logger.warning(f"No files generated for session {session_id}")
            
    except Exception as e:
        logger.error(f"Error in research session {session_id}: {e}")
        from schemas import create_error_event
        error_event = create_error_event(
            session_id=session_id,
            error_type="session_error",
            message=f"Session error: {str(e)}",
            recoverable=False
        )
        await websocket_manager.send_event(session_id, error_event)

async def periodic_cleanup():
    """Periodically clean up old files and sessions"""
    while True:
        try:
            # Wait 1 hour between cleanups
            await asyncio.sleep(3600)
            
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
        host="0.0.0.0",  # Bind to all interfaces - most permissive
        port=12656,
        reload=True,
        log_level="info"
    )
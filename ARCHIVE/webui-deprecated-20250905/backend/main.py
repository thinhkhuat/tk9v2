"""
FastAPI Backend for Deep Research MCP Web UI
Python 3.11+ with WebSocket support
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import socketio
from typing import Optional, Dict, Any, List
import asyncio
import redis.asyncio as redis
from celery import Celery
from pydantic import BaseModel, Field
from datetime import datetime
import uuid
import os
from pathlib import Path
import sys

# Add parent directory to path for multi_agents import
sys.path.append(str(Path(__file__).parent.parent.parent))

from multi_agents.main import run_research_task
from .auth import verify_token, get_current_user
from .database import Database, ResearchSession
from .models import ResearchRequest, ResearchResponse, AgentProgress
from .storage import SupabaseStorage

# Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

# Initialize services
redis_client = redis.from_url(REDIS_URL)
celery_app = Celery("research_tasks", broker=REDIS_URL)
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins=ALLOWED_ORIGINS)
storage = SupabaseStorage(SUPABASE_URL, SUPABASE_KEY)
db = Database()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    await redis_client.ping()
    await db.connect()
    yield
    # Cleanup
    await redis_client.close()
    await db.disconnect()

# Create FastAPI app
app = FastAPI(
    title="Deep Research MCP API",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Socket.IO app
socket_app = socketio.ASGIApp(sio, app)

# ============================================================================
# WebSocket Events
# ============================================================================

@sio.event
async def connect(sid, environ, auth):
    """Handle WebSocket connection"""
    if auth and 'userId' in auth:
        user_id = auth['userId']
        await sio.save_session(sid, {'user_id': user_id})
        await sio.enter_room(sid, f"user_{user_id}")
        print(f"User {user_id} connected with session {sid}")
    else:
        await sio.disconnect(sid)

@sio.event
async def disconnect(sid):
    """Handle WebSocket disconnection"""
    session = await sio.get_session(sid)
    if session and 'user_id' in session:
        print(f"User {session['user_id']} disconnected")

@sio.event
async def join_research_session(sid, data):
    """Join a specific research session room"""
    session_id = data.get('session_id')
    if session_id:
        await sio.enter_room(sid, f"session_{session_id}")
        await sio.emit('joined_session', {'session_id': session_id}, to=sid)

@sio.event
async def leave_research_session(sid, data):
    """Leave a research session room"""
    session_id = data.get('session_id')
    if session_id:
        await sio.leave_room(sid, f"session_{session_id}")

# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/api/v1/health")
async def health_check():
    """System health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "redis": await redis_client.ping(),
            "database": await db.health_check(),
            "storage": await storage.health_check()
        }
    }

@app.post("/api/v1/research/sessions")
async def create_research_session(
    request: ResearchRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    """Create a new research session"""
    # Create session in database
    session = await db.create_research_session(
        user_id=current_user['id'],
        query=request.query,
        tone=request.tone,
        language=request.language,
        provider_config=request.provider_config.dict() if request.provider_config else {},
        task_config=request.task_config.dict() if request.task_config else {}
    )
    
    # Queue the research task
    background_tasks.add_task(
        execute_research_task,
        session_id=session.id,
        user_id=current_user['id'],
        research_params=request.dict()
    )
    
    # Notify via WebSocket
    await sio.emit(
        'research_started',
        {
            'session_id': session.id,
            'query': request.query,
            'status': 'queued'
        },
        room=f"user_{current_user['id']}"
    )
    
    return {
        "session_id": session.id,
        "status": "queued",
        "message": "Research task has been queued for processing"
    }

@app.get("/api/v1/research/sessions")
async def list_research_sessions(
    page: int = 1,
    limit: int = 10,
    status: Optional[str] = None,
    current_user = Depends(get_current_user)
):
    """List user's research sessions with pagination"""
    sessions = await db.get_user_sessions(
        user_id=current_user['id'],
        page=page,
        limit=limit,
        status=status
    )
    
    return {
        "sessions": sessions,
        "page": page,
        "limit": limit,
        "total": await db.count_user_sessions(current_user['id'], status)
    }

@app.get("/api/v1/research/sessions/{session_id}")
async def get_research_session(
    session_id: str,
    current_user = Depends(get_current_user)
):
    """Get detailed research session information"""
    session = await db.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.user_id != current_user['id']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get agent execution logs
    agent_logs = await db.get_agent_executions(session_id)
    
    # Get generated files
    files = await db.get_session_files(session_id)
    
    return {
        "session": session,
        "agent_logs": agent_logs,
        "files": files
    }

@app.post("/api/v1/research/sessions/{session_id}/cancel")
async def cancel_research_session(
    session_id: str,
    current_user = Depends(get_current_user)
):
    """Cancel a running research session"""
    session = await db.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.user_id != current_user['id']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if session.status not in ['queued', 'running']:
        raise HTTPException(status_code=400, detail="Session cannot be cancelled")
    
    # Update session status
    await db.update_session_status(session_id, 'cancelled')
    
    # Cancel Celery task if running
    celery_app.control.revoke(session_id, terminate=True)
    
    # Notify via WebSocket
    await sio.emit(
        'research_cancelled',
        {'session_id': session_id},
        room=f"session_{session_id}"
    )
    
    return {"message": "Research session cancelled"}

@app.get("/api/v1/research/sessions/{session_id}/files/{filename}")
async def download_research_file(
    session_id: str,
    filename: str,
    current_user = Depends(get_current_user)
):
    """Download a generated research file"""
    session = await db.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.user_id != current_user['id']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get file from storage
    file_path = f"research-reports/{session_id}/{filename}"
    file_url = await storage.get_signed_url(file_path)
    
    if not file_url:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Return redirect to signed URL
    return {"download_url": file_url}

@app.get("/api/v1/providers/llm")
async def list_llm_providers():
    """List available LLM providers and their status"""
    providers = [
        {
            "name": "openai",
            "display_name": "OpenAI",
            "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
            "status": "available" if os.getenv("OPENAI_API_KEY") else "not_configured"
        },
        {
            "name": "google_gemini",
            "display_name": "Google Gemini",
            "models": ["gemini-2.0-flash", "gemini-1.5-pro"],
            "status": "available" if os.getenv("GOOGLE_API_KEY") else "not_configured"
        },
        {
            "name": "anthropic",
            "display_name": "Anthropic Claude",
            "models": ["claude-3-opus", "claude-3-sonnet"],
            "status": "available" if os.getenv("ANTHROPIC_API_KEY") else "not_configured"
        }
    ]
    return {"providers": providers}

@app.get("/api/v1/providers/search")
async def list_search_providers():
    """List available search providers and their status"""
    providers = [
        {
            "name": "tavily",
            "display_name": "Tavily",
            "status": "available" if os.getenv("TAVILY_API_KEY") else "not_configured"
        },
        {
            "name": "brave",
            "display_name": "Brave Search",
            "status": "available" if os.getenv("BRAVE_API_KEY") else "not_configured"
        },
        {
            "name": "duckduckgo",
            "display_name": "DuckDuckGo",
            "status": "available"  # No API key required
        }
    ]
    return {"providers": providers}

# ============================================================================
# Background Tasks
# ============================================================================

async def execute_research_task(session_id: str, user_id: str, research_params: dict):
    """Execute research task with progress updates"""
    try:
        # Update session status
        await db.update_session_status(session_id, 'running')
        await db.update_session_started(session_id)
        
        # Create progress callback
        async def on_agent_progress(agent_name: str, status: str, message: str):
            # Save to database
            await db.create_agent_execution(
                session_id=session_id,
                agent_name=agent_name,
                status=status,
                message=message
            )
            
            # Emit WebSocket event
            await sio.emit(
                'agent_progress',
                {
                    'session_id': session_id,
                    'agent_name': agent_name,
                    'status': status,
                    'message': message,
                    'timestamp': datetime.utcnow().isoformat()
                },
                room=f"session_{session_id}"
            )
        
        # Run the research task
        result = await run_research_task(
            **research_params,
            progress_callback=on_agent_progress,
            write_to_files=False  # We'll handle file storage ourselves
        )
        
        # Upload files to Supabase Storage
        files_uploaded = []
        if result.get('final_reports'):
            for format_type, content in result['final_reports'].items():
                filename = f"{session_id}.{format_type}"
                storage_path = f"research-reports/{session_id}/{filename}"
                
                # Upload to storage
                await storage.upload_file(storage_path, content)
                
                # Save file record
                await db.create_research_file(
                    session_id=session_id,
                    filename=filename,
                    file_type=format_type,
                    storage_path=storage_path,
                    file_size=len(content)
                )
                
                files_uploaded.append({
                    'type': format_type,
                    'filename': filename
                })
        
        # Update session with results
        await db.update_session_completed(
            session_id=session_id,
            report_content=result.get('draft', ''),
            translated_content=result.get('translation_result', ''),
            agent_logs=result.get('agent_logs', [])
        )
        
        # Emit completion event
        await sio.emit(
            'research_completed',
            {
                'session_id': session_id,
                'files': files_uploaded,
                'timestamp': datetime.utcnow().isoformat()
            },
            room=f"session_{session_id}"
        )
        
    except Exception as e:
        # Update session with error
        await db.update_session_failed(session_id, str(e))
        
        # Emit error event
        await sio.emit(
            'research_error',
            {
                'session_id': session_id,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            },
            room=f"session_{session_id}"
        )

# ============================================================================
# Celery Tasks
# ============================================================================

@celery_app.task(name="execute_research")
def execute_research_celery(session_id: str, user_id: str, research_params: dict):
    """Celery task wrapper for research execution"""
    asyncio.run(execute_research_task(session_id, user_id, research_params))

# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        socket_app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
# Web Dashboard - Component Context

## Purpose

The Web Dashboard is a real-time monitoring interface for the TK9 Deep Research MCP system. It provides a browser-based UI for submitting research queries, monitoring progress via WebSocket, and managing research outputs. Built with FastAPI backend and vanilla JavaScript frontend, it serves as the primary user interface for production deployments.

## Current Status: Production Ready

**Last Updated**: 2025-10-31
**Status**: ✅ Operational - Deployed at https://tk9.thinhkhuat.com
**Production IP**: 192.168.2.22:12656 (binds to 0.0.0.0)
**Known Issue**: WebSocket 404 errors via Caddy proxy (direct access works)

## Component-Specific Development Guidelines

### Code Organization
- **Backend**: FastAPI application with async/await throughout
- **Frontend**: Vanilla JavaScript (no build step required)
- **Styling**: Tailwind CSS via CDN
- **Real-time**: WebSocket for live progress updates
- **File Management**: Two-tier system (basic + enhanced)

### Development Patterns
```python
# FastAPI endpoint pattern
@app.post("/api/resource", response_model=ResponseModel)
async def endpoint_name(request: RequestModel, background_tasks: BackgroundTasks):
    """Endpoint description"""
    try:
        # Validation
        if not validate(request):
            raise HTTPException(status_code=400, detail="...")

        # Async processing
        background_tasks.add_task(process_task, ...)

        return ResponseModel(...)
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### WebSocket Pattern
```python
# Connection management
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket_manager.handle_websocket(websocket, session_id)

# Message broadcasting
await websocket_manager.broadcast(session_id, message)
```

### Security Considerations
- **Input Sanitization**: All research queries sanitized
- **Path Traversal Protection**: Filename validation prevents directory traversal
- **MIME Type Validation**: Proper content-type headers for downloads
- **CORS**: Configured for production domain only
- **Rate Limiting**: TODO - Not yet implemented

## Major Subsystem Organization

### 1. FastAPI Application (`main.py` - 290 lines)
**Core server and API endpoints**

**Key Endpoints**:
- `GET /` - Serve dashboard HTML
- `POST /api/research` - Submit new research query
- `GET /api/session/{id}` - Get session status and files
- `GET /api/sessions` - List all research sessions
- `GET /download/{session}/{file}` - Download research output
- `WS /ws/{session}` - WebSocket for real-time updates

**Application Lifecycle**:
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize components
    logger.info("Starting Web Dashboard")
    cleanup_task = asyncio.create_task(periodic_cleanup())

    yield

    # Shutdown: Cleanup
    cleanup_task.cancel()
    logger.info("Shutdown complete")
```

**Background Tasks**:
- Periodic session cleanup (old sessions/files)
- Research execution in background
- Log streaming management

### 2. CLI Execution Layer (`cli_executor.py` - 161 lines)
**Manages research execution as subprocess**

**Responsibilities**:
- Spawns research CLI as subprocess
- Streams stdout/stderr in real-time
- Tracks session status (running/completed/failed)
- Sanitizes user input for shell safety

**Command Execution**:
```python
cmd = [
    "uv", "run", "python", "-m", "main",
    "-r", sanitized_subject,
    "-l", language,
    "--save-files",
    "--verbose"
]

process = await asyncio.create_subprocess_exec(
    *cmd,
    stdout=asyncio.subprocess.PIPE,
    stderr=asyncio.subprocess.STDOUT,
    cwd=self.project_root
)
```

**Session Management**:
- Tracks running processes by session ID
- Stores start time, subject, return code
- Provides status queries for API

### 3. File Management System

#### Basic File Manager (`file_manager.py` - 276 lines)
**Standard file operations and listing**

**Capabilities**:
- List all research sessions from outputs directory
- Find files for specific session
- Validate filenames (prevent directory traversal)
- MIME type detection for proper download headers
- UUID to friendly filename conversion

**File Discovery**:
```python
async def get_all_research_sessions() -> list[ResearchSession]:
    """Scans outputs/ directory for research runs"""
    # Finds run_[timestamp]_[query]/ directories
    # Extracts final reports and metadata
```

#### Enhanced File Manager (`file_manager_enhanced.py` - 480 lines)
**Advanced file operations with streaming**

**Additional Features**:
- Streaming file downloads for large files
- Range request support (partial downloads)
- Enhanced session metadata extraction
- Draft file exploration
- Directory browsing with recursive scanning

**Streaming Pattern**:
```python
async def stream_file(file_path: Path) -> AsyncGenerator[bytes, None]:
    """Stream file in chunks for memory efficiency"""
    async with aiofiles.open(file_path, 'rb') as f:
        while chunk := await f.read(CHUNK_SIZE):
            yield chunk
```

### 4. WebSocket Management (`websocket_handler.py` - 133 lines)
**Real-time bidirectional communication**

**Connection Lifecycle**:
```python
class WebSocketManager:
    connections: Dict[str, List[WebSocket]] = {}

    async def handle_websocket(self, websocket, session_id):
        await websocket.accept()
        self.connections[session_id].append(websocket)

        try:
            await self.stream_logs_to_websocket(websocket, session_id)
        except WebSocketDisconnect:
            self.connections[session_id].remove(websocket)
```

**Log Streaming**:
- Connects to CLI executor's log generator
- Forwards research progress to WebSocket clients
- Handles multiple clients per session
- Graceful disconnect and reconnection

**Message Format**:
```json
{
    "type": "log",
    "session_id": "uuid",
    "message": "[AGENT] Progress update",
    "timestamp": "2025-10-31T10:30:00Z"
}
```

### 5. Data Models (`models.py` - 46 lines)
**Pydantic models for API contracts**

**Models**:
```python
class ResearchRequest(BaseModel):
    subject: str  # Research query
    language: str = "vi"  # Target translation language

class ResearchResponse(BaseModel):
    session_id: str
    status: str  # started/running/completed/failed
    message: str
    websocket_url: str

class SessionStatus(BaseModel):
    session_id: str
    status: str
    progress: float  # 0-100
    files: List[str]
    error_message: Optional[str]

class ResearchSession(BaseModel):
    session_id: str
    subject: str
    timestamp: str
    files: List[str]
    status: str
```

### 6. Frontend (`templates/index.html` + `static/`)
**Single-page application with WebSocket client**

**Structure**:
- `templates/index.html` - Main dashboard template
- `static/js/dashboard.js` - WebSocket client and UI logic
- `static/css/dashboard.css` - Custom styles (Tailwind base)
- `static/css/enhanced-downloads.css` - Download manager styles
- `static/js/enhanced-downloads.js` - Download UI enhancements

**Frontend Features**:
- Research query submission form
- Real-time log display (WebSocket)
- Session management (list, select, delete)
- File browser with download buttons
- Progress indicators and status badges
- Error handling and reconnection logic

**WebSocket Client Pattern**:
```javascript
const ws = new WebSocket(`ws://${location.host}/ws/${sessionId}`);

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    appendLog(data.message);
    updateProgress(data.progress);
};

ws.onerror = (error) => {
    console.error('WebSocket error:', error);
    showReconnectOption();
};
```

## Architectural Patterns

### 1. Background Task Processing
**Pattern**: FastAPI BackgroundTasks for async research

```python
@app.post("/api/research")
async def submit_research(request: ResearchRequest, background_tasks: BackgroundTasks):
    session_id = str(uuid.uuid4())

    # Return immediately, process in background
    background_tasks.add_task(
        start_research_session,
        session_id,
        request.subject,
        request.language
    )

    return ResearchResponse(session_id=session_id, status="started")
```

**Rationale**: Research takes 5-30 minutes - can't block HTTP request

### 2. WebSocket Fan-Out
**Pattern**: One-to-many log broadcasting

```python
class WebSocketManager:
    connections: Dict[str, List[WebSocket]] = {}

    async def broadcast(self, session_id: str, message: str):
        for ws in self.connections.get(session_id, []):
            try:
                await ws.send_text(message)
            except:
                # Remove dead connections
                self.connections[session_id].remove(ws)
```

**Rationale**: Multiple browser tabs/users can monitor same session

### 3. Process Lifecycle Management
**Pattern**: Async subprocess with stream capture

```python
process = await asyncio.create_subprocess_exec(
    *cmd,
    stdout=asyncio.subprocess.PIPE,
    stderr=asyncio.subprocess.STDOUT
)

# Stream output asynchronously
async for line in process.stdout:
    await websocket_manager.broadcast(session_id, line)

return_code = await process.wait()
```

**Rationale**: Non-blocking I/O, real-time feedback, proper cleanup

### 4. File Discovery Pattern
**Pattern**: Filesystem scanning with caching

```python
async def get_all_research_sessions():
    outputs_dir = PROJECT_ROOT / "outputs"
    sessions = []

    for run_dir in outputs_dir.glob("run_*"):
        session = await extract_session_metadata(run_dir)
        sessions.append(session)

    return sorted(sessions, key=lambda s: s.timestamp, reverse=True)
```

**Rationale**: No database needed, filesystem is source of truth

### 5. Static File Serving
**Pattern**: FastAPI StaticFiles with proper MIME types

```python
app.mount("/static", StaticFiles(directory=WEB_STATIC_PATH), name="static")

@app.get("/download/{session}/{file}")
async def download_file(session: str, file: str):
    mime_type = get_mime_type(file)
    return FileResponse(
        path=file_path,
        media_type=mime_type,
        filename=friendly_name
    )
```

**Rationale**: Efficient static serving, proper browser handling

### 6. Input Sanitization
**Pattern**: Whitelist-based validation

```python
def _sanitize_input(self, subject: str) -> str:
    # Remove shell metacharacters
    forbidden = ['|', '&', ';', '>', '<', '`', '$', '(', ')']
    sanitized = subject
    for char in forbidden:
        sanitized = sanitized.replace(char, '')
    return sanitized.strip()

def is_valid_filename(self, filename: str) -> bool:
    # Prevent directory traversal
    if '..' in filename or '/' in filename:
        return False
    return True
```

**Rationale**: Prevent command injection and path traversal attacks

## Integration Points

### Upstream Dependencies
- **Multi-Agent System** (`/multi_agents/`) - Research execution via CLI
- **CLI Interface** (`/cli/` + `/main.py`) - Subprocess invocation
- **Output Directory** (`/outputs/`) - Filesystem-based session storage

### Downstream Dependencies
- **Browser Clients** - JavaScript WebSocket connections
- **Caddy Reverse Proxy** - Production HTTPS termination and routing
- **File System** - Direct file access for serving downloads

### Network Architecture
```
Internet → Caddy (443) → Dashboard (12656) → CLI Subprocess
                                              ↓
                                         Outputs Directory
```

**Production Configuration**:
- **Internal**: http://192.168.2.22:12656
- **External**: https://tk9.thinhkhuat.com (via Caddy)
- **Binding**: 0.0.0.0:12656 (all interfaces)

### Environment Variables
```bash
# Dashboard Configuration
DASHBOARD_PORT=12656
DASHBOARD_HOST=0.0.0.0

# CORS Configuration
ALLOWED_ORIGINS=https://tk9.thinhkhuat.com

# File Paths
PROJECT_ROOT=/path/to/tk9_source_deploy
OUTPUTS_DIR=${PROJECT_ROOT}/outputs
```

### Startup Script (`start_dashboard.sh`)
```bash
#!/bin/bash
cd "$(dirname "$0")"
uvicorn main:app --host 0.0.0.0 --port 12656 --reload
```

## Development Patterns

### Adding New API Endpoint
1. **Define Pydantic Model**: Add to `models.py`
   ```python
   class NewRequest(BaseModel):
       field: str
   ```

2. **Create Endpoint**: Add to `main.py`
   ```python
   @app.post("/api/new-endpoint", response_model=NewResponse)
   async def new_endpoint(request: NewRequest):
       # Implementation
       return NewResponse(...)
   ```

3. **Update Frontend**: Add JavaScript in `dashboard.js`
   ```javascript
   async function callNewEndpoint(data) {
       const response = await fetch('/api/new-endpoint', {
           method: 'POST',
           headers: {'Content-Type': 'application/json'},
           body: JSON.stringify(data)
       });
       return await response.json();
   }
   ```

### Adding WebSocket Messages
1. **Define Message Type**: Document in `websocket_handler.py`
2. **Send from Backend**:
   ```python
   await websocket_manager.broadcast(session_id, json.dumps({
       "type": "new_event",
       "data": {...}
   }))
   ```

3. **Handle in Frontend**:
   ```javascript
   ws.onmessage = (event) => {
       const msg = JSON.parse(event.data);
       if (msg.type === 'new_event') {
           handleNewEvent(msg.data);
       }
   };
   ```

### Testing Dashboard Locally
```bash
# Terminal 1: Start dashboard
cd web_dashboard
./start_dashboard.sh

# Terminal 2: Test research
curl -X POST http://localhost:12656/api/research \
  -H "Content-Type: application/json" \
  -d '{"subject": "test query", "language": "en"}'

# Browser: Open http://localhost:12656
```

### Debugging WebSocket Issues
1. **Check Browser Console**: Look for connection errors
2. **Check Server Logs**: Uvicorn logs WebSocket events
3. **Test Direct Connection**: Bypass proxy if deployed
4. **Verify Port Binding**: `lsof -i :12656`
5. **Check Firewall**: Ensure port is open

## Performance Considerations

### Concurrent Sessions
- **Current**: Supports multiple simultaneous research sessions
- **Bottleneck**: CPU-bound research, not dashboard
- **Scaling**: Dashboard itself is lightweight, scale multi-agent system

### File System Performance
- **Listing Sessions**: O(n) scan of outputs directory
- **Optimization**: Consider caching session list for large deployments
- **Large Files**: Enhanced file manager streams in chunks

### WebSocket Scalability
- **Current**: In-memory connection tracking
- **Limit**: ~1000 concurrent WebSocket connections per instance
- **Scaling**: Use Redis pub/sub for multi-instance deployments

### Memory Usage
- **Dashboard**: ~50 MB baseline
- **Per Session**: ~10 MB (connection + buffers)
- **Large Downloads**: Streaming prevents memory spikes

## Common Issues and Solutions

### Issue: WebSocket 404 via Caddy Proxy
**Status**: Known issue, under investigation
**Symptoms**: WebSocket connections fail with 404 when accessing via https://tk9.thinhkhuat.com
**Workaround**: Direct access to http://192.168.2.22:12656 works correctly
**Root Cause**: Caddy WebSocket upgrade configuration issue

**Current Caddy Config**:
```caddy
tk9.thinhkhuat.com {
    encode gzip

    @websockets {
        header Connection *Upgrade*
        header Upgrade websocket
    }

    reverse_proxy @websockets 192.168.2.22:12656
    reverse_proxy 192.168.2.22:12656 {
        header_up Host {host}
        header_up X-Real-IP {remote}
    }
}
```

**Investigation**: WebSocket route may need explicit path matching

### Issue: Session Not Found
**Cause**: Research hasn't started writing files yet
**Solution**: Add delay before checking session status
**Frontend**: Poll every 5 seconds until files appear

### Issue: Slow File Listing
**Cause**: Large number of research sessions (100+)
**Solution**: Implement pagination or caching
**TODO**: Add session list caching

### Issue: Process Zombie
**Cause**: CLI subprocess not properly terminated
**Solution**: Ensure cleanup in exception handlers
**Pattern**:
```python
try:
    await process.wait()
finally:
    if process.returncode is None:
        process.terminate()
        await asyncio.wait_for(process.wait(), timeout=5.0)
```

## Production Deployment

### System Service Configuration
```ini
[Unit]
Description=TK9 Web Dashboard
After=network.target

[Service]
Type=simple
User=tk9
WorkingDirectory=/home/tk9/tk9_source_deploy/web_dashboard
ExecStart=/home/tk9/tk9_source_deploy/web_dashboard/start_dashboard.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Monitoring
- **Health Check**: `GET /` should return 200
- **Metrics**: Log analysis for error rates
- **WebSocket**: Monitor connection count
- **Disk Space**: Watch outputs directory growth

### Backup Strategy
- **Research Outputs**: Regular backup of `/outputs/`
- **Configuration**: Version control for code
- **Sessions**: Consider retention policy (delete old sessions)

## Cross-References

### Related Documentation
- **[Multi-Agent System](/multi_agents/CONTEXT.md)** - Backend research execution
- **[CLI Interface](/cli/CONTEXT.md)** - Command-line invocation patterns
- **[Project Structure](/docs/ai-context/project-structure.md)** - Overall architecture

### Key Files
- `web_dashboard/main.py:1-150` - FastAPI application setup and main endpoints
- `web_dashboard/cli_executor.py:1-100` - Subprocess execution and streaming
- `web_dashboard/websocket_handler.py:1-133` - WebSocket connection management
- `web_dashboard/file_manager.py:1-276` - Basic file operations
- `web_dashboard/file_manager_enhanced.py:1-480` - Advanced file handling
- `web_dashboard/templates/index.html` - Frontend dashboard UI
- `web_dashboard/static/js/dashboard.js` - WebSocket client and interactivity

### External Dependencies
- **FastAPI 0.116.0+** - Web framework
- **Uvicorn 0.25.0+** - ASGI server
- **WebSockets** - Real-time protocol
- **Jinja2** - HTML templating
- **Tailwind CSS** - Frontend styling (CDN)

---

*This component context provides architectural guidance for the Web Dashboard. For deployment instructions, see `/DEPLOYMENT.md`. For troubleshooting, see `/docs/MULTI_AGENT_TROUBLESHOOTING.md`.*

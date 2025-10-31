# Deep Research MCP Web Dashboard

A simple web interface that serves as a proxy to the existing CLI system, allowing remote users to submit research queries and download results.

## Features

- **Simple Web Interface**: Clean, user-friendly dashboard for research submission
- **Real-time Log Streaming**: Watch the multi-agent research process in real-time via WebSocket
- **File Downloads**: Automatic detection and serving of the 6 output files (PDF, DOCX, MD in both English and Vietnamese)
- **No Code Changes**: Completely separate from existing codebase - uses CLI as-is
- **Session Management**: Track multiple concurrent research sessions
- **Error Handling**: Graceful error handling and recovery

## Architecture

```
web_dashboard/
├── main.py                      # FastAPI server
├── models.py                    # Pydantic models  
├── cli_executor.py              # CLI command execution
├── websocket_handler.py         # WebSocket streaming
├── file_manager.py              # File management
├── requirements.txt             # Dependencies
├── static/
│   ├── css/dashboard.css        # Styling
│   ├── js/dashboard.js          # Main frontend logic
│   ├── js/websocket-client.js   # WebSocket client
│   └── downloads/               # Temporary downloads
└── templates/
    └── index.html               # Dashboard UI
```

## Installation

1. **Install dependencies**:
   ```bash
   cd web_dashboard
   pip install -r requirements.txt
   ```

2. **Ensure main project works**:
   ```bash
   cd ..
   python main.py --help  # Should work without errors
   ```

## Running the Dashboard

1. **Start the web server**:
   ```bash
   cd web_dashboard
   python main.py
   ```

2. **Access the dashboard**:
   - Open your browser to: http://localhost:12656
   - The dashboard will be ready to use

## How It Works

### User Workflow
1. User opens the web dashboard
2. User enters research subject in the text field
3. User selects output language (default: Vietnamese)
4. User clicks "Start Research"
5. Dashboard streams real-time CLI logs via WebSocket
6. When complete, 6 files are available for download:
   - `research_report.pdf`
   - `research_report.docx`
   - `research_report.md`
   - `research_report_vi.pdf` (Vietnamese)
   - `research_report_vi.docx` (Vietnamese)
   - `research_report_vi.md` (Vietnamese)

### Technical Flow
1. **POST /api/research** - Submit research request
2. **WebSocket /ws/{session_id}** - Real-time log streaming
3. **CLI Execution** - Runs: `uv run python -m main -r "SUBJECT" -l vi --save-files`
4. **File Detection** - Monitors `./outputs/` for completion
5. **File Serving** - Makes files available at `/download/{session_id}/{filename}`

## API Endpoints

- `GET /` - Dashboard HTML interface
- `POST /api/research` - Submit research request
- `GET /api/session/{session_id}` - Get session status
- `WebSocket /ws/{session_id}` - Real-time log streaming
- `GET /download/{session_id}/{filename}` - Download output files
- `GET /api/health` - Health check

## Configuration

The dashboard automatically detects the project root and uses the existing CLI system. No configuration required.

### Environment Variables (Optional)
- `WEB_DASHBOARD_HOST` - Host to bind to (default: 0.0.0.0)
- `WEB_DASHBOARD_PORT` - Port to bind to (default: 12656)
- `MAX_FILE_AGE_HOURS` - Auto-cleanup age (default: 24 hours)

## Security

- **Input Sanitization**: Research subjects are sanitized to prevent command injection
- **File Validation**: Only expected output files can be downloaded
- **Session Isolation**: Each session has isolated download directory
- **Auto Cleanup**: Old files are automatically cleaned up after 24 hours

## Development

### Running in Development Mode
```bash
cd web_dashboard
python main.py
# Server will auto-reload on file changes
```

### Testing the Complete Workflow
1. Start the dashboard: `python main.py`
2. Open http://localhost:12656
3. Enter a simple research topic like "artificial intelligence"
4. Watch the real-time logs
5. Download the generated files when complete

### Troubleshooting

**Dashboard won't start:**
- Check that port 12656 is available
- Ensure all dependencies are installed
- Check project root path is correct

**Research fails:**
- Verify the main CLI works: `cd .. && python main.py --help`
- Check API keys are configured in main project
- Review logs in the web dashboard

**Files not appearing:**
- Check `./outputs/` directory exists and has files
- Verify file permissions
- Check dashboard logs for file detection issues

## Production Deployment

### Using Docker
```bash
# Build image
docker build -t deep-research-dashboard .

# Run container
docker run -p 12656:12656 -v $(pwd)/..:/app/project deep-research-dashboard
```

### Using systemd
Create `/etc/systemd/system/research-dashboard.service`:
```ini
[Unit]
Description=Deep Research Dashboard
After=network.target

[Service]
Type=simple
User=research
WorkingDirectory=/path/to/deep-research-mcp-og/web_dashboard
ExecStart=/path/to/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### Nginx Reverse Proxy
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:12656;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

## Monitoring

The dashboard provides several monitoring endpoints:

- `/api/health` - Basic health check
- WebSocket connection count in health response
- Active session tracking
- Automatic cleanup reporting

## Limitations

- **Concurrent Sessions**: Limited by system resources (recommended: 5-10 concurrent)
- **File Storage**: Files are temporarily stored in `static/downloads/`
- **Session Persistence**: Sessions don't persist across server restarts
- **Authentication**: No built-in authentication (add reverse proxy auth if needed)

## Contributing

The web dashboard is designed to be completely independent of the main codebase. To add features:

1. Keep all changes within the `web_dashboard/` directory
2. Don't modify any existing project files
3. Test with the existing CLI to ensure compatibility
4. Follow the existing code patterns for consistency
# TK9 V2 Dashboard Startup Script

## Overview

The `start_v2_dashboard.sh` script is a comprehensive, production-ready launcher for the TK9 Deep Research MCP Dashboard V2, managing both the backend (FastAPI) and frontend (Vue/Vite) simultaneously with a single command.

## Features

### ✅ Automatic Dependency Management
- **Python Dependencies**: Detects missing Python packages and offers automatic installation
- **Node.js Dependencies**: Checks for frontend dependencies and installs if needed
- **Version Detection**: Automatically finds suitable Python version (3.12, 3.11, 3.10, 3)

### ✅ Interactive Environment Configuration
- **Smart Detection**: Loads existing `.env` file if available
- **Missing Variables**: Prompts interactively for any missing required environment variables
- **Secure Input**: Hides sensitive values (API keys, secrets) during input
- **Auto-Save**: Option to save configuration to `.env` file for future use
- **Validation**: Ensures all required variables are configured before starting

### ✅ Graceful Shutdown
- **Single Command**: Press `Ctrl+C` once to stop both backend and frontend
- **Signal Handling**: Properly handles SIGTERM, SIGINT, and SIGKILL
- **Process Cleanup**: Waits up to 5 seconds for graceful shutdown, then force-kills if needed
- **No Zombies**: Guaranteed cleanup of all child processes

### ✅ Process Isolation
- **TK9 Only**: Only manages processes started by this script
- **Port Protection**: Detects if TK9 processes are using required ports
- **Safe Kill**: Only kills TK9-related processes (main.py, vite)
- **External Safety**: Never touches unrelated system processes

### ✅ Robust Error Handling
- **Directory Validation**: Checks for required files and directories before starting
- **Port Conflicts**: Detects and resolves port conflicts intelligently
- **Health Checks**: Waits for services to be ready with timeout protection
- **Process Monitoring**: Continuously monitors both services and restarts on failure

### ✅ Clear Terminal Output
- **Color-Coded**: Success (green), errors (red), warnings (yellow), info (cyan)
- **Sectioned**: Organized output with clear headers and sections
- **Progress Indicators**: Step-by-step feedback during startup
- **Access Info**: Clear display of all access URLs and process IDs

## Usage

### Basic Usage

```bash
cd /path/to/tk9_source_deploy/web_dashboard
./start_v2_dashboard.sh
```

### First-Time Setup

On first run, the script will:

1. **Check Dependencies**
   - Detect Python installation
   - Check for required Python packages
   - Verify Node.js and npm
   - Check for frontend dependencies

2. **Prompt for Installation**
   ```
   Install missing Python packages? [Y/n]: Y
   Install frontend dependencies? [Y/n]: Y
   ```

3. **Configure Environment**
   ```
   Configure: Supabase Project URL
   Enter SUPABASE_URL [default: https://your-project.supabase.co]:

   Configure: Supabase Service Role Key
   Enter SUPABASE_SERVICE_KEY: ********

   Save configuration to .env file? [Y/n]: Y
   ```

4. **Start Services**
   - Backend starts on port 12656
   - Frontend starts on port 5173
   - Both services health-checked before reporting ready

### Subsequent Runs

After initial setup, the script will:
- Load existing `.env` configuration
- Skip dependency installation if already satisfied
- Start both services immediately

### Stopping the Dashboard

**Method 1: Graceful Shutdown (Recommended)**
```bash
Press Ctrl+C
```

The script will:
- Send SIGTERM to both processes
- Wait up to 5 seconds for graceful shutdown
- Force-kill if processes don't terminate
- Display shutdown status

**Method 2: Kill Script (Not Recommended)**
```bash
# From another terminal
pkill -f start_v2_dashboard.sh
```

Note: This will still trigger cleanup handlers.

## Required Environment Variables

The script requires the following environment variables to be configured:

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `SUPABASE_URL` | Supabase project URL | Yes | `https://xyz.supabase.co` |
| `SUPABASE_SERVICE_KEY` | Supabase service role key | Yes | `eyJhbG...` |
| `SUPABASE_ANON_KEY` | Supabase anonymous key | Yes | `eyJhbG...` |
| `JWT_SECRET` | JWT secret for token validation | Yes | `your-jwt-secret` |
| `HOST` | Server host binding | No (default: 0.0.0.0) | `0.0.0.0` |
| `PORT` | Backend server port | No (default: 12656) | `12656` |
| `CORS_ORIGINS` | Allowed CORS origins | No (auto-configured) | `http://localhost:5173` |

### Getting Supabase Credentials

1. Go to [Supabase Dashboard](https://app.supabase.com)
2. Select your project
3. Navigate to **Settings** → **API**
4. Copy the following:
   - **Project URL** → `SUPABASE_URL`
   - **anon public** key → `SUPABASE_ANON_KEY`
   - **service_role** key → `SUPABASE_SERVICE_KEY`
5. Navigate to **Settings** → **API** → **JWT Secret**
   - Copy **JWT Secret** → `JWT_SECRET`

## Access URLs

Once running, the dashboard is accessible via:

### Local Access
- **Frontend**: http://localhost:5173
- **Backend**: http://localhost:12656
- **API Docs**: http://localhost:12656/docs

### Network Access
- **Internal Network**: http://192.168.2.22:12656
- **Public (via Caddy)**: https://tk9.thinhkhuat.com

## Troubleshooting

### Port Already in Use

**Error**: `Port 12656 is already in use by PID 12345`

**Solution**: The script will detect if the process is TK9-related and offer to kill it:
```
Kill existing backend process? [Y/n]: Y
```

If not TK9-related, manually kill the process:
```bash
lsof -ti:12656 | xargs kill -9
```

### Backend/Frontend Won't Start

**Check 1: Dependencies Installed**
```bash
# Python dependencies
python3 -m pip install -r requirements.txt

# Frontend dependencies
cd frontend_poc && npm install
```

**Check 2: Environment Variables**
```bash
# Check if .env exists and is valid
cat .env

# Manually test backend
python3 main.py
```

**Check 3: Logs**
The script redirects output to `/dev/null` for cleaner display. To see full logs:

Edit script temporarily and remove `> /dev/null 2>&1` from:
- Line ~458: `$python_cmd "$BACKEND_MAIN" > /dev/null 2>&1 &`
- Line ~493: `npm run dev > /dev/null 2>&1 &`

### Process Monitoring

To manually check if processes are running:

```bash
# Check backend
curl http://localhost:12656/health

# Check frontend
curl http://localhost:5173

# View process info
ps aux | grep main.py
ps aux | grep vite
```

### Environment Variable Issues

**Missing Required Variables**: The script will prompt interactively

**Invalid Values**: Check `.env` file for placeholder values like:
- `your-project.supabase.co`
- `your_service_role_key_here`

These indicate the variable needs to be configured.

### Cleanup Stuck Processes

If cleanup fails and processes are orphaned:

```bash
# Kill all TK9 backend processes
pkill -f "python.*main.py"

# Kill all Vite processes
pkill -f "vite"

# Nuclear option: kill by port
lsof -ti:12656 | xargs kill -9
lsof -ti:5173 | xargs kill -9
```

## Architecture

### Script Flow

```
┌─────────────────────────────────────────────────────────┐
│                    Script Startup                       │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│  1. Validate Directory Structure                        │
│     ✓ Check main.py exists                              │
│     ✓ Check frontend_poc/ exists                        │
│     ✓ Check package.json exists                         │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│  2. Detect Python Installation                          │
│     → Try: python3.12, python3.11, python3.10, python3  │
│     → Select first available                            │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│  3. Check Python Dependencies                           │
│     → Check: fastapi, uvicorn, websockets, pydantic     │
│     → Prompt to install if missing                      │
│     → Run: pip install -r requirements.txt              │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│  4. Check Node.js Dependencies                          │
│     → Verify Node.js & npm installed                    │
│     → Check if node_modules/ exists                     │
│     → Prompt to install if missing                      │
│     → Run: npm install                                  │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│  5. Configure Environment                               │
│     → Load existing .env file (if exists)               │
│     → Check required variables:                         │
│       • SUPABASE_URL                                    │
│       • SUPABASE_SERVICE_KEY                            │
│       • SUPABASE_ANON_KEY                               │
│       • JWT_SECRET                                      │
│     → Prompt for missing variables                      │
│     → Offer to save to .env file                        │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│  6. Start Backend Server                                │
│     → Check port 12656 available                        │
│     → Start: python main.py &                           │
│     → Wait for health check (30s timeout)               │
│     → Store PID for cleanup                             │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│  7. Start Frontend Server                               │
│     → Check port 5173 available                         │
│     → Start: npm run dev &                              │
│     → Wait for server ready (30s timeout)               │
│     → Store PID for cleanup                             │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│  8. Display Access Information                          │
│     → Show all access URLs                              │
│     → Display process IDs                               │
│     → Show shutdown instructions                        │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│  9. Monitor Processes (Loop)                            │
│     → Check backend alive every 5s                      │
│     → Check frontend alive every 5s                     │
│     → Exit if either dies                               │
│     → Wait for Ctrl+C signal                            │
└─────────────────────────────────────────────────────────┘
                           ↓
                      [Ctrl+C Press]
                           ↓
┌─────────────────────────────────────────────────────────┐
│  10. Cleanup & Graceful Shutdown                        │
│      → Send SIGTERM to frontend                         │
│      → Wait 5s for graceful shutdown                    │
│      → Force kill if needed (SIGKILL)                   │
│      → Send SIGTERM to backend                          │
│      → Wait 5s for graceful shutdown                    │
│      → Force kill if needed (SIGKILL)                   │
│      → Display shutdown status                          │
│      → Exit script                                      │
└─────────────────────────────────────────────────────────┘
```

### Signal Handling

The script registers cleanup handlers for:
- **EXIT**: Normal script termination
- **SIGINT**: Ctrl+C interrupt
- **SIGTERM**: Termination signal
- **SIGKILL**: Force kill signal

All handlers call the same `cleanup()` function, which:
1. Checks if cleanup already done (prevents double-cleanup)
2. Kills frontend process gracefully (SIGTERM)
3. Waits 5 seconds for graceful shutdown
4. Force kills if still running (SIGKILL)
5. Repeats for backend process
6. Displays status messages

### Process Tracking

The script maintains global variables:
- `BACKEND_PID`: Process ID of backend (FastAPI/Uvicorn)
- `FRONTEND_PID`: Process ID of frontend (Vite dev server)
- `CLEANUP_DONE`: Boolean flag to prevent double-cleanup

These are used for:
- Process health monitoring
- Graceful shutdown
- Cleanup validation

## Comparison with V1 Script

| Feature | V1 (start_dashboard.sh) | V2 (start_v2_dashboard.sh) |
|---------|------------------------|----------------------------|
| Manages Backend | ✅ Yes | ✅ Yes |
| Manages Frontend | ❌ No | ✅ Yes |
| Auto Dependency Install | ❌ Manual | ✅ Automatic |
| Environment Config | ❌ Manual | ✅ Interactive Prompts |
| Graceful Shutdown | ⚠️ Basic | ✅ Full Signal Handling |
| Process Monitoring | ❌ No | ✅ Continuous |
| Port Conflict Resolution | ❌ No | ✅ Intelligent Detection |
| Color-Coded Output | ⚠️ Minimal | ✅ Full Color Coding |
| Health Checks | ⚠️ CLI only | ✅ HTTP Health Endpoints |
| Single Ctrl+C Shutdown | ❌ No | ✅ Yes |
| Process Isolation | ⚠️ Manual | ✅ Automatic (TK9 only) |

## Advanced Usage

### Silent Mode (Non-Interactive)

For automated environments, pre-configure `.env` file:

```bash
# Create .env with all required variables
cat > web_dashboard/.env << 'EOF'
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_service_role_key
SUPABASE_ANON_KEY=your_anon_key
JWT_SECRET=your_jwt_secret
EOF

# Run script (will not prompt)
./start_v2_dashboard.sh
```

### Custom Ports

Override default ports via environment variables:

```bash
# Backend on port 8000, frontend on port 3000
PORT=8000 VITE_PORT=3000 ./start_v2_dashboard.sh
```

Note: Frontend port requires modifying `vite.config.ts`:

```typescript
export default defineConfig({
  server: {
    port: parseInt(process.env.VITE_PORT || '5173')
  }
})
```

### Background Execution

Run dashboard in background with nohup:

```bash
nohup ./start_v2_dashboard.sh > dashboard.log 2>&1 &
```

Stop later:

```bash
pkill -f start_v2_dashboard.sh
```

### Systemd Service

For production, create a systemd service:

```ini
# /etc/systemd/system/tk9-dashboard.service
[Unit]
Description=TK9 Deep Research Dashboard V2
After=network.target

[Service]
Type=simple
User=tk9user
WorkingDirectory=/path/to/tk9_source_deploy/web_dashboard
ExecStart=/path/to/tk9_source_deploy/web_dashboard/start_v2_dashboard.sh
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable tk9-dashboard
sudo systemctl start tk9-dashboard
sudo systemctl status tk9-dashboard
```

## Contributing

When improving the script:

1. **Maintain Color Coding**: Use defined color variables
2. **Add Error Handling**: Check return codes, handle failures gracefully
3. **Update Documentation**: Keep this README synchronized
4. **Test Thoroughly**: Test all code paths (success, failure, edge cases)
5. **Preserve Safety**: Never modify external processes

## License

Part of TK9 Deep Research MCP Server project.
© 2025 TK9 Team. All rights reserved.

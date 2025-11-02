# TK9 V2 Dashboard - Production Deployment Guide

## Overview

The `start_v2_dashboard.sh` script is a **production-optimized** launcher for the TK9 Deep Research MCP Dashboard V2, designed for reliable deployment with automatic dependency management, production logging, and graceful shutdown.

## Production Ports

- **Backend (FastAPI)**: Port `12689`
- **Frontend (Vue/Vite)**: Port `8592`

## Production Features

### ✅ Optimized for Production

1. **Production Build**
   - Frontend served via Vite preview (optimized production build)
   - Automatic build if `dist/` not found
   - Minified, tree-shaken bundles

2. **Non-Interactive Mode**
   - No user prompts (requires `.env` file)
   - Auto-installs missing dependencies
   - Fails fast if environment not configured

3. **Production Logging**
   - All output logged to timestamped files
   - Separate logs for backend and frontend
   - Log rotation via timestamps
   - Location: `web_dashboard/logs/`

4. **Graceful Shutdown**
   - Single `Ctrl+C` stops both services
   - 5-second graceful shutdown period
   - Automatic cleanup of processes
   - Force-kill as fallback

5. **Health Monitoring**
   - HTTP health checks on startup
   - Continuous process monitoring
   - Auto-restart on failure (planned)
   - Clear status reporting

6. **Security**
   - Sensitive values hidden in output
   - Process isolation (TK9 only)
   - Environment validation
   - Port conflict resolution

## Quick Start

### 1. Prerequisites

Ensure you have:
- Python 3.10+ (3.12 recommended)
- Node.js 18+
- npm or pnpm
- Properly configured `.env` file

### 2. Environment Configuration

Create or verify `web_dashboard/.env`:

```bash
# Required for production
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_service_role_key_here
SUPABASE_ANON_KEY=your_anon_key_here
JWT_SECRET=your_jwt_secret_here

# Server configuration (auto-configured)
HOST=0.0.0.0
PORT=12689

# CORS origins (auto-configured for production)
CORS_ORIGINS=http://localhost:8592,http://192.168.2.22:8592,https://tk9v2.thinhkhuat.com
```

**Important**: Do not use placeholder values like `your-project.supabase.co` or `your_*_here`. The script will reject these in production mode.

### 3. Start Production Dashboard

```bash
cd /path/to/tk9_source_deploy/web_dashboard
./start_v2_dashboard.sh
```

### 4. Verify Deployment

The script will output:

```
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║    🚀 TK9 Deep Research MCP - V2 Dashboard [PRODUCTION]       ║
║                                                                ║
║    Backend Port: 12689  │  Frontend Port: 8592                ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝

✓ Dashboard is now running in PRODUCTION mode!

Frontend Access (Port 8592):
  Local:     http://localhost:8592
  Internal:  http://192.168.2.22:8592
  Public:    https://tk9v2.thinhkhuat.com

Backend Access (Port 12689):
  Local:     http://localhost:12689
  Internal:  http://192.168.2.22:12689
  API Docs:  http://localhost:12689/docs
  Health:    http://localhost:12689/health

Production Configuration:
  Mode:         PRODUCTION
  Backend PID:  12345
  Frontend PID: 12346
  Backend Log:  /path/to/logs/backend_20251102_223000.log
  Frontend Log: /path/to/logs/frontend_20251102_223000.log

Monitoring:
  Backend:   tail -f /path/to/logs/backend_20251102_223000.log
  Frontend:  tail -f /path/to/logs/frontend_20251102_223000.log
  All Logs:   tail -f /path/to/logs/*.log

⚠  Press Ctrl+C to stop all services gracefully
```

## Production Deployment Workflow

### First-Time Deployment

```bash
# 1. Clone/update repository
cd /path/to/tk9_source_deploy
git pull origin main

# 2. Configure environment
cd web_dashboard
cp .env.example .env
# Edit .env with production values

# 3. Run startup script (will auto-install dependencies)
./start_v2_dashboard.sh
```

The script will automatically:
- ✅ Detect Python 3.12/3.11/3.10
- ✅ Install missing Python packages
- ✅ Install missing Node.js packages
- ✅ Build frontend for production
- ✅ Start backend on port 12689
- ✅ Start frontend on port 8592
- ✅ Perform health checks
- ✅ Display access information

### Subsequent Deployments

```bash
cd /path/to/tk9_source_deploy/web_dashboard
./start_v2_dashboard.sh
```

The script will:
- ✅ Skip dependency installation (if satisfied)
- ✅ Use existing production build (if available)
- ✅ Start both services immediately

### Updating Code

```bash
# 1. Stop running dashboard
# Press Ctrl+C in the terminal running the script

# 2. Update code
git pull origin main

# 3. Rebuild frontend (if frontend changed)
cd frontend_poc
npm run build

# 4. Restart dashboard
cd ..
./start_v2_dashboard.sh
```

## Production Operations

### Monitoring Logs

**Real-time monitoring**:
```bash
# Backend logs
tail -f web_dashboard/logs/backend_*.log

# Frontend logs
tail -f web_dashboard/logs/frontend_*.log

# All logs
tail -f web_dashboard/logs/*.log
```

**Search logs**:
```bash
# Find errors in backend
grep -i "error" web_dashboard/logs/backend_*.log

# Find specific request
grep "POST /api/research" web_dashboard/logs/backend_*.log

# Last 100 lines
tail -100 web_dashboard/logs/backend_*.log
```

### Health Checks

**Backend health**:
```bash
curl http://localhost:12689/health
# Expected: {"status": "healthy"}
```

**Frontend health**:
```bash
curl -I http://localhost:8592
# Expected: HTTP/1.1 200 OK
```

**Process status**:
```bash
# Check if processes are running
ps aux | grep "main.py"
ps aux | grep "vite"

# Check port usage
lsof -i :12689
lsof -i :8592
```

### Stopping the Dashboard

**Graceful shutdown** (recommended):
```bash
# In the terminal running the script
Press Ctrl+C
```

**From another terminal**:
```bash
# Kill the script (will trigger cleanup)
pkill -f start_v2_dashboard.sh

# Or kill processes directly
pkill -f "python.*main.py"
pkill -f "vite.*preview"
```

### Restarting Services

**Full restart**:
```bash
# Stop
Press Ctrl+C

# Start
./start_v2_dashboard.sh
```

**Rebuild frontend only**:
```bash
cd frontend_poc
npm run build
cd ..
# No need to restart if backend is still running
```

## Production Best Practices

### 1. Environment Management

- ✅ **Never commit** `.env` file to git
- ✅ Use `.env.example` as template
- ✅ Rotate secrets regularly
- ✅ Use different `.env` for dev/staging/prod
- ✅ Backup `.env` file securely

### 2. Log Management

```bash
# Archive old logs (weekly)
cd web_dashboard/logs
tar -czf logs_$(date +%Y%m%d).tar.gz *.log
rm *.log

# Or use logrotate (recommended)
# Create /etc/logrotate.d/tk9-dashboard
```

### 3. Process Management

**Using systemd** (recommended for production):

Create `/etc/systemd/system/tk9-dashboard-v2.service`:

```ini
[Unit]
Description=TK9 Deep Research Dashboard V2 (Production)
After=network.target

[Service]
Type=simple
User=tk9user
WorkingDirectory=/path/to/tk9_source_deploy/web_dashboard
ExecStart=/path/to/tk9_source_deploy/web_dashboard/start_v2_dashboard.sh
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable tk9-dashboard-v2
sudo systemctl start tk9-dashboard-v2
sudo systemctl status tk9-dashboard-v2
```

Manage service:
```bash
# View logs
sudo journalctl -u tk9-dashboard-v2 -f

# Restart
sudo systemctl restart tk9-dashboard-v2

# Stop
sudo systemctl stop tk9-dashboard-v2
```

### 4. Reverse Proxy Configuration

**Caddy** (recommended):

Add to `/etc/caddy/Caddyfile`:

```caddy
tk9v2.thinhkhuat.com {
    # Frontend
    reverse_proxy localhost:8592

    # Enable gzip compression
    encode gzip

    # Security headers
    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains"
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
        Referrer-Policy "strict-origin-when-cross-origin"
    }

    # WebSocket support
    @websocket {
        header Connection *Upgrade*
        header Upgrade websocket
    }
    reverse_proxy @websocket localhost:8592
}

api-tk9v2.thinhkhuat.com {
    # Backend API
    reverse_proxy localhost:12689

    # Enable gzip
    encode gzip

    # CORS headers (if needed)
    header Access-Control-Allow-Origin "https://tk9v2.thinhkhuat.com"
}
```

Reload Caddy:
```bash
sudo systemctl reload caddy
```

**Nginx** (alternative):

```nginx
# Frontend
server {
    listen 80;
    server_name tk9v2.thinhkhuat.com;

    location / {
        proxy_pass http://localhost:8592;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}

# Backend
server {
    listen 80;
    server_name api-tk9v2.thinhkhuat.com;

    location / {
        proxy_pass http://localhost:12689;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 5. Monitoring & Alerting

**Simple monitoring script**:

Create `monitor_dashboard.sh`:

```bash
#!/bin/bash

# Check backend health
if ! curl -sf http://localhost:12689/health > /dev/null; then
    echo "ALERT: Backend is down!" | mail -s "TK9 Dashboard Alert" admin@example.com
fi

# Check frontend
if ! curl -sf http://localhost:8592 > /dev/null; then
    echo "ALERT: Frontend is down!" | mail -s "TK9 Dashboard Alert" admin@example.com
fi
```

Add to crontab:
```bash
# Check every 5 minutes
*/5 * * * * /path/to/monitor_dashboard.sh
```

## Troubleshooting

### Issue: Port Already in Use

**Error**: `Port 12689 is already in use by PID 12345`

**Solution**:
```bash
# Check what's using the port
lsof -i :12689

# If it's an old TK9 process, script will offer to kill it
# Otherwise, kill manually:
kill -9 $(lsof -ti:12689)
```

### Issue: Environment Variables Missing

**Error**: `PRODUCTION ERROR: 4 required environment variable(s) missing`

**Solution**:
```bash
# Check .env file exists
ls -la web_dashboard/.env

# Verify values are not placeholders
cat web_dashboard/.env | grep -E "SUPABASE_URL|SUPABASE_SERVICE_KEY"

# If placeholders found, update with real values
nano web_dashboard/.env
```

### Issue: Frontend Build Fails

**Error**: `Frontend build failed`

**Solution**:
```bash
# Check frontend log
tail -f web_dashboard/logs/frontend_*.log

# Try manual build
cd web_dashboard/frontend_poc
npm run build

# If TypeScript errors, check:
npm run typecheck

# If dependency issues:
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Issue: Backend Won't Start

**Error**: `Backend process died unexpectedly`

**Solution**:
```bash
# Check backend log
tail -f web_dashboard/logs/backend_*.log

# Common issues:
# 1. Python dependencies missing
pip install -r web_dashboard/requirements.txt

# 2. Port conflict
lsof -ti:12689 | xargs kill -9

# 3. Database connection issues
# Verify SUPABASE_* variables in .env

# Try manual start
cd web_dashboard
python3 main.py
```

### Issue: Processes Won't Stop

**Error**: Ctrl+C doesn't stop services

**Solution**:
```bash
# Force kill all TK9 processes
pkill -9 -f "python.*main.py"
pkill -9 -f "vite.*preview"

# Or by port
lsof -ti:12689 | xargs kill -9
lsof -ti:8592 | xargs kill -9
```

### Issue: High Memory/CPU Usage

**Check resource usage**:
```bash
# Process stats
ps aux | grep -E "main.py|vite" | grep -v grep

# Detailed monitoring
top -p $(pgrep -f "main.py")
```

**Solutions**:
- Check logs for infinite loops or errors
- Restart services
- Consider increasing system resources
- Check for memory leaks in application code

## Security Considerations

### 1. Network Security

- ✅ Use HTTPS in production (via Caddy/Nginx)
- ✅ Enable firewall rules
- ✅ Restrict internal ports (12689, 8592) to localhost
- ✅ Only expose via reverse proxy

### 2. Environment Variables

- ✅ Never commit `.env` to git
- ✅ Use strong JWT secrets (32+ characters)
- ✅ Rotate Supabase keys regularly
- ✅ Restrict service role key usage

### 3. Process Isolation

- ✅ Run as non-root user
- ✅ Use systemd for process management
- ✅ Set resource limits (memory, CPU)
- ✅ Enable AppArmor/SELinux profiles

### 4. Logging

- ✅ Don't log sensitive data (passwords, keys)
- ✅ Rotate logs regularly
- ✅ Monitor for suspicious activity
- ✅ Set appropriate file permissions (640)

## Performance Optimization

### 1. Frontend

```bash
# Enable Vite build optimizations (vite.config.ts)
export default defineConfig({
  build: {
    minify: 'terser',
    rollupOptions: {
      output: {
        manualChunks: {
          'vue-vendor': ['vue', 'vue-router', 'pinia'],
          'ui-vendor': ['vue-toastification'],
        }
      }
    }
  }
})
```

### 2. Backend

```python
# Use production ASGI server (uvicorn with workers)
# In main.py:
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=12689,
        workers=4,  # Use CPU count
        log_level="info",
        access_log=False  # Disable for performance
    )
```

### 3. Caching

Configure Caddy/Nginx caching for static assets:

```caddy
tk9v2.thinhkhuat.com {
    @static {
        path *.js *.css *.png *.jpg *.jpeg *.gif *.ico *.woff *.woff2
    }
    header @static Cache-Control "public, max-age=31536000, immutable"

    reverse_proxy localhost:8592
}
```

## Maintenance

### Daily
- ✅ Check logs for errors
- ✅ Monitor disk space
- ✅ Verify health endpoints

### Weekly
- ✅ Archive old logs
- ✅ Review security alerts
- ✅ Check for dependency updates

### Monthly
- ✅ Update dependencies
- ✅ Rotate secrets/keys
- ✅ Review performance metrics
- ✅ Test backup/restore procedures

## Support

For issues:
1. Check this guide
2. Review logs (`tail -f logs/*.log`)
3. Test manually (`python3 main.py`, `npm run build`)
4. Check GitHub issues
5. Contact TK9 team

## Version History

- **v2.0-PRODUCTION** (2025-11-02): Production-optimized release
  - Ports: 12689 (backend), 8592 (frontend)
  - Non-interactive environment configuration
  - Production logging and monitoring
  - Graceful shutdown handling
  - Automatic dependency management

---

© 2025 TK9 Deep Research Team. All rights reserved.

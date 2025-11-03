# TK9 Deep Research MCP - Docker Deployment Guide (Dual Service)

**Version**: v2.0.0
**Last Updated**: 2025-11-03
**Status**: ✅ Production Ready
**Architecture**: Dual-service (FastAPI Backend + Vue 3 Frontend)

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Prerequisites](#prerequisites)
- [Quick Deploy (5 Minutes)](#quick-deploy-5-minutes)
- [Manual Deployment (Step-by-Step)](#manual-deployment-step-by-step)
- [Environment Variables](#environment-variables)
- [Service Details](#service-details)
- [Development vs Production](#development-vs-production)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)
- [Monitoring and Maintenance](#monitoring-and-maintenance)
- [Backup and Recovery](#backup-and-recovery)
- [Scaling Considerations](#scaling-considerations)

---

## Architecture Overview

### System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Internet (HTTPS)                        │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ↓
┌──────────────────────────────────────────────────────────────────┐
│                      Caddy v2 (:443)                             │
│  • SSL/TLS Termination (Let's Encrypt)                           │
│  • Domain Routing (tk9v2.thinhkhuat.com)                         │
│  • WebSocket Upgrades                                            │
│  • HTTP/2 & Compression                                          │
└───────────────┬──────────────────────────────────────────────────┘
                │
                ├────────────────────┬─────────────────────────────┐
                │                    │                             │
                ↓                    ↓                             ↓
    ┌───────────────────┐ ┌──────────────────┐       ┌─────────────────────┐
    │   Route: /        │ │  Route: /api/*   │       │   Route: /ws/*      │
    └───────────────────┘ └──────────────────┘       └─────────────────────┘
                │                    │                             │
                ↓                    ↓                             │
    ┌────────────────────┐ ┌─────────────────────────────────────┴─────────┐
    │  tk9-frontend      │ │           tk9-backend                          │
    │  Port: 8592        │ │           Port: 12689                          │
    ├────────────────────┤ ├────────────────────────────────────────────────┤
    │ Vue 3 + Vite       │ │ FastAPI + LangGraph                            │
    │ TypeScript         │ │ 7-Agent Research Orchestration                 │
    │ Tailwind CSS       │ │ • searcher (BRAVE search)                      │
    │                    │ │ • planner (research planning)                  │
    │ nginx (internal)   │ │ • researcher (web scraping + analysis)         │
    │ • Static files     │ │ • writer (markdown generation)                 │
    │ • SPA routing      │ │ • publisher (output management)                │
    │                    │ │ • translator (50+ languages)                   │
    │ 512MB RAM          │ │ • orchestrator (coordination)                  │
    │ 1 CPU              │ │                                                │
    │ 200MB disk         │ │ 8GB RAM (limit), 2GB (reserved)                │
    └────────────────────┘ │ 4 CPUs (limit), 1 CPU (reserved)               │
                           │ 1.69GB disk (image)                            │
                           └────────────────────────────────────────────────┘
                                                │
                                                ↓
                           ┌────────────────────────────────────────┐
                           │       Shared Volumes                   │
                           ├────────────────────────────────────────┤
                           │ • ./outputs → /app/outputs (research)  │
                           │ • ./logs → /app/logs (application)     │
                           │ • ./data → /app/data (cache/temp)      │
                           │ • ./.env → /app/.env (config)          │
                           └────────────────────────────────────────┘
```

### Network Topology

- **Bridge Network**: `tk9-network` (Docker bridge driver)
- **Backend**: `192.168.2.22:12689` (internal) → `https://tk9v2.thinhkhuat.com/api/*` (external)
- **Frontend**: `192.168.2.22:8592` (internal) → `https://tk9v2.thinhkhuat.com/` (external)
- **WebSocket**: `192.168.2.22:12689` (internal) → `wss://tk9v2.thinhkhuat.com/ws/*` (external)

### Port Mappings

| Service         | Internal Port | External Port | Protocol    | Purpose                      |
|-----------------|---------------|---------------|-------------|------------------------------|
| Backend         | 12689         | 12689         | HTTP        | FastAPI REST API             |
| Backend WS      | 12689         | 12689         | WebSocket   | Real-time agent updates      |
| Frontend        | 8592          | 8592          | HTTP        | Vue 3 SPA                    |
| Caddy (public)  | 443           | 443           | HTTPS       | External SSL termination     |

---

## Prerequisites

### Required Software

```bash
# Docker Engine 20.10+
docker --version
# Expected: Docker version 20.10.0 or higher

# Docker Compose v2.0+
docker-compose --version
# Expected: Docker Compose version 2.0.0 or higher

# Git (for cloning repository)
git --version
```

### System Requirements

**Minimum**:
- 2 CPU cores
- 4GB RAM
- 10GB disk space
- Ubuntu 20.04+ / Debian 11+ / macOS 12+

**Recommended** (Production):
- 4+ CPU cores
- 8GB+ RAM
- 20GB+ disk space (for outputs and logs)
- SSD storage

### Required API Keys

You **must** have at least these API keys:

1. **GOOGLE_API_KEY** (Gemini) - Primary LLM provider
2. **BRAVE_API_KEY** (BRAVE Search) - Primary search provider

**Optional** (but recommended):
- `OPENAI_API_KEY` - Fallback LLM provider
- `TAVILY_API_KEY` - Fallback search provider
- `ANTHROPIC_API_KEY` - Alternative LLM provider

### Network Requirements

- **Outbound HTTPS** (443): For API calls to Google, BRAVE, OpenAI, etc.
- **Inbound HTTPS** (443): For public access (if using Caddy)
- **Internal Ports**: 12689 (backend), 8592 (frontend)

---

## Quick Deploy (5 Minutes)

### 1. Clone Repository

```bash
cd /Users/thinhkhuat/»DEV•local«
git clone <repo-url> tk9_source_deploy
cd tk9_source_deploy
```

### 2. Configure Environment

```bash
# Copy .env file (or create new one)
cp .env .env.backup  # Backup if exists

# Edit .env file
nano .env
```

**Required variables**:
```bash
# API Keys (REQUIRED)
GOOGLE_API_KEY=your_google_api_key_here
BRAVE_API_KEY=your_brave_api_key_here

# LLM Configuration
PRIMARY_LLM_PROVIDER=google_gemini
PRIMARY_LLM_MODEL=gemini-2.5-flash
LLM_STRATEGY=primary_only

# Search Configuration
PRIMARY_SEARCH_PROVIDER=brave
SEARCH_STRATEGY=primary_only

# Research Settings
RESEARCH_LANGUAGE=vi
SEARCH_COUNTRY=VN
```

### 3. Deploy Services

```bash
# Build and start services
docker-compose up -d

# Follow logs (optional)
docker-compose logs -f
```

### 4. Verify Deployment

```bash
# Check service status
docker-compose ps
# Expected: Both services "Up" and "healthy"

# Test backend
curl http://localhost:12689/health
# Expected: {"status": "healthy", "agents": 7, "version": "v2.0.0"}

# Test frontend
curl -I http://localhost:8592
# Expected: HTTP/1.1 200 OK
```

**Done!** Services are now running:
- Backend: http://localhost:12689
- Frontend: http://localhost:8592
- Public (if Caddy configured): https://tk9v2.thinhkhuat.com

---

## Manual Deployment (Step-by-Step)

### Step 1: Prepare Environment

```bash
# Create required directories
mkdir -p outputs logs data

# Set permissions (if needed)
chmod -R 755 outputs logs data
```

### Step 2: Configure Environment Variables

Create `.env` file with ALL required variables:

```bash
# ============================================================================
# API KEYS (REQUIRED)
# ============================================================================
GOOGLE_API_KEY=AIza...your_key_here
BRAVE_API_KEY=BSA...your_key_here

# Optional fallback providers
OPENAI_API_KEY=sk-...your_key_here
TAVILY_API_KEY=tvly-...your_key_here
ANTHROPIC_API_KEY=sk-ant-...your_key_here

# ============================================================================
# LLM CONFIGURATION
# ============================================================================
PRIMARY_LLM_PROVIDER=google_gemini
PRIMARY_LLM_MODEL=gemini-2.5-flash
LLM_STRATEGY=primary_only  # Options: primary_only, primary_with_fallback

# ============================================================================
# SEARCH CONFIGURATION
# ============================================================================
PRIMARY_SEARCH_PROVIDER=brave
SEARCH_STRATEGY=primary_only  # Options: primary_only, primary_with_fallback

# BRAVE Search Configuration
RETRIEVER=custom
RETRIEVER_ENDPOINT=https://brave-local-provider.local

# ============================================================================
# RESEARCH SETTINGS
# ============================================================================
RESEARCH_LANGUAGE=vi      # Language code: en, vi, zh, etc.
SEARCH_COUNTRY=VN         # Country code for search results
DEFAULT_TONE=objective    # Options: objective, critical, enthusiastic

# ============================================================================
# SERVER CONFIGURATION
# ============================================================================
HOST=0.0.0.0
PORT=12689
LOG_LEVEL=INFO            # Options: DEBUG, INFO, WARNING, ERROR
DEBUG=false

# ============================================================================
# CORS CONFIGURATION
# ============================================================================
CORS_ORIGINS=http://localhost:8592,http://192.168.2.22:8592,https://tk9v2.thinhkhuat.com

# ============================================================================
# SUPABASE (Optional - for persistence)
# ============================================================================
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here

# ============================================================================
# BUILD CONFIGURATION
# ============================================================================
BUILD_VERSION=v2.0.0
TAG=latest
```

### Step 3: Build Docker Images

#### Backend Image

```bash
# Build backend (multi-stage build)
docker build -f Dockerfile.backend -t tk9-backend:latest .

# Expected build time: 5-10 minutes
# Final image size: ~1.69GB

# Verify dependencies
docker run --rm tk9-backend:latest python -c "import langgraph; print('✓ LangGraph installed')"
docker run --rm tk9-backend:latest python -c "import fastapi; print('✓ FastAPI installed')"
docker run --rm tk9-backend:latest python -c "import google.generativeai; print('✓ Gemini SDK installed')"
```

**Build stages**:
1. **Builder stage** (python:3.12-slim):
   - Install build dependencies
   - Create virtualenv
   - Install Python packages from `requirements-backend-minimal.txt`

2. **Runtime stage** (python:3.12-slim):
   - Copy virtualenv from builder
   - Install runtime dependencies (curl, pandoc)
   - Copy application code
   - Expose port 12689

#### Frontend Image

```bash
# Build frontend (multi-stage build)
docker build -f Dockerfile.frontend -t tk9-frontend:latest .

# Expected build time: 2-5 minutes
# Final image size: ~50MB (nginx + static files)

# Verify nginx config
docker run --rm tk9-frontend:latest cat /etc/nginx/conf.d/default.conf
```

**Build stages**:
1. **Builder stage** (node:20-alpine):
   - Install Node.js dependencies
   - Build Vue 3 app with Vite (`npm run build`)
   - Output to `/build/dist`

2. **Runtime stage** (nginx:alpine):
   - Copy built files to `/usr/share/nginx/html`
   - Configure nginx for SPA routing (port 8592)
   - Enable gzip compression

### Step 4: Start Services with Docker Compose

```bash
# Start in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# Stop following logs: Ctrl+C (services keep running)
```

### Step 5: Verify Services

#### Check Container Status

```bash
docker-compose ps

# Expected output:
# NAME           STATUS                  PORTS
# tk9-backend    Up 30s (healthy)        0.0.0.0:12689->12689/tcp
# tk9-frontend   Up 30s (healthy)        0.0.0.0:8592->8592/tcp
```

#### Test Backend Health

```bash
# Health endpoint
curl http://localhost:12689/health

# Expected response:
{
  "status": "healthy",
  "version": "v2.0.0",
  "agents": {
    "total": 7,
    "available": ["searcher", "planner", "researcher", "writer", "publisher", "translator", "orchestrator"]
  },
  "providers": {
    "llm": "google_gemini",
    "search": "brave"
  }
}
```

#### Test Frontend

```bash
# Homepage
curl -I http://localhost:8592/

# Expected:
HTTP/1.1 200 OK
Server: nginx
Content-Type: text/html

# SPA route (should still return 200 due to fallback)
curl -I http://localhost:8592/dashboard
# Expected: HTTP/1.1 200 OK
```

#### Test WebSocket Connection

```bash
# Install wscat if needed
npm install -g wscat

# Test WebSocket
wscat -c ws://localhost:12689/ws/test

# Expected: Connection established
# Press Ctrl+C to disconnect
```

### Step 6: Configure Caddy (Production)

See [CADDY_CONFIGURATION.md](./CADDY_CONFIGURATION.md) for complete Caddy setup.

**Quick Caddyfile**:
```caddy
tk9v2.thinhkhuat.com {
    encode gzip

    handle /api/* {
        reverse_proxy http://192.168.2.22:12689
    }

    handle /ws/* {
        reverse_proxy http://192.168.2.22:12689
    }

    handle /* {
        reverse_proxy http://192.168.2.22:8592
    }
}
```

---

## Environment Variables

### Critical Variables (REQUIRED)

| Variable              | Description                           | Example                      |
|-----------------------|---------------------------------------|------------------------------|
| `GOOGLE_API_KEY`      | Gemini API key (primary LLM)          | `AIza...`                    |
| `BRAVE_API_KEY`       | BRAVE Search API key (primary search) | `BSA...`                     |
| `PRIMARY_LLM_PROVIDER`| LLM provider name                     | `google_gemini`              |
| `PRIMARY_LLM_MODEL`   | Gemini model name                     | `gemini-2.5-flash`           |
| `PRIMARY_SEARCH_PROVIDER` | Search provider name              | `brave`                      |

### Optional Variables

| Variable              | Default           | Description                              |
|-----------------------|-------------------|------------------------------------------|
| `RESEARCH_LANGUAGE`   | `vi`              | Output language (ISO 639-1 code)         |
| `SEARCH_COUNTRY`      | `VN`              | Search result country filter             |
| `LOG_LEVEL`           | `INFO`            | Logging verbosity                        |
| `DEBUG`               | `false`           | Enable debug mode                        |
| `CORS_ORIGINS`        | (see example)     | Allowed frontend origins                 |
| `LLM_STRATEGY`        | `primary_only`    | `primary_only` or `primary_with_fallback`|
| `SEARCH_STRATEGY`     | `primary_only`    | `primary_only` or `primary_with_fallback`|

### Build-Time Variables

| Variable              | Default           | Description                              |
|-----------------------|-------------------|------------------------------------------|
| `BUILD_VERSION`       | `v2.0.0`          | Application version tag                  |
| `TAG`                 | `latest`          | Docker image tag                         |

---

## Service Details

### Backend Service (tk9-backend)

**Image**: `tk9-backend:latest`
**Base**: Python 3.12 (slim)
**Port**: 12689
**Resources**:
- CPU: 1-4 cores (reserved: 1, limit: 4)
- Memory: 2-8GB (reserved: 2GB, limit: 8GB)

**Key Components**:
- FastAPI web framework
- LangGraph agent orchestration
- 7 specialized agents (searcher, planner, researcher, writer, publisher, translator, orchestrator)
- Multi-provider support (Gemini, OpenAI, Anthropic)
- BRAVE Search integration

**Volumes**:
- `./outputs:/app/outputs` - Research output files
- `./logs:/app/logs` - Application logs
- `./data:/app/data` - Cache and temporary data
- `./.env:/app/.env` - Environment configuration (read-only)

**Health Check**:
```bash
curl -f http://localhost:12689/health
# Runs every 30s, timeout 10s, retries 3, start_period 40s
```

### Frontend Service (tk9-frontend)

**Image**: `tk9-frontend:latest`
**Base**: nginx:alpine
**Port**: 8592
**Resources**:
- CPU: 0.25-1 core (reserved: 0.25, limit: 1)
- Memory: 128-512MB (reserved: 128MB, limit: 512MB)

**Key Components**:
- Vue 3 SPA
- Vite build tool
- TypeScript
- Tailwind CSS
- nginx for static serving

**nginx Configuration**:
- SPA routing: `try_files $uri $uri/ /index.html;`
- Gzip compression enabled
- Static asset caching (1 year)

**Health Check**:
```bash
wget --no-verbose --tries=1 --spider http://localhost:8592/
# Runs every 30s, timeout 5s, retries 3, start_period 10s
```

---

## Development vs Production

### Development Mode

**Enabled by**: `docker-compose.override.yml` (automatically loaded)

**Features**:
- Hot reload for both services
- Volume mounts for source code
- Debug logging enabled
- No resource limits
- Faster iteration

**Start development**:
```bash
# Uses docker-compose.yml + docker-compose.override.yml automatically
docker-compose up -d
```

**Backend hot reload**:
- Mounts `./multi_agents` → `/app/multi_agents`
- Mounts `./providers` → `/app/providers`
- Uvicorn reloads on code changes

**Frontend hot reload**:
- Mounts `./web_dashboard/frontend_poc` → `/app`
- Vite dev server (`npm run dev`)
- HMR (Hot Module Replacement)

### Production Mode

**Enabled by**: Explicitly disable override file

**Features**:
- Optimized builds (no source mounts)
- Resource limits enforced
- Production logging (INFO level)
- Health checks enforced
- Restart policies enabled

**Start production**:
```bash
# Disable override file
docker-compose -f docker-compose.yml up -d

# Or rename override file temporarily
mv docker-compose.override.yml docker-compose.override.yml.disabled
docker-compose up -d
```

**Differences**:
- No hot reload (must rebuild on changes)
- Smaller attack surface (no source code access)
- Better resource management
- Suitable for server deployment

---

## Verification

### 1. Container Health

```bash
# Check all containers
docker ps --filter "name=tk9"

# Expected output:
# CONTAINER ID   IMAGE                  STATUS
# abc123...      tk9-backend:latest     Up 5 minutes (healthy)
# def456...      tk9-frontend:latest    Up 5 minutes (healthy)
```

### 2. Network Connectivity

```bash
# Test backend from host
curl http://localhost:12689/health

# Test frontend from host
curl -I http://localhost:8592

# Test backend from frontend container
docker exec tk9-frontend wget -O- http://tk9-backend:12689/health
```

### 3. Log Verification

```bash
# View backend logs
docker logs tk9-backend --tail 50

# View frontend logs
docker logs tk9-frontend --tail 50

# Follow logs from both
docker-compose logs -f
```

**Expected backend logs**:
```
INFO: Started server process
INFO: Uvicorn running on http://0.0.0.0:12689
INFO: Application startup complete
INFO: LLM Provider: google_gemini (model: gemini-2.5-flash)
INFO: Search Provider: brave
```

**Expected frontend logs**:
```
/docker-entrypoint.sh: Configuration complete; ready for start up
```

### 4. Resource Usage

```bash
# Monitor resources
docker stats tk9-backend tk9-frontend

# Expected (approximate):
# NAME          CPU %     MEM USAGE / LIMIT
# tk9-backend   5-15%     500MB / 8GB
# tk9-frontend  0.5-2%    50MB / 512MB
```

### 5. End-to-End Test

```bash
# Start a research session (requires valid API keys)
curl -X POST http://localhost:12689/api/research \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Latest AI developments",
    "language": "en"
  }'

# Expected: JSON response with session ID
# Check outputs/ directory for generated files
ls -l outputs/
```

---

## Troubleshooting

### Issue 1: ModuleNotFoundError - langchain.docstore or google.generativeai

**Symptoms**:
```bash
docker logs tk9-backend
# ModuleNotFoundError: No module named 'langchain.docstore'
# or: ModuleNotFoundError: No module named 'google.generativeai'
```

**Root Causes** (2025-11-03 Resolution):

#### Problem #1: langchain 1.0+ Removed Backward Compatibility

**What Happened**:
- UV dependency resolver installed langchain **1.0.3** (latest version)
- langchain 1.0+ **removed** the `langchain.docstore` module (breaking change)
- gpt-researcher and legacy code still import `from langchain.docstore.document import Document`

**Evidence**:
```bash
# Check installed version
docker exec tk9-backend pip list | grep "^langchain "
# If shows 1.0.x → WRONG (breaks backward compatibility)
# Should show 0.3.x → CORRECT (maintains langchain.docstore)
```

**Correct Fix**:
Pin langchain to 0.3.x series in `requirements-backend-minimal.txt`:
```python
# Langchain ecosystem - pin to 0.3.x for backward compatibility
# langchain 1.0+ removed langchain.docstore module (breaking change)
langchain>=0.3.0,<1.0.0
```

#### Problem #2: Missing Old Google AI SDK

**What Happened**:
- Code imports `google.generativeai` (old SDK package name)
- Only `google-genai` (new SDK) was installed
- Host environment has **BOTH** SDKs for compatibility during SDK transition

**Evidence**:
```bash
# Check installed packages
docker exec tk9-backend pip list | grep -i "google.*genai"
# Must have BOTH:
# google-genai         1.47.0    ← New SDK
# google-generativeai  0.8.4     ← Old SDK (REQUIRED for legacy imports)
```

**Correct Fix**:
Add both SDKs in `requirements-backend-minimal.txt`:
```python
# LLM Providers - EXACT HOST VERSIONS
google-genai==1.47.0              # New SDK
google-generativeai==0.8.4        # Old SDK for legacy imports
```

#### Verification Steps

**1. Check langchain version constraint**:
```bash
docker exec tk9-backend cat /app/requirements-backend-minimal.txt | grep "langchain"
# Expected:
# langchain>=0.3.0,<1.0.0
```

**2. Test langchain.docstore import**:
```bash
docker exec tk9-backend python -c "from langchain.docstore.document import Document; print('✓ Import works')"
# Should print: ✓ Import works
# Should NOT error
```

**3. Check Google AI SDKs**:
```bash
docker exec tk9-backend pip list | grep -E "(google-genai|google-generativeai)"
# Must show BOTH:
# google-genai         1.47.0
# google-generativeai  0.8.4
```

**4. Test full import chain**:
```bash
docker exec tk9-backend python -c "from multi_agents.agents.researcher import ResearchAgent; print('✓ All imports OK')"
# Should print: ✓ All imports OK
# Warnings about missing API keys are normal (no .env in test)
```

#### Rebuild with Correct Dependencies

If checks fail, rebuild with corrected requirements:
```bash
# 1. Update requirements-backend-minimal.txt
nano requirements-backend-minimal.txt

# Ensure these lines exist:
# langchain>=0.3.0,<1.0.0
# google-genai==1.47.0
# google-generativeai==0.8.4

# 2. Rebuild image
docker-compose down
docker-compose build --no-cache tk9-backend
docker-compose up -d

# 3. Verify fix
docker exec tk9-backend python -c "from langchain.docstore.document import Document; print('✓ Fixed')"
```

#### Why This Matters

**Strategic Version Pinning**:
- ❌ **WRONG**: Remove all version constraints (lets resolver pick latest)
- ❌ **WRONG**: Pin exact versions from host (creates incompatibilities)
- ✅ **CORRECT**: Pin major version boundaries (`>=0.3.0,<1.0.0`)

**Dual SDK Support**:
- Modern codebases often run BOTH old and new SDKs during transitions
- Old SDK: `google-generativeai` (import `google.generativeai`)
- New SDK: `google-genai` (import `google.genai`)
- Both required for compatibility

**Key Takeaways**:
1. Major version bumps (0.x → 1.x) often remove deprecated APIs
2. Check host environment for BOTH old and new SDKs
3. Use strategic version constraints, not exact pins
4. Always verify imports after dependency changes
5. See Phase 6 notes in `CLAUDE.md` for full context

### Issue 2: Frontend Returns 404 on Routes

**Symptoms**: Direct URL access (e.g., `/dashboard`) returns 404

**Cause**: SPA routing misconfigured in nginx

**Solution**:
```bash
# Verify nginx config
docker exec tk9-frontend cat /etc/nginx/conf.d/default.conf | grep try_files

# Expected: try_files $uri $uri/ /index.html;

# If missing, rebuild frontend:
docker-compose build --no-cache tk9-frontend
docker-compose up -d tk9-frontend
```

### Issue 3: CORS Errors

**Symptoms**: Browser console shows CORS policy errors

**Cause**: Frontend domain not in `CORS_ORIGINS`

**Solution**:
```bash
# Edit docker-compose.yml
nano docker-compose.yml

# Update CORS_ORIGINS to include frontend URL:
environment:
  - CORS_ORIGINS=http://localhost:8592,http://192.168.2.22:8592,https://tk9v2.thinhkhuat.com

# Restart backend
docker-compose restart tk9-backend
```

### Issue 4: WebSocket Connection Failed

**Symptoms**: WebSocket connections timeout or fail

**Causes**:
1. Backend not running
2. Firewall blocking WebSocket
3. Caddy not configured for WebSocket upgrade

**Solutions**:

**Check backend**:
```bash
docker logs tk9-backend | grep -i websocket
```

**Test WebSocket directly**:
```bash
wscat -c ws://localhost:12689/ws/test
# Should connect successfully
```

**Verify Caddy** (if using):
```bash
# Check Caddy logs
sudo journalctl -u caddy -n 50 | grep -i websocket

# Verify upgrade header
curl -I https://tk9v2.thinhkhuat.com/ws/test \
  -H "Upgrade: websocket" \
  -H "Connection: Upgrade"
```

### Issue 5: Containers Stuck in Unhealthy State

**Symptoms**: `docker ps` shows "unhealthy" status

**Cause**: Health check endpoint failing

**Solutions**:

**Backend unhealthy**:
```bash
# Test health endpoint manually
curl http://localhost:12689/health

# Check logs for errors
docker logs tk9-backend --tail 100

# Restart if needed
docker-compose restart tk9-backend
```

**Frontend unhealthy**:
```bash
# Test frontend
curl -I http://localhost:8592

# Check nginx logs
docker logs tk9-frontend

# Restart
docker-compose restart tk9-frontend
```

### Issue 6: Port Already in Use

**Symptoms**:
```
Error: bind: address already in use
```

**Cause**: Another service using port 12689 or 8592

**Solution**:
```bash
# Find process using port
lsof -i :12689
lsof -i :8592

# Kill process or change port in docker-compose.yml
# To change port:
nano docker-compose.yml
# Change "12689:12689" to "12690:12689" (example)

docker-compose up -d
```

### Issue 7: API Keys Not Working

**Symptoms**:
```
docker logs tk9-backend | grep -i "api key"
# Error: Invalid API key
```

**Cause**: Incorrect or missing API keys in `.env`

**Solution**:
```bash
# Verify .env file
cat .env | grep -E "GOOGLE_API_KEY|BRAVE_API_KEY"

# Update keys
nano .env

# Restart backend (environment must be reloaded)
docker-compose down
docker-compose up -d

# Test
curl http://localhost:12689/health
```

---

## Monitoring and Maintenance

### Daily Monitoring

```bash
# Check service status
docker-compose ps

# Check resource usage
docker stats tk9-backend tk9-frontend --no-stream

# Check disk usage (outputs, logs)
du -sh outputs/ logs/
```

### Log Management

```bash
# View recent logs
docker-compose logs --tail=100

# Search for errors
docker-compose logs | grep -i error

# Export logs for analysis
docker-compose logs > tk9-logs-$(date +%Y%m%d).log
```

**Log Rotation**: Docker JSON logs are automatically rotated:
- Max size: 10MB (backend), 10MB (frontend)
- Max files: 5 (backend), 3 (frontend)

### Updating Application

```bash
# 1. Pull latest changes
git pull origin main

# 2. Rebuild images
docker-compose build --no-cache

# 3. Restart services (zero downtime with Caddy)
docker-compose up -d

# 4. Verify deployment
docker-compose ps
curl http://localhost:12689/health
```

### Restart Services

```bash
# Restart specific service
docker-compose restart tk9-backend

# Restart all services
docker-compose restart

# Restart with rebuild
docker-compose up -d --build
```

### Clean Up

```bash
# Remove stopped containers
docker-compose down

# Remove images
docker-compose down --rmi all

# Clean up volumes (⚠️ deletes data)
docker-compose down -v

# Clean up Docker system
docker system prune -a
```

---

## Backup and Recovery

### Files to Backup

1. **Configuration**:
   - `.env` (API keys and config)
   - `docker-compose.yml`
   - `docker-compose.override.yml`

2. **Data**:
   - `outputs/` (research results)
   - `logs/` (application logs)
   - `data/` (cache and temp data)

3. **Caddy** (if applicable):
   - `/etc/caddy/Caddyfile`
   - `/var/lib/caddy/` (SSL certificates)

### Backup Script

```bash
#!/bin/bash
# backup-tk9.sh

BACKUP_DIR="/backups/tk9-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup config
cp .env "$BACKUP_DIR/"
cp docker-compose.yml "$BACKUP_DIR/"
cp docker-compose.override.yml "$BACKUP_DIR/" 2>/dev/null || true

# Backup data
tar -czf "$BACKUP_DIR/outputs.tar.gz" outputs/
tar -czf "$BACKUP_DIR/logs.tar.gz" logs/
tar -czf "$BACKUP_DIR/data.tar.gz" data/

echo "✓ Backup created: $BACKUP_DIR"
```

**Run backup**:
```bash
chmod +x backup-tk9.sh
./backup-tk9.sh
```

### Recovery

```bash
# 1. Stop services
docker-compose down

# 2. Restore config
cp /backups/tk9-YYYYMMDD-HHMMSS/.env .
cp /backups/tk9-YYYYMMDD-HHMMSS/docker-compose.yml .

# 3. Restore data
tar -xzf /backups/tk9-YYYYMMDD-HHMMSS/outputs.tar.gz
tar -xzf /backups/tk9-YYYYMMDD-HHMMSS/logs.tar.gz
tar -xzf /backups/tk9-YYYYMMDD-HHMMSS/data.tar.gz

# 4. Rebuild and start
docker-compose up -d --build
```

---

## Scaling Considerations

### Horizontal Scaling (Multiple Instances)

**Backend** can be scaled horizontally:
```bash
# Run 3 backend instances
docker-compose up -d --scale tk9-backend=3
```

**Requirements**:
- Load balancer (Caddy or nginx upstream)
- Shared session storage (Redis or Supabase)
- Stateless agent design (already implemented)

**Caddyfile for load balancing**:
```caddy
tk9v2.thinhkhuat.com {
    handle /api/* {
        reverse_proxy http://192.168.2.22:12689 \
                     http://192.168.2.22:12690 \
                     http://192.168.2.22:12691 {
            lb_policy round_robin
            health_uri /health
            health_interval 10s
        }
    }
}
```

### Vertical Scaling (More Resources)

**Increase backend resources** in `docker-compose.yml`:
```yaml
services:
  tk9-backend:
    deploy:
      resources:
        limits:
          cpus: '8.0'    # Increase from 4.0
          memory: 16G    # Increase from 8G
```

### Database Optimization

**Enable Supabase** for persistent sessions:
```bash
# Add to .env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key

# Restart backend
docker-compose restart tk9-backend
```

**Benefits**:
- Session persistence across restarts
- Multi-instance session sharing
- Research history tracking

---

## Production Checklist

Before deploying to production, verify:

- [ ] **Environment**: All API keys configured in `.env`
- [ ] **Builds**: Both images built successfully (`docker images | grep tk9`)
- [ ] **Health Checks**: Both services healthy (`docker-compose ps`)
- [ ] **Networking**: Backend and frontend reachable internally
- [ ] **Caddy**: Configured and running (see `CADDY_CONFIGURATION.md`)
- [ ] **Domain**: DNS points to server (`dig tk9v2.thinhkhuat.com`)
- [ ] **SSL**: Certificate obtained and valid (`curl -I https://tk9v2.thinhkhuat.com`)
- [ ] **WebSocket**: Connections work (`wscat -c wss://tk9v2.thinhkhuat.com/ws/test`)
- [ ] **CORS**: Frontend can call backend API (check browser console)
- [ ] **Logs**: Log directories exist and writable (`ls -ld logs/ outputs/`)
- [ ] **Backup**: Backup script configured and tested
- [ ] **Monitoring**: Resource monitoring in place (`docker stats`)
- [ ] **Documentation**: Team knows how to deploy and troubleshoot

---

## Access Points

### Local Development

```bash
# Backend
curl http://localhost:12689/health

# Frontend
open http://localhost:8592
```

### Internal Network

```bash
# Backend
curl http://192.168.2.22:12689/health

# Frontend
open http://192.168.2.22:8592
```

### Production (Public)

```bash
# Frontend
open https://tk9v2.thinhkhuat.com

# Backend API
curl https://tk9v2.thinhkhuat.com/api/health

# WebSocket
wscat -c wss://tk9v2.thinhkhuat.com/ws/test
```

---

## Additional Resources

- **Caddy Configuration**: [CADDY_CONFIGURATION.md](./CADDY_CONFIGURATION.md)
- **Project README**: [../../README.md](../../README.md)
- **Implementation Status**: [../../docs/IMPLEMENTATION_STATUS_2025-11-01.md](../../docs/IMPLEMENTATION_STATUS_2025-11-01.md)
- **Docker Compose Reference**: https://docs.docker.com/compose/
- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **Vue 3 Documentation**: https://vuejs.org/
- **Caddy Documentation**: https://caddyserver.com/docs/

---

## Support

**Issues**: Open GitHub issue or check existing documentation
**Logs**: Always include logs when reporting issues (`docker-compose logs`)
**Environment**: Verify `.env` configuration before troubleshooting

---

**Last Updated**: 2025-11-03
**Maintainer**: TK9 Development Team
**Version**: v2.0.0 (Production Ready)

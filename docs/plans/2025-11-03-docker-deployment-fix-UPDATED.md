# Docker Deployment Fix - Full Stack Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix ModuleNotFoundError and deploy complete TK9 Deep Research MCP with Backend (FastAPI) + Frontend (Vue 3)

**Architecture:**
- **Backend**: FastAPI on port 12689 (Python 3.12+, langgraph dependencies)
- **Frontend**: Vue 3 + Vite production build on port 8592
- **Reverse Proxy**: Caddy routing tk9v2.thinhkhuat.com to both services

**Tech Stack:** Docker, Docker Compose, Python 3.12+, Vue 3, Vite, FastAPI, LangGraph, Node.js 18+

---

## Problem Analysis

**Current Issues:**
1. `ModuleNotFoundError: No module named 'langgraph'` - Dependencies not installed
2. Missing Vue frontend (port 8592) from Docker deployment
3. Dockerfile uses `uv sync` but no proper `pyproject.toml`/`uv.lock` exists
4. No multi-service orchestration in docker-compose.yml

**Complete Architecture:**
```
Internet (HTTPS/WSS)
    ↓
┌──────────────────────────────────────────┐
│   Caddy v2 Reverse Proxy                 │
│   tk9v2.thinhkhuat.com                   │
│   - Auto HTTPS/SSL                       │
│   - Auto WebSocket upgrade               │
└──┬──────────────┬──────────────┬─────────┘
   │              │              │
   │ (/)          │ (/api/*)     │ (/ws/*)
   │              │              │
   ↓              ↓              ↓
┌──────────┐  ┌────────────────────────────┐
│ Frontend │  │      Backend (FastAPI)     │
│ (Vue 3)  │  │      Port 12689            │
│ Port 8592│  │  - REST API endpoints      │
│          │  │  - WebSocket server        │
│ nginx:   │  │  - 7-agent orchestration   │
│ - Static │  └────────────────────────────┘
│ - SPA    │
└──────────┘

Internal Docker Network: tk9-network
```

**Key Architecture Points:**
- **Caddy v2**: External reverse proxy (HTTPS, WebSocket, routing)
- **Nginx**: Internal static file server + SPA routing only
- **No internal proxying**: Caddy routes traffic directly to each service

---

## Task 1: Create Multi-Stage Dockerfile for Backend

**Files:**
- Create: `Dockerfile.backend`
- Reference: `multi_agents/requirements.txt`
- Reference: `requirements-prod.txt`
- Reference: `web_dashboard/requirements.txt`

**Step 1: Create consolidated backend requirements**

Create: `requirements-backend.txt`

```txt
# TK9 Deep Research MCP - Backend Dependencies
# For FastAPI backend on port 12689

# ============================================================================
# Core Multi-Agent Framework
# ============================================================================
langgraph>=0.0.20
gpt-researcher>=0.14.1
langgraph-cli
python-dotenv>=1.0.0
weasyprint>=60.0
json5
loguru

# ============================================================================
# FastAPI Backend
# ============================================================================
fastapi>=0.116.0
uvicorn[standard]>=0.25.0
pydantic>=2.5.0
pydantic-settings>=2.1.0

# ============================================================================
# LangChain & AI
# ============================================================================
langchain>=0.1.0
langchain-community>=0.0.10

# ============================================================================
# LLM Providers
# ============================================================================
openai>=1.12.0
google-generativeai>=0.8.0
anthropic>=0.25.0

# ============================================================================
# Web & HTTP
# ============================================================================
aiohttp>=3.10.0
requests>=2.31.0
beautifulsoup4>=4.12.0
lxml>=4.9.0
httpx>=0.26.0
websockets>=12.0

# ============================================================================
# Document Processing
# ============================================================================
jinja2>=3.1.0
pypandoc>=1.11
python-docx>=1.1.0
reportlab>=4.0.0

# ============================================================================
# Async & Concurrency
# ============================================================================
nest-asyncio>=1.6.0
asyncio-throttle>=1.0.0

# ============================================================================
# Database (Supabase integration)
# ============================================================================
supabase>=2.0.0
sqlalchemy>=2.0.0
alembic>=1.13.0
psycopg2-binary>=2.9.0

# ============================================================================
# Monitoring & Logging
# ============================================================================
structlog>=23.2.0
python-json-logger>=2.0.0

# ============================================================================
# Security
# ============================================================================
cryptography>=41.0.0
python-multipart>=0.0.6
certifi>=2023.11.17

# ============================================================================
# Data Processing
# ============================================================================
pandas>=2.1.0
numpy>=1.24.0
python-dateutil>=2.8.0

# ============================================================================
# Production Server
# ============================================================================
gunicorn>=21.2.0
```

**Step 2: Create Backend Dockerfile**

Create: `Dockerfile.backend`

```dockerfile
# TK9 Deep Research MCP - Backend Dockerfile
# FastAPI backend with Python 3.12+ and all dependencies

# ============================================================================
# Stage 1: Builder
# ============================================================================
FROM python:3.12-slim as builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Copy requirements
COPY requirements-backend.txt ./

# Create venv and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements-backend.txt

# ============================================================================
# Stage 2: Runtime
# ============================================================================
FROM python:3.12-slim as runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app:$PYTHONPATH"

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    pandoc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appgroup && useradd -r -g appgroup -d /app -s /bin/bash appuser

WORKDIR /app

# Copy venv from builder
COPY --from=builder --chown=appuser:appgroup /opt/venv /opt/venv

# Copy application code
COPY --chown=appuser:appgroup multi_agents/ ./multi_agents/
COPY --chown=appuser:appgroup web_dashboard/ ./web_dashboard/
COPY --chown=appuser:appgroup config/ ./config/
COPY --chown=appuser:appgroup providers/ ./providers/
COPY --chown=appuser:appgroup mcp_server.py ./

# Create required directories
RUN mkdir -p /app/outputs /app/logs /app/data \
    && chown -R appuser:appgroup /app

# Health check for backend
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:12689/health || exit 1

USER appuser

# Expose backend port
EXPOSE 12689

# Start backend
CMD ["python", "-m", "uvicorn", "web_dashboard.main:app", "--host", "0.0.0.0", "--port", "12689"]
```

**Step 3: Test backend build**

Run:
```bash
cd /Users/thinhkhuat/»DEV•local«/tk9_source_deploy
docker build -f Dockerfile.backend -t tk9-backend:test .
```

Expected: Build completes successfully

**Step 4: Verify langgraph installed**

Run:
```bash
docker run --rm tk9-backend:test python -c "import langgraph; print('✓ langgraph version:', langgraph.__version__)"
```

Expected: Prints langgraph version

**Step 5: Commit backend Dockerfile**

```bash
git add Dockerfile.backend requirements-backend.txt
git commit -m "feat(docker): Add backend Dockerfile with langgraph dependencies

- Created Dockerfile.backend for FastAPI backend (port 12689)
- Consolidated all backend dependencies in requirements-backend.txt
- Multi-stage build with Python 3.12-slim
- Fixed ModuleNotFoundError for langgraph
- Added health check endpoint
- Non-root user for security"
```

---

## Task 2: Create Multi-Stage Dockerfile for Frontend

**Files:**
- Create: `Dockerfile.frontend`
- Reference: `web_dashboard/frontend_poc/package.json`
- Reference: `web_dashboard/frontend_poc/vite.config.ts`

**Step 1: Create Frontend Dockerfile**

Create: `Dockerfile.frontend`

```dockerfile
# TK9 Deep Research MCP - Frontend Dockerfile
# Vue 3 + Vite production build served on port 8592

# ============================================================================
# Stage 1: Builder
# ============================================================================
FROM node:18-alpine as builder

WORKDIR /build

# Copy package files
COPY web_dashboard/frontend_poc/package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY web_dashboard/frontend_poc/ ./

# Build for production
RUN npm run build

# ============================================================================
# Stage 2: Runtime with nginx
# ============================================================================
FROM nginx:alpine as runtime

# Copy simplified nginx config (Caddy handles routing)
COPY <<EOF /etc/nginx/conf.d/default.conf
server {
    listen 8592;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript
               application/x-javascript application/xml+rss
               application/json application/javascript;

    # SPA routing - all routes serve index.html
    # (Caddy handles /api/ and /ws/ routing externally)
    location / {
        try_files \$uri \$uri/ /index.html;
    }

    # Cache static assets
    location ~* \\.(?:css|js|jpg|jpeg|gif|png|ico|woff|woff2|ttf|svg)\$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Copy built files from builder
COPY --from=builder /build/dist /usr/share/nginx/html

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8592/ || exit 1

# Expose frontend port
EXPOSE 8592

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
```

**Step 2: Test frontend build**

Run:
```bash
cd /Users/thinhkhuat/»DEV•local«/tk9_source_deploy
docker build -f Dockerfile.frontend -t tk9-frontend:test .
```

Expected: Build completes with production Vite build

**Step 3: Test frontend serves correctly**

Run:
```bash
docker run --rm -p 8592:8592 tk9-frontend:test &
sleep 5
curl -I http://localhost:8592
```

Expected: HTTP 200 OK

**Step 4: Commit frontend Dockerfile**

```bash
git add Dockerfile.frontend
git commit -m "feat(docker): Add frontend Dockerfile for Vue 3 production build

- Created Dockerfile.frontend for Vue 3 + Vite (port 8592)
- Multi-stage build: Node 18 builder + nginx runtime
- Nginx configured for SPA routing ONLY (internal container use)
- Static asset caching with 1-year expiry
- Caddy v2 handles external routing, API proxy, and WebSocket
- Health check endpoint"
```

---

## Task 3: Create Comprehensive Docker Compose

**Files:**
- Modify: `docker-compose.yml` (complete rewrite)
- Create: `.dockerignore`
- Create: `docker-compose.override.yml`

**Step 1: Create .dockerignore**

Create: `.dockerignore`

```
# Python
__pycache__/
*.py[cod]
*.so
.Python
venv/
.venv/
*.egg-info/

# Node
node_modules/
npm-debug.log
.npm

# Environment
.env
.env.local

# IDEs
.vscode/
.idea/
*.swp
.DS_Store

# Logs & Outputs
logs/
*.log
outputs/
data/

# Git
.git/
.gitignore

# Documentation
docs/
*.md
!README.md

# Archives
ARCHIVE/

# Tests
.pytest_cache/
.coverage

# Temp
tmp/
temp/
*.tmp

# Docker
Dockerfile*
docker-compose*
.dockerignore
```

**Step 2: Create production docker-compose.yml**

Update: `docker-compose.yml`

```yaml
version: '3.8'

services:
  # ============================================================================
  # TK9 Backend - FastAPI on port 12689
  # ============================================================================
  tk9-backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
      args:
        BUILD_VERSION: ${BUILD_VERSION:-v2.0.0}
    image: tk9-backend:${TAG:-latest}
    container_name: tk9-backend
    restart: unless-stopped

    environment:
      # Server
      - HOST=0.0.0.0
      - PORT=12689
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - DEBUG=${DEBUG:-false}

      # AI Providers (7-agent system)
      - PRIMARY_LLM_PROVIDER=${PRIMARY_LLM_PROVIDER:-google_gemini}
      - PRIMARY_LLM_MODEL=${PRIMARY_LLM_MODEL:-gemini-2.5-flash-preview-04-17-thinking}
      - PRIMARY_SEARCH_PROVIDER=${PRIMARY_SEARCH_PROVIDER:-brave}

      # API Keys
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - BRAVE_API_KEY=${BRAVE_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - TAVILY_API_KEY=${TAVILY_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}

      # Research Config
      - RESEARCH_LANGUAGE=${RESEARCH_LANGUAGE:-vi}
      - SEARCH_COUNTRY=${SEARCH_COUNTRY:-VN}
      - LLM_STRATEGY=${LLM_STRATEGY:-primary_only}
      - SEARCH_STRATEGY=${SEARCH_STRATEGY:-primary_only}

      # BRAVE Search
      - RETRIEVER=${RETRIEVER:-custom}
      - RETRIEVER_ENDPOINT=${RETRIEVER_ENDPOINT:-https://brave-local-provider.local}

      # CORS (allow frontend)
      - CORS_ORIGINS=http://localhost:8592,http://192.168.2.22:8592,https://tk9v2.thinhkhuat.com

      # Supabase
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}

    ports:
      - "12689:12689"

    volumes:
      - ./outputs:/app/outputs:rw
      - ./logs:/app/logs:rw
      - ./data:/app/data:rw
      - ./.env:/app/.env:ro

    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 8G
        reservations:
          cpus: '1.0'
          memory: 2G

    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:12689/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

    networks:
      - tk9-network

    logging:
      driver: json-file
      options:
        max-size: 10m
        max-file: "5"

  # ============================================================================
  # TK9 Frontend - Vue 3 on port 8592
  # ============================================================================
  tk9-frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
      args:
        BUILD_VERSION: ${BUILD_VERSION:-v2.0.0}
    image: tk9-frontend:${TAG:-latest}
    container_name: tk9-frontend
    restart: unless-stopped

    ports:
      - "8592:8592"

    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 128M

    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:8592/"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 10s

    networks:
      - tk9-network

    depends_on:
      tk9-backend:
        condition: service_healthy

    logging:
      driver: json-file
      options:
        max-size: 10m
        max-file: "3"

# ============================================================================
# Networks
# ============================================================================
networks:
  tk9-network:
    driver: bridge
    name: tk9-network
```

**Step 3: Create docker-compose.override.yml for development**

Create: `docker-compose.override.yml`

```yaml
# Local Development Override
# Automatically merged with docker-compose.yml

version: '3.8'

services:
  tk9-backend:
    # Hot reload for backend
    volumes:
      - ./multi_agents:/app/multi_agents:ro
      - ./web_dashboard:/app/web_dashboard:ro
      - ./providers:/app/providers:ro

    environment:
      - DEBUG=true
      - LOG_LEVEL=DEBUG

    command: ["python", "-m", "uvicorn", "web_dashboard.main:app", "--host", "0.0.0.0", "--port", "12689", "--reload"]

  tk9-frontend:
    # For development, use Vite dev server instead of nginx
    build:
      target: builder

    command: ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "8592"]

    volumes:
      - ./web_dashboard/frontend_poc/src:/build/src:ro
```

**Step 4: Test full stack locally**

Run:
```bash
cd /Users/thinhkhuat/»DEV•local«/tk9_source_deploy

# Create .env
cp web_dashboard/.env web_dashboard/.env.backup
cat > .env << EOF
GOOGLE_API_KEY=your-key
BRAVE_API_KEY=your-key
BUILD_VERSION=v2.0.0
TAG=latest
EOF

# Build and start
docker-compose up --build -d

# Check logs
docker-compose logs -f

# Test endpoints
curl http://localhost:12689/health  # Backend
curl http://localhost:8592          # Frontend
```

Expected:
- Both services start successfully
- Backend health check returns 200
- Frontend serves Vue app
- No ModuleNotFoundError

**Step 5: Commit docker-compose files**

```bash
git add docker-compose.yml docker-compose.override.yml .dockerignore
git commit -m "feat(docker): Complete docker-compose for dual-service architecture

- Backend (FastAPI) on port 12689
- Frontend (Vue 3) on port 8592
- Network isolation with tk9-network
- Health checks for both services
- Resource limits optimized for 7-agent system
- Development override for hot reload
- Created .dockerignore for clean builds"
```

---

## Task 4: Update Deployment Scripts for Dual Services

**Files:**
- Update: `deploy/deploy.sh`
- Update: `deploy/README.md`

**Step 1: Update deployment script for dual services**

Update: `deploy/deploy.sh` (add after build_images function)

```bash
verify_services() {
    log "Verifying both services..."

    # Check backend
    MAX_RETRIES=30
    RETRY_COUNT=0

    log "Checking backend (port 12689)..."
    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        if curl -f http://localhost:12689/health &>/dev/null; then
            log "✓ Backend health check passed"
            break
        fi
        RETRY_COUNT=$((RETRY_COUNT + 1))
        sleep 2
    done

    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        error "Backend health check failed"
    fi

    # Check frontend
    RETRY_COUNT=0
    log "Checking frontend (port 8592)..."
    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        if curl -f http://localhost:8592 &>/dev/null; then
            log "✓ Frontend is serving"
            break
        fi
        RETRY_COUNT=$((RETRY_COUNT + 1))
        sleep 2
    done

    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        error "Frontend check failed"
    fi

    log "✓ All services verified"
}
```

**Step 2: Update show_status function**

Update in `deploy/deploy.sh`:

```bash
show_status() {
    log "Deployment Status:"
    cd "$DEPLOY_PATH"
    docker-compose ps

    log ""
    log "Access points:"
    log "  Backend:"
    log "    - Local: http://localhost:12689"
    log "    - Internal: http://192.168.2.22:12689"
    log ""
    log "  Frontend:"
    log "    - Local: http://localhost:8592"
    log "    - Internal: http://192.168.2.22:8592"
    log "    - Public: https://tk9v2.thinhkhuat.com"
    log ""
    log "Useful commands:"
    log "  - View logs: cd $DEPLOY_PATH && docker-compose logs -f"
    log "  - Backend logs: docker-compose logs -f tk9-backend"
    log "  - Frontend logs: docker-compose logs -f tk9-frontend"
    log "  - Restart: docker-compose restart"
    log "  - Stop: docker-compose down"
}
```

**Step 3: Test deployment script**

Run:
```bash
./deploy/deploy.sh
```

Expected: Complete deployment with both services verified

**Step 4: Commit deployment updates**

```bash
git add deploy/
git commit -m "feat(deploy): Update deployment scripts for dual-service architecture

- Added verification for both backend and frontend
- Updated status display with both service endpoints
- Added separate log commands for each service
- Enhanced health checks for complete stack"
```

---

## Task 5: Configure Caddy v2 for External Routing

**Files:**
- Document: Caddyfile configuration for tk9v2.thinhkhuat.com

**Architecture Reminder:**
```
Caddy v2 = External traffic manager (SSL, routing, WebSocket)
Nginx = Internal static file server (SPA routing only)
```

**Step 1: Create Caddyfile configuration**

Add to your Caddyfile:

```caddy
# TK9 v2 Dashboard - Caddy-First Architecture
# Caddy handles: HTTPS, WebSocket upgrades, routing
# Nginx handles: Static files, SPA fallback routing

tk9v2.thinhkhuat.com {
    # Automatic HTTPS with Let's Encrypt (Caddy default)
    # Automatic HTTP/2 and compression

    # Frontend - Static files and SPA routes (default)
    # All requests go here unless matched below
    reverse_proxy localhost:8592 {
        # Frontend health check
        health_uri /
        health_interval 30s
    }

    # Backend API - Explicit routing
    handle_path /api/* {
        reverse_proxy localhost:12689 {
            # Backend health check
            health_uri /health
            health_interval 30s
        }
    }

    # WebSocket - Real-time agent updates
    # Caddy automatically handles WebSocket upgrade headers
    handle_path /ws/* {
        reverse_proxy localhost:12689
    }

    # Access logging
    log {
        output file /var/log/caddy/tk9v2-access.log {
            roll_size 100mb
            roll_keep 10
        }
        format json
        level INFO
    }

    # Error handling
    handle_errors {
        @5xx expression {http.error.status_code} >= 500
        respond @5xx "Service temporarily unavailable" 503
    }
}
```

**Why This Configuration Works:**

1. **Frontend (/)**: Caddy forwards to nginx:8592 → nginx serves static files + SPA routing
2. **API (/api/*)**: Caddy forwards directly to FastAPI:12689
3. **WebSocket (/ws/*)**: Caddy forwards to FastAPI:12689 with automatic upgrade headers
4. **HTTPS**: Caddy automatically obtains and renews SSL certificates
5. **No CORS needed**: All traffic appears to come from same domain

**Step 2: Reload Caddy configuration**

Run:
```bash
# Test configuration first
caddy validate --config /path/to/Caddyfile

# Reload without downtime
caddy reload --config /path/to/Caddyfile
```

**Step 3: Verify routing**

Test each route:
```bash
# Frontend
curl -I https://tk9v2.thinhkhuat.com
# Expected: 200 OK, HTML from Vue app

# Backend API
curl -I https://tk9v2.thinhkhuat.com/api/health
# Expected: 200 OK, JSON health status

# WebSocket (check with browser DevTools or wscat)
wscat -c wss://tk9v2.thinhkhuat.com/ws/
# Expected: WebSocket connection established
```

**Step 4: Document current setup**

Create: `docs/CADDY_CONFIGURATION.md`

```markdown
# Caddy v2 Configuration for TK9

## Architecture

Caddy v2 is the **external reverse proxy** handling:
- ✅ Auto HTTPS/SSL (Let's Encrypt)
- ✅ WebSocket upgrade headers (automatic)
- ✅ Traffic routing (/, /api/*, /ws/*)
- ✅ Compression (gzip/brotli)
- ✅ HTTP/2

Nginx is **internal** (inside Docker) handling:
- ✅ Static file serving
- ✅ SPA routing (try_files fallback)
- ✅ Asset caching

## Current Caddyfile

See main Caddyfile for complete configuration.

## Services Managed

- tk9.thinhkhuat.com (v1 - legacy)
- tk9v2.thinhkhuat.com (v2 - current)
- Dozens of other services

## Why Caddy?

1. **Automatic HTTPS** - No manual certificate management
2. **Zero config WebSockets** - Upgrade headers handled automatically
3. **Performance** - Built-in HTTP/2, compression
4. **Simplicity** - JSON or Caddyfile syntax
5. **Reliability** - Battle-tested across your infrastructure
```

**Step 5: Commit documentation**

```bash
git add docs/CADDY_CONFIGURATION.md
git commit -m "docs(caddy): Document Caddy v2 reverse proxy configuration

- Caddy handles external routing, SSL, WebSocket upgrades
- Nginx handles internal static serving and SPA routing
- Clear separation of concerns
- Complete Caddyfile example for tk9v2.thinhkhuat.com"
```

---

## Task 6: Create Comprehensive Documentation

**Files:**
- Create: `docs/DOCKER_DEPLOYMENT_DUAL_SERVICE.md`

**Step 1: Create dual-service deployment guide**

Create: `docs/DOCKER_DEPLOYMENT_DUAL_SERVICE.md`

```markdown
# TK9 Deep Research MCP - Dual Service Docker Deployment

## Architecture Overview

```
┌──────────────────────────────────────────────────┐
│         Caddy Reverse Proxy                      │
│         tk9v2.thinhkhuat.com                     │
└────────┬──────────────┬──────────────────────────┘
         │              │
    ┌────┴─────┐   ┌────┴──────┐
    │ Frontend │   │  Backend  │
    │ Vue 3    │   │  FastAPI  │
    │ Port8592 │   │ Port12689 │
    │ Nginx    │   │  Python   │
    └──────────┘   └───────────┘
```

## Services

### Backend (FastAPI)
- **Port**: 12689
- **Technology**: Python 3.12+, FastAPI, LangGraph
- **Purpose**: 7-agent research orchestration
- **Health**: http://localhost:12689/health

### Frontend (Vue 3)
- **Port**: 8592
- **Technology**: Vue 3, Vite, TypeScript, Tailwind CSS
- **Purpose**: User interface for research dashboard
- **Serves**: Production-built static files via nginx

## Quick Deploy

```bash
# 1. Configure environment
cp .env.example .env
nano .env  # Add API keys

# 2. Deploy
./deploy/deploy.sh

# 3. Verify
curl http://localhost:12689/health  # Backend
curl http://localhost:8592           # Frontend
```

## Manual Deployment

### Build Images

```bash
# Backend
docker build -f Dockerfile.backend -t tk9-backend:latest .

# Frontend
docker build -f Dockerfile.frontend -t tk9-frontend:latest .
```

### Start Services

```bash
docker-compose up -d
```

### Verify Deployment

```bash
# Check status
docker-compose ps

# View logs
docker-compose logs -f tk9-backend
docker-compose logs -f tk9-frontend

# Test endpoints
curl http://localhost:12689/health
curl http://localhost:8592
```

## Environment Variables

### Backend (.env)

```bash
# Required
GOOGLE_API_KEY=your-key
BRAVE_API_KEY=your-key

# Optional
OPENAI_API_KEY=your-key
TAVILY_API_KEY=your-key
ANTHROPIC_API_KEY=your-key

# Config
PRIMARY_LLM_PROVIDER=google_gemini
PRIMARY_LLM_MODEL=gemini-2.5-flash-preview-04-17-thinking
PRIMARY_SEARCH_PROVIDER=brave
RESEARCH_LANGUAGE=vi
```

### Frontend Environment

Frontend config is baked into build from:
- `web_dashboard/frontend_poc/.env`
- `VITE_API_BASE_URL` points to backend

## Troubleshooting

### Backend: ModuleNotFoundError

**Solution**:
```bash
# Rebuild without cache
docker-compose down
docker build --no-cache -f Dockerfile.backend -t tk9-backend:latest .
docker-compose up -d

# Verify langgraph installed
docker exec tk9-backend python -c "import langgraph; print(langgraph.__version__)"
```

### Frontend: 404 on Routes

**Cause**: Nginx not configured for SPA routing

**Solution**: Check `Dockerfile.frontend` has:
```nginx
location / {
    try_files $uri $uri/ /index.html;
}
```

### CORS Errors

**Solution**: Add frontend URL to backend CORS:
```bash
CORS_ORIGINS=http://localhost:8592,https://tk9v2.thinhkhuat.com
```

### WebSocket Connection Failed

**Solution**: Ensure Caddy config has WebSocket upgrade:
```caddy
@websockets {
    header Connection *Upgrade*
    header Upgrade websocket
}
```

## Development Mode

Use docker-compose.override.yml:

```bash
docker-compose up
# Both services have hot reload enabled
```

## Production Checklist

- [ ] API keys configured in .env
- [ ] Build both images successfully
- [ ] Backend health check passes
- [ ] Frontend serves correctly
- [ ] Caddy configuration updated
- [ ] Domain resolves to server
- [ ] WebSocket connections work
- [ ] CORS configured correctly
- [ ] Logs directory created
- [ ] Backups configured

## Access Points

### Local Development
- **Backend**: http://localhost:12689
- **Frontend**: http://localhost:8592

### Internal Network
- **Backend**: http://192.168.2.22:12689
- **Frontend**: http://192.168.2.22:8592

### Production
- **Public**: https://tk9v2.thinhkhuat.com (via Caddy)

## Monitoring

```bash
# Resource usage
docker stats

# Service status
docker-compose ps

# Logs
docker-compose logs -f

# Backend logs only
docker-compose logs -f tk9-backend

# Frontend logs only
docker-compose logs -f tk9-frontend
```

## Maintenance

### Update Application

```bash
./deploy/update.sh
```

### Restart Services

```bash
docker-compose restart
```

### Rebuild from Scratch

```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Rollback

```bash
./deploy/rollback.sh
```

## Architecture Notes

**Separation of Concerns:**

1. **Caddy v2 (External Layer)**
   - HTTPS/SSL (automatic Let's Encrypt)
   - Traffic routing (/, /api/*, /ws/*)
   - WebSocket upgrade headers (automatic)
   - Compression and HTTP/2

2. **Nginx (Internal Container Layer)**
   - Static file serving only
   - SPA routing (try_files fallback)
   - Asset caching
   - NO proxying to backend (Caddy does this)

3. **Services**
   - Frontend: nginx:8592 (static files + SPA)
   - Backend: FastAPI:12689 (API + WebSocket)

4. **Why This Architecture?**
   - Caddy already manages dozens of services
   - No duplication of proxy logic
   - Cleaner container isolation
   - Simpler debugging (clear responsibilities)
```

**Step 2: Commit documentation**

```bash
git add docs/DOCKER_DEPLOYMENT_DUAL_SERVICE.md
git commit -m "docs(docker): Add comprehensive dual-service deployment guide

- Architecture diagram showing both services
- Backend (port 12689) and Frontend (port 8592) deployment
- Troubleshooting for ModuleNotFoundError
- CORS and WebSocket configuration
- Development and production modes
- Complete production checklist"
```

---

## Execution Summary

**Plan saved to**: `docs/plans/2025-11-03-docker-deployment-fix-UPDATED.md`

**Architecture: Caddy-First Design**
```
Caddy v2 (External) → nginx:8592 (Frontend) + FastAPI:12689 (Backend)
                       ↓                       ↓
                   Static + SPA          API + WebSocket
```

**Complete Plan Tasks**:
1. ✅ Backend Dockerfile (FastAPI + langgraph dependencies)
2. ✅ Frontend Dockerfile (Vue 3 production with nginx SPA routing)
3. ✅ Docker Compose (dual-service orchestration with health checks)
4. ✅ Deployment scripts (verification for both services)
5. ✅ Caddy v2 configuration (external routing, SSL, WebSocket)
6. ✅ Comprehensive documentation (deployment + Caddy)

**Services**:
- **Backend**: Port 12689 (Python 3.12+, FastAPI, 7 agents, langgraph)
- **Frontend**: Port 8592 (Vue 3, Vite, nginx for static + SPA routing)

**Key Architectural Decisions**:
- ✅ Caddy v2 handles all external routing (no nginx proxying)
- ✅ Nginx simplified to static file server + SPA fallback only
- ✅ No CORS needed (single domain via Caddy)
- ✅ Caddy auto-handles WebSocket upgrades
- ✅ Clear separation: External (Caddy) vs Internal (nginx)

**Fixes Implemented**:
- ✅ ModuleNotFoundError: langgraph now in requirements-backend.txt
- ✅ Missing frontend: Complete Vue 3 Dockerfile added
- ✅ uv issues: Replaced with pip + virtual env
- ✅ Multi-service: docker-compose orchestrates both

**Next Steps**:
1. Execute plan using superpowers:executing-plans
2. Test locally first (localhost:12689 + localhost:8592)
3. Deploy to `/Users/thinhkhuat/Docker/Caddy/site/tk9v2`
4. Update Caddy configuration with new block
5. Verify tk9v2.thinhkhuat.com domain access

---

## Ready to Execute?

The plan is complete and reflects your Caddy-first infrastructure. All architectural decisions documented.

Shall I proceed with implementation?

# Docker Deployment Fix Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix ModuleNotFoundError for langgraph and properly containerize TK9 Deep Research MCP with all dependencies

**Architecture:** Refactor Dockerfile to use pip with requirements files instead of uv, update docker-compose.yml for web dashboard deployment, ensure Python 3.12+ compatibility, and add proper volume mounts for the deployment location

**Tech Stack:** Docker, Docker Compose, Python 3.12+, pip, FastAPI, LangGraph

---

## Problem Analysis

**Current Issue:**
```
ModuleNotFoundError: No module named 'langgraph'
```

**Root Causes:**
1. Dockerfile uses `uv sync` but no proper `pyproject.toml` or `uv.lock` exists
2. Dependencies are split between `multi_agents/requirements.txt` and `requirements-prod.txt`
3. Dockerfile expects uv package manager but requirements use pip
4. Docker image doesn't properly install multi_agents dependencies
5. Deployment path is `/Users/thinhkhuat/Docker/Caddy/site/tk9v2/` but container expects `/app/`

---

## Task 1: Fix Dockerfile to Use Pip with Proper Dependencies

**Files:**
- Modify: `Dockerfile` (entire file)
- Reference: `multi_agents/requirements.txt`
- Reference: `requirements-prod.txt`

**Step 1: Create consolidated requirements file for Docker**

Create: `requirements.txt`

```txt
# TK9 Deep Research MCP - Docker Production Dependencies
# Consolidated from multi_agents/requirements.txt and requirements-prod.txt

# ============================================================================
# Core Multi-Agent Framework (from multi_agents/requirements.txt)
# ============================================================================
langgraph>=0.0.20
gpt-researcher>=0.14.1
langgraph-cli
python-dotenv>=1.0.0
weasyprint>=60.0
json5
loguru

# ============================================================================
# Core Framework Dependencies
# ============================================================================
fastapi>=0.116.0
uvicorn[standard]>=0.25.0
pydantic>=2.5.0
pydantic-settings>=2.1.0

# ============================================================================
# LangChain Dependencies
# ============================================================================
langchain>=0.1.0
langchain-community>=0.0.10

# ============================================================================
# LLM Provider Dependencies
# ============================================================================
openai>=1.12.0
google-generativeai>=0.8.0
anthropic>=0.25.0

# ============================================================================
# Search and Web Scraping
# ============================================================================
aiohttp>=3.10.0
requests>=2.31.0
beautifulsoup4>=4.12.0
lxml>=4.9.0
httpx>=0.26.0

# ============================================================================
# Document Processing and Export
# ============================================================================
jinja2>=3.1.0
pypandoc>=1.11
python-docx>=1.1.0
reportlab>=4.0.0

# ============================================================================
# Async and Concurrency
# ============================================================================
nest-asyncio>=1.6.0
asyncio-throttle>=1.0.0

# ============================================================================
# Database and Caching
# ============================================================================
redis>=5.0.0
sqlalchemy>=2.0.0
alembic>=1.13.0

# ============================================================================
# Monitoring and Logging
# ============================================================================
prometheus-client>=0.19.0
structlog>=23.2.0
python-json-logger>=2.0.0

# ============================================================================
# Security and Validation
# ============================================================================
cryptography>=41.0.0
python-multipart>=0.0.6
email-validator>=2.1.0
certifi>=2023.11.17

# ============================================================================
# Data Processing
# ============================================================================
pandas>=2.1.0
numpy>=1.24.0
python-dateutil>=2.8.0
python-magic>=0.4.27

# ============================================================================
# Production Server
# ============================================================================
gunicorn>=21.2.0
supervisor>=4.2.0
psutil>=5.9.0

# ============================================================================
# MCP Server
# ============================================================================
mcp>=0.9.0
```

**Step 2: Rewrite Dockerfile to use pip**

Update: `Dockerfile`

```dockerfile
# Dockerfile for TK9 Deep Research MCP Server
# Multi-stage build for optimized production image with Python 3.12+

# ============================================================================
# Stage 1: Build stage with full Python toolchain
# ============================================================================
FROM python:3.12-slim as builder

# Set environment variables for build optimization
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

# Install system dependencies for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /build

# Copy requirements files
COPY requirements.txt ./

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies with verbose output for debugging
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt --verbose

# ============================================================================
# Stage 2: Runtime stage with minimal dependencies
# ============================================================================
FROM python:3.12-slim as runtime

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app:$PYTHONPATH"

# Install runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    pandoc \
    texlive-latex-base \
    texlive-fonts-recommended \
    texlive-fonts-extra \
    texlive-latex-extra \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r appgroup && useradd -r -g appgroup -d /app -s /bin/bash appuser

# Set work directory
WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder --chown=appuser:appgroup /opt/venv /opt/venv

# Copy application code
COPY --chown=appuser:appgroup . .

# Create required directories with proper permissions
RUN mkdir -p /app/outputs /app/logs /app/data /app/web_dashboard \
    && chown -R appuser:appgroup /app

# Health check endpoint (for web dashboard)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:12656/health || exit 1

# Switch to non-root user
USER appuser

# Expose ports
# 12656 for web dashboard
# 8000 for MCP server
EXPOSE 12656 8000

# Default command - web dashboard
CMD ["python", "web_dashboard/main.py"]

# ============================================================================
# Build arguments for customization
# ============================================================================
ARG BUILD_VERSION=latest
ARG BUILD_DATE
ARG VCS_REF

# Metadata labels
LABEL maintainer="TK9 Deep Research Team" \
      version="${BUILD_VERSION}" \
      description="TK9 Multi-agent deep research system with 7 active agents" \
      org.opencontainers.image.title="TK9 Deep Research MCP" \
      org.opencontainers.image.description="7-agent deep research system with orchestrator" \
      org.opencontainers.image.version="${BUILD_VERSION}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.revision="${VCS_REF}"
```

**Step 3: Test Docker build locally**

Run:
```bash
cd /Users/thinhkhuat/»DEV•local«/tk9_source_deploy
docker build -t tk9-deep-research:test .
```

Expected: Build completes successfully with all dependencies installed

**Step 4: Verify langgraph is installed**

Run:
```bash
docker run --rm tk9-deep-research:test python -c "import langgraph; print('langgraph version:', langgraph.__version__)"
```

Expected: Prints langgraph version without errors

**Step 5: Commit Dockerfile changes**

```bash
git add Dockerfile requirements.txt
git commit -m "fix(docker): Replace uv with pip, consolidate requirements for proper dependency installation

- Consolidated multi_agents/requirements.txt and requirements-prod.txt
- Changed from uv to pip for better compatibility
- Added Python 3.12-slim base image (3.12+ required)
- Fixed langgraph ModuleNotFoundError
- Added health check for web dashboard on port 12656
- Updated metadata labels for TK9 7-agent system"
```

---

## Task 2: Update Docker Compose for Web Dashboard Deployment

**Files:**
- Modify: `docker-compose.yml` (major refactor)
- Create: `.dockerignore`
- Create: `docker-compose.override.yml` (for local development)

**Step 1: Create .dockerignore file**

Create: `.dockerignore`

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Environment
.env
.env.local
.env.*.local
*.env

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/
.hypothesis/

# Logs
logs/
*.log

# Outputs
outputs/
data/

# Git
.git/
.gitignore
.gitattributes

# Documentation
docs/
*.md
!README.md

# Archives
ARCHIVE/

# Node (if any)
node_modules/
npm-debug.log

# Temporary files
tmp/
temp/
*.tmp

# Docker
Dockerfile*
docker-compose*
.dockerignore
```

**Step 2: Create updated docker-compose.yml for web dashboard**

Update: `docker-compose.yml`

```yaml
version: '3.8'

services:
  # ============================================================================
  # TK9 Web Dashboard (v2) - Main Service
  # ============================================================================
  tk9-dashboard:
    build:
      context: .
      dockerfile: Dockerfile
      args:
        BUILD_VERSION: ${BUILD_VERSION:-v2.0.0}
        BUILD_DATE: ${BUILD_DATE}
        VCS_REF: ${VCS_REF}
    image: tk9-deep-research:${TAG:-latest}
    container_name: tk9-dashboard
    restart: unless-stopped

    # Environment configuration
    environment:
      # Server Configuration
      - HOST=0.0.0.0
      - PORT=12656
      - NODE_ENV=${NODE_ENV:-production}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - DEBUG=${DEBUG:-false}

      # Multi-Provider Configuration (7 Active Agents System)
      - PRIMARY_LLM_PROVIDER=${PRIMARY_LLM_PROVIDER:-google_gemini}
      - PRIMARY_LLM_MODEL=${PRIMARY_LLM_MODEL:-gemini-2.5-flash-preview-04-17-thinking}
      - PRIMARY_SEARCH_PROVIDER=${PRIMARY_SEARCH_PROVIDER:-brave}

      # API Keys (loaded from .env)
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - TAVILY_API_KEY=${TAVILY_API_KEY}
      - BRAVE_API_KEY=${BRAVE_API_KEY}

      # Language and Search Configuration
      - RESEARCH_LANGUAGE=${RESEARCH_LANGUAGE:-vi}
      - SEARCH_COUNTRY=${SEARCH_COUNTRY:-VN}
      - SEARCH_LANGUAGE=${SEARCH_LANGUAGE:-vi}

      # Provider Settings
      - PROVIDER_TIMEOUT=${PROVIDER_TIMEOUT:-30}
      - PROVIDER_MAX_RETRIES=${PROVIDER_MAX_RETRIES:-3}
      - LLM_STRATEGY=${LLM_STRATEGY:-primary_only}
      - SEARCH_STRATEGY=${SEARCH_STRATEGY:-primary_only}

      # BRAVE Search Configuration
      - RETRIEVER=${RETRIEVER:-custom}
      - RETRIEVER_ENDPOINT=${RETRIEVER_ENDPOINT:-https://brave-local-provider.local}

      # Feature Flags
      - ENABLE_CACHING=${ENABLE_CACHING:-true}
      - COST_TRACKING=${COST_TRACKING:-true}

    # Port mapping - Web Dashboard
    ports:
      - "${DASHBOARD_PORT:-12656}:12656"

    # Volume mounts for persistent data
    volumes:
      - ./outputs:/app/outputs:rw
      - ./logs:/app/logs:rw
      - ./data:/app/data:rw
      - ./.env:/app/.env:ro

    # Resource limits (optimized for 7-agent system)
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 8G
        reservations:
          cpus: '1.0'
          memory: 2G

    # Health check for web dashboard
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:12656/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

    # Logging configuration
    logging:
      driver: json-file
      options:
        max-size: 10m
        max-file: "5"

    # Network configuration
    networks:
      - tk9-network

    # Dependencies
    depends_on:
      redis:
        condition: service_healthy

  # ============================================================================
  # Redis Cache (Required for session management and caching)
  # ============================================================================
  redis:
    image: redis:7-alpine
    container_name: tk9-redis
    restart: unless-stopped
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD:-tk9deepresearch2024}

    ports:
      - "${REDIS_PORT:-6379}:6379"

    volumes:
      - redis_data:/data

    environment:
      - REDIS_PASSWORD=${REDIS_PASSWORD:-tk9deepresearch2024}

    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.25'
          memory: 256M

    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 10s

    networks:
      - tk9-network

  # ============================================================================
  # Prometheus (Optional - for monitoring)
  # ============================================================================
  prometheus:
    image: prom/prometheus:latest
    container_name: tk9-prometheus
    restart: unless-stopped

    ports:
      - "${PROMETHEUS_PORT:-9090}:9090"

    volumes:
      - ./deploy/monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus

    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.enable-lifecycle'

    networks:
      - tk9-network

    profiles:
      - monitoring

  # ============================================================================
  # Grafana Dashboard (Optional - for monitoring visualization)
  # ============================================================================
  grafana:
    image: grafana/grafana:latest
    container_name: tk9-grafana
    restart: unless-stopped

    ports:
      - "${GRAFANA_PORT:-3000}:3000"

    volumes:
      - grafana_data:/var/lib/grafana

    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD:-admin}
      - GF_USERS_ALLOW_SIGN_UP=false

    depends_on:
      - prometheus

    networks:
      - tk9-network

    profiles:
      - monitoring

# ============================================================================
# Networks
# ============================================================================
networks:
  tk9-network:
    driver: bridge
    name: tk9-network

# ============================================================================
# Volumes
# ============================================================================
volumes:
  redis_data:
    name: tk9-redis-data
  prometheus_data:
    name: tk9-prometheus-data
  grafana_data:
    name: tk9-grafana-data
```

**Step 3: Create docker-compose.override.yml for local development**

Create: `docker-compose.override.yml`

```yaml
# Docker Compose Override for Local Development
# This file is automatically merged with docker-compose.yml when running docker-compose
# Use this for local development overrides

version: '3.8'

services:
  tk9-dashboard:
    # Override for local development
    build:
      target: runtime

    # Mount source code for hot reload (development only)
    volumes:
      - ./multi_agents:/app/multi_agents:ro
      - ./web_dashboard:/app/web_dashboard:ro
      - ./providers:/app/providers:ro
      - ./config:/app/config:ro
      - ./outputs:/app/outputs:rw
      - ./logs:/app/logs:rw

    # Enable debug mode
    environment:
      - DEBUG=true
      - LOG_LEVEL=DEBUG

    # Override command for development
    command: ["python", "-m", "uvicorn", "web_dashboard.main:app", "--host", "0.0.0.0", "--port", "12656", "--reload"]
```

**Step 4: Create .env.example for deployment**

Create: `.env.example`

```bash
# TK9 Deep Research MCP - Environment Configuration
# Copy this file to .env and fill in your actual values

# ============================================================================
# Build Configuration
# ============================================================================
BUILD_VERSION=v2.0.0
TAG=latest
NODE_ENV=production

# ============================================================================
# Server Configuration
# ============================================================================
DASHBOARD_PORT=12656
HOST=0.0.0.0
LOG_LEVEL=INFO
DEBUG=false

# ============================================================================
# Primary Providers (Recommended Configuration)
# ============================================================================
PRIMARY_LLM_PROVIDER=google_gemini
PRIMARY_LLM_MODEL=gemini-2.5-flash-preview-04-17-thinking
PRIMARY_SEARCH_PROVIDER=brave

# ============================================================================
# API Keys (REQUIRED - Add your actual keys)
# ============================================================================
GOOGLE_API_KEY=your-google-api-key-here
BRAVE_API_KEY=your-brave-api-key-here
OPENAI_API_KEY=your-openai-api-key-here
TAVILY_API_KEY=your-tavily-api-key-here
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# ============================================================================
# Language and Search Settings
# ============================================================================
RESEARCH_LANGUAGE=vi
SEARCH_COUNTRY=VN
SEARCH_LANGUAGE=vi

# ============================================================================
# Provider Settings
# ============================================================================
PROVIDER_TIMEOUT=30
PROVIDER_MAX_RETRIES=3
LLM_STRATEGY=primary_only
SEARCH_STRATEGY=primary_only

# ============================================================================
# BRAVE Search Configuration
# ============================================================================
RETRIEVER=custom
RETRIEVER_ENDPOINT=https://brave-local-provider.local

# ============================================================================
# Feature Flags
# ============================================================================
ENABLE_CACHING=true
COST_TRACKING=true

# ============================================================================
# Redis Configuration
# ============================================================================
REDIS_PORT=6379
REDIS_PASSWORD=tk9deepresearch2024

# ============================================================================
# Optional Monitoring
# ============================================================================
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
GRAFANA_PASSWORD=admin
```

**Step 5: Test docker-compose locally**

Run:
```bash
cd /Users/thinhkhuat/»DEV•local«/tk9_source_deploy

# Create .env from example
cp .env.example .env
# Edit .env with actual API keys

# Build and start services
docker-compose up --build -d

# Check logs
docker-compose logs -f tk9-dashboard

# Test health endpoint
curl http://localhost:12656/health
```

Expected:
- Services start successfully
- No ModuleNotFoundError
- Health endpoint returns 200 OK
- Dashboard accessible at http://localhost:12656

**Step 6: Commit docker-compose changes**

```bash
git add docker-compose.yml docker-compose.override.yml .dockerignore .env.example
git commit -m "feat(docker): Update docker-compose for TK9 web dashboard deployment

- Refactored docker-compose.yml for 7-agent system
- Added web dashboard as main service on port 12656
- Added Redis dependency for session management
- Created .dockerignore for cleaner builds
- Added docker-compose.override.yml for local development
- Created .env.example with all configuration options
- Updated resource limits for multi-agent orchestration
- Added health checks and proper logging"
```

---

## Task 3: Create Deployment Scripts for Remote Server

**Files:**
- Create: `deploy/deploy.sh`
- Create: `deploy/update.sh`
- Create: `deploy/rollback.sh`
- Create: `deploy/README.md`

**Step 1: Create main deployment script**

Create: `deploy/deploy.sh`

```bash
#!/bin/bash
# TK9 Deep Research MCP - Production Deployment Script
# Deploys to remote server with proper error handling

set -e  # Exit on error
set -u  # Exit on undefined variable

# ============================================================================
# Configuration
# ============================================================================
DEPLOY_PATH="/Users/thinhkhuat/Docker/Caddy/site/tk9v2"
BACKUP_PATH="/Users/thinhkhuat/Docker/Caddy/backups/tk9v2"
LOG_FILE="/Users/thinhkhuat/Docker/Caddy/logs/deploy-$(date +%Y%m%d-%H%M%S).log"
REQUIRED_PYTHON_VERSION="3.12"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ============================================================================
# Functions
# ============================================================================

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1" | tee -a "$LOG_FILE"
}

check_requirements() {
    log "Checking deployment requirements..."

    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
    fi

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed"
    fi

    # Check Python version
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1-2)
    if [ "$(printf '%s\n' "$REQUIRED_PYTHON_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_PYTHON_VERSION" ]; then
        error "Python $REQUIRED_PYTHON_VERSION+ is required (found $PYTHON_VERSION)"
    fi

    # Check .env file
    if [ ! -f ".env" ]; then
        error ".env file not found. Copy from .env.example and configure."
    fi

    log "✓ All requirements met"
}

create_backup() {
    log "Creating backup..."

    mkdir -p "$BACKUP_PATH"
    BACKUP_NAME="tk9v2-backup-$(date +%Y%m%d-%H%M%S).tar.gz"

    if [ -d "$DEPLOY_PATH" ]; then
        cd "$DEPLOY_PATH/.."
        tar -czf "$BACKUP_PATH/$BACKUP_NAME" tk9v2/ 2>/dev/null || warn "Backup creation had warnings"
        log "✓ Backup created: $BACKUP_NAME"
    else
        warn "Deploy path does not exist, skipping backup"
    fi
}

stop_services() {
    log "Stopping existing services..."

    if [ -d "$DEPLOY_PATH" ] && [ -f "$DEPLOY_PATH/docker-compose.yml" ]; then
        cd "$DEPLOY_PATH"
        docker-compose down || warn "Some containers may not have stopped cleanly"
    fi

    log "✓ Services stopped"
}

deploy_code() {
    log "Deploying code to $DEPLOY_PATH..."

    # Create deploy directory if it doesn't exist
    mkdir -p "$DEPLOY_PATH"

    # Copy files (excluding what's in .dockerignore)
    rsync -av --delete \
        --exclude='.git' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='.env' \
        --exclude='venv' \
        --exclude='.venv' \
        --exclude='logs/*' \
        --exclude='outputs/*' \
        --exclude='data/*' \
        --exclude='ARCHIVE' \
        --exclude='docs' \
        --exclude='node_modules' \
        ./ "$DEPLOY_PATH/"

    # Copy .env if it doesn't exist
    if [ ! -f "$DEPLOY_PATH/.env" ]; then
        cp .env "$DEPLOY_PATH/.env"
        log "✓ Copied .env file"
    fi

    log "✓ Code deployed"
}

build_images() {
    log "Building Docker images..."

    cd "$DEPLOY_PATH"
    docker-compose build --no-cache

    log "✓ Images built"
}

start_services() {
    log "Starting services..."

    cd "$DEPLOY_PATH"
    docker-compose up -d

    log "✓ Services started"
}

verify_deployment() {
    log "Verifying deployment..."

    # Wait for services to be ready
    sleep 10

    # Check container status
    cd "$DEPLOY_PATH"
    if ! docker-compose ps | grep -q "Up"; then
        error "Containers are not running"
    fi

    # Check health endpoint
    MAX_RETRIES=30
    RETRY_COUNT=0

    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        if curl -f http://localhost:12656/health &>/dev/null; then
            log "✓ Health check passed"
            break
        fi

        RETRY_COUNT=$((RETRY_COUNT + 1))
        log "Waiting for service to be ready... ($RETRY_COUNT/$MAX_RETRIES)"
        sleep 2
    done

    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        error "Service health check failed after $MAX_RETRIES attempts"
    fi

    # Check logs for errors
    if docker-compose logs tk9-dashboard | grep -i "error" | grep -v "404" &>/dev/null; then
        warn "Errors found in logs, please check: docker-compose logs tk9-dashboard"
    fi

    log "✓ Deployment verified"
}

show_status() {
    log "Deployment Status:"
    cd "$DEPLOY_PATH"
    docker-compose ps

    log ""
    log "Access points:"
    log "  - Local: http://localhost:12656"
    log "  - Internal: http://192.168.2.22:12656"
    log "  - Public v2: https://tk9v2.thinhkhuat.com"
    log ""
    log "Useful commands:"
    log "  - View logs: cd $DEPLOY_PATH && docker-compose logs -f"
    log "  - Restart: cd $DEPLOY_PATH && docker-compose restart"
    log "  - Stop: cd $DEPLOY_PATH && docker-compose down"
}

# ============================================================================
# Main Deployment Flow
# ============================================================================

main() {
    log "========================================="
    log "TK9 Deep Research MCP Deployment"
    log "========================================="
    log ""

    check_requirements
    create_backup
    stop_services
    deploy_code
    build_images
    start_services
    verify_deployment
    show_status

    log ""
    log "========================================="
    log "✓ Deployment completed successfully!"
    log "========================================="
}

# Run main function
main "$@"
```

**Step 2: Make deployment script executable**

Run:
```bash
chmod +x deploy/deploy.sh
```

**Step 3: Create update script (for quick updates without rebuild)**

Create: `deploy/update.sh`

```bash
#!/bin/bash
# TK9 Deep Research MCP - Quick Update Script
# Updates code and restarts services without full rebuild

set -e

DEPLOY_PATH="/Users/thinhkhuat/Docker/Caddy/site/tk9v2"

echo "Updating TK9 Deep Research MCP..."

# Copy updated code
rsync -av --delete \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='.env' \
    --exclude='logs/*' \
    --exclude='outputs/*' \
    ./ "$DEPLOY_PATH/"

# Restart services
cd "$DEPLOY_PATH"
docker-compose restart tk9-dashboard

echo "✓ Update complete"
echo "Check logs: docker-compose logs -f tk9-dashboard"
```

**Step 4: Make update script executable**

Run:
```bash
chmod +x deploy/update.sh
```

**Step 5: Create rollback script**

Create: `deploy/rollback.sh`

```bash
#!/bin/bash
# TK9 Deep Research MCP - Rollback Script
# Rolls back to previous backup

set -e

DEPLOY_PATH="/Users/thinhkhuat/Docker/Caddy/site/tk9v2"
BACKUP_PATH="/Users/thinhkhuat/Docker/Caddy/backups/tk9v2"

echo "Available backups:"
ls -lt "$BACKUP_PATH"/*.tar.gz | head -5

read -p "Enter backup filename to restore: " BACKUP_FILE

if [ ! -f "$BACKUP_PATH/$BACKUP_FILE" ]; then
    echo "Error: Backup file not found"
    exit 1
fi

echo "Stopping services..."
cd "$DEPLOY_PATH"
docker-compose down

echo "Restoring backup..."
cd "$DEPLOY_PATH/.."
tar -xzf "$BACKUP_PATH/$BACKUP_FILE"

echo "Starting services..."
cd "$DEPLOY_PATH"
docker-compose up -d

echo "✓ Rollback complete"
```

**Step 6: Make rollback script executable**

Run:
```bash
chmod +x deploy/rollback.sh
```

**Step 7: Create deployment documentation**

Create: `deploy/README.md`

```markdown
# TK9 Deep Research MCP - Deployment Guide

## Quick Start

### First Deployment
```bash
# 1. Copy environment file
cp .env.example .env
# Edit .env with your API keys

# 2. Run deployment
./deploy/deploy.sh
```

### Updates
```bash
# Quick update (no rebuild)
./deploy/update.sh

# Full deployment (with rebuild)
./deploy/deploy.sh
```

### Rollback
```bash
./deploy/rollback.sh
```

## Deployment Paths

- **Source**: `/Users/thinhkhuat/»DEV•local«/tk9_source_deploy`
- **Deploy**: `/Users/thinhkhuat/Docker/Caddy/site/tk9v2`
- **Backups**: `/Users/thinhkhuat/Docker/Caddy/backups/tk9v2`
- **Logs**: `/Users/thinhkhuat/Docker/Caddy/logs`

## Access Points

- **Local**: http://localhost:12656
- **Internal**: http://192.168.2.22:12656
- **Public v1**: https://tk9.thinhkhuat.com (via Caddy)
- **Public v2**: https://tk9v2.thinhkhuat.com (via Caddy)

## Common Commands

### View Logs
```bash
cd /Users/thinhkhuat/Docker/Caddy/site/tk9v2
docker-compose logs -f tk9-dashboard
```

### Restart Services
```bash
cd /Users/thinhkhuat/Docker/Caddy/site/tk9v2
docker-compose restart
```

### Stop Services
```bash
cd /Users/thinhkhuat/Docker/Caddy/site/tk9v2
docker-compose down
```

### Check Status
```bash
cd /Users/thinhkhuat/Docker/Caddy/site/tk9v2
docker-compose ps
```

### Rebuild from Scratch
```bash
cd /Users/thinhkhuat/Docker/Caddy/site/tk9v2
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Troubleshooting

### ModuleNotFoundError
If you see `ModuleNotFoundError: No module named 'langgraph'`:
1. Check that requirements.txt includes langgraph
2. Rebuild image: `docker-compose build --no-cache`
3. Check build logs for pip install errors

### Service Won't Start
1. Check logs: `docker-compose logs tk9-dashboard`
2. Verify .env file has all required API keys
3. Check port 12656 is not in use: `lsof -i :12656`

### Health Check Failing
1. Wait 30-40 seconds for service to fully start
2. Check logs for startup errors
3. Verify Python dependencies installed correctly

## Caddy Configuration

Update Caddyfile for tk9v2 domain:

```caddy
# v2 dashboard
tk9v2.thinhkhuat.com {
    encode gzip
    @websockets {
        header Connection *Upgrade*
        header Upgrade websocket
    }
    reverse_proxy @websockets 192.168.2.22:12656
    reverse_proxy 192.168.2.22:12656
}
```

Then reload Caddy:
```bash
caddy reload --config /path/to/Caddyfile
```

## Monitoring

### Enable Monitoring Stack
```bash
cd /Users/thinhkhuat/Docker/Caddy/site/tk9v2
docker-compose --profile monitoring up -d
```

Access:
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

## Security Notes

1. Never commit .env files
2. Use strong Redis password in production
3. Keep API keys secure
4. Run containers as non-root user (already configured)
5. Regularly update base images for security patches
```

**Step 8: Test deployment script**

Run:
```bash
cd /Users/thinhkhuat/»DEV•local«/tk9_source_deploy
./deploy/deploy.sh
```

Expected: Complete deployment with all services running

**Step 9: Commit deployment scripts**

```bash
git add deploy/
chmod +x deploy/*.sh
git commit -m "feat(deploy): Add production deployment scripts for remote server

- Created deploy.sh for full deployment with backups
- Created update.sh for quick code updates
- Created rollback.sh for emergency rollback
- Added comprehensive deployment documentation
- Configured for /Users/thinhkhuat/Docker/Caddy/site/tk9v2 path
- Added health checks and verification steps
- Includes Caddy configuration example"
```

---

## Task 4: Update Caddy Configuration for tk9v2 Domain

**Files:**
- Document: Caddy configuration (not in repo)

**Step 1: Update Caddyfile**

Add to Caddyfile:
```caddy
# TK9 v2 Dashboard
tk9v2.thinhkhuat.com {
    encode gzip

    # WebSocket support for real-time updates
    @websockets {
        header Connection *Upgrade*
        header Upgrade websocket
    }
    reverse_proxy @websockets 192.168.2.22:12656

    # HTTP reverse proxy
    reverse_proxy 192.168.2.22:12656

    # Access logging
    log {
        output file /var/log/caddy/tk9v2-access.log
        format json
    }
}
```

**Step 2: Reload Caddy**

Run:
```bash
caddy reload --config /path/to/Caddyfile
```

Expected: Configuration reloaded successfully

**Step 3: Test tk9v2 domain**

Run:
```bash
curl -I https://tk9v2.thinhkhuat.com/health
```

Expected: HTTP 200 OK

---

## Task 5: Create Quick Reference Documentation

**Files:**
- Create: `docs/DOCKER_DEPLOYMENT.md`

**Step 1: Create comprehensive Docker deployment guide**

Create: `docs/DOCKER_DEPLOYMENT.md`

```markdown
# TK9 Deep Research MCP - Docker Deployment Guide

## Overview

This guide covers deploying TK9 Deep Research MCP using Docker and Docker Compose for production use.

## System Requirements

- **Python**: 3.12+ (required)
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **RAM**: 8GB minimum, 16GB recommended
- **CPU**: 4 cores minimum
- **Disk**: 20GB minimum

## Architecture

```
┌─────────────────────────────────────────────┐
│           Caddy Reverse Proxy               │
│  tk9.thinhkhuat.com / tk9v2.thinhkhuat.com  │
└──────────────┬──────────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────────┐
│        TK9 Dashboard Container              │
│         (Port 12656)                        │
│  ┌────────────────────────────────────┐    │
│  │  7 Active Agents:                  │    │
│  │  - Search, Plan, Research,         │    │
│  │    Write, Publish, Translate       │    │
│  │  - Orchestrator (coordinator)      │    │
│  └────────────────────────────────────┘    │
└──────────────┬──────────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────────┐
│         Redis Container                     │
│    (Session & Cache Storage)                │
└─────────────────────────────────────────────┘
```

## Quick Deploy

```bash
# 1. Clone repository
cd /Users/thinhkhuat/»DEV•local«/tk9_source_deploy

# 2. Configure environment
cp .env.example .env
nano .env  # Add your API keys

# 3. Deploy
./deploy/deploy.sh
```

## Manual Deployment Steps

### 1. Build Image

```bash
docker build -t tk9-deep-research:latest .
```

### 2. Start Services

```bash
docker-compose up -d
```

### 3. Verify Deployment

```bash
# Check container status
docker-compose ps

# Check logs
docker-compose logs -f tk9-dashboard

# Test health endpoint
curl http://localhost:12656/health
```

## Environment Configuration

Required environment variables in `.env`:

```bash
# API Keys (REQUIRED)
GOOGLE_API_KEY=your-key
BRAVE_API_KEY=your-key

# Optional but recommended
OPENAI_API_KEY=your-key
TAVILY_API_KEY=your-key
ANTHROPIC_API_KEY=your-key

# Provider Configuration
PRIMARY_LLM_PROVIDER=google_gemini
PRIMARY_LLM_MODEL=gemini-2.5-flash-preview-04-17-thinking
PRIMARY_SEARCH_PROVIDER=brave

# Language Settings
RESEARCH_LANGUAGE=vi
SEARCH_COUNTRY=VN
```

## Troubleshooting

### ModuleNotFoundError: No module named 'langgraph'

**Cause**: Dependencies not properly installed during Docker build

**Solution**:
```bash
# Rebuild without cache
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Verify langgraph is installed
docker exec tk9-dashboard python -c "import langgraph; print(langgraph.__version__)"
```

### Container Keeps Restarting

**Diagnosis**:
```bash
docker-compose logs tk9-dashboard | tail -50
```

**Common Causes**:
1. Missing API keys in .env
2. Port 12656 already in use
3. Insufficient memory

### Health Check Failing

**Solution**:
```bash
# Check if service is responding
docker exec tk9-dashboard curl http://localhost:12656/health

# Check Python process
docker exec tk9-dashboard ps aux | grep python

# Restart service
docker-compose restart tk9-dashboard
```

## Maintenance

### View Logs
```bash
# Follow logs
docker-compose logs -f tk9-dashboard

# Last 100 lines
docker-compose logs --tail=100 tk9-dashboard

# Search for errors
docker-compose logs tk9-dashboard | grep -i error
```

### Update Application
```bash
# Quick update (no rebuild)
./deploy/update.sh

# Full deployment with rebuild
./deploy/deploy.sh
```

### Backup and Restore
```bash
# Backup
./deploy/deploy.sh  # Automatic backup before deploy

# Restore
./deploy/rollback.sh
```

### Clean Up
```bash
# Stop and remove containers
docker-compose down

# Remove all data (WARNING: destructive)
docker-compose down -v

# Clean Docker system
docker system prune -a
```

## Performance Tuning

### Resource Limits

Adjust in `docker-compose.yml`:

```yaml
services:
  tk9-dashboard:
    deploy:
      resources:
        limits:
          cpus: '4.0'      # Increase for faster processing
          memory: 8G       # Increase for larger research tasks
        reservations:
          cpus: '1.0'
          memory: 2G
```

### Redis Optimization

```yaml
services:
  redis:
    command: redis-server --maxmemory 2gb --maxmemory-policy allkeys-lru
```

## Security Best Practices

1. **Use strong passwords**:
   - Change Redis password in .env
   - Never commit .env files

2. **Network isolation**:
   - Services communicate via internal network
   - Only expose necessary ports

3. **Non-root user**:
   - Container runs as `appuser` (already configured)

4. **Regular updates**:
   ```bash
   # Update base images
   docker-compose pull
   docker-compose up -d
   ```

5. **Secrets management**:
   - Use Docker secrets for production
   - Or use environment variable injection

## Monitoring

### Enable Monitoring Stack

```bash
docker-compose --profile monitoring up -d
```

Access:
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

### Key Metrics

1. **Container Health**:
   ```bash
   docker stats tk9-dashboard
   ```

2. **API Response Times**:
   Check Prometheus metrics at `/metrics` endpoint

3. **Resource Usage**:
   ```bash
   docker-compose top
   ```

## Production Checklist

Before deploying to production:

- [ ] Set strong Redis password
- [ ] Configure all API keys
- [ ] Test deployment in staging
- [ ] Set up monitoring
- [ ] Configure backups
- [ ] Set up log rotation
- [ ] Configure Caddy SSL
- [ ] Test health endpoints
- [ ] Verify WebSocket connection
- [ ] Load test with sample queries
- [ ] Document rollback procedure

## Support

For issues or questions:
1. Check logs: `docker-compose logs -f`
2. Verify configuration: `docker-compose config`
3. Review troubleshooting section above
4. Check GitHub issues
```

**Step 2: Commit documentation**

```bash
git add docs/DOCKER_DEPLOYMENT.md
git commit -m "docs(docker): Add comprehensive Docker deployment guide

- Added architecture diagram
- Included troubleshooting section for ModuleNotFoundError
- Documented manual and automated deployment
- Added performance tuning guidelines
- Included security best practices
- Added monitoring setup instructions
- Created production deployment checklist"
```

---

## Execution Summary

**Plan saved to**: `docs/plans/2025-11-03-docker-deployment-fix.md`

**Key Changes**:
1. ✅ Fixed Dockerfile to use pip instead of uv
2. ✅ Consolidated requirements into single file
3. ✅ Updated docker-compose.yml for web dashboard (port 12656)
4. ✅ Created deployment scripts with backups and rollback
5. ✅ Added comprehensive documentation

**Next Steps**:
1. Execute this plan using superpowers:executing-plans
2. Test deployment locally first
3. Deploy to remote server at `/Users/thinhkhuat/Docker/Caddy/site/tk9v2`
4. Verify tk9v2.thinhkhuat.com domain works
5. Monitor for any issues

---

## Two Execution Options

**Plan complete and saved to `docs/plans/2025-11-03-docker-deployment-fix.md`.**

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration with immediate feedback

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints at task boundaries

**Which approach would you prefer?**

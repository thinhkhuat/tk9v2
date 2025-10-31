# TK9 Deployment Infrastructure - Foundational Documentation

## Purpose

This document describes TK9's deployment strategies, infrastructure architecture, containerization approach, monitoring systems, and operational procedures for running the deep research platform in production environments.

## Production Deployment Overview

TK9 is currently deployed in production at **https://tk9.thinhkhuat.com** (internal IP: 192.168.2.22:12656) using a Docker-based deployment with Caddy reverse proxy for SSL termination and routing.

### Deployment Stack

```
Internet (HTTPS/443)
       ↓
Caddy Reverse Proxy (SSL termination, routing)
       ↓
Web Dashboard (0.0.0.0:12656)
       ↓
Multi-Agent System (subprocess execution)
       ↓
Provider APIs (Google Gemini, BRAVE Search, etc.)
```

## Deployment Methods

### 1. Docker Deployment (Production - Recommended)

**Current Production Setup**:

```bash
# Build image
docker build -t tk9-research .

# Run container
docker run -d \
  -p 12656:12656 \
  -v $(pwd)/.env:/app/.env \
  -v $(pwd)/outputs:/app/outputs \
  --name tk9-dashboard \
  --restart unless-stopped \
  tk9-research
```

**Docker Compose** (full stack):

```yaml
version: '3.8'
services:
  tk9-dashboard:
    build: .
    ports:
      - "12656:12656"
    volumes:
      - ./.env:/app/.env
      - ./outputs:/app/outputs
    environment:
      - DASHBOARD_HOST=0.0.0.0
      - DASHBOARD_PORT=12656
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:12656/"]
      interval: 30s
      timeout: 10s
      retries: 3
```

**Dockerfile Structure**:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    pandoc \
    texlive-xetex \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 12656

# Run dashboard
CMD ["python", "web_dashboard/main.py"]
```

**Cross-Reference**: [Deployment System CONTEXT.md](/deploy/CONTEXT.md)

### 2. Systemd Service (Production Alternative)

**Service Configuration** (`/etc/systemd/system/tk9-dashboard.service`):

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

**Startup Script** (`web_dashboard/start_dashboard.sh`):

```bash
#!/bin/bash
cd "$(dirname "$0")"
source ../.venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 12656 --reload
```

**Service Management**:
```bash
# Start service
sudo systemctl start tk9-dashboard

# Enable on boot
sudo systemctl enable tk9-dashboard

# Check status
sudo systemctl status tk9-dashboard

# View logs
sudo journalctl -u tk9-dashboard -f
```

### 3. Bare Metal Deployment

**Installation**:

```bash
# Clone repository
git clone <repository-url>
cd tk9_source_deploy

# Create virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with API keys

# Run web dashboard
cd web_dashboard
./start_dashboard.sh
```

### 4. Cloud Deployments

**AWS Lambda** (Serverless):
- Function: Deep research MCP as Lambda function
- API Gateway: REST API endpoint
- S3: Research output storage
- CloudWatch: Logging and monitoring

**Google Cloud Platform**:
- Cloud Functions: Research execution
- Cloud Storage: Output persistence
- Cloud Monitoring: Metrics and alerts

**Azure**:
- Azure Functions: Research engine
- Azure Blob Storage: File storage
- Application Insights: Monitoring

**Note**: Cloud deployments are documented but not currently in production use.

## Reverse Proxy Configuration

### Caddy Proxy (Production)

**Configuration** (`Caddyfile.validated`):

```caddy
tk9.thinhkhuat.com {
    encode gzip

    # WebSocket support
    @websockets {
        header Connection *Upgrade*
        header Upgrade websocket
    }

    reverse_proxy @websockets 192.168.2.22:12656
    reverse_proxy 192.168.2.22:12656 {
        header_up Host {host}
        header_up X-Real-IP {remote}
        header_up X-Forwarded-For {remote}
        header_up X-Forwarded-Proto {scheme}
    }

    # Security headers
    header {
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
        X-XSS-Protection "1; mode=block"
        Referrer-Policy "strict-origin-when-cross-origin"
    }
}
```

**SSL/TLS**:
- Automatic certificate provisioning via Caddy
- HTTPS-only (443)
- HTTP → HTTPS redirect automatic
- Certificate auto-renewal

**Known Issue**: WebSocket connections via proxy return 404 errors. Direct connection to `http://192.168.2.22:12656` works correctly.

**Cross-Reference**: [Web Dashboard CONTEXT.md](/web_dashboard/CONTEXT.md)

## Infrastructure Architecture

### Network Architecture

```
┌─────────────────────────────────────────────┐
│          External Network (Internet)        │
└────────────────┬────────────────────────────┘
                 │ HTTPS (443)
     ┌───────────▼───────────┐
     │  Caddy Reverse Proxy  │
     │  - SSL Termination    │
     │  - Load Balancing     │
     │  - Security Headers   │
     └───────────┬───────────┘
                 │ HTTP (Internal)
     ┌───────────▼─────────────────────┐
     │  TK9 Web Dashboard               │
     │  192.168.2.22:12656             │
     │  - FastAPI Server               │
     │  - WebSocket Handler            │
     │  - File Manager                 │
     └───────────┬─────────────────────┘
                 │ Subprocess Execution
     ┌───────────▼─────────────────────┐
     │  Multi-Agent Research System    │
     │  - CLI Execution                │
     │  - State Management             │
     │  - Provider System              │
     └───────────┬─────────────────────┘
                 │ API Calls
     ┌───────────▼────────────────────┐
     │  External Provider APIs        │
     │  - Google Gemini               │
     │  - BRAVE Search                │
     │  - OpenAI (fallback)           │
     │  - Tavily (fallback)           │
     └────────────────────────────────┘
```

### File System Architecture

```
/home/tk9/tk9_source_deploy/
├── web_dashboard/          # Dashboard application
│   ├── main.py             # FastAPI server
│   ├── start_dashboard.sh  # Startup script
│   └── static/             # Frontend assets
├── multi_agents/           # Research engine
│   ├── agents/             # Agent implementations
│   ├── providers/          # Provider system
│   └── config/             # Configuration
├── outputs/                # Research outputs (persistent)
│   └── run_*/              # Individual research sessions
├── .env                    # Environment configuration
├── .venv/                  # Python virtual environment
└── logs/                   # Application logs
```

## Environment Configuration

### Production Environment Variables

```bash
# Environment
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Dashboard
DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=12656

# LLM Configuration (Production-optimized)
PRIMARY_LLM_PROVIDER=google_gemini
PRIMARY_LLM_MODEL=gemini-2.5-flash-preview-04-17-thinking
LLM_STRATEGY=primary_only

# Search Configuration
PRIMARY_SEARCH_PROVIDER=brave
SEARCH_STRATEGY=primary_only
RETRIEVER=custom
RETRIEVER_ENDPOINT=https://brave-local-provider.local

# API Keys (production)
GOOGLE_API_KEY=${SECRET_GOOGLE_API_KEY}
BRAVE_API_KEY=${SECRET_BRAVE_API_KEY}

# Performance
MAX_CONCURRENT_REQUESTS=5
TIMEOUT_SECONDS=30
ENABLE_CACHING=true

# CORS (production domain only)
ALLOWED_ORIGINS=https://tk9.thinhkhuat.com
```

**Cross-Reference**: [Configuration Management CONTEXT.md](/multi_agents/config/CONTEXT.md)

## Monitoring & Observability

### Health Checks

**Endpoint**: `GET /` or `GET /health`

```bash
# Check dashboard health
curl http://192.168.2.22:12656/

# Check via proxy
curl https://tk9.thinhkhuat.com/
```

**Health Check Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime_seconds": 3600
}
```

### Log Management

**Dashboard Logs**:
```bash
# Systemd service logs
sudo journalctl -u tk9-dashboard -f

# Docker logs
docker logs -f tk9-dashboard

# Application logs
tail -f /var/log/tk9/dashboard.log
```

**Research Execution Logs**:
```bash
# Per-session logs
tail -f outputs/run_*/drafts/WORKFLOW_SUMMARY.md

# Real-time via WebSocket
# Connect to ws://192.168.2.22:12656/ws/{session_id}
```

**Log Rotation**:
- Automatic rotation at 100MB
- 10 backup files retained
- Compressed archives

### Metrics (Future Enhancement)

**Planned Prometheus Metrics**:
- `tk9_requests_total` - Total research requests
- `tk9_request_duration_seconds` - Research execution time
- `tk9_provider_calls_total` - Provider API calls
- `tk9_provider_failures_total` - Provider failures
- `tk9_websocket_connections` - Active WebSocket connections

**Planned Grafana Dashboards**:
- System overview (requests, errors, latency)
- Provider health (success rate, failover events)
- Cost tracking (API usage by provider)
- Performance trends (execution time over time)

## Deployment Procedures

### Initial Deployment

**Step 1: Prepare Environment**
```bash
# Clone repository
git clone <repository-url>
cd tk9_source_deploy

# Create .env file
cp .env.example .env
# Edit .env with production values
```

**Step 2: Deploy Application**
```bash
# Option A: Docker
docker-compose up -d

# Option B: Systemd
sudo cp deploy/tk9-dashboard.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now tk9-dashboard
```

**Step 3: Configure Reverse Proxy**
```bash
# Copy Caddy configuration
sudo cp Caddyfile.validated /etc/caddy/Caddyfile

# Reload Caddy
sudo systemctl reload caddy
```

**Step 4: Verify Deployment**
```bash
# Check service status
systemctl status tk9-dashboard

# Test health endpoint
curl http://localhost:12656/
curl https://tk9.thinhkhuat.com/

# Monitor logs
journalctl -u tk9-dashboard -f
```

### Updates and Rollbacks

**Update Procedure**:
```bash
# Pull latest code
cd tk9_source_deploy
git pull origin main

# Backup current deployment
./deploy.sh backup

# Restart service
sudo systemctl restart tk9-dashboard

# Verify health
./deploy.sh health
```

**Rollback Procedure**:
```bash
# Stop service
sudo systemctl stop tk9-dashboard

# Checkout previous version
git checkout <previous-commit>

# Restore dependencies if needed
pip install -r requirements.txt

# Restart service
sudo systemctl start tk9-dashboard

# Verify
systemctl status tk9-dashboard
```

### Zero-Downtime Deployment (Future)

**Blue-Green Deployment**:
1. Deploy new version to secondary port
2. Test new deployment
3. Switch Caddy to point to new port
4. Graceful shutdown of old version

**Rolling Update** (multi-instance):
1. Deploy to 50% of instances
2. Monitor health and errors
3. Deploy to remaining instances
4. Complete rollout

## Backup & Recovery

### Backup Strategy

**What to Backup**:
- `.env` file (encrypted secrets)
- `outputs/` directory (research outputs)
- Database (if applicable - currently filesystem-based)
- Configuration files

**Backup Script**:
```bash
#!/bin/bash
BACKUP_DIR="/backups/tk9"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p ${BACKUP_DIR}/${TIMESTAMP}

# Backup configuration
cp .env ${BACKUP_DIR}/${TIMESTAMP}/
cp -r deploy/ ${BACKUP_DIR}/${TIMESTAMP}/

# Backup outputs (incremental)
rsync -av --link-dest=${BACKUP_DIR}/latest \
  outputs/ ${BACKUP_DIR}/${TIMESTAMP}/outputs/

# Update latest link
ln -sfn ${TIMESTAMP} ${BACKUP_DIR}/latest
```

**Automated Backups**:
```cron
# Daily backups at 2 AM
0 2 * * * /home/tk9/tk9_source_deploy/scripts/backup.sh
```

### Recovery Procedures

**Restore from Backup**:
```bash
# Stop service
sudo systemctl stop tk9-dashboard

# Restore configuration
cp /backups/tk9/<timestamp>/.env .

# Restore outputs
rsync -av /backups/tk9/<timestamp>/outputs/ outputs/

# Restart service
sudo systemctl start tk9-dashboard
```

## Security Considerations

### Network Security

**Firewall Rules**:
```bash
# Allow HTTPS
sudo ufw allow 443/tcp

# Allow SSH (management)
sudo ufw allow 22/tcp

# Block direct dashboard access (use proxy only)
sudo ufw deny 12656/tcp
```

**SSL/TLS**:
- TLS 1.2+ only
- Strong cipher suites
- HSTS enabled
- Certificate auto-renewal

### Application Security

**API Key Management**:
- Keys stored in `.env` file (not committed)
- File permissions: `chmod 600 .env`
- Rotate keys quarterly
- Monitor usage for anomalies

**Input Validation**:
- Research queries sanitized
- Filename validation (prevent path traversal)
- MIME type validation for downloads
- WebSocket message validation

**CORS Configuration**:
```python
# Production CORS (web_dashboard/main.py)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://tk9.thinhkhuat.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"]
)
```

### Container Security (Docker)

**Best Practices Applied**:
- Non-root user in container
- Read-only root filesystem where possible
- No privileged mode
- Regular image updates
- Security scanning with Trivy

## Scaling Strategies

### Current Deployment (Single Instance)

**Vertical Scaling**:
- Increase CPU/RAM allocation
- Optimize Python process (memory cleanup)
- Provider connection pooling

**Resource Limits**:
```yaml
# Docker Compose resource limits
services:
  tk9-dashboard:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
        reservations:
          cpus: '2'
          memory: 4G
```

### Future Scaling (Multi-Instance)

**Horizontal Scaling Architecture**:

```
Load Balancer
    ↓
┌────┴────┬────────┬────────┐
│ Inst 1  │ Inst 2 │ Inst 3 │
└─────────┴────────┴────────┘
         ↓
    Shared Storage
    (NFS/S3 for outputs/)
         ↓
    Provider APIs
```

**Considerations**:
- Session affinity for WebSocket connections
- Shared filesystem for research outputs
- Redis for session state (optional)
- Load balancer health checks

## Operational Procedures

### Routine Maintenance

**Daily**:
- Check dashboard health: `curl https://tk9.thinhkhuat.com/`
- Review error logs: `journalctl -u tk9-dashboard -p err`
- Monitor disk space: `df -h outputs/`

**Weekly**:
- Review provider API usage and costs
- Check for application updates
- Verify backup integrity
- Review WebSocket connection metrics

**Monthly**:
- Rotate API keys (if policy requires)
- Update dependencies: `pip install --upgrade -r requirements.txt`
- Review and archive old research outputs
- Security patch updates

### Troubleshooting

**Dashboard Not Responding**:
```bash
# Check service status
systemctl status tk9-dashboard

# Check port binding
lsof -i :12656

# Check logs
journalctl -u tk9-dashboard -n 100

# Restart service
sudo systemctl restart tk9-dashboard
```

**WebSocket Connection Issues**:
```bash
# Test direct connection (bypass proxy)
wscat -c ws://192.168.2.22:12656/ws/test-session

# Check Caddy logs
sudo journalctl -u caddy -f

# Verify Caddy configuration
sudo caddy validate --config /etc/caddy/Caddyfile
```

**Research Execution Failures**:
```bash
# Check provider API connectivity
curl -I https://generativelanguage.googleapis.com
curl -I https://api.search.brave.com

# Verify API keys
python main.py --config

# Check provider logs
grep "provider" /var/log/tk9/dashboard.log
```

## Cross-References

### Related Documentation
- **[DEPLOYMENT.md](/DEPLOYMENT.md)** - Comprehensive deployment guide with one-click scripts
- **[PRODUCTION-CHECKLIST.md](/PRODUCTION-CHECKLIST.md)** - Pre-deployment validation checklist
- **[Deployment System CONTEXT.md](/deploy/CONTEXT.md)** - Deployment configuration details
- **[Web Dashboard CONTEXT.md](/web_dashboard/CONTEXT.md)** - Dashboard deployment specifics

### Related Tier 1 Documentation
- **[System Integration](/docs/ai-context/system-integration.md)** - Cross-component communication patterns
- **[Project Structure](/docs/ai-context/project-structure.md)** - Complete file organization

### Key Deployment Files
- `Dockerfile` - Container image definition
- `docker-compose.yml` - Multi-container orchestration
- `Caddyfile.validated` - Reverse proxy configuration
- `deploy/tk9-dashboard.service` - Systemd service file
- `web_dashboard/start_dashboard.sh` - Startup script
- `deploy/` - Deployment configurations and scripts

---

*This foundational document provides deployment and infrastructure knowledge for TK9. For detailed deployment procedures, see `/DEPLOYMENT.md`. Last updated: 2025-10-31*

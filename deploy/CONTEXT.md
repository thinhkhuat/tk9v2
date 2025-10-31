# Deployment System - Component Context

## Purpose

Production deployment infrastructure for TK9 supporting Docker, Kubernetes, AWS Lambda, and bare-metal deployments. Includes monitoring, CI/CD workflows, and operational tooling for reliable production service.

## Current Status: Production Deployed

**Last Updated**: 2025-10-31
**Status**: ✅ Production at https://tk9.thinhkhuat.com
**Deployment**: Docker + Caddy reverse proxy on 192.168.2.22:12656

## Deployment Structures

```
deploy/
├── aws/                    # AWS deployment configurations
│   ├── lambda/            # Serverless deployment
│   ├── ecs/               # Container orchestration
│   └── cloudformation/    # Infrastructure as code
└── monitoring/            # Monitoring and observability
    ├── prometheus/        # Metrics collection
    ├── grafana/          # Visualization dashboards
    └── alerts/           # Alert rules
```

## Deployment Methods

### Method 1: Docker (Recommended)
```bash
# Build container
docker build -t tk9-research .

# Run
docker run -d \
  -p 12656:12656 \
  -v $(pwd)/.env:/app/.env \
  -v $(pwd)/outputs:/app/outputs \
  --name tk9-dashboard \
  tk9-research
```

### Method 2: Docker Compose
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
    restart: always
```

### Method 3: Systemd Service
```ini
[Unit]
Description=TK9 Web Dashboard
After=network.target

[Service]
Type=simple
User=tk9
WorkingDirectory=/opt/tk9
ExecStart=/opt/tk9/web_dashboard/start_dashboard.sh
Restart=always

[Install]
WantedBy=multi-user.target
```

### Method 4: AWS Lambda (Serverless)
```bash
# Deploy serverless
./deploy.sh --target lambda --region us-east-1
```

## Production Configuration

### Reverse Proxy (Caddy)
```caddy
tk9.thinhkhuat.com {
    encode gzip
    reverse_proxy 192.168.2.22:12656 {
        header_up Host {host}
        header_up X-Real-IP {remote}
    }
}
```

### Environment Variables
```bash
# Production settings
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Dashboard
DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=12656

# Providers (production-optimized)
PRIMARY_LLM_PROVIDER=google_gemini
PRIMARY_LLM_MODEL=gemini-2.5-flash-preview-04-17-thinking
PRIMARY_SEARCH_PROVIDER=brave
LLM_STRATEGY=primary_only
SEARCH_STRATEGY=primary_only
```

## Monitoring & Observability

### Health Checks
```bash
# Dashboard health
curl http://192.168.2.22:12656/

# API health
curl http://192.168.2.22:12656/api/sessions
```

### Logs
```bash
# Application logs
tail -f /var/log/tk9/app.log

# Dashboard logs
tail -f /var/log/tk9/dashboard.log

# Research execution logs
tail -f outputs/run_*/drafts/WORKFLOW_SUMMARY.md
```

### Metrics (Prometheus format)
- Request count and latency
- Research completion rate
- Provider success/failure rate
- Memory and CPU usage
- WebSocket connection count

## Deployment Checklist

**Pre-Deployment**:
- [ ] Run test suite (`python -m pytest`)
- [ ] Validate configuration (`python main.py --config`)
- [ ] Check API keys and quotas
- [ ] Review recent changes and fixes
- [ ] Backup current production data

**Deployment**:
- [ ] Pull latest code
- [ ] Install dependencies (`pip install -r requirements-prod.txt`)
- [ ] Apply database migrations (if any)
- [ ] Update environment variables
- [ ] Restart services
- [ ] Verify health checks

**Post-Deployment**:
- [ ] Monitor logs for errors
- [ ] Test research execution
- [ ] Verify WebSocket connections
- [ ] Check file generation
- [ ] Monitor provider usage

## Rollback Procedure

```bash
# Stop current deployment
systemctl stop tk9-dashboard

# Revert to previous version
git checkout <previous-commit>
pip install -r requirements-prod.txt

# Restart
systemctl start tk9-dashboard
systemctl status tk9-dashboard
```

## Cross-References

- **[DEPLOYMENT.md](/DEPLOYMENT.md)** - Detailed deployment guide
- **[PRODUCTION-CHECKLIST.md](/PRODUCTION-CHECKLIST.md)** - Production readiness checklist
- **[Web Dashboard](/web_dashboard/CONTEXT.md)** - Dashboard deployment specifics
- **[Troubleshooting](/docs/MULTI_AGENT_TROUBLESHOOTING.md)** - Production issues

---

*For detailed deployment procedures, see `/DEPLOYMENT.md`. For production checklist, see `/PRODUCTION-CHECKLIST.md`.*

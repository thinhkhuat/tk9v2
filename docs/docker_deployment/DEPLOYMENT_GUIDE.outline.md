# TK9 Deep Research MCP - Dual Service Docker Deployment

> **TODO**: Expand this outline in next session

## Architecture Overview
- ASCII diagram showing Caddy → Frontend + Backend
- Network topology
- Port mappings (12689 backend, 8592 frontend)

## Services

### Backend (FastAPI)
- Port 12689
- Python 3.12, FastAPI, LangGraph
- 7-agent research orchestration
- Health: http://localhost:12689/health

### Frontend (Vue 3)
- Port 8592
- Vue 3, Vite, TypeScript, Tailwind CSS
- nginx serving static files + SPA routing

## Quick Deploy
1. Configure environment (`cp .env.example .env`)
2. Deploy (`./deploy/deploy.sh`)
3. Verify (curl commands)

## Manual Deployment

### Build Images
- Backend: `docker build -f Dockerfile.backend -t tk9-backend:latest .`
- Frontend: `docker build -f Dockerfile.frontend -t tk9-frontend:latest .`

### Start Services
- `docker-compose up -d`

### Verify Deployment
- Status: `docker-compose ps`
- Logs: `docker-compose logs -f`
- Test endpoints

## Environment Variables

### Backend (.env)
- Required: GOOGLE_API_KEY, BRAVE_API_KEY
- Optional: OPENAI_API_KEY, TAVILY_API_KEY, ANTHROPIC_API_KEY
- Config: PRIMARY_LLM_PROVIDER, PRIMARY_LLM_MODEL, RESEARCH_LANGUAGE

### Frontend Environment
- Build-time: VITE_API_BASE_URL

## Troubleshooting

### Backend: ModuleNotFoundError
- Cause: Missing dependencies
- Solution: Rebuild with `--no-cache`
- Verify: `docker exec tk9-backend python -c "import langgraph"`

### Frontend: 404 on Routes
- Cause: SPA routing misconfigured
- Solution: Check nginx `try_files $uri $uri/ /index.html;`

### CORS Errors
- Solution: Update CORS_ORIGINS in docker-compose.yml

### WebSocket Connection Failed
- Solution: Ensure Caddy WebSocket upgrade headers

## Development Mode
- Uses docker-compose.override.yml automatically
- Hot reload for both services

## Production Checklist
- [ ] API keys configured in .env
- [ ] Both images built successfully
- [ ] Health checks passing
- [ ] Caddy configured for tk9v2.thinhkhuat.com
- [ ] Domain resolves to server
- [ ] WebSocket connections work
- [ ] CORS configured correctly
- [ ] Logs directory created
- [ ] Backups configured

## Access Points

### Local Development
- Backend: http://localhost:12689
- Frontend: http://localhost:8592

### Internal Network
- Backend: http://192.168.2.22:12689
- Frontend: http://192.168.2.22:8592

### Production
- Public: https://tk9v2.thinhkhuat.com

## Monitoring
- Resource usage: `docker stats`
- Service status: `docker-compose ps`
- Logs: `docker-compose logs -f [service]`

## Maintenance

### Update Application
- Pull changes, rebuild, restart

### Restart Services
- `docker-compose restart`

### Rebuild from Scratch
- `docker-compose down`
- `docker-compose build --no-cache`
- `docker-compose up -d`

## Architecture Notes

### Separation of Concerns
1. **Caddy v2 (External)**: HTTPS/SSL, routing, WebSocket upgrades
2. **Nginx (Internal)**: Static files, SPA routing only
3. **Services**: FastAPI backend, Vue frontend

### Why Caddy-First?
- Already manages dozens of services
- No duplication of proxy logic
- Cleaner container isolation
- Simpler debugging

# Caddy v2 Configuration for TK9

> **TODO**: Expand this outline in next session

## Architecture
- Overview of Caddy's role (external reverse proxy)
- Separation of concerns (Caddy vs Nginx)
- What Caddy handles vs what Nginx handles

## Current Caddyfile
- Complete Caddyfile configuration for tk9v2.thinhkhuat.com
- Route definitions:
  * / → Frontend (port 8592)
  * /api/* → Backend (port 12689)
  * /ws/* → WebSocket (port 12689)
- SSL/HTTPS configuration
- Health check endpoints
- Logging setup

## Services Managed
- tk9.thinhkhuat.com (v1 - legacy)
- tk9v2.thinhkhuat.com (v2 - current)

## Why Caddy?
- Automatic HTTPS/SSL
- Zero-config WebSocket upgrades
- Built-in HTTP/2 & compression
- Simplicity & reliability

## Verification Commands
- Test frontend: `curl https://tk9v2.thinhkhuat.com`
- Test API: `curl https://tk9v2.thinhkhuat.com/api/health`
- Test WebSocket: `wscat -c wss://tk9v2.thinhkhuat.com/ws/`

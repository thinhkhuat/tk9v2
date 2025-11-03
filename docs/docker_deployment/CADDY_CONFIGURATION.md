# Caddy v2 Reverse Proxy Configuration for TK9

**Version**: v2.0.0
**Last Updated**: 2025-11-03
**Domain**: tk9v2.thinhkhuat.com
**Purpose**: External HTTPS/SSL termination and routing for TK9 dual-service architecture

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Separation of Concerns](#separation-of-concerns)
- [Complete Caddyfile Configuration](#complete-caddyfile-configuration)
- [Route Definitions](#route-definitions)
- [Why Caddy?](#why-caddy)
- [Services Managed](#services-managed)
- [Verification Commands](#verification-commands)
- [SSL/HTTPS Configuration](#sslhttps-configuration)
- [WebSocket Support](#websocket-support)
- [Troubleshooting](#troubleshooting)

---

## Architecture Overview

```
Internet (HTTPS)
    ↓
Caddy v2 (:443) — SSL Termination, Routing, WebSocket Upgrades
    ↓
    ├─→ Frontend (192.168.2.22:8592) — Vue 3 SPA
    │   └─→ nginx (internal) — Static files + SPA routing only
    │
    └─→ Backend (192.168.2.22:12689) — FastAPI + WebSocket
        └─→ 7-agent LangGraph orchestration
```

**Key Responsibilities**:
- **Caddy**: External HTTPS/SSL, routing, WebSocket upgrade, compression
- **Nginx (internal)**: Static file serving, SPA routing (`try_files`)
- **Docker Services**: Backend (12689), Frontend (8592)

---

## Separation of Concerns

### What Caddy Handles (External Layer)

1. **SSL/TLS Termination**
   - Automatic HTTPS with Let's Encrypt
   - Certificate management and renewal
   - Modern TLS 1.2/1.3 support

2. **External Routing**
   - Domain-based routing (`tk9v2.thinhkhuat.com`)
   - Path-based routing (`/`, `/api/*`, `/ws/*`)
   - WebSocket protocol upgrades

3. **Performance Features**
   - HTTP/2 and HTTP/3 support
   - Automatic gzip compression
   - Response buffering

4. **Security**
   - HTTPS enforcement
   - Header management
   - Rate limiting (if configured)

### What Nginx Handles (Internal Layer)

1. **Static File Serving**
   - Serve built Vue 3 assets from `/usr/share/nginx/html`
   - Efficient static file delivery

2. **SPA Routing**
   - `try_files $uri $uri/ /index.html;` for client-side routing
   - Fallback to `index.html` for all non-file routes

3. **Container Isolation**
   - Runs inside `tk9-frontend` container
   - No external SSL/proxy logic
   - Simple, focused configuration

### Why This Architecture?

✅ **Benefits**:
- **No Duplication**: Caddy manages SSL once for dozens of services
- **Cleaner Containers**: Containers focus on serving content, not routing
- **Easier Debugging**: Clear separation between external and internal layers
- **Scalability**: Add new services without container-level proxy changes
- **Maintenance**: Update Caddy config without rebuilding containers

❌ **What We Avoid**:
- Duplicate SSL configuration in every container
- Complex nginx configs handling both external routing AND static files
- Certificate management inside containers
- Port forwarding complexity

---

## Complete Caddyfile Configuration

**Location**: `/etc/caddy/Caddyfile` (on Caddy host server)

```caddy
# TK9 Deep Research MCP - Dual Service Configuration
# Backend: FastAPI (12689) | Frontend: Vue 3 (8592)

tk9v2.thinhkhuat.com {
    # Enable gzip compression
    encode gzip

    # Health check endpoint (proxied from backend)
    handle /health {
        reverse_proxy http://192.168.2.22:12689
    }

    # Backend API routes
    handle /api/* {
        reverse_proxy http://192.168.2.22:12689 {
            # Preserve original headers
            header_up Host {host}
            header_up X-Real-IP {remote}
            header_up X-Forwarded-For {remote}
            header_up X-Forwarded-Proto {scheme}
        }
    }

    # WebSocket routes for real-time agent updates
    handle /ws/* {
        reverse_proxy http://192.168.2.22:12689 {
            # WebSocket-specific headers (automatic upgrade)
            header_up Host {host}
            header_up X-Real-IP {remote}
            header_up X-Forwarded-For {remote}
            header_up X-Forwarded-Proto {scheme}

            # Increase timeouts for long-running research sessions
            transport http {
                read_timeout 300s
                write_timeout 300s
            }
        }
    }

    # Frontend - catch-all for SPA routing
    handle /* {
        reverse_proxy http://192.168.2.22:8592 {
            header_up Host {host}
            header_up X-Real-IP {remote}
            header_up X-Forwarded-For {remote}
            header_up X-Forwarded-Proto {scheme}
        }
    }

    # Logging
    log {
        output file /var/log/caddy/tk9v2_access.log {
            roll_size 100mb
            roll_keep 5
        }
        format json
    }

    # Error handling
    handle_errors {
        @5xx expression {http.error.status_code} >= 500
        handle @5xx {
            respond "Service temporarily unavailable" 503
        }
    }
}

# Legacy v1 domain (if still in use)
tk9.thinhkhuat.com {
    # Redirect to v2 or maintain separate config
    redir https://tk9v2.thinhkhuat.com{uri} permanent
}
```

---

## Route Definitions

### 1. Frontend Routes (`/`)

**Pattern**: `/*` (catch-all)
**Destination**: `http://192.168.2.22:8592`
**Purpose**: Vue 3 SPA with client-side routing

**Examples**:
```
https://tk9v2.thinhkhuat.com/             → Frontend (index.html)
https://tk9v2.thinhkhuat.com/dashboard    → Frontend (SPA route)
https://tk9v2.thinhkhuat.com/research/123 → Frontend (SPA route)
```

**Flow**:
1. Caddy receives HTTPS request
2. Proxies to `192.168.2.22:8592`
3. Nginx serves static files or falls back to `index.html`
4. Vue Router handles client-side navigation

### 2. Backend API Routes (`/api/*`)

**Pattern**: `/api/*`
**Destination**: `http://192.168.2.22:12689`
**Purpose**: FastAPI REST endpoints

**Examples**:
```
https://tk9v2.thinhkhuat.com/api/health    → Backend health check
https://tk9v2.thinhkhuat.com/api/research  → Start research session
https://tk9v2.thinhkhuat.com/api/sessions  → List sessions
```

**Headers Forwarded**:
- `Host`: Original domain
- `X-Real-IP`: Client IP address
- `X-Forwarded-For`: Proxy chain
- `X-Forwarded-Proto`: `https`

### 3. WebSocket Routes (`/ws/*`)

**Pattern**: `/ws/*`
**Destination**: `http://192.168.2.22:12689`
**Purpose**: Real-time agent status updates

**Examples**:
```
wss://tk9v2.thinhkhuat.com/ws/research/123 → WebSocket connection
```

**Special Handling**:
- Automatic protocol upgrade (`HTTP → WebSocket`)
- Extended timeouts (300s read/write)
- Persistent connections for long research sessions

### 4. Health Check Route (`/health`)

**Pattern**: `/health`
**Destination**: `http://192.168.2.22:12689`
**Purpose**: Backend availability check

**Example**:
```bash
curl https://tk9v2.thinhkhuat.com/health
# Expected: {"status": "healthy", "agents": 7, "version": "v2.0.0"}
```

---

## Why Caddy?

### 1. Automatic HTTPS/SSL

```caddy
# No manual certificate configuration needed!
tk9v2.thinhkhuat.com {
    # Caddy automatically:
    # - Obtains Let's Encrypt certificate
    # - Renews before expiration
    # - Redirects HTTP → HTTPS
}
```

**Comparison with nginx**:
```nginx
# nginx requires manual cert management:
server {
    listen 443 ssl;
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    # ... dozens more SSL config lines
}
```

### 2. Zero-Config WebSocket Upgrades

Caddy automatically detects WebSocket upgrade requests:

```caddy
# This "just works" for WebSocket:
handle /ws/* {
    reverse_proxy http://192.168.2.22:12689
}
```

**nginx equivalent** requires explicit configuration:
```nginx
location /ws/ {
    proxy_pass http://192.168.2.22:12689;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    # ... more WebSocket-specific config
}
```

### 3. Built-in HTTP/2 & Compression

```caddy
# Enable gzip with one line:
encode gzip
```

### 4. Simplicity & Reliability

**Caddyfile**: 50 lines of readable configuration
**nginx equivalent**: 100+ lines of complex syntax

---

## Services Managed

### tk9v2.thinhkhuat.com (Current/Primary)

**Services**:
- Backend: FastAPI (port 12689)
- Frontend: Vue 3 (port 8592)
- WebSocket: Real-time agent updates

**Status**: ✅ Production (v2.0.0)

### tk9.thinhkhuat.com (Legacy)

**Status**: 🔄 Redirects to tk9v2.thinhkhuat.com

**Migration Note**: Users should update bookmarks to v2 domain.

---

## Verification Commands

### 1. Test Frontend

```bash
# Homepage
curl -I https://tk9v2.thinhkhuat.com/
# Expected: HTTP/2 200, content-type: text/html

# SPA route (should still return 200)
curl -I https://tk9v2.thinhkhuat.com/dashboard
# Expected: HTTP/2 200 (nginx fallback to index.html)
```

### 2. Test Backend API

```bash
# Health check
curl https://tk9v2.thinhkhuat.com/health
# Expected: {"status": "healthy", ...}

# API endpoint (requires authentication)
curl https://tk9v2.thinhkhuat.com/api/sessions
# Expected: JSON response or 401 Unauthorized
```

### 3. Test WebSocket

**Using `wscat`** (install: `npm install -g wscat`):

```bash
wscat -c wss://tk9v2.thinhkhuat.com/ws/test
# Expected: Connection established
# You should receive WebSocket messages
```

**Using browser console**:

```javascript
const ws = new WebSocket('wss://tk9v2.thinhkhuat.com/ws/test');
ws.onopen = () => console.log('✅ Connected');
ws.onmessage = (e) => console.log('Message:', e.data);
ws.onerror = (e) => console.error('❌ Error:', e);
```

### 4. Test SSL Certificate

```bash
# Check certificate details
openssl s_client -connect tk9v2.thinhkhuat.com:443 -servername tk9v2.thinhkhuat.com < /dev/null

# Verify certificate expiration
echo | openssl s_client -connect tk9v2.thinhkhuat.com:443 2>/dev/null | \
  openssl x509 -noout -dates
```

### 5. Verify Routing

```bash
# Test that /api/* goes to backend (port 12689)
curl -I https://tk9v2.thinhkhuat.com/api/health

# Test that / goes to frontend (port 8592)
curl -I https://tk9v2.thinhkhuat.com/

# Both should return 200 OK
```

---

## SSL/HTTPS Configuration

### Automatic Certificate Management

Caddy automatically:
1. Obtains certificates from Let's Encrypt on first request
2. Stores certificates in `/var/lib/caddy/.local/share/caddy`
3. Renews certificates 30 days before expiration
4. Redirects HTTP (port 80) → HTTPS (port 443)

### Manual Certificate Reload

If needed (rare):

```bash
# Reload Caddy configuration
sudo caddy reload --config /etc/caddy/Caddyfile

# Or restart Caddy service
sudo systemctl reload caddy
```

### Certificate Storage

**Location**: `/var/lib/caddy/.local/share/caddy/certificates/acme-v02.api.letsencrypt.org-directory/`

**Backup**: Ensure certificates are included in server backups.

---

## WebSocket Support

### How It Works

1. **Client initiates WebSocket connection**:
   ```
   wss://tk9v2.thinhkhuat.com/ws/research/abc123
   ```

2. **Caddy detects `Upgrade: websocket` header**:
   - Automatically proxies to backend (12689)
   - Maintains persistent connection

3. **Backend sends real-time updates**:
   - Agent status changes
   - Research progress
   - File generation notifications

### Extended Timeouts

WebSocket connections have extended timeouts for long research sessions:

```caddy
transport http {
    read_timeout 300s   # 5 minutes
    write_timeout 300s  # 5 minutes
}
```

**Why**: Research sessions can take several minutes. Standard HTTP timeouts (30-60s) would disconnect prematurely.

### Testing WebSocket Connections

```bash
# Test with wscat
wscat -c wss://tk9v2.thinhkhuat.com/ws/research/test-session

# Expected output:
# Connected (press CTRL+C to quit)
# < {"type": "agent_status", "agent": "searcher", "status": "running"}
# < {"type": "progress", "step": 1, "total": 7}
```

---

## Troubleshooting

### Issue: 502 Bad Gateway

**Symptoms**: Caddy returns 502 when accessing frontend or backend

**Causes**:
1. Backend/frontend containers not running
2. Wrong IP address in Caddyfile (should be `192.168.2.22`, NOT `.222`)
3. Port conflicts

**Solutions**:
```bash
# Check container status
docker ps | grep tk9

# Verify backend health
curl http://192.168.2.22:12689/health

# Verify frontend
curl http://192.168.2.22:8592

# Check Caddy logs
sudo journalctl -u caddy -f
```

### Issue: WebSocket Connection Failed

**Symptoms**: Browser shows "WebSocket connection failed" in console

**Causes**:
1. Backend not running
2. WebSocket route not configured
3. Firewall blocking WebSocket traffic

**Solutions**:
```bash
# Test backend WebSocket endpoint directly
wscat -c ws://192.168.2.22:12689/ws/test

# Check Caddy handles WebSocket
curl -I https://tk9v2.thinhkhuat.com/ws/test \
  -H "Upgrade: websocket" \
  -H "Connection: Upgrade"

# Reload Caddy config
sudo caddy reload --config /etc/caddy/Caddyfile
```

### Issue: Certificate Errors

**Symptoms**: Browser shows "Your connection is not private"

**Causes**:
1. Certificate not yet obtained
2. DNS not pointing to server
3. Firewall blocking port 80/443

**Solutions**:
```bash
# Force certificate renewal
sudo caddy stop
sudo caddy start --config /etc/caddy/Caddyfile

# Check DNS resolution
dig tk9v2.thinhkhuat.com +short
# Should return: [Your server IP]

# Test certificate issuance
curl -I https://tk9v2.thinhkhuat.com/
```

### Issue: CORS Errors in Browser

**Symptoms**: Browser console shows "CORS policy" errors

**Cause**: Backend CORS configuration doesn't include frontend domain

**Solution**: Verify `CORS_ORIGINS` in `docker-compose.yml`:

```yaml
environment:
  - CORS_ORIGINS=http://localhost:8592,http://192.168.2.22:8592,https://tk9v2.thinhkhuat.com
```

Then restart backend:
```bash
docker-compose restart tk9-backend
```

### Issue: Slow Response Times

**Symptoms**: Pages load slowly or timeout

**Causes**:
1. Backend container resource constraints
2. Network latency
3. LLM API rate limiting

**Solutions**:
```bash
# Check container resources
docker stats tk9-backend tk9-frontend

# Check backend logs for LLM errors
docker logs tk9-backend --tail 100 | grep -i "rate\|timeout\|error"

# Verify backend performance directly
time curl http://192.168.2.22:12689/health
```

---

## Updating Caddy Configuration

### 1. Edit Caddyfile

```bash
sudo nano /etc/caddy/Caddyfile
```

### 2. Test Configuration

```bash
caddy validate --config /etc/caddy/Caddyfile
```

### 3. Reload Without Downtime

```bash
sudo caddy reload --config /etc/caddy/Caddyfile
```

**Note**: Caddy performs zero-downtime config reloads.

---

## Additional Resources

- **Caddy Documentation**: https://caddyserver.com/docs/
- **Reverse Proxy Guide**: https://caddyserver.com/docs/quick-starts/reverse-proxy
- **Caddyfile Syntax**: https://caddyserver.com/docs/caddyfile
- **Docker Deployment Guide**: `./DEPLOYMENT_GUIDE.md`
- **Project README**: `../../README.md`

---

**Last Updated**: 2025-11-03
**Maintainer**: TK9 Development Team
**Related Documents**: `DEPLOYMENT_GUIDE.md`, `docker-compose.yml`

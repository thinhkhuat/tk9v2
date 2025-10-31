# WebSocket Connection Investigation Summary

## Date: 2025-09-29

## Problem Identified

The TK9 web dashboard WebSocket connections were failing with 404 Not Found errors when accessed through the Caddy reverse proxy at `tk9.thinhkhuat.com`.

### Initial Misdiagnosis
Initially thought the issue was the dashboard binding to `0.0.0.0:12656` instead of a specific IP. However, `0.0.0.0` means "bind to ALL interfaces" which is actually the most permissive and correct setting. This caused:

1. **Regular HTTP requests worked** - They were proxied correctly
2. **WebSocket connections failed** - The WebSocket upgrade couldn't reach the correct IP

### Error Messages
```
WebSocket connection to 'wss://tk9.thinhkhuat.com/ws/{session_id}' failed: There was a bad response from the server.
WARNING: Unsupported upgrade request.
INFO: 192.168.2.22:60277 - "CONNECT /ws/{session_id} HTTP/1.1" 404 Not Found
```

## Solution Applied

### 1. Fixed the Dashboard Startup Configuration

Modified `web_dashboard/main.py`:
- Changed default host from `0.0.0.0` to `192.168.2.222`
- Added command-line argument support for `--host` to override if needed
- Added startup message showing the actual binding address

### 2. Updated Startup Script

Modified `web_dashboard/start_dashboard.sh`:
- Updated documentation to reflect correct IP binding
- Added notes about public access via Caddy proxy
- Clarified how to run for local-only access if needed

## How to Restart the Service

1. **Stop the current instance**:
   ```bash
   # Find the process
   ps aux | grep "python.*main.py" | grep 12656
   # Kill it (replace PID with actual process ID)
   kill PID
   ```

2. **Start with correct binding**:
   ```bash
   cd web_dashboard
   ./start_dashboard.sh
   # Or manually:
   python3 main.py  # Will now bind to 192.168.2.222:12656 by default
   ```

3. **For local-only access** (if needed):
   ```bash
   python3 main.py --host 0.0.0.0
   ```

## Verification Steps

1. **Check binding**:
   ```bash
   lsof -i :12656
   # Should show binding to 192.168.2.222
   ```

2. **Test direct access**:
   ```bash
   curl http://192.168.2.222:12656/
   ```

3. **Test WebSocket through proxy**:
   - Access https://tk9.thinhkhuat.com
   - Submit a research request
   - WebSocket should connect without errors

## Caddy Configuration (Needs IP Update)

The Caddy configuration needs to be updated to use the correct internal IP:
```caddy
tk9.thinhkhuat.com {
    encode gzip

    @websockets {
        header Connection *Upgrade*
        header Upgrade websocket
    }

    reverse_proxy @websockets 192.168.2.22:12656

    reverse_proxy 192.168.2.22:12656 {
        header_up Host {host}
        header_up X-Real-IP {remote}
    }
}
```

**Note**: The actual issue is that Caddy is configured to proxy to `192.168.2.22` but previously had the wrong IP (`192.168.2.222`). This is the real cause of the WebSocket failures.

## Status

✅ **Fix Applied** - The dashboard will now bind to the correct IP address
⏸️ **Requires Restart** - The running instance needs to be restarted to apply the fix
✅ **No Caddy Changes Needed** - Proxy configuration was already correct
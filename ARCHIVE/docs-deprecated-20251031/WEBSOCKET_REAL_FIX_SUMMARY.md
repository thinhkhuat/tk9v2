# TK9 WebSocket Connection - Real Issue Analysis

## Date: 2025-09-29
## Project: TK9 Deep Research MCP (NOT Viber Dashboard)

## The Real Problem

The TK9 web dashboard WebSocket connections are failing with 404 Not Found errors when accessed through the Caddy reverse proxy at `tk9.thinhkhuat.com`.

### Key Understanding

1. **Dashboard binding to `0.0.0.0:12656` is CORRECT**
   - `0.0.0.0` means "listen on ALL interfaces"
   - This is the most permissive setting
   - It accepts connections from localhost, 192.168.2.22, and any other interface
   - **This was never the problem**

2. **The Real Issue**
   - Caddy is configured to proxy to `192.168.2.22:12656`
   - The dashboard IS listening on port 12656 on ALL interfaces (including 192.168.2.22)
   - WebSocket upgrade requests are getting a 404 response

### Likely Root Causes

Since the dashboard is correctly binding to all interfaces, the WebSocket failure is likely due to:

1. **Caddy WebSocket Configuration Issue**
   - The WebSocket matcher might not be working correctly
   - Headers might not be passed through properly

2. **WebSocket Path Issue**
   - The client might be trying to connect to the wrong WebSocket path
   - There might be a mismatch between what the client requests and what the server expects

3. **Protocol Issue**
   - The server is seeing `CONNECT` requests instead of WebSocket upgrade requests
   - This suggests the WebSocket upgrade headers aren't being properly handled

## Current Configuration

### Dashboard (web_dashboard/main.py) - CORRECT ✅
```python
uvicorn.run(
    "main:app",
    host="0.0.0.0",  # Bind to all interfaces - CORRECT
    port=12656,
    reload=True,
    log_level="info"
)
```

### WebSocket Endpoint - EXISTS ✅
```python
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time log streaming"""
    await websocket_manager.handle_websocket(websocket, session_id)
```

### Caddy Configuration (Current)
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

## What We've Confirmed

1. ✅ Dashboard is running on port 12656
2. ✅ Dashboard is accessible via `http://localhost:12656`
3. ✅ WebSocket endpoint exists at `/ws/{session_id}`
4. ✅ Regular HTTP requests work through Caddy
5. ❌ WebSocket connections fail with 404

## Next Steps to Investigate

1. **Test WebSocket directly** (bypassing Caddy):
   ```bash
   # Test if WebSocket works directly
   curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" \
        -H "Sec-WebSocket-Version: 13" -H "Sec-WebSocket-Key: test" \
        http://192.168.2.22:12656/ws/test-session
   ```

2. **Check if Caddy is properly forwarding WebSocket headers**
3. **Verify the client is using the correct WebSocket URL format**
4. **Check server logs for what path is actually being requested**

## Important Notes

- This is the **TK9 Deep Research MCP** project
- The internal IP is **192.168.2.22** (not 192.168.2.222)
- Dashboard binding to `0.0.0.0` is **correct and should not be changed**
- The issue is likely in the proxy configuration or WebSocket upgrade handling
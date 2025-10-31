# WebSocket Fix Instructions

## Problem Identified
The WebSocket connections are failing because Caddy is sending `CONNECT` method requests instead of proper WebSocket upgrade requests (`GET` with upgrade headers).

## Root Cause
The current Caddy configuration doesn't properly handle WebSocket upgrade headers, causing it to treat WebSocket requests as HTTP CONNECT tunnel requests.

## Solution

### 1. Update Caddy Configuration
Replace your current Caddy configuration with the fixed version:

```bash
# Backup current configuration
sudo cp /etc/caddy/Caddyfile /etc/caddy/Caddyfile.backup

# Apply the fixed configuration
sudo cp Caddyfile.fixed /etc/caddy/Caddyfile

# Test configuration
sudo caddy validate --config /etc/caddy/Caddyfile

# Reload Caddy
sudo systemctl reload caddy
# or
sudo caddy reload
```

### 2. Key Changes in the Fixed Configuration

1. **Explicit WebSocket Handling**: Uses `handle @websockets` block to specifically process WebSocket connections
2. **Header Preservation**: Properly forwards Connection and Upgrade headers using `{http.request.header.*}` syntax
3. **Disable Buffering**: Sets `flush_interval -1` for WebSocket connections
4. **Separate Handlers**: Different handling for WebSocket vs regular HTTP requests

### 3. Testing After Fix

Test the WebSocket connection:

```javascript
// In browser console at https://tk9.thinhkhuat.com
const ws = new WebSocket('wss://tk9.thinhkhuat.com/ws/test-session');
ws.onopen = () => console.log('WebSocket connected!');
ws.onerror = (e) => console.error('WebSocket error:', e);
ws.onclose = (e) => console.log('WebSocket closed:', e.code, e.reason);
```

### 4. Expected Behavior After Fix

Server logs should show:
```
INFO:     192.168.2.22:xxxxx - "GET /ws/{session_id} HTTP/1.1" 101 Switching Protocols
```

Instead of:
```
WARNING:  Unsupported upgrade request.
INFO:     192.168.2.22:xxxxx - "CONNECT /ws/{session_id} HTTP/1.1" 404 Not Found
```

### 5. Alternative Minimal Fix

If the above doesn't work, try this simpler configuration:

```caddy
tk9.thinhkhuat.com {
    reverse_proxy 192.168.2.22:12656
}
```

Caddy v2 should automatically handle WebSocket upgrades with just `reverse_proxy`.

### 6. Verification Steps

1. Check Caddy is running: `sudo systemctl status caddy`
2. Check for errors: `sudo journalctl -u caddy -f`
3. Test WebSocket directly: `curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" https://tk9.thinhkhuat.com/ws/test`
4. Monitor dashboard logs: `tail -f /path/to/dashboard/logs`

### 7. If Issues Persist

1. Check Caddy version: `caddy version` (should be v2.x)
2. Ensure no firewall blocking WebSocket
3. Verify FastAPI is properly handling WebSocket at `/ws/{session_id}`
4. Check browser console for client-side errors

## Notes

- The CONNECT method issue indicates Caddy is treating the WebSocket as an HTTP proxy tunnel
- Proper WebSocket upgrades require GET method with specific headers
- The fix ensures headers are properly forwarded and buffering is disabled
# Manual Testing Guide - WebSocket Reliability Fixes

**Date**: 2025-11-05
**Purpose**: Verify WebSocket fixes for Docker deployment (Tasks 6-7)

---

## Prerequisites

### Required Tools
```bash
# Install wscat for WebSocket testing
npm install -g wscat

# Install jq for JSON parsing
brew install jq  # macOS
# or: apt-get install jq  # Linux
```

### Required Files
All code changes have been committed. You have:
- ✅ Enhanced WebSocket logging (backend + frontend)
- ✅ Heartbeat mechanism (30s ping/pong)
- ✅ Message acknowledgment system (5s retry, 3 max)
- ✅ Polling fallback (10s interval when WebSocket stale)
- ✅ Docker network optimizations
- ✅ Diagnostic script (`scripts/diagnose-websocket.sh`)

---

## Task 6: Docker Network Diagnostics

### Step 1: Rebuild Docker Containers

The docker-compose.yml has been updated with network optimizations. Rebuild:

```bash
# Stop existing containers
docker-compose down

# Rebuild with new configuration
docker-compose build --no-cache

# Start containers
docker-compose up -d

# Verify both containers are running
docker ps | grep tk9
```

**Expected Output**:
```
tk9-backend    ... Up ... 0.0.0.0:12689->12689/tcp
tk9-frontend   ... Up ... 0.0.0.0:8592->8592/tcp
```

### Step 2: Run Diagnostic Script

```bash
# Make sure script is executable (already done via chmod)
./scripts/diagnose-websocket.sh
```

**What to Check**:

1. **Container Status**: Both tk9-backend and tk9-frontend should be "Up"
2. **Docker Network**: Should show tk9-backend and tk9-frontend with IPs
3. **Backend Health**: Should return `{"status":"healthy"}`
4. **WebSocket Test**: Should connect and receive pong (requires wscat)
5. **Error Logs**: Should see recent WebSocket activity logs
6. **Network QoS**: Should show "No traffic control configured" (normal)
7. **Open Connections**: Should show 0 (no active sessions yet)

**Save Output**:
```bash
./scripts/diagnose-websocket.sh > diagnostic-baseline.txt
```

### Step 3: Verify Network Settings

Check that TCP keepalive settings were applied:

```bash
# Check backend container sysctls
docker exec tk9-backend sysctl net.ipv4.tcp_keepalive_time
docker exec tk9-backend sysctl net.ipv4.tcp_keepalive_intvl
docker exec tk9-backend sysctl net.ipv4.tcp_keepalive_probes
```

**Expected Output**:
```
net.ipv4.tcp_keepalive_time = 60
net.ipv4.tcp_keepalive_intvl = 10
net.ipv4.tcp_keepalive_probes = 6
```

### Step 4: Check Network MTU

```bash
# Check bridge network MTU
docker network inspect tk9-network | jq '.[].Options'
```

**Expected Output**:
```json
{
  "com.docker.network.bridge.enable_icc": "true",
  "com.docker.network.bridge.enable_ip_masquerade": "true",
  "com.docker.network.bridge.name": "tk9-br0",
  "com.docker.network.driver.mtu": "1500"
}
```

---

## Task 7: End-to-End Testing

### Test 1: Normal Operation (No Issues)

**Objective**: Verify all enhancements work correctly in normal conditions

#### Step 1: Start Research Session

1. Open browser: `http://192.168.2.22:8592` (or localhost:8592)
2. Open Browser DevTools (F12)
3. Go to **Console** tab
4. Go to **Network** tab → Filter: **WS** (WebSocket)
5. Submit research query: "Test WebSocket reliability in Docker"

#### Step 2: Monitor Console Logs

**What to Look For**:

✅ **Connection**:
```
✅ [2025-11-05T...] WebSocket connected {sessionId: "abc12345", url: "ws://..."}
```

✅ **Heartbeat (every 30s)**:
```
💓 Responded to ping from server
💓 Received pong from server
```

✅ **Event Reception**:
```
📥 [2025-11-05T...] WebSocket received: agent_update {eventType: "agent_update", payloadSize: 234, ...}
✅ Sent ack for agent_update (abc12345)
```

✅ **All 7 Agents Update**:
- Browser → Editor → Researcher → Writer → Publisher → Translator → Orchestrator

✅ **Files Appear**:
```
📁 Polling discovered 0 new files  # (because WebSocket is working)
```

❌ **Should NOT See**:
```
⚠️ WebSocket appears stale...  # Should NOT appear in normal operation
🔄 Polling state for session...  # Should NOT appear if WebSocket works
```

#### Step 3: Check Backend Logs

```bash
# Watch backend logs in real-time
docker logs -f tk9-backend | grep "📤\|💓\|✅"
```

**Expected Logs**:
```
📤 🔒 Sending agent_update to 1 connection(s) for session abc12345
✅ Ack received for message abc12345 (session abc12345)
💓 Sent ping to session abc12345
💓 Received pong from session abc12345
```

#### Step 4: Check Network Tab

In Browser DevTools → Network → WS:

1. Click on the WebSocket connection
2. Go to **Messages** tab
3. Verify you see:
   - Green ↑ arrows (outgoing): `{"type":"pong"}`, `{"type":"ack"}`
   - White ↓ arrows (incoming): `{"type":"ping"}`, `{"event_type":"agent_update"}`

**Save Screenshot**: `docs/testing/normal-operation-websocket-messages.png`

---

### Test 2: Simulated Packet Loss

**Objective**: Verify message acknowledgment retry works

#### Step 1: Add Packet Loss to Docker Container

```bash
# Add 20% packet loss (simulates poor network)
docker exec tk9-backend tc qdisc add dev eth0 root netem loss 20%

# Verify it's applied
docker exec tk9-backend tc qdisc show dev eth0
```

**Expected Output**:
```
qdisc netem 8001: root refcnt 2 limit 1000 loss 20%
```

#### Step 2: Start Research Session

Submit another research query and monitor console.

**What to Look For**:

✅ **Retry Messages in Backend**:
```bash
docker logs -f tk9-backend | grep "🔄"
```

**Expected**:
```
🔄 Retry 1/3 for message abc12345 (agent_update)
🔄 Retry 2/3 for message abc12345 (agent_update)
✅ Ack received for message abc12345  # Eventually succeeds
```

✅ **All Agents Still Update** (despite packet loss)

✅ **No Missing Agent Cards** (all 7 agents visible)

#### Step 3: Remove Packet Loss

```bash
# Remove packet loss
docker exec tk9-backend tc qdisc del dev eth0 root

# Verify it's removed
docker exec tk9-backend tc qdisc show dev eth0
```

**Expected Output**:
```
qdisc noqueue 0: root refcnt 2
```

---

### Test 3: WebSocket Degradation (Polling Fallback)

**Objective**: Verify polling kicks in when WebSocket fails

#### Step 1: Simulate WebSocket Degradation

```bash
# Block 80% of WebSocket traffic (severe degradation)
docker exec tk9-backend iptables -A OUTPUT -p tcp --dport 12689 -m statistic --mode random --probability 0.8 -j DROP
```

#### Step 2: Start Research Session

Submit research query and monitor console.

**What to Look For**:

⚠️ **Stale WebSocket Detection (after ~30s)**:
```
⚠️ WebSocket appears stale (no messages for 30.2s) - starting polling fallback every 10s
```

✅ **Polling Starts**:
```
🔄 Polling state for session abc12345
📁 Polling discovered 3 new files  # Files discovered via polling!
```

✅ **Eventually Completes**:
```
✅ Polling detected research completion
🎉 Research completed successfully!
🛑 Stopped state polling
```

✅ **Files Appear in Drawer** (discovered via polling, not WebSocket)

✅ **Agent Cards Eventually Update** (via polling state sync)

#### Step 3: Remove iptables Rule

```bash
# Remove the rule
docker exec tk9-backend iptables -D OUTPUT -p tcp --dport 12689 -m statistic --mode random --probability 0.8 -j DROP

# Verify WebSocket recovers
# Submit new research - should see normal operation again
```

**Expected After Removal**:
```
✅ WebSocket recovered - stopping polling fallback
```

---

### Test 4: Complete Failure Scenario

**Objective**: Test worst-case scenario and recovery

#### Step 1: Kill Backend Mid-Research

```bash
# Start a research session
# After 10 seconds, kill backend
docker stop tk9-backend

# Wait 5 seconds
# Restart backend
docker start tk9-backend
```

**What to Look For**:

❌ **Connection Closed**:
```
🔌 [timestamp] WebSocket disconnected {code: 1006, reason: "", wasClean: false}
🔄 Attempting to reconnect in 3 seconds...
```

✅ **Auto-Reconnect**:
```
🔄 Reconnecting to session abc12345...
✅ [timestamp] WebSocket connected
```

✅ **Session Resumes** (if backend preserved session state)

---

## Documentation for Test Results

### Fill Out Failure Pattern Template

Update `docs/debugging/websocket-failure-pattern.md` with test results:

```bash
# Copy template for test run
cp docs/debugging/websocket-failure-pattern.md docs/debugging/test-run-2025-11-05.md
```

**Fill in**:
- Environment: Docker
- URL: http://192.168.2.22:8592
- Session ID: (from console)
- Agent Update Timeline: (which agents updated, when)
- File Generation Timeline: (files discovered, timestamps)
- WebSocket Connection Status: (any disconnects?)
- Browser Console Errors: (paste any errors)
- Backend Logs: (paste relevant logs)
- Network Tab Frames: (how many sent vs received)

### Expected Results Summary

After all tests:

✅ **Normal Operation**:
- All 7 agents update
- Files appear immediately
- No polling activation
- Heartbeat every 30s

✅ **20% Packet Loss**:
- Message retries visible
- All agents eventually update
- No permanent failures

✅ **80% Degradation**:
- Polling activates after 30s
- Files discovered via polling
- Research completes successfully

✅ **Complete Failure + Recovery**:
- Auto-reconnect works
- Session resumes

---

## Success Criteria

### All Must Pass ✅

- [ ] Diagnostic script runs without errors
- [ ] TCP keepalive settings applied correctly
- [ ] WebSocket connects successfully
- [ ] Heartbeat ping/pong every 30s
- [ ] All 7 agents update in normal operation
- [ ] Acks sent for critical events
- [ ] Message retry works with 20% packet loss
- [ ] Polling activates when WebSocket stale (30s)
- [ ] Files discovered via polling when WebSocket fails
- [ ] Auto-reconnect works after connection loss
- [ ] No missing agent cards
- [ ] No missing files after reload

---

## Troubleshooting

### Issue: wscat not installed
```bash
npm install -g wscat
# or: yarn global add wscat
```

### Issue: jq not installed
```bash
brew install jq  # macOS
# or: apt-get install jq  # Linux
```

### Issue: Docker network not found
```bash
# Recreate network
docker-compose down
docker network rm tk9-network
docker-compose up -d
```

### Issue: Backend not responding
```bash
# Check backend logs
docker logs tk9-backend --tail 100

# Check if process is running
docker exec tk9-backend ps aux | grep uvicorn
```

### Issue: WebSocket connection refused
```bash
# Check if port is listening
docker exec tk9-backend netstat -tlnp | grep 12689

# Check firewall
sudo ufw status  # if using ufw
```

---

## Next Steps After Testing

1. **If all tests pass**: Update CLAUDE.md status to "✅ WebSocket reliability fixes verified"
2. **If tests fail**: Document failures in failure pattern template, investigate root cause
3. **Deploy to production**: Once verified, deploy updated containers to production
4. **Monitor**: Watch production logs for retry/polling activity

---

## Files Modified (Reference)

- `web_dashboard/websocket_handler.py` - Enhanced logging, heartbeat, ack tracking
- `web_dashboard/message_ack_tracker.py` - New ack tracker component
- `web_dashboard/frontend_poc/src/stores/sessionStore.ts` - Polling fallback, acks
- `web_dashboard/frontend_poc/src/types/events.ts` - message_id field
- `web_dashboard/frontend_poc/src/config/api.ts` - STATE_POLL_INTERVAL
- `docker-compose.yml` - Network optimizations
- `scripts/diagnose-websocket.sh` - Diagnostic tool

**All changes committed to git. Ready for deployment.**

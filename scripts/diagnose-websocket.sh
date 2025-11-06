#!/bin/bash
# WebSocket diagnostic script for Docker deployment

echo "=========================================="
echo "TK9 WebSocket Diagnostics"
echo "=========================================="
echo ""

# Check if containers are running
echo "1. Container Status:"
docker ps | grep tk9 || echo "❌ No TK9 containers running"
echo ""

# Check Docker network
echo "2. Docker Network:"
docker network inspect tk9-network | jq -r '.[] | .Containers | to_entries[] | "\(.value.Name): \(.value.IPv4Address)"'
echo ""

# Check backend health
echo "3. Backend Health:"
curl -s http://localhost:12689/api/health | jq '.' || echo "❌ Backend not responding"
echo ""

# Check WebSocket connection
echo "4. WebSocket Test:"
wscat -c ws://localhost:12689/ws/test-diagnostic -x '{"type":"ping"}' 2>&1 | head -5 || echo "❌ WebSocket connection failed (install: npm install -g wscat)"
echo ""

# Check backend logs for WebSocket errors
echo "5. Recent WebSocket Errors (last 20 lines):"
docker logs tk9-backend 2>&1 | grep -i "websocket\|ws\|connection" | tail -20
echo ""

# Check for packet loss (requires tc)
echo "6. Network QoS (if tc configured):"
docker exec tk9-backend tc qdisc show dev eth0 2>/dev/null || echo "ℹ️ No traffic control configured (expected for normal operation)"
echo ""

# Check open connections
echo "7. Open WebSocket Connections:"
docker exec tk9-backend netstat -an | grep :12689 | grep ESTABLISHED | wc -l
echo ""

echo "=========================================="
echo "Diagnostics complete"
echo "=========================================="

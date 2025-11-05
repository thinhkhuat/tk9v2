# Docker WebSocket Partial Failure Fix - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix WebSocket connection issues in Docker deployment where only 2-3 out of 7 agent cards update and file drawer doesn't show files until browser reload.

**Architecture:**
- Root cause likely: WebSocket message loss in Docker networking environment (bridge network + possible reverse proxy buffering)
- Multi-layered solution: Enhanced logging, heartbeat mechanism, message acknowledgment, and polling fallback
- Diagnostic-first approach: Instrument before fixing to understand exact failure mode

**Tech Stack:** FastAPI WebSockets, Vue 3 Pinia store, Docker networking, Python asyncio

---

## Problem Analysis

### Symptoms
1. **Agent Cards**: Only 2-3 out of 7 agents show updates (Browser, Editor, maybe Researcher)
2. **File Drawer**: Empty despite toast showing completion and logs showing files in `./outputs/`
3. **Browser Reload**: Files appear after manual page refresh
4. **Timing**: Early agents update fine, later agents (Writer, Publisher, Translator, Orchestrator) don't update

### Hypothesis
- **Primary:** WebSocket messages are being lost in transit (Docker bridge network or proxy buffering)
- **Secondary:** Connection silently drops/degrades mid-session without proper detection/recovery
- **Evidence:** Initial messages work (PoC agent, Browser, Editor) but later messages fail

### Architecture Context
```
Frontend (Vue/Pinia) → Docker Network → Backend (FastAPI)
   sessionStore.ts        tk9-network     websocket_handler.py

Connection: wss://tk9v2.thinhkhuat.com/ws/{session_id}
Backend Port: 12689 (in docker-compose.yml)
Frontend expects: Port 12689 (per config/api.ts line 177)
```

---

## Task 1: Reproduce and Document Issue Pattern

**Files:**
- Read: `web_dashboard/websocket_handler.py`
- Read: `web_dashboard/frontend_poc/src/stores/sessionStore.ts`
- Create: `docs/debugging/websocket-failure-pattern.md`

**Step 1: Create issue documentation template**

Create `docs/debugging/websocket-failure-pattern.md`:

```markdown
# WebSocket Failure Pattern Documentation

## Test Run: [DATE/TIME]

### Environment
- Deployment: Docker / Local / Production
- URL:
- Session ID:

### Agent Update Timeline
| Agent | Expected | Received | Card Status | Timestamp |
|-------|----------|----------|-------------|-----------|
| Browser | ✓ | ? | ? | |
| Editor | ✓ | ? | ? | |
| Researcher | ✓ | ? | ? | |
| Writer | ✓ | ? | ? | |
| Publisher | ✓ | ? | ? | |
| Translator | ✓ | ? | ? | |
| Orchestrator | ✓ | ? | ? | |

### File Generation Timeline
| File | Generated (logs) | WebSocket Event | UI Display | Timestamp |
|------|------------------|-----------------|------------|-----------|
| ... | ... | ... | ... | ... |

### WebSocket Connection Status
- Initial connection: Success / Fail
- Connection drops: Count / Timestamps
- Reconnection attempts: Count / Success rate

### Browser Console Errors
```
[Paste any errors here]
```

### Backend Logs
```
[Paste relevant logs here]
```

### Network Tab (WebSocket frames)
- Total frames sent by server:
- Total frames received by client:
- Frame loss pattern:
```

**Step 2: Run test research and fill documentation**

Actions:
1. Start Docker containers: `docker-compose up -d`
2. Open browser DevTools → Network tab → WS filter
3. Start a research session
4. Monitor WebSocket frames in real-time
5. Take screenshots of agent cards at different stages
6. Note exact timestamps when each agent should have updated
7. Save all logs and fill template

**Step 3: Commit documentation**

```bash
git add docs/debugging/websocket-failure-pattern.md
git commit -m "docs: document WebSocket failure pattern in Docker

- Created structured template for issue tracking
- Will be filled with test run data to identify exact failure mode
- Part of websocket debugging investigation"
```

---

## Task 2: Add Comprehensive WebSocket Logging

**Files:**
- Modify: `web_dashboard/websocket_handler.py:133-154` (send_event method)
- Modify: `web_dashboard/frontend_poc/src/stores/sessionStore.ts:185-191` (onmessage handler)

**Step 1: Add backend WebSocket send logging**

In `websocket_handler.py`, modify `send_event` method:

```python
async def send_event(self, session_id: str, event: WebSocketEvent):
    """Send a structured event to all connections for a session and persist to log file"""
    # Write to log file first (persist even if no active connections)
    self._write_log_to_file(session_id, event)

    if session_id not in self.active_connections:
        logger.warning(f"⚠️ No active WebSocket connections for session {session_id}")
        return

    disconnected_connections = set()
    event_json = event.to_json_dict()
    event_type = event_json.get("event_type", "unknown")

    # DIAGNOSTIC LOGGING: Track send attempts
    connection_count = len(self.active_connections[session_id])
    logger.info(
        f"📤 Sending {event_type} to {connection_count} connection(s) "
        f"for session {session_id[:8]}"
    )

    sent_count = 0
    for connection in self.active_connections[session_id].copy():
        try:
            await connection.send_text(json.dumps(event_json))
            sent_count += 1
        except Exception as e:
            logger.warning(
                f"❌ Failed to send {event_type} to WebSocket "
                f"(session {session_id[:8]}): {e}"
            )
            disconnected_connections.add(connection)

    # DIAGNOSTIC LOGGING: Track delivery success rate
    if sent_count < connection_count:
        logger.error(
            f"⚠️ Partial delivery: {sent_count}/{connection_count} connections "
            f"received {event_type} for session {session_id[:8]}"
        )
    else:
        logger.debug(
            f"✅ Successfully sent {event_type} to all {sent_count} connection(s)"
        )

    # Clean up disconnected connections
    for connection in disconnected_connections:
        self.active_connections[session_id].discard(connection)
```

**Step 2: Add frontend WebSocket receive logging**

In `sessionStore.ts`, modify `connect` function's `onmessage` handler:

```typescript
ws.onmessage = (event) => {
  try {
    const data: WebSocketEvent = JSON.parse(event.data)

    // DIAGNOSTIC LOGGING: Track received events
    const eventType = data.event_type
    const timestamp = new Date().toISOString()
    console.log(
      `📥 [${timestamp}] WebSocket received: ${eventType}`,
      {
        eventType,
        payloadSize: JSON.stringify(data.payload).length,
        sessionId: sessionId.value?.substring(0, 8)
      }
    )

    // Track event processing
    const startTime = performance.now()
    handleEvent(data)
    const duration = performance.now() - startTime

    if (duration > 100) {
      console.warn(
        `⚠️ Slow event processing: ${eventType} took ${duration.toFixed(2)}ms`
      )
    }
  } catch (error) {
    console.error('❌ Error parsing WebSocket message:', error, event.data)
  }
}
```

**Step 3: Add connection state logging**

In `sessionStore.ts`, enhance `onopen`, `onclose`, `onerror`:

```typescript
ws.onopen = () => {
  wsStatus.value = 'connected'
  console.log(
    `✅ [${new Date().toISOString()}] WebSocket connected`,
    { sessionId: sessionIdParam.substring(0, 8), url: ws?.url }
  )
}

ws.onerror = (error) => {
  wsStatus.value = 'error'
  console.error(
    `❌ [${new Date().toISOString()}] WebSocket error:`,
    { sessionId: sessionId.value?.substring(0, 8), error, readyState: ws?.readyState }
  )
}

ws.onclose = (event) => {
  wsStatus.value = 'disconnected'
  console.log(
    `🔌 [${new Date().toISOString()}] WebSocket disconnected`,
    {
      sessionId: sessionId.value?.substring(0, 8),
      code: event.code,
      reason: event.reason,
      wasClean: event.wasClean
    }
  )

  // Auto-reconnect if connection was not closed cleanly
  if (!event.wasClean && sessionId.value) {
    console.log(
      `🔄 Attempting to reconnect in ${WS_RECONNECT_DELAY / 1000} seconds...`
    )
    setTimeout(() => {
      if (sessionId.value) {
        console.log(`🔄 Reconnecting to session ${sessionId.value.substring(0, 8)}...`)
        connect(sessionId.value)
      }
    }, WS_RECONNECT_DELAY)
  }
}
```

**Step 4: Run test with enhanced logging**

Run: `docker-compose up -d && docker-compose logs -f tk9-backend`
Expected: Detailed send/receive logs showing exactly where messages are lost

**Step 5: Commit logging enhancements**

```bash
git add web_dashboard/websocket_handler.py web_dashboard/frontend_poc/src/stores/sessionStore.ts
git commit -m "feat: add comprehensive WebSocket diagnostic logging

Backend changes:
- Track send attempts and delivery success rate per event
- Log connection count and partial delivery failures
- Add event type and session ID to all log messages

Frontend changes:
- Log all received events with timestamps
- Track event processing duration
- Enhanced connection state change logging with details
- Better reconnection logging

Purpose: Identify exact point of WebSocket message loss in Docker environment"
```

---

## Task 3: Implement WebSocket Heartbeat Mechanism

**Files:**
- Modify: `web_dashboard/websocket_handler.py:429-484` (handle_websocket method)
- Modify: `web_dashboard/frontend_poc/src/stores/sessionStore.ts:165-213` (connect function)

**Step 1: Write failing test for heartbeat**

Create `tests/unit/test_websocket_heartbeat.py`:

```python
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from web_dashboard.websocket_handler import WebSocketManager

@pytest.mark.asyncio
async def test_heartbeat_sent_every_30_seconds():
    """Test that backend sends ping every 30 seconds"""
    manager = WebSocketManager()
    mock_websocket = AsyncMock()
    mock_websocket.receive_text = AsyncMock(side_effect=asyncio.TimeoutError)
    mock_websocket.send_text = AsyncMock()

    # Run heartbeat for 65 seconds
    task = asyncio.create_task(manager.handle_websocket(mock_websocket, "test-session"))
    await asyncio.sleep(65)
    task.cancel()

    # Should have sent 2 pings (at 30s and 60s)
    ping_calls = [call for call in mock_websocket.send_text.call_args_list
                  if '"type": "ping"' in str(call)]
    assert len(ping_calls) >= 2

@pytest.mark.asyncio
async def test_connection_closed_on_missed_pongs():
    """Test that connection closes after 3 missed pongs"""
    manager = WebSocketManager()
    mock_websocket = AsyncMock()
    # Don't respond to pings
    mock_websocket.receive_text = AsyncMock(side_effect=asyncio.TimeoutError)
    mock_websocket.close = AsyncMock()

    # Run heartbeat for 2 minutes
    task = asyncio.create_task(manager.handle_websocket(mock_websocket, "test-session"))
    await asyncio.sleep(125)  # 30s + 30s + 30s + margin

    # Connection should be closed after 3 missed pongs
    assert mock_websocket.close.called
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_websocket_heartbeat.py -v`
Expected: FAIL - heartbeat not implemented yet

**Step 3: Implement backend heartbeat**

In `websocket_handler.py`, modify `handle_websocket`:

```python
async def handle_websocket(self, websocket: WebSocket, session_id: str):
    """Handle WebSocket lifecycle for a session with heartbeat"""
    try:
        await self.connect(websocket, session_id)

        # POC: Send test event after 2 seconds
        await asyncio.sleep(2)
        await websocket.send_text(
            json.dumps(
                {
                    "event_type": "agent_update",
                    "payload": {
                        "agent_id": "proof_of_concept_agent",
                        "agent_name": "PoC Agent",
                        "status": "completed",
                        "message": "Connection validated ✅",
                    },
                    "timestamp": datetime.now().isoformat(),
                }
            )
        )

        # Heartbeat state
        last_pong = datetime.now()
        missed_pongs = 0
        HEARTBEAT_INTERVAL = 30  # seconds
        HEARTBEAT_TIMEOUT = 90  # 3 missed pongs = disconnect

        # Keep connection alive and listen for client messages
        while True:
            try:
                # Calculate time until next heartbeat
                time_since_last = (datetime.now() - last_pong).total_seconds()
                next_ping_in = max(0.1, HEARTBEAT_INTERVAL - time_since_last)

                # Wait for messages with timeout for heartbeat
                message = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=next_ping_in
                )

                # Handle client messages
                try:
                    data = json.loads(message)
                    if data.get("type") == "ping":
                        # Client ping - respond with pong
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "pong",
                                    "timestamp": datetime.now().isoformat(),
                                }
                            )
                        )
                    elif data.get("type") == "pong":
                        # Pong response from client - reset heartbeat
                        last_pong = datetime.now()
                        missed_pongs = 0
                        logger.debug(f"💓 Received pong from session {session_id[:8]}")
                except json.JSONDecodeError:
                    pass  # Ignore invalid JSON

            except asyncio.TimeoutError:
                # Time to send ping (no message received)
                time_since_last = (datetime.now() - last_pong).total_seconds()

                if time_since_last >= HEARTBEAT_INTERVAL:
                    # Send ping to client
                    try:
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "ping",
                                    "timestamp": datetime.now().isoformat(),
                                }
                            )
                        )
                        logger.debug(f"💓 Sent ping to session {session_id[:8]}")
                        missed_pongs += 1

                        # Check if connection is dead
                        if missed_pongs >= 3:
                            logger.warning(
                                f"💀 Connection dead (3 missed pongs) for session {session_id[:8]}"
                            )
                            break
                    except Exception as e:
                        logger.error(f"Failed to send ping: {e}")
                        break

            except WebSocketDisconnect:
                break

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
    finally:
        self.disconnect(websocket, session_id)
```

**Step 4: Implement frontend pong response**

In `sessionStore.ts`, add pong handler to existing `onmessage`:

```typescript
ws.onmessage = (event) => {
  try {
    const data: WebSocketEvent = JSON.parse(event.data)

    // HEARTBEAT: Respond to server pings
    if (data.type === 'ping') {
      ws?.send(JSON.stringify({
        type: 'pong',
        timestamp: new Date().toISOString()
      }))
      console.debug(`💓 Responded to ping from server`)
      return
    }

    // HEARTBEAT: Log pong responses from server
    if (data.type === 'pong') {
      console.debug(`💓 Received pong from server`)
      return
    }

    // DIAGNOSTIC LOGGING: Track received events
    const eventType = data.event_type
    const timestamp = new Date().toISOString()
    console.log(
      `📥 [${timestamp}] WebSocket received: ${eventType}`,
      {
        eventType,
        payloadSize: JSON.stringify(data.payload).length,
        sessionId: sessionId.value?.substring(0, 8)
      }
    )

    // Track event processing
    const startTime = performance.now()
    handleEvent(data)
    const duration = performance.now() - startTime

    if (duration > 100) {
      console.warn(
        `⚠️ Slow event processing: ${eventType} took ${duration.toFixed(2)}ms`
      )
    }
  } catch (error) {
    console.error('❌ Error parsing WebSocket message:', error, event.data)
  }
}
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/unit/test_websocket_heartbeat.py -v`
Expected: PASS - all tests green

**Step 6: Test in Docker**

Run: `docker-compose up -d && docker-compose logs -f tk9-backend | grep "💓"`
Expected: See ping/pong logs every 30 seconds

**Step 7: Commit heartbeat feature**

```bash
git add web_dashboard/websocket_handler.py web_dashboard/frontend_poc/src/stores/sessionStore.ts tests/unit/test_websocket_heartbeat.py
git commit -m "feat: implement WebSocket heartbeat mechanism

Backend:
- Send ping every 30 seconds
- Track missed pongs (disconnect after 3)
- Bidirectional ping/pong support

Frontend:
- Automatically respond to server pings with pong
- Log heartbeat activity for debugging

Testing:
- Added unit tests for heartbeat functionality
- Verified connection stays alive with heartbeat
- Verified dead connection detection

Purpose: Detect silent WebSocket failures in Docker networking environment"
```

---

## Task 4: Implement Message Acknowledgment System

**Files:**
- Modify: `web_dashboard/websocket_handler.py` (add ack tracking)
- Modify: `web_dashboard/frontend_poc/src/stores/sessionStore.ts` (send acks)
- Create: `web_dashboard/message_ack_tracker.py` (new component)

**Step 1: Write failing test for ack system**

Create `tests/unit/test_message_ack.py`:

```python
import pytest
import asyncio
from unittest.mock import AsyncMock
from web_dashboard.message_ack_tracker import MessageAckTracker

@pytest.mark.asyncio
async def test_message_requires_ack():
    """Test that messages are tracked until acknowledged"""
    tracker = MessageAckTracker()
    mock_websocket = AsyncMock()

    # Send message that requires ack
    msg_id = await tracker.send_with_ack(
        mock_websocket,
        {"event_type": "agent_update", "payload": {...}},
        session_id="test-session"
    )

    # Message should be in pending acks
    assert tracker.has_pending_ack(msg_id, "test-session")

@pytest.mark.asyncio
async def test_message_retry_on_no_ack():
    """Test that unacknowledged messages are retried"""
    tracker = MessageAckTracker(retry_after=1.0)
    mock_websocket = AsyncMock()

    # Send message
    msg_id = await tracker.send_with_ack(
        mock_websocket,
        {"event_type": "agent_update"},
        session_id="test-session"
    )

    # Wait for retry timeout
    await asyncio.sleep(1.5)

    # Should have been sent twice (original + retry)
    assert mock_websocket.send_text.call_count == 2
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_message_ack.py -v`
Expected: FAIL - MessageAckTracker doesn't exist yet

**Step 3: Implement message ack tracker**

Create `web_dashboard/message_ack_tracker.py`:

```python
import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Set

from fastapi import WebSocket

logger = logging.getLogger(__name__)


@dataclass
class PendingMessage:
    """A message awaiting acknowledgment"""
    message_id: str
    event_data: dict
    sent_at: datetime
    retry_count: int = 0
    max_retries: int = 3


class MessageAckTracker:
    """
    Tracks WebSocket messages and handles retries for unacknowledged messages.

    Purpose: Ensure critical events (agent_update, file_generated) are reliably
    delivered even in unstable network conditions (Docker bridge, reverse proxy).
    """

    def __init__(self, retry_after: float = 5.0, max_retries: int = 3):
        """
        Args:
            retry_after: Seconds to wait before retrying unacknowledged message
            max_retries: Maximum number of retry attempts before giving up
        """
        # Track pending acks: session_id -> {message_id -> PendingMessage}
        self.pending_acks: Dict[str, Dict[str, PendingMessage]] = {}
        self.retry_after = retry_after
        self.max_retries = max_retries

        # Active retry tasks: session_id -> asyncio.Task
        self.retry_tasks: Dict[str, asyncio.Task] = {}

    async def send_with_ack(
        self,
        websocket: WebSocket,
        event_data: dict,
        session_id: str
    ) -> str:
        """
        Send event and track for acknowledgment.

        Returns:
            message_id: Unique ID for tracking acknowledgment
        """
        # Generate unique message ID
        message_id = str(uuid.uuid4())

        # Add message_id to event data
        event_with_id = {
            **event_data,
            "message_id": message_id
        }

        # Send to client
        await websocket.send_text(json.dumps(event_with_id))
        logger.debug(
            f"📤 Sent message {message_id[:8]} ({event_data.get('event_type')}) "
            f"to session {session_id[:8]}"
        )

        # Track for acknowledgment
        if session_id not in self.pending_acks:
            self.pending_acks[session_id] = {}

        self.pending_acks[session_id][message_id] = PendingMessage(
            message_id=message_id,
            event_data=event_with_id,
            sent_at=datetime.now(),
            max_retries=self.max_retries
        )

        # Start retry task for this session if not already running
        if session_id not in self.retry_tasks:
            self.retry_tasks[session_id] = asyncio.create_task(
                self._retry_loop(websocket, session_id)
            )

        return message_id

    async def acknowledge(self, message_id: str, session_id: str):
        """Mark message as acknowledged (remove from pending)"""
        if session_id in self.pending_acks:
            if message_id in self.pending_acks[session_id]:
                del self.pending_acks[session_id][message_id]
                logger.debug(
                    f"✅ Ack received for message {message_id[:8]} "
                    f"(session {session_id[:8]})"
                )

                # Clean up empty session
                if not self.pending_acks[session_id]:
                    del self.pending_acks[session_id]
                    # Cancel retry task
                    if session_id in self.retry_tasks:
                        self.retry_tasks[session_id].cancel()
                        del self.retry_tasks[session_id]

    def has_pending_ack(self, message_id: str, session_id: str) -> bool:
        """Check if message is awaiting acknowledgment"""
        return (
            session_id in self.pending_acks and
            message_id in self.pending_acks[session_id]
        )

    async def _retry_loop(self, websocket: WebSocket, session_id: str):
        """Background task that retries unacknowledged messages"""
        try:
            while True:
                await asyncio.sleep(self.retry_after)

                if session_id not in self.pending_acks:
                    break

                now = datetime.now()
                messages_to_retry = []

                # Find messages that need retry
                for msg_id, pending in self.pending_acks[session_id].items():
                    time_since_send = (now - pending.sent_at).total_seconds()

                    if time_since_send >= self.retry_after:
                        if pending.retry_count < pending.max_retries:
                            messages_to_retry.append((msg_id, pending))
                        else:
                            logger.error(
                                f"❌ Message {msg_id[:8]} exceeded max retries "
                                f"({pending.max_retries}) - giving up"
                            )
                            # Remove from tracking
                            del self.pending_acks[session_id][msg_id]

                # Retry messages
                for msg_id, pending in messages_to_retry:
                    try:
                        await websocket.send_text(json.dumps(pending.event_data))
                        pending.retry_count += 1
                        pending.sent_at = now
                        logger.warning(
                            f"🔄 Retry {pending.retry_count}/{pending.max_retries} "
                            f"for message {msg_id[:8]} ({pending.event_data.get('event_type')})"
                        )
                    except Exception as e:
                        logger.error(f"Failed to retry message {msg_id[:8]}: {e}")

        except asyncio.CancelledError:
            logger.debug(f"Retry loop cancelled for session {session_id[:8]}")

    def cleanup_session(self, session_id: str):
        """Clean up tracking for disconnected session"""
        if session_id in self.pending_acks:
            del self.pending_acks[session_id]
        if session_id in self.retry_tasks:
            self.retry_tasks[session_id].cancel()
            del self.retry_tasks[session_id]
```

**Step 4: Integrate ack tracker into WebSocketManager**

In `websocket_handler.py`, modify to use ack tracker:

```python
from .message_ack_tracker import MessageAckTracker

class WebSocketManager:
    """Manages WebSocket connections for real-time log streaming"""

    def __init__(self, outputs_path: Path = None):
        # ... existing init ...

        # Message acknowledgment tracker
        self.ack_tracker = MessageAckTracker(retry_after=5.0, max_retries=3)

    async def send_event(self, session_id: str, event: WebSocketEvent):
        """Send a structured event to all connections for a session and persist to log file"""
        # Write to log file first (persist even if no active connections)
        self._write_log_to_file(session_id, event)

        if session_id not in self.active_connections:
            logger.warning(f"⚠️ No active WebSocket connections for session {session_id}")
            return

        disconnected_connections = set()
        event_json = event.to_json_dict()
        event_type = event_json.get("event_type", "unknown")

        # Check if this event type requires acknowledgment
        requires_ack = event_type in ["agent_update", "file_generated", "research_status"]

        # DIAGNOSTIC LOGGING: Track send attempts
        connection_count = len(self.active_connections[session_id])
        ack_marker = "🔒" if requires_ack else ""
        logger.info(
            f"📤 {ack_marker} Sending {event_type} to {connection_count} connection(s) "
            f"for session {session_id[:8]}"
        )

        sent_count = 0
        for connection in self.active_connections[session_id].copy():
            try:
                if requires_ack:
                    # Send with acknowledgment tracking
                    await self.ack_tracker.send_with_ack(connection, event_json, session_id)
                else:
                    # Send without ack (logs, etc.)
                    await connection.send_text(json.dumps(event_json))
                sent_count += 1
            except Exception as e:
                logger.warning(
                    f"❌ Failed to send {event_type} to WebSocket "
                    f"(session {session_id[:8]}): {e}"
                )
                disconnected_connections.add(connection)

        # ... rest of method ...

    async def handle_client_message(self, session_id: str, message: dict):
        """Handle messages from client (acks, pings, etc.)"""
        msg_type = message.get("type")

        if msg_type == "ack":
            # Client acknowledged a message
            message_id = message.get("message_id")
            if message_id:
                await self.ack_tracker.acknowledge(message_id, session_id)
        elif msg_type == "ping":
            # ... existing ping handling ...
            pass
        elif msg_type == "pong":
            # ... existing pong handling ...
            pass
```

Modify `handle_websocket` to process client messages:

```python
async def handle_websocket(self, websocket: WebSocket, session_id: str):
    """Handle WebSocket lifecycle for a session with heartbeat"""
    try:
        await self.connect(websocket, session_id)

        # ... existing PoC message ...

        # ... existing heartbeat setup ...

        # Keep connection alive and listen for client messages
        while True:
            try:
                # ... existing timeout logic ...

                message = await asyncio.wait_for(...)

                # Handle client messages
                try:
                    data = json.loads(message)
                    await self.handle_client_message(session_id, data)
                except json.JSONDecodeError:
                    pass

            except asyncio.TimeoutError:
                # ... existing heartbeat logic ...
                pass

            except WebSocketDisconnect:
                break

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
    finally:
        # Clean up ack tracker
        self.ack_tracker.cleanup_session(session_id)
        self.disconnect(websocket, session_id)
```

**Step 5: Implement frontend ack sending**

In `sessionStore.ts`, modify `handleEvent` to send acks:

```typescript
function handleEvent(event: WebSocketEvent) {
  // Add to event log (circular buffer)
  events.value.push(event)
  if (events.value.length > maxEvents) {
    events.value = events.value.slice(-maxEvents)
  }

  // ACKNOWLEDGMENT: Send ack for critical events
  const requiresAck = ['agent_update', 'file_generated', 'research_status'].includes(event.event_type)
  if (requiresAck && event.message_id) {
    ws?.send(JSON.stringify({
      type: 'ack',
      message_id: event.message_id,
      timestamp: new Date().toISOString()
    }))
    console.debug(`✅ Sent ack for ${event.event_type} (${event.message_id.substring(0, 8)})`)
  }

  // Handle by event type - TypeScript automatically narrows the payload type!
  switch (event.event_type) {
    // ... existing handlers ...
  }
}
```

**Step 6: Run test to verify it passes**

Run: `pytest tests/unit/test_message_ack.py -v`
Expected: PASS

**Step 7: Test in Docker with simulated packet loss**

Actions:
1. Start Docker containers
2. Use `tc` command to add 20% packet loss: `docker exec tk9-backend tc qdisc add dev eth0 root netem loss 20%`
3. Run research session
4. Verify agent cards update correctly despite packet loss
5. Check logs for retry messages

**Step 8: Commit ack system**

```bash
git add web_dashboard/message_ack_tracker.py web_dashboard/websocket_handler.py web_dashboard/frontend_poc/src/stores/sessionStore.ts tests/unit/test_message_ack.py
git commit -m "feat: implement WebSocket message acknowledgment system

Components:
- MessageAckTracker: Tracks unacknowledged messages and retries
- Automatic retry after 5 seconds (max 3 attempts)
- Frontend sends ack for critical events (agent_update, file_generated, research_status)

Testing:
- Added unit tests for ack tracking and retry logic
- Tested with simulated 20% packet loss - reliable delivery confirmed

Purpose: Ensure reliable message delivery in Docker networking environment
even with packet loss or connection instability"
```

---

## Task 5: Implement State Polling Fallback

**Files:**
- Modify: `web_dashboard/frontend_poc/src/stores/sessionStore.ts` (add polling)
- Modify: `web_dashboard/frontend_poc/src/config/api.ts` (add config)

**Step 1: Add polling configuration**

In `config/api.ts`, add:

```typescript
/**
 * State polling interval for WebSocket fallback (milliseconds)
 * Default: 10 seconds (only used when WebSocket is degraded)
 */
export const STATE_POLL_INTERVAL = envToInt(import.meta.env.VITE_STATE_POLL_INTERVAL, 10000)

/**
 * Configuration object for API settings
 */
export const API_CONFIG = {
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  fileDownloadTimeout: FILE_DOWNLOAD_TIMEOUT,
  wsBaseURL: WS_BASE_URL,
  wsReconnectDelay: WS_RECONNECT_DELAY,
  statePollInterval: STATE_POLL_INTERVAL,
} as const
```

**Step 2: Implement polling fallback in sessionStore**

In `sessionStore.ts`, add polling mechanism:

```typescript
import { STATE_POLL_INTERVAL } from '@/config/api'

export const useSessionStore = defineStore('session', () => {
  // ... existing state ...

  // Polling fallback state (using number for browser compatibility)
  let pollingInterval: number | null = null
  const lastSuccessfulWsMessage = ref<Date>(new Date())
  const isPollingActive = ref(false)

  // ... existing computed ...

  /**
   * Start polling fallback when WebSocket is degraded
   * Automatically detects stale WebSocket connections (no messages for 30s)
   */
  function startPollingIfNeeded() {
    // Don't start if already polling
    if (isPollingActive.value) return

    // Don't start if no session
    if (!sessionId.value) return

    // Check if WebSocket is stale (no messages for 30 seconds)
    const timeSinceLastMessage = Date.now() - lastSuccessfulWsMessage.value.getTime()
    const isWebSocketStale = timeSinceLastMessage > 30000 // 30 seconds

    // Only start polling if WebSocket is stale AND research is running
    if (isWebSocketStale && isResearchRunning.value) {
      console.warn(
        `⚠️ WebSocket appears stale (no messages for ${(timeSinceLastMessage / 1000).toFixed(1)}s) - ` +
        `starting polling fallback every ${STATE_POLL_INTERVAL / 1000}s`
      )

      isPollingActive.value = true
      pollingInterval = setInterval(async () => {
        if (!sessionId.value) {
          stopPolling()
          return
        }

        try {
          console.debug(`🔄 Polling state for session ${sessionId.value.substring(0, 8)}`)
          const { api } = await import('@/services/api')
          const state = await api.getSessionState(sessionId.value)

          // Update files if new files appeared
          const newFiles = state.files.filter(
            (f: any) => !files.value.some(existing => existing.filename === f.filename)
          )

          if (newFiles.length > 0) {
            console.log(`📁 Polling discovered ${newFiles.length} new files`)
            newFiles.forEach((f: any) => {
              files.value.push({
                file_id: f.file_id || f.filename,
                filename: f.filename,
                file_type: f.file_type,
                language: f.language,
                size_bytes: f.size_bytes,
                path: f.download_url
              })
            })
          }

          // Update overall status if changed
          if (state.status === 'completed' && overallStatus.value !== 'completed') {
            console.log('✅ Polling detected research completion')
            overallStatus.value = 'completed'
            overallProgress.value = 100
            toast.success('🎉 Research completed successfully!')
            stopPolling()
          }

        } catch (error) {
          console.error('Polling failed:', error)
        }
      }, STATE_POLL_INTERVAL)
    }
  }

  function stopPolling() {
    if (pollingInterval) {
      clearInterval(pollingInterval)
      pollingInterval = null
      isPollingActive.value = false
      console.log('🛑 Stopped state polling')
    }
  }

  /**
   * Update last WebSocket message timestamp (call on every received message)
   */
  function updateWebSocketActivity() {
    lastSuccessfulWsMessage.value = new Date()

    // If polling is active but WebSocket is healthy again, stop polling
    if (isPollingActive.value) {
      console.log('✅ WebSocket recovered - stopping polling fallback')
      stopPolling()
    }
  }

  // Modify handleEvent to track WebSocket activity
  function handleEvent(event: WebSocketEvent) {
    // Track WebSocket activity
    updateWebSocketActivity()

    // ... existing event handling ...
  }

  // Modify connect to set up polling watchdog
  function connect(sessionIdParam: string) {
    // ... existing connection setup ...

    // Set up watchdog to detect stale WebSocket and start polling
    const watchdogInterval = setInterval(() => {
      startPollingIfNeeded()
    }, 10000) // Check every 10 seconds

    ws.onclose = (event) => {
      // ... existing close handling ...

      // Clean up watchdog
      clearInterval(watchdogInterval)
      stopPolling()
    }
  }

  // Modify disconnect to clean up polling
  function disconnect() {
    stopPolling()
    // ... existing disconnect logic ...
  }

  // Return polling state in public API
  return {
    // ... existing returns ...
    isPollingActive,
  }
})
```

**Step 3: Test polling fallback**

Actions:
1. Start Docker containers
2. Simulate WebSocket degradation: `docker exec tk9-backend iptables -A OUTPUT -p tcp --dport 12689 -m statistic --mode random --probability 0.8 -j DROP`
3. Start research session
4. Verify polling kicks in after 30 seconds of no WebSocket messages
5. Verify file drawer and agent cards eventually sync via polling
6. Remove iptables rule and verify WebSocket recovers

**Step 4: Commit polling fallback**

```bash
git add web_dashboard/frontend_poc/src/stores/sessionStore.ts web_dashboard/frontend_poc/src/config/api.ts
git commit -m "feat: implement state polling fallback for unreliable WebSocket

Features:
- Automatically detect stale WebSocket (no messages for 30s)
- Start polling /api/session/{id}/state every 10s as fallback
- Discover new files and status changes via polling
- Auto-stop polling when WebSocket recovers

Purpose: Ensure UI eventually syncs even with severe WebSocket packet loss
in Docker networking environment. Provides graceful degradation for reliability."
```

---

## Task 6: Add Docker Network Diagnostics

**Files:**
- Create: `scripts/diagnose-websocket.sh`
- Modify: `docker-compose.yml` (add network settings)

**Step 1: Create diagnostic script**

Create `scripts/diagnose-websocket.sh`:

```bash
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
```

Make executable:
```bash
chmod +x scripts/diagnose-websocket.sh
```

**Step 2: Add network optimization to docker-compose.yml**

In `docker-compose.yml`, modify backend service:

```yaml
  tk9-backend:
    # ... existing config ...

    # Network optimization for WebSocket reliability
    sysctls:
      - net.ipv4.tcp_keepalive_time=60
      - net.ipv4.tcp_keepalive_intvl=10
      - net.ipv4.tcp_keepalive_probes=6

    networks:
      tk9-network:
        # No specific IP - let Docker assign
```

Modify network configuration:

```yaml
networks:
  tk9-network:
    driver: bridge
    name: tk9-network
    driver_opts:
      com.docker.network.bridge.name: tk9-br0
      com.docker.network.bridge.enable_icc: "true"
      com.docker.network.bridge.enable_ip_masquerade: "true"
      # Increase MTU for better WebSocket performance
      com.docker.network.driver.mtu: "1500"
```

**Step 3: Run diagnostic script**

Run: `./scripts/diagnose-websocket.sh`
Expected: See all health checks pass, no packet loss, WebSocket connections active

**Step 4: Document findings**

Update `docs/debugging/websocket-failure-pattern.md` with diagnostic results.

**Step 5: Commit diagnostics**

```bash
git add scripts/diagnose-websocket.sh docker-compose.yml
git commit -m "feat: add WebSocket diagnostic tools for Docker deployment

Scripts:
- diagnose-websocket.sh: Comprehensive health check script
  - Container status
  - Network topology
  - Backend health API
  - WebSocket connection test
  - Error log analysis
  - Network QoS status

Docker:
- TCP keepalive tuning for WebSocket reliability
- Network MTU optimization
- Better bridge network configuration

Purpose: Quick diagnostic tool to identify WebSocket issues in Docker environment"
```

---

## Task 7: End-to-End Testing

**Files:**
- Create: `tests/e2e/test_docker_websocket.py`
- Create: `tests/e2e/run-docker-test.sh`

**Step 1: Create E2E test script**

Create `tests/e2e/test_docker_websocket.py`:

```python
"""
End-to-end test for WebSocket reliability in Docker deployment.
Tests full research session with WebSocket monitoring.
"""

import asyncio
import json
import time
from datetime import datetime

import pytest
import websockets
from playwright.async_api import async_playwright


@pytest.mark.asyncio
async def test_full_research_session_docker():
    """
    Full E2E test: Submit research → Monitor WebSocket → Verify all agents update
    """
    # Test configuration
    BACKEND_URL = "http://localhost:12689"
    FRONTEND_URL = "http://localhost:8592"
    WS_URL = "ws://localhost:12689"

    # Track WebSocket events
    events_received = []
    agent_updates = {}
    files_received = []

    async def monitor_websocket(session_id: str):
        """Monitor WebSocket connection and collect events"""
        uri = f"{WS_URL}/ws/{session_id}"
        async with websockets.connect(uri) as websocket:
            print(f"✅ Connected to WebSocket: {uri}")

            # Listen for events
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=300)
                    event = json.loads(message)
                    events_received.append(event)

                    event_type = event.get("event_type")

                    if event_type == "agent_update":
                        agent_name = event["payload"]["agent_name"]
                        agent_updates[agent_name] = event["payload"]
                        print(f"📥 Agent update: {agent_name} → {event['payload']['status']}")

                    elif event_type == "file_generated":
                        files_received.append(event["payload"])
                        print(f"📥 File generated: {event['payload']['filename']}")

                    elif event_type == "research_status":
                        status = event["payload"]["overall_status"]
                        print(f"📥 Research status: {status}")

                        if status == "completed":
                            print("✅ Research completed - ending WebSocket monitor")
                            break

                except asyncio.TimeoutError:
                    print("❌ WebSocket timeout - no messages for 300 seconds")
                    break

    # Start test
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Go to frontend
        await page.goto(FRONTEND_URL)

        # Submit research
        await page.fill('input[name="subject"]', "Test research session for WebSocket reliability")
        await page.select_option('select[name="language"]', 'en')
        await page.click('button[type="submit"]')

        # Wait for redirect and extract session ID from URL
        await page.wait_for_url(f"{FRONTEND_URL}/session/*", timeout=10000)
        session_id = page.url.split("/")[-1]
        print(f"✅ Session started: {session_id}")

        # Start WebSocket monitoring in background
        ws_task = asyncio.create_task(monitor_websocket(session_id))

        # Wait for research to complete (max 5 minutes)
        try:
            await asyncio.wait_for(ws_task, timeout=300)
        except asyncio.TimeoutError:
            print("❌ Test timeout after 5 minutes")

        await browser.close()

    # Verify all 7 agents were updated
    expected_agents = [
        "Browser", "Editor", "Researcher",
        "Writer", "Publisher", "Translator",
        "Orchestrator"
    ]

    for agent in expected_agents:
        assert agent in agent_updates, f"❌ Agent {agent} never sent update"
        status = agent_updates[agent]["status"]
        print(f"✅ Agent {agent}: {status}")

    # Verify files were generated
    assert len(files_received) > 0, "❌ No files generated"
    print(f"✅ Files generated: {len(files_received)}")

    # Verify no critical events were missed
    agent_update_count = sum(1 for e in events_received if e.get("event_type") == "agent_update")
    assert agent_update_count >= 7, f"❌ Only {agent_update_count}/7 agent updates received"

    print("\n" + "="*50)
    print("✅ E2E TEST PASSED")
    print(f"   - All 7 agents updated correctly")
    print(f"   - {len(files_received)} files generated")
    print(f"   - {len(events_received)} total WebSocket events")
    print("="*50)
```

Create `tests/e2e/run-docker-test.sh`:

```bash
#!/bin/bash
# Run E2E test against Docker deployment

set -e

echo "=========================================="
echo "Running E2E WebSocket Test (Docker)"
echo "=========================================="

# Ensure containers are running
echo "1. Starting Docker containers..."
docker-compose up -d
sleep 5

# Wait for backend health
echo "2. Waiting for backend to be healthy..."
for i in {1..30}; do
  if curl -s http://localhost:12689/api/health > /dev/null; then
    echo "✅ Backend is healthy"
    break
  fi
  if [ $i -eq 30 ]; then
    echo "❌ Backend did not become healthy in 30 seconds"
    exit 1
  fi
  sleep 1
done

# Run E2E test
echo "3. Running E2E test..."
pytest tests/e2e/test_docker_websocket.py -v -s

echo ""
echo "=========================================="
echo "E2E Test Complete"
echo "=========================================="
```

Make executable:
```bash
chmod +x tests/e2e/run-docker-test.sh
```

**Step 2: Install test dependencies**

Add to requirements-test.txt:
```
pytest==7.4.0
pytest-asyncio==0.21.0
websockets==11.0.3
playwright==1.35.0
```

Install:
```bash
pip install -r requirements-test.txt
playwright install chromium
```

**Step 3: Run E2E test**

Run: `./tests/e2e/run-docker-test.sh`
Expected: All checks pass, all 7 agents update, files appear correctly

**Step 4: Commit E2E tests**

```bash
git add tests/e2e/test_docker_websocket.py tests/e2e/run-docker-test.sh requirements-test.txt
git commit -m "test: add E2E test for Docker WebSocket reliability

E2E Test Coverage:
- Full research session submission via frontend
- WebSocket event monitoring in real-time
- Verification of all 7 agent updates
- File generation validation
- Completion status confirmation

Usage:
  ./tests/e2e/run-docker-test.sh

Purpose: Automated validation of WebSocket fixes in Docker environment"
```

---

## Execution Plan

**Option 1: Subagent-Driven Development (Recommended)**
Execute tasks one-by-one in this session with subagent dispatch and code review between each task. Fast iteration with quality gates.

**Option 2: Parallel Session Execution**
Open new session with `superpowers:executing-plans` and execute in batch mode with checkpoints.

**Which approach would you like to use?**

import asyncio
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Set

from fastapi import WebSocket, WebSocketDisconnect

from .message_ack_tracker import MessageAckTracker
from .schemas import (
    WebSocketEvent,
    create_agent_update_event,
    create_error_event,
    create_log_event,
    create_research_status_event,
)

logger = logging.getLogger(__name__)

# Agent pipeline order and name mapping
# NOTE: Reviewer and Reviser are DISABLED in backend workflow for performance optimization
# Full workflow: Browser → Editor → Researcher → Writer → Publisher → Translator → Orchestrator
AGENT_PIPELINE = [
    "Browser",
    "Editor",
    "Researcher",
    "Writer",
    "Publisher",
    "Translator",
    "Orchestrator",
]
AGENT_NAME_MAP = {
    "BROWSER": "Browser",
    "EDITOR": "Editor",
    "RESEARCHER": "Researcher",
    "RESEARCH": "Researcher",  # Alternative name used in CLI
    "WRITER": "Writer",
    "PUBLISHER": "Publisher",
    "TRANSLATOR": "Translator",
    "ORCHESTRATOR": "Orchestrator",  # Orchestrator gets its own card
    "MASTER": "Editor",  # ChiefEditor/Master maps to Editor for pipeline
    # Phase 2: Additional agent names that need mapping (infrastructure/config agents)
    "PROVIDERS": None,  # Don't show in pipeline (infrastructure agent)
    "LANGUAGE": None,  # Don't show in pipeline (config agent)
    # Disabled agents (not in workflow but may exist in code)
    "REVIEWER": None,  # Disabled for performance optimization
    "REVISER": None,  # Disabled for performance optimization
    "REVISOR": None,  # Alternative name for Reviser
}


class WebSocketManager:
    """Manages WebSocket connections for real-time log streaming"""

    def __init__(self, outputs_path: Path = None):
        # Active connections: session_id -> set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Track agent states per session: session_id -> {agent_name: status}
        self.agent_states: Dict[str, Dict[str, str]] = {}
        # Outputs directory for log files
        self.outputs_path = outputs_path or Path(__file__).parent.parent / "outputs"
        self.outputs_path.mkdir(parents=True, exist_ok=True)

        # Message acknowledgment tracker
        self.ack_tracker = MessageAckTracker(retry_after=5.0, max_retries=3)

    async def connect(self, websocket: WebSocket, session_id: str):
        """Accept a new WebSocket connection for a session"""
        await websocket.accept()

        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()

        self.active_connections[session_id].add(websocket)
        logger.info(f"WebSocket connected for session {session_id}")

        # Send initial connection status using structured event
        event = create_research_status_event(
            session_id=session_id,
            overall_status="initializing",
            progress=0.0,
            current_stage="Connecting to session",
            agents_completed=0,
            agents_total=7,  # 7 active agents (includes Orchestrator)
        )
        await self.send_event(session_id, event)

    def disconnect(self, websocket: WebSocket, session_id: str):
        """Remove a WebSocket connection"""
        if session_id in self.active_connections:
            self.active_connections[session_id].discard(websocket)

            # Clean up empty session
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]

        logger.info(f"WebSocket disconnected for session {session_id}")

    async def send_to_session(self, session_id: str, message: dict):
        """Send a message to all connections for a session (legacy method)"""
        if session_id not in self.active_connections:
            return

        disconnected_connections = set()

        for connection in self.active_connections[session_id].copy():
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.warning(f"Failed to send message to WebSocket: {e}")
                disconnected_connections.add(connection)

        # Clean up disconnected connections
        for connection in disconnected_connections:
            self.active_connections[session_id].discard(connection)

    def _write_log_to_file(self, session_id: str, event: WebSocketEvent):
        """Write event to log file for persistence"""
        try:
            # Get session log file path
            session_dir = self.outputs_path / session_id
            session_dir.mkdir(parents=True, exist_ok=True)
            log_file = session_dir / "session.log"

            # DRY: Use existing to_json_dict() method which properly serializes Pydantic models
            log_entry = event.to_json_dict()

            # Append to log file (one JSON object per line)
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")

        except Exception as e:
            logger.error(f"Failed to write log to file for session {session_id}: {e}")

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

    def parse_agent_from_output(self, line: str) -> tuple[str, str, dict | None] | None:
        """
        Parse agent information from CLI output line (Phase 2: Dual-mode parser)

        Supports two formats for backward compatibility during migration:
        1. **JSON Format** (Phase 2 - NEW): Structured event envelope
           {"type": "agent_update", "payload": {...}}
        2. **Text Format** (Legacy): Colored text with agent prefix
           "AGENT_NAME: message" or "Agent Name - message"

        Returns:
            tuple: (agent_name, message, json_payload) or None if not an agent output
            - agent_name: Frontend-compatible agent name (e.g., "Researcher")
            - message: Human-readable message
            - json_payload: Full JSON payload if JSON format, None if text format

        Migration Path:
            During migration, some agents will output JSON while others output text.
            This parser handles both gracefully, allowing incremental agent migration.
            Once all agents are migrated, the legacy text parsing can be removed.
        """
        # ========================================================================
        # PHASE 2 (NEW): Try parsing as JSON first
        # ========================================================================
        try:
            # Attempt to parse as JSON
            event = json.loads(line.strip())

            # Validate it's an agent_update event with proper structure
            if (
                isinstance(event, dict)
                and event.get("type") == "agent_update"
                and "payload" in event
            ):
                payload = event["payload"]

                # Extract and normalize agent name - ALWAYS apply mapping
                # The CLI may send "MASTER", "ORCHESTRATOR", "RESEARCHER" which need mapping
                raw_agent_name = payload.get("agent_name", "")
                agent_id = payload.get("agent_id", "")

                # Try mapping by agent_name first (uppercase comparison)
                agent_name_upper = raw_agent_name.upper()
                if agent_name_upper in AGENT_NAME_MAP:
                    mapped_name = AGENT_NAME_MAP[agent_name_upper]
                    # Check if infrastructure agent (mapped to None)
                    if mapped_name is None:
                        logger.debug(f"⏭️ Skipping infrastructure agent: {raw_agent_name}")
                        return None
                    agent_name = mapped_name
                # Try mapping by agent_id if name mapping didn't work
                elif agent_id:
                    agent_id_upper = agent_id.upper()
                    if agent_id_upper in AGENT_NAME_MAP:
                        mapped_name = AGENT_NAME_MAP[agent_id_upper]
                        # Check if infrastructure agent
                        if mapped_name is None:
                            logger.debug(f"⏭️ Skipping infrastructure agent: {agent_id}")
                            return None
                        agent_name = mapped_name
                    else:
                        # No mapping found, use capitalized version
                        agent_name = agent_id.capitalize()
                else:
                    # Fallback: use raw agent_name if no mapping found
                    agent_name = raw_agent_name if raw_agent_name else "Unknown"

                message = payload.get("message", "")

                logger.info(f"✅ Parsed JSON agent update: {agent_name} - {message[:50]}...")
                return (agent_name, message, payload)

        except (json.JSONDecodeError, KeyError, TypeError):
            # Not JSON or invalid structure, fall through to legacy text parsing
            pass

        # ========================================================================
        # LEGACY: Text format parsing (to be deprecated)
        # ========================================================================

        # Strip ANSI color codes first (e.g., \x1b[36m, \x1b[0m)
        ansi_escape = re.compile(r"\x1b\[[0-9;]*[mGKHF]")
        clean_line = ansi_escape.sub("", line).strip()

        # Try pattern 1: "AGENT_NAME: message" (uppercase with colon)
        match = re.search(r"([A-Z_]+):\s*(.+)", clean_line)
        if match:
            cli_agent_name = match.group(1)
            message = match.group(2).strip()
            if cli_agent_name in AGENT_NAME_MAP:
                frontend_agent_name = AGENT_NAME_MAP[cli_agent_name]
                if frontend_agent_name is not None:
                    logger.debug(f"📝 Parsed legacy text (pattern 1): {frontend_agent_name}")
                    return (frontend_agent_name, message, None)
                else:
                    # Agent is mapped to None - skip it (infrastructure agent)
                    logger.debug(f"⏭️ Skipping infrastructure agent: {cli_agent_name}")
                    return None

        # Try pattern 2: "Agent Name - message" (mixed case with hyphen)
        match = re.search(
            r"(Browser|Editor|Researcher|Writer|Publisher|Translator|Reviewer|Reviser)\s*-\s*(.+)",
            clean_line,
        )
        if match:
            agent_name = match.group(1)
            message = match.group(2).strip()
            # Agent name is already in frontend format
            logger.debug(f"📝 Parsed legacy text (pattern 2): {agent_name}")
            return (agent_name, message, None)

        return None

    async def update_agent_status(
        self,
        session_id: str,
        agent_name: str,
        message: str,
        json_payload: dict | None = None,
    ):
        """
        Update agent status and send agent_update event (Phase 2: Enhanced for JSON)

        Handles both legacy text-based status inference and new JSON-based explicit status.

        Args:
            session_id: Research session ID
            agent_name: Frontend-compatible agent name (e.g., "Researcher")
            message: Human-readable status message
            json_payload: Optional JSON payload from structured output (Phase 2)
                         Contains explicit status, progress, data, etc.
        """
        # Initialize agent states for this session if needed
        if session_id not in self.agent_states:
            self.agent_states[session_id] = {}

        # ========================================================================
        # PHASE 2: Use explicit data from JSON payload if available
        # ========================================================================
        if json_payload:
            # Extract explicit status and progress from JSON
            status = json_payload.get("status", "running")
            progress = json_payload.get("progress")  # Use only if explicitly provided

            # DON'T use artificial progress - only real progress from agents
            # If progress not provided, leave as None (frontend will show status without percentage)

            # Store the status
            self.agent_states[session_id][agent_name] = status
            if progress is not None:
                self.agent_states[session_id][f"{agent_name}_progress"] = progress

            # Create and send agent_update event using JSON data
            agent_event = create_agent_update_event(
                session_id=session_id,
                agent_id=json_payload.get("agent_id", agent_name.lower()),
                agent_name=agent_name,
                status=status,
                progress=progress,  # May be None - that's OK
                message=message,
            )
            await self.send_event(session_id, agent_event)
            progress_str = f"{progress}%" if progress is not None else "status only"
            logger.info(
                f"✅ Sent JSON-based agent_update: {agent_name} → {status} ({progress_str})"
            )
            return

        # ========================================================================
        # LEGACY: Infer status from message content (text-based agents)
        # ========================================================================

        # Determine agent status based on message keywords
        message_lower = message.lower()

        if any(
            keyword in message_lower for keyword in ["completed", "done", "finished", "success"]
        ):
            status = "completed"
            progress = 100
        elif any(keyword in message_lower for keyword in ["error", "failed", "exception"]):
            status = "error"
            progress = self.agent_states[session_id].get(f"{agent_name}_progress", 0)
        else:
            # Agent is running
            status = "running"
            # Estimate progress based on agent position in pipeline
            try:
                agent_index = AGENT_PIPELINE.index(agent_name)
                # Running agents are typically 10-90% through their work
                progress = min(90, 10 + (agent_index * 10))
            except ValueError:
                progress = 50  # Default progress for unknown agents

        # Store the status
        self.agent_states[session_id][agent_name] = status
        self.agent_states[session_id][f"{agent_name}_progress"] = progress

        # Create and send agent_update event
        agent_event = create_agent_update_event(
            session_id=session_id,
            agent_id=agent_name.lower(),
            agent_name=agent_name,
            status=status,
            progress=progress,
            message=message,
        )
        await self.send_event(session_id, agent_event)
        logger.info(f"📝 Sent text-based agent_update: {agent_name} → {status} ({progress}%)")

    async def stream_cli_output(self, session_id: str, cli_executor, subject: str, language: str):
        """Stream CLI output to all connected WebSocket clients using structured events"""
        try:
            # Initialize agent states for this session
            self.agent_states[session_id] = {}

            # Send initial research status
            start_event = create_research_status_event(
                session_id=session_id,
                overall_status="running",
                progress=0.0,
                current_stage="Starting research pipeline",
                agents_completed=0,
                agents_total=7,  # 7 active agents (includes Orchestrator)
            )
            await self.send_event(session_id, start_event)

            # Stream CLI output with agent parsing
            async for output_line in cli_executor.execute_research(subject, language, session_id):
                # Always send log event
                log_event = create_log_event(
                    session_id=session_id,
                    level="info",
                    message=output_line.rstrip(),
                    source="cli_executor",
                )
                await self.send_event(session_id, log_event)

                # Parse for agent updates (Phase 2: supports both JSON and text)
                parsed = self.parse_agent_from_output(output_line)
                if parsed:
                    agent_name, message, json_payload = parsed
                    logger.info(f"Parsed agent update: {agent_name} - {message[:50]}...")
                    await self.update_agent_status(session_id, agent_name, message, json_payload)

            # Send completion event
            completion_event = create_research_status_event(
                session_id=session_id,
                overall_status="completed",
                progress=100.0,
                current_stage="Research completed",
                agents_completed=7,
                agents_total=7,  # 7 active agents (includes Orchestrator)
            )
            await self.send_event(session_id, completion_event)

            # Clean up agent states
            if session_id in self.agent_states:
                del self.agent_states[session_id]

        except Exception as e:
            logger.error(f"Error streaming CLI output for session {session_id}: {e}")
            error_event = create_error_event(
                session_id=session_id,
                error_type="research_execution_error",
                message=f"Error during research: {str(e)}",
                recoverable=False,
            )
            await self.send_event(session_id, error_event)

            # Clean up agent states on error
            if session_id in self.agent_states:
                del self.agent_states[session_id]

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
                        msg_type = data.get("type")

                        if msg_type == "ping":
                            # Client ping - respond with pong
                            await websocket.send_text(
                                json.dumps(
                                    {
                                        "type": "pong",
                                        "timestamp": datetime.now().isoformat(),
                                    }
                                )
                            )
                        elif msg_type == "pong":
                            # Pong response from client - reset heartbeat
                            last_pong = datetime.now()
                            missed_pongs = 0
                            logger.debug(f"💓 Received pong from session {session_id[:8]}")
                        elif msg_type == "ack":
                            # Client acknowledged a message
                            message_id = data.get("message_id")
                            if message_id:
                                await self.ack_tracker.acknowledge(message_id, session_id)
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
            # Clean up ack tracker
            self.ack_tracker.cleanup_session(session_id)
            self.disconnect(websocket, session_id)

    def get_session_connection_count(self, session_id: str) -> int:
        """Get number of active connections for a session"""
        return len(self.active_connections.get(session_id, set()))

    def get_all_sessions(self) -> list:
        """Get list of all active sessions"""
        return list(self.active_connections.keys())

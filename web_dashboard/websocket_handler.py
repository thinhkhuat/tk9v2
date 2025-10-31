import asyncio
import json
import logging
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
from models import LogMessage
from schemas import (
    create_agent_update_event,
    create_research_status_event,
    create_log_event,
    create_error_event,
    WebSocketEvent
)

logger = logging.getLogger(__name__)

class WebSocketManager:
    """Manages WebSocket connections for real-time log streaming"""
    
    def __init__(self):
        # Active connections: session_id -> set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        
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
            agents_total=8
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

    async def send_event(self, session_id: str, event: WebSocketEvent):
        """Send a structured event to all connections for a session"""
        if session_id not in self.active_connections:
            return

        disconnected_connections = set()
        event_json = event.to_json_dict()

        for connection in self.active_connections[session_id].copy():
            try:
                await connection.send_text(json.dumps(event_json))
            except Exception as e:
                logger.warning(f"Failed to send event to WebSocket: {e}")
                disconnected_connections.add(connection)

        # Clean up disconnected connections
        for connection in disconnected_connections:
            self.active_connections[session_id].discard(connection)
    
    async def stream_cli_output(self, session_id: str, cli_executor, subject: str, language: str):
        """Stream CLI output to all connected WebSocket clients using structured events"""
        try:
            # Send initial research status
            start_event = create_research_status_event(
                session_id=session_id,
                overall_status="running",
                progress=0.0,
                current_stage="Starting research pipeline",
                agents_completed=0,
                agents_total=8
            )
            await self.send_event(session_id, start_event)

            # Stream CLI output as log events
            async for output_line in cli_executor.execute_research(subject, language, session_id):
                log_event = create_log_event(
                    session_id=session_id,
                    level="info",
                    message=output_line.rstrip(),
                    source="cli_executor"
                )
                await self.send_event(session_id, log_event)

            # Send completion event
            completion_event = create_research_status_event(
                session_id=session_id,
                overall_status="completed",
                progress=100.0,
                current_stage="Research completed",
                agents_completed=8,
                agents_total=8
            )
            await self.send_event(session_id, completion_event)

        except Exception as e:
            logger.error(f"Error streaming CLI output for session {session_id}: {e}")
            error_event = create_error_event(
                session_id=session_id,
                error_type="research_execution_error",
                message=f"Error during research: {str(e)}",
                recoverable=False
            )
            await self.send_event(session_id, error_event)
    
    async def handle_websocket(self, websocket: WebSocket, session_id: str):
        """Handle WebSocket lifecycle for a session"""
        try:
            await self.connect(websocket, session_id)

            # POC: Send test event after 2 seconds
            await asyncio.sleep(2)
            await websocket.send_text(json.dumps({
                "event_type": "agent_update",
                "payload": {
                    "agent_id": "proof_of_concept_agent",
                    "agent_name": "PoC Agent",
                    "status": "completed",
                    "message": "Connection validated ✅"
                },
                "timestamp": datetime.now().isoformat()
            }))

            # Keep connection alive and listen for any client messages
            while True:
                try:
                    # Wait for messages from client (like ping/pong)
                    message = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
                    
                    # Handle client messages if needed
                    try:
                        data = json.loads(message)
                        if data.get("type") == "ping":
                            await websocket.send_text(json.dumps({
                                "type": "pong",
                                "timestamp": datetime.now().isoformat()
                            }))
                    except json.JSONDecodeError:
                        pass  # Ignore invalid JSON
                        
                except asyncio.TimeoutError:
                    # No message received, continue (this keeps the connection alive)
                    pass
                except WebSocketDisconnect:
                    break
                    
        except WebSocketDisconnect:
            pass
        except Exception as e:
            logger.error(f"WebSocket error for session {session_id}: {e}")
        finally:
            self.disconnect(websocket, session_id)
    
    def get_session_connection_count(self, session_id: str) -> int:
        """Get number of active connections for a session"""
        return len(self.active_connections.get(session_id, set()))
    
    def get_all_sessions(self) -> list:
        """Get list of all active sessions"""
        return list(self.active_connections.keys())
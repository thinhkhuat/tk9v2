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

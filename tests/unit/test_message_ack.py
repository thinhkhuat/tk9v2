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
        {"event_type": "agent_update", "payload": {"test": "data"}},
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

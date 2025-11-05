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

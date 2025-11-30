"""Tests for WebSocket integration."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

# Check if websockets is available for testing
try:
    import websockets

    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False


class TestWebSocketWithoutWebsockets:
    """Tests that work without websockets installed."""

    def test_import_raises_without_websockets(self):
        """Import should raise ImportError if websockets not installed."""
        if WEBSOCKETS_AVAILABLE:
            pytest.skip("websockets is installed, cannot test ImportError")

        with pytest.raises(ImportError, match="pip install cnckit\\[websocket\\]"):
            from cnckit.integrations.websocket import WebSocketServer  # noqa: F401


@pytest.mark.skipif(not WEBSOCKETS_AVAILABLE, reason="websockets not installed")
class TestMessageFormatting:
    """Tests for message creation functions."""

    def test_create_message_basic(self):
        """create_message creates valid JSON with type and timestamp."""
        from cnckit.integrations.websocket import create_message

        msg = create_message("test_type")
        parsed = json.loads(msg)

        assert parsed["type"] == "test_type"
        assert "timestamp" in parsed
        assert "T" in parsed["timestamp"]  # ISO format
        assert parsed["data"] == {}

    def test_create_message_with_data(self):
        """create_message includes data payload."""
        from cnckit.integrations.websocket import create_message

        data = {"key": "value", "number": 42}
        msg = create_message("test_type", data)
        parsed = json.loads(msg)

        assert parsed["data"] == data

    def test_job_to_dict(self):
        """job_to_dict converts Job to dictionary."""
        from cnckit.core import Job
        from cnckit.integrations.websocket import job_to_dict

        job = Job(path=Path("/test/part.ngc"), priority=5, name="Test Part")
        result = job_to_dict(job)

        assert result["id"] == "/test/part.ngc"
        assert result["name"] == "Test Part"
        assert result["path"] == "/test/part.ngc"
        assert result["priority"] == 5
        assert result["status"] == "pending"
        assert "created_at" in result


@pytest.mark.skipif(not WEBSOCKETS_AVAILABLE, reason="websockets not installed")
class TestWebSocketServerInit:
    """Tests for WebSocketServer initialization."""

    def test_init_with_defaults(self):
        """WebSocketServer initializes with default values."""
        from cnckit.integrations.websocket import WebSocketServer

        server = WebSocketServer()

        assert server.host == "localhost"
        assert server.port == 8765
        assert server.is_running is False
        assert server.client_count == 0

    def test_init_with_custom_values(self):
        """WebSocketServer accepts custom host and port."""
        from cnckit.integrations.websocket import WebSocketServer

        server = WebSocketServer(host="0.0.0.0", port=9000)

        assert server.host == "0.0.0.0"
        assert server.port == 9000


@pytest.mark.skipif(not WEBSOCKETS_AVAILABLE, reason="websockets not installed")
class TestWebSocketServerLifecycle:
    """Tests for server start/stop lifecycle."""

    @pytest.mark.asyncio
    async def test_start_sets_running_flag(self):
        """start() sets is_running to True."""
        from cnckit.integrations.websocket import WebSocketServer

        server = WebSocketServer(port=18765)

        # serve() is an async function that returns a server object
        async def mock_serve(*args, **kwargs):
            return AsyncMock()

        with patch("cnckit.integrations.websocket.serve", side_effect=mock_serve):
            await server.start()

            assert server.is_running is True

            await server.stop()

    @pytest.mark.asyncio
    async def test_start_raises_if_already_running(self):
        """start() raises RuntimeError if already running."""
        from cnckit.integrations.websocket import WebSocketServer

        server = WebSocketServer(port=18766)

        async def mock_serve(*args, **kwargs):
            return AsyncMock()

        with patch("cnckit.integrations.websocket.serve", side_effect=mock_serve):
            await server.start()

            with pytest.raises(RuntimeError, match="already running"):
                await server.start()

            await server.stop()

    @pytest.mark.asyncio
    async def test_stop_clears_running_flag(self):
        """stop() sets is_running to False."""
        from cnckit.integrations.websocket import WebSocketServer

        server = WebSocketServer(port=18767)

        async def mock_serve(*args, **kwargs):
            return AsyncMock()

        with patch("cnckit.integrations.websocket.serve", side_effect=mock_serve):
            await server.start()
            await server.stop()

            assert server.is_running is False

    @pytest.mark.asyncio
    async def test_stop_is_idempotent(self):
        """stop() can be called multiple times safely."""
        from cnckit.integrations.websocket import WebSocketServer

        server = WebSocketServer(port=18768)

        # Stop without starting - should not raise
        await server.stop()
        await server.stop()

        assert server.is_running is False

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Server works as async context manager."""
        from cnckit.integrations.websocket import WebSocketServer

        server = WebSocketServer(port=18769)

        async def mock_serve(*args, **kwargs):
            return AsyncMock()

        with patch("cnckit.integrations.websocket.serve", side_effect=mock_serve):
            async with server:
                assert server.is_running is True

            assert server.is_running is False


@pytest.mark.skipif(not WEBSOCKETS_AVAILABLE, reason="websockets not installed")
class TestWebSocketBroadcast:
    """Tests for broadcasting methods."""

    @pytest.fixture
    def server_with_mock_client(self):
        """Create server with a mock client."""
        from cnckit.integrations.websocket import WebSocketServer

        server = WebSocketServer()
        mock_client = AsyncMock()
        server._clients.add(mock_client)
        server._running = True
        return server, mock_client

    @pytest.mark.asyncio
    async def test_broadcast_sends_to_client(self, server_with_mock_client):
        """broadcast() sends message to connected client."""
        server, mock_client = server_with_mock_client

        await server.broadcast('{"type": "test"}')

        mock_client.send.assert_called_once_with('{"type": "test"}')

    @pytest.mark.asyncio
    async def test_broadcast_to_multiple_clients(self):
        """broadcast() sends to all connected clients."""
        from cnckit.integrations.websocket import WebSocketServer

        server = WebSocketServer()
        client1 = AsyncMock()
        client2 = AsyncMock()
        server._clients = {client1, client2}
        server._running = True

        await server.broadcast('{"type": "test"}')

        client1.send.assert_called_once()
        client2.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_broadcast_removes_disconnected_clients(self):
        """broadcast() removes clients that raise ConnectionClosed."""
        from cnckit.integrations.websocket import WebSocketServer

        server = WebSocketServer()
        good_client = AsyncMock()
        bad_client = AsyncMock()
        bad_client.send.side_effect = websockets.exceptions.ConnectionClosed(None, None)

        server._clients = {good_client, bad_client}
        server._running = True

        await server.broadcast('{"type": "test"}')

        # Bad client should be removed
        assert bad_client not in server._clients
        assert good_client in server._clients

    @pytest.mark.asyncio
    async def test_broadcast_with_no_clients(self):
        """broadcast() handles empty client list gracefully."""
        from cnckit.integrations.websocket import WebSocketServer

        server = WebSocketServer()
        server._running = True

        # Should not raise
        await server.broadcast('{"type": "test"}')

    @pytest.mark.asyncio
    async def test_broadcast_machine_state(self, server_with_mock_client):
        """broadcast_machine_state sends formatted message."""
        server, mock_client = server_with_mock_client

        await server.broadcast_machine_state(
            state="running",
            position={"x": 10.0, "y": 20.0, "z": 5.0},
            progress=0.5,
            current_program="/test.ngc",
            tool=1,
        )

        call_args = mock_client.send.call_args
        payload = json.loads(call_args[0][0])

        assert payload["type"] == "machine_state"
        assert payload["data"]["state"] == "running"
        assert payload["data"]["progress"] == 0.5
        assert payload["data"]["tool"] == 1

    @pytest.mark.asyncio
    async def test_broadcast_job_started(self, server_with_mock_client):
        """broadcast_job_started sends job data."""
        from cnckit.core import Job

        server, mock_client = server_with_mock_client
        job = Job(path=Path("/test.ngc"))

        await server.broadcast_job_started(job)

        call_args = mock_client.send.call_args
        payload = json.loads(call_args[0][0])

        assert payload["type"] == "job_started"
        assert payload["data"]["job"]["path"] == "/test.ngc"

    @pytest.mark.asyncio
    async def test_broadcast_job_completed(self, server_with_mock_client):
        """broadcast_job_completed sends job data."""
        from cnckit.core import Job

        server, mock_client = server_with_mock_client
        job = Job(path=Path("/test.ngc"))
        job.mark_completed()

        await server.broadcast_job_completed(job)

        call_args = mock_client.send.call_args
        payload = json.loads(call_args[0][0])

        assert payload["type"] == "job_completed"

    @pytest.mark.asyncio
    async def test_broadcast_job_failed(self, server_with_mock_client):
        """broadcast_job_failed sends job data with error."""
        from cnckit.core import Job

        server, mock_client = server_with_mock_client
        job = Job(path=Path("/test.ngc"))
        job.mark_failed("Tool broke")

        await server.broadcast_job_failed(job, error="Tool broke")

        call_args = mock_client.send.call_args
        payload = json.loads(call_args[0][0])

        assert payload["data"]["error"] == "Tool broke"

    @pytest.mark.asyncio
    async def test_broadcast_queue_empty(self, server_with_mock_client):
        """broadcast_queue_empty sends empty message."""
        server, mock_client = server_with_mock_client

        await server.broadcast_queue_empty()

        call_args = mock_client.send.call_args
        payload = json.loads(call_args[0][0])

        assert payload["type"] == "queue_empty"

    @pytest.mark.asyncio
    async def test_broadcast_scheduler_state(self, server_with_mock_client):
        """broadcast_scheduler_state sends state data."""
        from cnckit.core import Job

        server, mock_client = server_with_mock_client
        job = Job(path=Path("/test.ngc"))

        await server.broadcast_scheduler_state(state="running", current_job=job)

        call_args = mock_client.send.call_args
        payload = json.loads(call_args[0][0])

        assert payload["type"] == "scheduler_state"
        assert payload["data"]["state"] == "running"
        assert payload["data"]["current_job"]["path"] == "/test.ngc"


@pytest.mark.skipif(not WEBSOCKETS_AVAILABLE, reason="websockets not installed")
class TestWebSocketEventBinding:
    """Tests for event binding functionality."""

    def test_bind_events_registers_handlers(self):
        """bind_events registers event handlers."""
        from cnckit.core import Event, EventEmitter
        from cnckit.integrations.websocket import WebSocketServer

        server = WebSocketServer()
        events = EventEmitter()

        server.bind_events(events)

        # Check handlers are registered
        assert len(events.listeners(Event.JOB_STARTED)) > 0
        assert len(events.listeners(Event.JOB_COMPLETED)) > 0
        assert len(events.listeners(Event.JOB_FAILED)) > 0
        assert len(events.listeners(Event.QUEUE_EMPTY)) > 0

    def test_unbind_events_removes_handlers(self):
        """_unbind_events removes all event handlers."""
        from cnckit.core import Event, EventEmitter
        from cnckit.integrations.websocket import WebSocketServer

        server = WebSocketServer()
        events = EventEmitter()

        server.bind_events(events)
        server._unbind_events()

        # Handlers should be removed
        assert len(events.listeners(Event.JOB_STARTED)) == 0
        assert len(events.listeners(Event.JOB_COMPLETED)) == 0


@pytest.mark.skipif(not WEBSOCKETS_AVAILABLE, reason="websockets not installed")
class TestWebSocketClientHandling:
    """Tests for client connection handling."""

    @pytest.mark.asyncio
    async def test_handle_client_adds_to_set(self):
        """_handle_client adds client to clients set."""
        from cnckit.integrations.websocket import WebSocketServer

        server = WebSocketServer()

        # Create a mock websocket that supports async iteration
        class MockWebSocket:
            def __init__(self):
                self.send = AsyncMock()

            def __aiter__(self):
                return self

            async def __anext__(self):
                raise StopAsyncIteration

        mock_ws = MockWebSocket()

        await server._handle_client(mock_ws)

        # Client should be removed after handler exits
        assert mock_ws not in server._clients

    @pytest.mark.asyncio
    async def test_handle_message_responds_to_ping(self):
        """_handle_message responds to ping with pong."""
        from cnckit.integrations.websocket import WebSocketServer

        server = WebSocketServer()
        mock_ws = AsyncMock()

        await server._handle_message(mock_ws, '{"type": "ping"}')

        mock_ws.send.assert_called_once()
        call_args = mock_ws.send.call_args
        payload = json.loads(call_args[0][0])
        assert payload["type"] == "pong"

    @pytest.mark.asyncio
    async def test_handle_message_ignores_invalid_json(self):
        """_handle_message handles invalid JSON gracefully."""
        from cnckit.integrations.websocket import WebSocketServer

        server = WebSocketServer()
        mock_ws = AsyncMock()

        # Should not raise
        await server._handle_message(mock_ws, "not valid json")
        await server._handle_message(mock_ws, b"\xff\xfe")

        # No response sent for invalid messages
        mock_ws.send.assert_not_called()


@pytest.mark.skipif(not WEBSOCKETS_AVAILABLE, reason="websockets not installed")
class TestWebSocketIntegration:
    """Integration tests with real server (using available ports)."""

    @pytest.mark.asyncio
    async def test_real_server_starts_and_stops(self):
        """Real server can start and stop."""
        from cnckit.integrations.websocket import WebSocketServer

        # Use a random high port to avoid conflicts
        server = WebSocketServer(host="127.0.0.1", port=28765)

        await server.start()
        assert server.is_running is True

        await server.stop()
        assert server.is_running is False

    @pytest.mark.asyncio
    async def test_real_client_connection(self):
        """Real client can connect and receive messages."""
        from cnckit.integrations.websocket import WebSocketServer

        server = WebSocketServer(host="127.0.0.1", port=28766)

        async with server:
            # Connect a client
            async with websockets.connect("ws://127.0.0.1:28766") as client:
                # Should receive welcome message
                msg = await asyncio.wait_for(client.recv(), timeout=2.0)
                data = json.loads(msg)

                assert data["type"] == "connected"
                assert server.client_count == 1

            # Give server time to detect disconnect
            await asyncio.sleep(0.1)
            assert server.client_count == 0

    @pytest.mark.asyncio
    async def test_broadcast_reaches_client(self):
        """Broadcast message reaches connected client."""
        from cnckit.integrations.websocket import WebSocketServer

        server = WebSocketServer(host="127.0.0.1", port=28767)

        async with server, websockets.connect("ws://127.0.0.1:28767") as client:
            # Consume welcome message
            await client.recv()

            # Broadcast a message
            await server.broadcast_machine_state(
                state="idle",
                progress=0.0,
            )

            # Client should receive it
            msg = await asyncio.wait_for(client.recv(), timeout=2.0)
            data = json.loads(msg)

            assert data["type"] == "machine_state"
            assert data["data"]["state"] == "idle"

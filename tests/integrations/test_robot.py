"""Tests for Robot integration."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from cnckit.integrations.robot import (
    RobotCommand,
    RobotStatus,
    TCPRobotClient,
    create_message,
    job_to_dict,
)


class TestRobotCommand:
    """Tests for RobotCommand enum."""

    def test_command_values(self):
        """RobotCommand has expected values."""
        assert RobotCommand.LOAD_PART.value == "load_part"
        assert RobotCommand.UNLOAD_PART.value == "unload_part"
        assert RobotCommand.TOOL_CHANGE.value == "tool_change"
        assert RobotCommand.HOME.value == "home"
        assert RobotCommand.STOP.value == "stop"
        assert RobotCommand.PAUSE.value == "pause"
        assert RobotCommand.RESUME.value == "resume"


class TestRobotStatus:
    """Tests for RobotStatus dataclass."""

    def test_default_values(self):
        """RobotStatus has correct defaults."""
        status = RobotStatus()

        assert status.connected is False
        assert status.ready is False
        assert status.busy is False
        assert status.error is None
        assert status.position is None

    def test_custom_values(self):
        """RobotStatus accepts custom values."""
        status = RobotStatus(
            connected=True,
            ready=True,
            busy=False,
            error="Test error",
            position={"x": 1.0, "y": 2.0, "z": 3.0},
        )

        assert status.connected is True
        assert status.ready is True
        assert status.error == "Test error"
        assert status.position == {"x": 1.0, "y": 2.0, "z": 3.0}


class TestMessageFormatting:
    """Tests for message creation functions."""

    def test_create_message_basic(self):
        """create_message creates valid JSON with type and timestamp."""
        msg = create_message("test_type")
        parsed = json.loads(msg)

        assert parsed["type"] == "test_type"
        assert "timestamp" in parsed
        assert "T" in parsed["timestamp"]  # ISO format
        assert parsed["data"] == {}

    def test_create_message_with_data(self):
        """create_message includes data payload."""
        data = {"key": "value", "number": 42}
        msg = create_message("test_type", data)
        parsed = json.loads(msg)

        assert parsed["data"] == data

    def test_job_to_dict(self):
        """job_to_dict converts Job to dictionary."""
        from cnckit.core import Job

        job = Job(path=Path("/test/part.ngc"), priority=5, name="Test Part")
        result = job_to_dict(job)

        assert result["id"] == "/test/part.ngc"
        assert result["name"] == "Test Part"
        assert result["path"] == "/test/part.ngc"
        assert result["priority"] == 5
        assert result["status"] == "pending"


class TestTCPRobotClientInit:
    """Tests for TCPRobotClient initialization."""

    def test_init_with_defaults(self):
        """TCPRobotClient initializes with specified host and port."""
        client = TCPRobotClient("192.168.1.100", 10000)

        assert client.host == "192.168.1.100"
        assert client.port == 10000
        assert client.is_connected is False

    def test_init_with_custom_options(self):
        """TCPRobotClient accepts custom timeout and terminator."""
        client = TCPRobotClient(
            "192.168.1.100",
            10000,
            timeout=5.0,
            terminator="\r\n",
            encoding="ascii",
        )

        assert client._timeout == 5.0
        assert client._terminator == "\r\n"
        assert client._encoding == "ascii"


class TestTCPRobotClientConnection:
    """Tests for TCPRobotClient connection management."""

    def test_connect_success(self):
        """connect() establishes socket connection."""
        client = TCPRobotClient("192.168.1.100", 10000)

        mock_socket = MagicMock()
        with patch("socket.socket", return_value=mock_socket):
            client.connect()

        assert client.is_connected is True
        mock_socket.connect.assert_called_once_with(("192.168.1.100", 10000))
        mock_socket.settimeout.assert_called_once_with(10.0)

    def test_connect_already_connected(self):
        """connect() does nothing if already connected."""
        client = TCPRobotClient("192.168.1.100", 10000)

        mock_socket = MagicMock()
        with patch("socket.socket", return_value=mock_socket):
            client.connect()
            client.connect()  # Second call

        # connect should only be called once
        assert mock_socket.connect.call_count == 1

    def test_connect_failure(self):
        """connect() raises ConnectionError on failure."""
        client = TCPRobotClient("192.168.1.100", 10000)

        mock_socket = MagicMock()
        mock_socket.connect.side_effect = OSError("Connection refused")
        with (
            patch("socket.socket", return_value=mock_socket),
            pytest.raises(ConnectionError, match="Failed to connect to robot"),
        ):
            client.connect()

        assert client.is_connected is False

    def test_disconnect(self):
        """disconnect() closes socket and clears state."""
        client = TCPRobotClient("192.168.1.100", 10000)

        mock_socket = MagicMock()
        with patch("socket.socket", return_value=mock_socket):
            client.connect()
            client.disconnect()

        assert client.is_connected is False
        mock_socket.close.assert_called_once()

    def test_disconnect_handles_socket_error(self):
        """disconnect() handles socket close errors gracefully."""
        client = TCPRobotClient("192.168.1.100", 10000)

        mock_socket = MagicMock()
        mock_socket.close.side_effect = OSError("Socket error")
        with patch("socket.socket", return_value=mock_socket):
            client.connect()
            # Should not raise
            client.disconnect()

        assert client.is_connected is False

    def test_reconnect(self):
        """reconnect() disconnects and connects again."""
        client = TCPRobotClient("192.168.1.100", 10000)

        mock_socket = MagicMock()
        with patch("socket.socket", return_value=mock_socket):
            client.connect()
            client.reconnect()

        # Should have connected twice (first connect, then reconnect)
        assert mock_socket.connect.call_count == 2


class TestTCPRobotClientCommunication:
    """Tests for TCPRobotClient command sending."""

    @pytest.fixture
    def connected_client(self):
        """Create a connected client with mock socket."""
        client = TCPRobotClient("192.168.1.100", 10000)
        mock_socket = MagicMock()
        mock_socket.recv.return_value = b"OK\n"

        with patch("socket.socket", return_value=mock_socket):
            client.connect()

        return client, mock_socket

    def test_send_command_not_connected(self):
        """send_command raises ConnectionError if not connected."""
        client = TCPRobotClient("192.168.1.100", 10000)

        with pytest.raises(ConnectionError, match="Not connected"):
            client.send_command("STATUS")

    def test_send_command_success(self, connected_client):
        """send_command sends command and returns response."""
        client, mock_socket = connected_client
        mock_socket.recv.return_value = b"OK\n"

        response = client.send_command("STATUS")

        assert response == "OK"
        mock_socket.sendall.assert_called_with(b"STATUS\n")

    def test_send_command_no_wait(self, connected_client):
        """send_command with wait_response=False returns None."""
        client, mock_socket = connected_client

        response = client.send_command("GO", wait_response=False)

        assert response is None
        mock_socket.sendall.assert_called_with(b"GO\n")
        mock_socket.recv.assert_not_called()

    def test_send_command_timeout(self, connected_client):
        """send_command raises TimeoutError on socket timeout."""
        client, mock_socket = connected_client
        mock_socket.recv.side_effect = TimeoutError("timed out")

        with pytest.raises(TimeoutError, match="Response timeout"):
            client.send_command("STATUS")

    def test_send_command_connection_closed(self, connected_client):
        """send_command raises ConnectionError if connection closed."""
        client, mock_socket = connected_client
        mock_socket.recv.return_value = b""  # Empty = connection closed

        with pytest.raises(ConnectionError, match="Connection closed"):
            client.send_command("STATUS")

    def test_send_json(self, connected_client):
        """send_json sends JSON and parses response."""
        client, mock_socket = connected_client
        mock_socket.recv.return_value = b'{"status": "ok"}\n'

        response = client.send_json({"command": "test"})

        assert response == {"status": "ok"}
        # Verify JSON was sent
        call_args = mock_socket.sendall.call_args[0][0]
        sent_data = json.loads(call_args.decode().rstrip("\n"))
        assert sent_data == {"command": "test"}

    def test_send_json_invalid_response(self, connected_client):
        """send_json wraps invalid JSON response."""
        client, mock_socket = connected_client
        mock_socket.recv.return_value = b"NOT JSON\n"

        response = client.send_json({"command": "test"})

        assert response == {"raw": "NOT JSON"}


class TestTCPRobotClientCommands:
    """Tests for TCPRobotClient standard commands."""

    @pytest.fixture
    def connected_client(self):
        """Create a connected client with mock socket."""
        client = TCPRobotClient("192.168.1.100", 10000)
        mock_socket = MagicMock()
        mock_socket.recv.return_value = b"OK\n"

        with patch("socket.socket", return_value=mock_socket):
            client.connect()

        return client, mock_socket

    def test_home(self, connected_client):
        """home() sends HOME command."""
        client, mock_socket = connected_client

        client.home()

        mock_socket.sendall.assert_called_with(b"HOME\n")

    def test_stop(self, connected_client):
        """stop() sends STOP command."""
        client, mock_socket = connected_client

        client.stop()

        mock_socket.sendall.assert_called_with(b"STOP\n")

    def test_pause(self, connected_client):
        """pause() sends PAUSE command."""
        client, mock_socket = connected_client

        client.pause()

        mock_socket.sendall.assert_called_with(b"PAUSE\n")

    def test_resume(self, connected_client):
        """resume() sends RESUME command."""
        client, mock_socket = connected_client

        client.resume()

        mock_socket.sendall.assert_called_with(b"RESUME\n")

    def test_load_part(self, connected_client):
        """load_part() sends LOAD_PART command."""
        client, mock_socket = connected_client

        client.load_part()

        mock_socket.sendall.assert_called_with(b"LOAD_PART\n")

    def test_load_part_with_id(self, connected_client):
        """load_part() with part_id includes ID in command."""
        client, mock_socket = connected_client

        client.load_part("part_001")

        mock_socket.sendall.assert_called_with(b"LOAD_PART part_001\n")

    def test_unload_part(self, connected_client):
        """unload_part() sends UNLOAD_PART command."""
        client, mock_socket = connected_client

        client.unload_part()

        mock_socket.sendall.assert_called_with(b"UNLOAD_PART\n")

    def test_unload_part_with_id(self, connected_client):
        """unload_part() with part_id includes ID in command."""
        client, mock_socket = connected_client

        client.unload_part("part_001")

        mock_socket.sendall.assert_called_with(b"UNLOAD_PART part_001\n")

    def test_tool_change(self, connected_client):
        """tool_change() sends TOOL_CHANGE command with tool number."""
        client, mock_socket = connected_client

        client.tool_change(5)

        mock_socket.sendall.assert_called_with(b"TOOL_CHANGE 5\n")

    def test_inspect(self, connected_client):
        """inspect() sends INSPECT command."""
        client, mock_socket = connected_client

        client.inspect("dimensional")

        mock_socket.sendall.assert_called_with(b"INSPECT dimensional\n")

    def test_move_to(self, connected_client):
        """move_to() sends MOVE command with coordinates."""
        client, mock_socket = connected_client

        client.move_to(10.5, 20.0, -5.0)

        mock_socket.sendall.assert_called_with(b"MOVE X10.5 Y20.0 Z-5.0\n")


class TestTCPRobotClientStatus:
    """Tests for TCPRobotClient get_status()."""

    @pytest.fixture
    def connected_client(self):
        """Create a connected client with mock socket."""
        client = TCPRobotClient("192.168.1.100", 10000)
        mock_socket = MagicMock()

        with patch("socket.socket", return_value=mock_socket):
            client.connect()

        return client, mock_socket

    def test_get_status_json_response(self, connected_client):
        """get_status parses JSON response."""
        client, mock_socket = connected_client
        mock_socket.recv.return_value = (
            b'{"ready": true, "busy": false, "position": {"x": 1.0}}\n'
        )

        status = client.get_status()

        assert status.connected is True
        assert status.ready is True
        assert status.busy is False
        assert status.position == {"x": 1.0}

    def test_get_status_text_response_ready(self, connected_client):
        """get_status parses READY text response."""
        client, mock_socket = connected_client
        mock_socket.recv.return_value = b"READY\n"

        status = client.get_status()

        assert status.connected is True
        assert status.ready is True
        assert status.busy is False

    def test_get_status_text_response_busy(self, connected_client):
        """get_status parses BUSY text response."""
        client, mock_socket = connected_client
        mock_socket.recv.return_value = b"BUSY\n"

        status = client.get_status()

        assert status.connected is True
        assert status.ready is False
        assert status.busy is True

    def test_get_status_connection_error(self, connected_client):
        """get_status returns error status on connection failure."""
        client, mock_socket = connected_client
        mock_socket.recv.side_effect = TimeoutError("timeout")

        status = client.get_status()

        assert status.connected is False
        assert "timeout" in status.error.lower()


class TestTCPRobotClientEventBinding:
    """Tests for TCPRobotClient event binding."""

    def test_bind_events(self):
        """bind_events registers handlers."""
        from cnckit.core import Event, EventEmitter

        client = TCPRobotClient("192.168.1.100", 10000)
        events = EventEmitter()

        client.bind_events(events)

        assert len(events.listeners(Event.JOB_STARTED)) > 0
        assert len(events.listeners(Event.JOB_COMPLETED)) > 0

    def test_unbind_events(self):
        """disconnect removes event handlers."""
        from cnckit.core import Event, EventEmitter

        client = TCPRobotClient("192.168.1.100", 10000)
        events = EventEmitter()

        client.bind_events(events)
        client.disconnect()

        assert len(events.listeners(Event.JOB_STARTED)) == 0
        assert len(events.listeners(Event.JOB_COMPLETED)) == 0

    def test_auto_load_on_job_started(self):
        """With auto_load, load_part is called on job started."""
        from cnckit.core import Event, EventEmitter, Job

        client = TCPRobotClient("192.168.1.100", 10000)
        events = EventEmitter()

        mock_socket = MagicMock()
        mock_socket.recv.return_value = b"OK\n"

        with patch("socket.socket", return_value=mock_socket):
            client.connect()

        client.bind_events(events, auto_load=True)

        job = Job(path=Path("/test.ngc"))
        events.emit(Event.JOB_STARTED, job)

        # Should have called LOAD_PART with job path
        mock_socket.sendall.assert_called_with(b"LOAD_PART /test.ngc\n")

    def test_auto_unload_on_job_completed(self):
        """With auto_unload, unload_part is called on job completed."""
        from cnckit.core import Event, EventEmitter, Job

        client = TCPRobotClient("192.168.1.100", 10000)
        events = EventEmitter()

        mock_socket = MagicMock()
        mock_socket.recv.return_value = b"OK\n"

        with patch("socket.socket", return_value=mock_socket):
            client.connect()

        client.bind_events(events, auto_unload=True)

        job = Job(path=Path("/test.ngc"))
        events.emit(Event.JOB_COMPLETED, job)

        mock_socket.sendall.assert_called_with(b"UNLOAD_PART /test.ngc\n")

    def test_no_auto_load_if_not_connected(self):
        """Auto load does nothing if not connected."""
        from cnckit.core import Event, EventEmitter, Job

        client = TCPRobotClient("192.168.1.100", 10000)
        events = EventEmitter()

        client.bind_events(events, auto_load=True)

        job = Job(path=Path("/test.ngc"))
        # Should not raise even though not connected
        events.emit(Event.JOB_STARTED, job)


class TestROS2InterfaceImportError:
    """Tests for ROS2Interface without rclpy."""

    def test_import_raises_without_rclpy(self):
        """ROS2Interface raises ImportError without rclpy."""
        # The ROS2Interface class checks on __init__, not import
        from cnckit.integrations.robot import ROS2Interface

        with (
            patch("builtins.__import__", side_effect=ImportError("No module")),
            pytest.raises(ImportError, match="rclpy is required"),
        ):
            ROS2Interface()


class TestROS2InterfaceWithMock:
    """Tests for ROS2Interface with mocked rclpy."""

    @pytest.fixture
    def mock_rclpy(self):
        """Create mock rclpy modules."""
        mock_node = MagicMock()
        mock_publisher = MagicMock()
        mock_node.create_publisher.return_value = mock_publisher
        mock_node.create_subscription.return_value = MagicMock()

        mock_node_class = MagicMock(return_value=mock_node)

        mock_string = MagicMock()

        return {
            "node": mock_node,
            "node_class": mock_node_class,
            "publisher": mock_publisher,
            "string": mock_string,
        }

    def test_init_creates_publishers(self, mock_rclpy):
        """ROS2Interface creates publishers for each topic."""
        with (
            patch.dict(
                "sys.modules",
                {
                    "rclpy": MagicMock(),
                    "rclpy.node": MagicMock(Node=mock_rclpy["node_class"]),
                    "std_msgs": MagicMock(),
                    "std_msgs.msg": MagicMock(String=mock_rclpy["string"]),
                },
            ),
        ):
            from cnckit.integrations.robot import ROS2Interface

            interface = ROS2Interface(node_name="test_node")

            assert interface.node_name == "test_node"
            # Should have created publishers
            assert mock_rclpy["node"].create_publisher.call_count == 5

    def test_publish_machine_state(self, mock_rclpy):
        """publish_machine_state publishes to correct topic."""
        with (
            patch.dict(
                "sys.modules",
                {
                    "rclpy": MagicMock(),
                    "rclpy.node": MagicMock(Node=mock_rclpy["node_class"]),
                    "std_msgs": MagicMock(),
                    "std_msgs.msg": MagicMock(String=mock_rclpy["string"]),
                },
            ),
        ):
            from cnckit.integrations.robot import ROS2Interface

            interface = ROS2Interface()
            interface.publish_machine_state("running", progress=0.5)

            # Verify publish was called
            mock_rclpy["publisher"].publish.assert_called()

    def test_on_command_callback(self, mock_rclpy):
        """on_command registers callback for commands."""
        with (
            patch.dict(
                "sys.modules",
                {
                    "rclpy": MagicMock(),
                    "rclpy.node": MagicMock(Node=mock_rclpy["node_class"]),
                    "std_msgs": MagicMock(),
                    "std_msgs.msg": MagicMock(String=mock_rclpy["string"]),
                },
            ),
        ):
            from cnckit.integrations.robot import ROS2Interface

            interface = ROS2Interface()

            callback = MagicMock()
            interface.on_command(callback)

            # Simulate receiving a command
            mock_msg = MagicMock()
            mock_msg.data = "START"
            interface._on_command(mock_msg)

            callback.assert_called_once_with("START")

    def test_bind_events(self, mock_rclpy):
        """bind_events registers event handlers."""
        with (
            patch.dict(
                "sys.modules",
                {
                    "rclpy": MagicMock(),
                    "rclpy.node": MagicMock(Node=mock_rclpy["node_class"]),
                    "std_msgs": MagicMock(),
                    "std_msgs.msg": MagicMock(String=mock_rclpy["string"]),
                },
            ),
        ):
            from cnckit.core import Event, EventEmitter
            from cnckit.integrations.robot import ROS2Interface

            interface = ROS2Interface()
            events = EventEmitter()

            interface.bind_events(events)

            assert len(events.listeners(Event.JOB_STARTED)) > 0
            assert len(events.listeners(Event.JOB_COMPLETED)) > 0
            assert len(events.listeners(Event.JOB_FAILED)) > 0
            assert len(events.listeners(Event.QUEUE_EMPTY)) > 0

    def test_unbind_events(self, mock_rclpy):
        """unbind_events removes event handlers."""
        with (
            patch.dict(
                "sys.modules",
                {
                    "rclpy": MagicMock(),
                    "rclpy.node": MagicMock(Node=mock_rclpy["node_class"]),
                    "std_msgs": MagicMock(),
                    "std_msgs.msg": MagicMock(String=mock_rclpy["string"]),
                },
            ),
        ):
            from cnckit.core import Event, EventEmitter
            from cnckit.integrations.robot import ROS2Interface

            interface = ROS2Interface()
            events = EventEmitter()

            interface.bind_events(events)
            interface.unbind_events()

            assert len(events.listeners(Event.JOB_STARTED)) == 0

    def test_destroy(self, mock_rclpy):
        """destroy() cleans up ROS2 resources."""
        with (
            patch.dict(
                "sys.modules",
                {
                    "rclpy": MagicMock(),
                    "rclpy.node": MagicMock(Node=mock_rclpy["node_class"]),
                    "std_msgs": MagicMock(),
                    "std_msgs.msg": MagicMock(String=mock_rclpy["string"]),
                },
            ),
        ):
            from cnckit.integrations.robot import ROS2Interface

            interface = ROS2Interface()
            interface.destroy()

            mock_rclpy["node"].destroy_node.assert_called_once()

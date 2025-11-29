"""
Robot interfaces for ROS2 and TCP-based robots.

Provides coordination between CNC machine and robotic systems.

Two interfaces are available:
- TCPRobotClient: Simple TCP socket client for robots with text-based protocols
- ROS2Interface: Full ROS2 node integration (requires ROS2 installation)
"""

from __future__ import annotations

import contextlib
import json
import socket
import threading
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

    from cnckit.core import Event, EventEmitter, Job


# =============================================================================
# Common Types and Utilities
# =============================================================================


class RobotCommand(Enum):
    """Standard robot commands."""

    LOAD_PART = "load_part"
    UNLOAD_PART = "unload_part"
    TOOL_CHANGE = "tool_change"
    INSPECT = "inspect"
    HOME = "home"
    PAUSE = "pause"
    RESUME = "resume"
    STOP = "stop"


@dataclass
class RobotStatus:
    """Robot status information."""

    connected: bool = False
    ready: bool = False
    busy: bool = False
    error: str | None = None
    position: dict[str, float] | None = None


def create_message(
    msg_type: str,
    data: dict[str, Any] | None = None,
) -> str:
    """
    Create a JSON message with standard format.

    Args:
        msg_type: Message type identifier
        data: Optional data payload

    Returns:
        JSON string with type, timestamp, and data
    """
    message = {
        "type": msg_type,
        "timestamp": datetime.now().isoformat(),
        "data": data or {},
    }
    return json.dumps(message)


def job_to_dict(job: Job) -> dict[str, Any]:
    """Convert a Job instance to a dictionary for serialization."""
    return {
        "id": str(job.path),
        "name": job.name or job.path.stem,
        "path": str(job.path),
        "priority": job.priority,
        "status": job.status.value,
    }


# =============================================================================
# TCP Robot Client
# =============================================================================


class TCPRobotClient:
    """
    TCP client for simple robot protocols.

    Sends commands to robots over TCP sockets using a simple text-based
    protocol. Suitable for industrial robots with basic command interfaces.

    The client supports:
    - Synchronous command/response communication
    - Configurable message terminators
    - Automatic reconnection
    - Event binding for CNC coordination

    Example:
        >>> from cnckit.integrations.robot import TCPRobotClient
        >>>
        >>> robot = TCPRobotClient("192.168.1.100", port=10000)
        >>> robot.connect()
        >>>
        >>> # Send command and get response
        >>> response = robot.send_command("STATUS")
        >>> print(response)
        >>>
        >>> # Use predefined commands
        >>> robot.load_part(part_id="part_001")
        >>> robot.unload_part()
        >>>
        >>> robot.disconnect()

    Protocol:
        Commands are sent as text with a configurable terminator (default: newline).
        Responses are read until the terminator is received.
    """

    def __init__(
        self,
        host: str,
        port: int,
        timeout: float = 10.0,
        terminator: str = "\n",
        encoding: str = "utf-8",
    ) -> None:
        """
        Initialize TCP connection parameters.

        Args:
            host: Robot hostname or IP address
            port: Robot TCP port
            timeout: Socket timeout in seconds (default: 10.0)
            terminator: Message terminator string (default: newline)
            encoding: Character encoding for messages (default: utf-8)
        """
        self._host = host
        self._port = port
        self._timeout = timeout
        self._terminator = terminator
        self._encoding = encoding
        self._socket: socket.socket | None = None
        self._connected = False
        self._lock = threading.Lock()

        # Event binding
        self._events: EventEmitter | None = None
        self._event_handlers: list[tuple[Event, Callable[..., Any]]] = []

    @property
    def host(self) -> str:
        """Get robot hostname."""
        return self._host

    @property
    def port(self) -> int:
        """Get robot port."""
        return self._port

    @property
    def is_connected(self) -> bool:
        """Check if connected to robot."""
        return self._connected

    # -------------------------------------------------------------------------
    # Connection Management
    # -------------------------------------------------------------------------

    def connect(self) -> None:
        """
        Connect to the robot.

        Raises:
            ConnectionError: If connection fails
        """
        if self._connected:
            return

        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(self._timeout)
            self._socket.connect((self._host, self._port))
            self._connected = True
        except OSError as e:
            self._socket = None
            raise ConnectionError(f"Failed to connect to robot: {e}") from e

    def disconnect(self) -> None:
        """Disconnect from the robot."""
        self._unbind_events()
        if self._socket is not None:
            with contextlib.suppress(OSError):
                self._socket.close()
            self._socket = None
        self._connected = False

    def reconnect(self) -> None:
        """Reconnect to the robot."""
        self.disconnect()
        self.connect()

    # -------------------------------------------------------------------------
    # Communication
    # -------------------------------------------------------------------------

    def send_command(
        self,
        command: str,
        wait_response: bool = True,
    ) -> str | None:
        """
        Send a command to the robot.

        Args:
            command: Command string to send
            wait_response: Whether to wait for a response

        Returns:
            Response string if wait_response is True, else None

        Raises:
            ConnectionError: If not connected
            TimeoutError: If response times out
        """
        if not self._connected or self._socket is None:
            raise ConnectionError("Not connected to robot")

        with self._lock:
            # Send command with terminator
            message = command + self._terminator
            self._socket.sendall(message.encode(self._encoding))

            if not wait_response:
                return None

            # Read response until terminator
            response = self._read_response()
            return response

    def _read_response(self) -> str:
        """Read response from robot until terminator."""
        if self._socket is None:
            raise ConnectionError("Not connected")

        buffer = ""
        while True:
            try:
                chunk = self._socket.recv(1024).decode(self._encoding)
                if not chunk:
                    raise ConnectionError("Connection closed by robot")
                buffer += chunk
                if self._terminator in buffer:
                    # Return everything before the terminator
                    response, _ = buffer.split(self._terminator, 1)
                    return response.strip()
            except TimeoutError as e:
                raise TimeoutError("Response timeout") from e

    def send_json(
        self,
        data: dict[str, Any],
        wait_response: bool = True,
    ) -> dict[str, Any] | None:
        """
        Send JSON command to the robot.

        Args:
            data: Dictionary to send as JSON
            wait_response: Whether to wait for a response

        Returns:
            Parsed JSON response if wait_response is True, else None
        """
        command = json.dumps(data)
        response = self.send_command(command, wait_response)
        if response is None:
            return None
        try:
            result: dict[str, Any] = json.loads(response)
            return result
        except json.JSONDecodeError:
            return {"raw": response}

    # -------------------------------------------------------------------------
    # Standard Robot Commands
    # -------------------------------------------------------------------------

    def get_status(self) -> RobotStatus:
        """
        Get robot status.

        Returns:
            RobotStatus with current state
        """
        try:
            response = self.send_command("STATUS")
            if response is None:
                return RobotStatus(connected=True)

            # Try to parse as JSON
            try:
                data = json.loads(response)
                return RobotStatus(
                    connected=True,
                    ready=data.get("ready", False),
                    busy=data.get("busy", False),
                    error=data.get("error"),
                    position=data.get("position"),
                )
            except json.JSONDecodeError:
                # Simple text response
                return RobotStatus(
                    connected=True,
                    ready="READY" in response.upper(),
                    busy="BUSY" in response.upper(),
                )
        except (ConnectionError, TimeoutError) as e:
            return RobotStatus(connected=False, error=str(e))

    def home(self) -> str | None:
        """Send robot to home position."""
        return self.send_command("HOME")

    def stop(self) -> str | None:
        """Emergency stop the robot."""
        return self.send_command("STOP")

    def pause(self) -> str | None:
        """Pause robot motion."""
        return self.send_command("PAUSE")

    def resume(self) -> str | None:
        """Resume robot motion."""
        return self.send_command("RESUME")

    def load_part(self, part_id: str | None = None) -> str | None:
        """
        Signal robot to load a part into the CNC.

        Args:
            part_id: Optional part identifier

        Returns:
            Robot response
        """
        if part_id:
            return self.send_command(f"LOAD_PART {part_id}")
        return self.send_command("LOAD_PART")

    def unload_part(self, part_id: str | None = None) -> str | None:
        """
        Signal robot to unload a part from the CNC.

        Args:
            part_id: Optional part identifier

        Returns:
            Robot response
        """
        if part_id:
            return self.send_command(f"UNLOAD_PART {part_id}")
        return self.send_command("UNLOAD_PART")

    def tool_change(self, tool_number: int) -> str | None:
        """
        Signal robot to perform tool change.

        Args:
            tool_number: Tool number to change to

        Returns:
            Robot response
        """
        return self.send_command(f"TOOL_CHANGE {tool_number}")

    def inspect(self, inspection_type: str = "visual") -> str | None:
        """
        Trigger robot-mounted inspection.

        Args:
            inspection_type: Type of inspection (visual, dimensional, etc.)

        Returns:
            Robot response (may include inspection results)
        """
        return self.send_command(f"INSPECT {inspection_type}")

    def move_to(self, x: float, y: float, z: float) -> str | None:
        """
        Move robot to position.

        Args:
            x: X coordinate
            y: Y coordinate
            z: Z coordinate

        Returns:
            Robot response
        """
        return self.send_command(f"MOVE X{x} Y{y} Z{z}")

    # -------------------------------------------------------------------------
    # Event Binding
    # -------------------------------------------------------------------------

    def bind_events(
        self,
        events: EventEmitter,
        auto_load: bool = False,
        auto_unload: bool = False,
    ) -> None:
        """
        Bind to EventEmitter for CNC coordination.

        When bound, the robot will respond to CNC events:
        - JOB_STARTED: Optionally load part
        - JOB_COMPLETED: Optionally unload part

        Args:
            events: EventEmitter to listen to
            auto_load: Automatically load part on job start
            auto_unload: Automatically unload part on job complete
        """
        from cnckit.core import Event

        self._events = events

        def on_job_started(job: Job) -> None:
            if auto_load and self._connected:
                self.load_part(str(job.path))

        def on_job_completed(job: Job) -> None:
            if auto_unload and self._connected:
                self.unload_part(str(job.path))

        handlers: list[tuple[Event, Callable[..., Any]]] = [
            (Event.JOB_STARTED, on_job_started),
            (Event.JOB_COMPLETED, on_job_completed),
        ]

        for event, handler in handlers:
            events.on(event, handler)
            self._event_handlers.append((event, handler))

    def _unbind_events(self) -> None:
        """Remove event handlers."""
        if self._events is not None:
            for event, handler in self._event_handlers:
                self._events.off(event, handler)
        self._event_handlers.clear()
        self._events = None


# =============================================================================
# ROS2 Interface
# =============================================================================


class ROS2Interface:
    """
    ROS2 interface for robot coordination.

    Publishes CNC events to ROS2 topics and subscribes to robot commands.
    Requires ROS2 to be installed and sourced.

    Topics Published:
        - /cnckit/machine_state (std_msgs/String): Machine state updates
        - /cnckit/job_started (std_msgs/String): Job started events
        - /cnckit/job_completed (std_msgs/String): Job completed events
        - /cnckit/job_failed (std_msgs/String): Job failed events

    Topics Subscribed:
        - /cnckit/commands (std_msgs/String): Incoming commands

    Example:
        >>> import rclpy
        >>> from cnckit.integrations.robot import ROS2Interface
        >>>
        >>> rclpy.init()
        >>> interface = ROS2Interface(node_name="cnckit_node")
        >>> interface.bind_events(events)
        >>>
        >>> # Publish machine state
        >>> interface.publish_machine_state("running")
        >>>
        >>> # Spin to process callbacks
        >>> rclpy.spin(interface.node)
        >>>
        >>> rclpy.shutdown()

    Note:
        ROS2 must be installed and the environment sourced before using
        this interface. See https://docs.ros.org/ for installation.
    """

    def __init__(
        self,
        node_name: str = "cnckit",
        namespace: str = "",
    ) -> None:
        """
        Initialize ROS2 node.

        Args:
            node_name: ROS2 node name (default: "cnckit")
            namespace: Optional ROS2 namespace

        Raises:
            ImportError: If rclpy is not installed
        """
        try:
            import rclpy  # noqa: F401
            from rclpy.node import Node
            from std_msgs.msg import String
        except ImportError:
            raise ImportError(
                "rclpy is required for ROS2 integration. "
                "Install ROS2 and source the setup script."
            ) from None

        # Store imports for later use
        self._String = String

        # Create node
        self._node = Node(node_name, namespace=namespace)
        self._node_name = node_name

        # Create publishers
        self._pub_machine_state = self._node.create_publisher(
            String, "cnckit/machine_state", 10
        )
        self._pub_job_started = self._node.create_publisher(
            String, "cnckit/job_started", 10
        )
        self._pub_job_completed = self._node.create_publisher(
            String, "cnckit/job_completed", 10
        )
        self._pub_job_failed = self._node.create_publisher(
            String, "cnckit/job_failed", 10
        )
        self._pub_queue_empty = self._node.create_publisher(
            String, "cnckit/queue_empty", 10
        )

        # Create subscriber for commands
        self._command_callback: Callable[[str], None] | None = None
        self._sub_commands = self._node.create_subscription(
            String,
            "cnckit/commands",
            self._on_command,
            10,
        )

        # Event binding
        self._events: EventEmitter | None = None
        self._event_handlers: list[tuple[Event, Callable[..., Any]]] = []

    @property
    def node(self) -> Any:
        """Get the ROS2 node for spinning."""
        return self._node

    @property
    def node_name(self) -> str:
        """Get the node name."""
        return self._node_name

    # -------------------------------------------------------------------------
    # Publishing
    # -------------------------------------------------------------------------

    def _publish(self, publisher: Any, message: str) -> None:
        """Publish a string message."""
        msg = self._String()
        msg.data = message
        publisher.publish(msg)

    def publish_machine_state(
        self,
        state: str,
        position: dict[str, float] | None = None,
        progress: float = 0.0,
    ) -> None:
        """
        Publish machine state to ROS2 topic.

        Args:
            state: Machine state (idle, running, etc.)
            position: Optional position dict
            progress: Program progress (0.0 to 1.0)
        """
        data = {
            "state": state,
            "position": position or {},
            "progress": progress,
        }
        self._publish(
            self._pub_machine_state,
            create_message("machine_state", data),
        )

    def publish_job_started(self, job: Job) -> None:
        """Publish job started event."""
        self._publish(
            self._pub_job_started,
            create_message("job_started", {"job": job_to_dict(job)}),
        )

    def publish_job_completed(self, job: Job) -> None:
        """Publish job completed event."""
        self._publish(
            self._pub_job_completed,
            create_message("job_completed", {"job": job_to_dict(job)}),
        )

    def publish_job_failed(self, job: Job, error: str | None = None) -> None:
        """Publish job failed event."""
        data = {"job": job_to_dict(job), "error": error or job.error}
        self._publish(
            self._pub_job_failed,
            create_message("job_failed", data),
        )

    def publish_queue_empty(self) -> None:
        """Publish queue empty event."""
        self._publish(
            self._pub_queue_empty,
            create_message("queue_empty"),
        )

    # -------------------------------------------------------------------------
    # Command Handling
    # -------------------------------------------------------------------------

    def _on_command(self, msg: Any) -> None:
        """Handle incoming command messages."""
        if self._command_callback is not None:
            self._command_callback(msg.data)

    def on_command(self, callback: Callable[[str], None]) -> None:
        """
        Register callback for incoming commands.

        Args:
            callback: Function to call with command string
        """
        self._command_callback = callback

    # -------------------------------------------------------------------------
    # Event Binding
    # -------------------------------------------------------------------------

    def bind_events(self, events: EventEmitter) -> None:
        """
        Bind to EventEmitter to automatically publish events.

        When bound, the interface will publish to ROS2 topics for:
        - JOB_STARTED -> /cnckit/job_started
        - JOB_COMPLETED -> /cnckit/job_completed
        - JOB_FAILED -> /cnckit/job_failed
        - QUEUE_EMPTY -> /cnckit/queue_empty

        Args:
            events: EventEmitter to listen to
        """
        from cnckit.core import Event

        self._events = events

        def on_job_started(job: Job) -> None:
            self.publish_job_started(job)

        def on_job_completed(job: Job) -> None:
            self.publish_job_completed(job)

        def on_job_failed(job: Job, error: str | None = None) -> None:
            self.publish_job_failed(job, error)

        def on_queue_empty() -> None:
            self.publish_queue_empty()

        handlers: list[tuple[Event, Callable[..., Any]]] = [
            (Event.JOB_STARTED, on_job_started),
            (Event.JOB_COMPLETED, on_job_completed),
            (Event.JOB_FAILED, on_job_failed),
            (Event.QUEUE_EMPTY, on_queue_empty),
        ]

        for event, handler in handlers:
            events.on(event, handler)
            self._event_handlers.append((event, handler))

    def unbind_events(self) -> None:
        """Remove event handlers."""
        if self._events is not None:
            for event, handler in self._event_handlers:
                self._events.off(event, handler)
        self._event_handlers.clear()
        self._events = None

    def destroy(self) -> None:
        """Clean up ROS2 resources."""
        self.unbind_events()
        self._node.destroy_node()


__all__ = [
    "ROS2Interface",
    "RobotCommand",
    "RobotStatus",
    "TCPRobotClient",
    "create_message",
    "job_to_dict",
]

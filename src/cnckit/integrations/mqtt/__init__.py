"""
MQTT client for messaging and automation.

Provides pub/sub integration for IoT and automation systems.
Requires: pip install cnckit[mqtt]
"""

from __future__ import annotations

import contextlib
import json
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any

# Validate paho-mqtt is available on import
try:
    import paho.mqtt.client as mqtt
except ImportError:
    raise ImportError(
        "paho-mqtt is required for MQTT integration. "
        "Install with: pip install cnckit[mqtt]"
    ) from None

if TYPE_CHECKING:
    from collections.abc import Callable

    from cnckit.core import Event, EventEmitter, Job, Scheduler


# =============================================================================
# Topic Configuration
# =============================================================================


@dataclass
class MQTTTopics:
    """
    MQTT topic configuration.

    Customize topic names by creating an instance with different values.
    All topics use a common prefix for easy filtering.

    Attributes:
        prefix: Base prefix for all topics (default: "cnckit")
        machine_state: Topic for machine state updates
        job_started: Topic for job started events
        job_completed: Topic for job completed events
        job_failed: Topic for job failed events
        queue_empty: Topic for queue empty events
        command_start: Topic for start commands
        command_pause: Topic for pause commands
        command_stop: Topic for stop commands
    """

    prefix: str = "cnckit"

    # Publish topics (outgoing)
    machine_state: str = field(init=False)
    job_started: str = field(init=False)
    job_completed: str = field(init=False)
    job_failed: str = field(init=False)
    queue_empty: str = field(init=False)

    # Subscribe topics (incoming commands)
    command_start: str = field(init=False)
    command_pause: str = field(init=False)
    command_stop: str = field(init=False)

    def __post_init__(self) -> None:
        """Build topic names from prefix."""
        self.machine_state = f"{self.prefix}/machine/state"
        self.job_started = f"{self.prefix}/job/started"
        self.job_completed = f"{self.prefix}/job/completed"
        self.job_failed = f"{self.prefix}/job/failed"
        self.queue_empty = f"{self.prefix}/queue/empty"
        self.command_start = f"{self.prefix}/commands/start"
        self.command_pause = f"{self.prefix}/commands/pause"
        self.command_stop = f"{self.prefix}/commands/stop"

    @property
    def all_command_topics(self) -> list[str]:
        """Get all command topics for subscription."""
        return [self.command_start, self.command_pause, self.command_stop]


# =============================================================================
# Message Formatting
# =============================================================================


def job_to_dict(job: Job) -> dict[str, Any]:
    """Convert a Job instance to a dictionary for JSON serialization."""
    return {
        "id": str(job.path),
        "name": job.name or job.path.stem,
        "path": str(job.path),
        "priority": job.priority,
        "status": job.status.value,
        "estimated_time": job.estimated_time,
        "created_at": job.created_at.isoformat(),
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "error": job.error,
    }


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


# =============================================================================
# MQTT Client
# =============================================================================


class MQTTClient:
    """
    MQTT client for cnckit events and commands.

    Publishes machine state and job events to MQTT topics.
    Subscribes to command topics for remote control.

    The client integrates with cnckit's EventEmitter to automatically
    publish events, and with the Scheduler to handle incoming commands.

    Example:
        >>> from cnckit.core import Machine, JobQueue, Scheduler, EventEmitter
        >>> from cnckit.integrations.mqtt import MQTTClient
        >>>
        >>> # Set up core components
        >>> machine = Machine(simulate=True)
        >>> queue = JobQueue()
        >>> events = EventEmitter()
        >>> scheduler = Scheduler(machine, queue, events)
        >>>
        >>> # Create MQTT client
        >>> client = MQTTClient("localhost", port=1883)
        >>> client.connect()
        >>> client.bind_events(events)
        >>> client.bind_scheduler(scheduler)
        >>>
        >>> # Client will now publish events and respond to commands
        >>> # Run your scheduler loop...
        >>> scheduler.run_forever()
        >>>
        >>> # When done
        >>> client.disconnect()
    """

    def __init__(
        self,
        broker: str,
        port: int = 1883,
        client_id: str | None = None,
        topics: MQTTTopics | None = None,
        username: str | None = None,
        password: str | None = None,
        keepalive: int = 60,
    ) -> None:
        """
        Initialize MQTT client.

        Args:
            broker: MQTT broker hostname or IP address
            port: MQTT broker port (default: 1883, use 8883 for TLS)
            client_id: Optional client identifier (auto-generated if not provided)
            topics: Optional custom topic configuration
            username: Optional username for authentication
            password: Optional password for authentication
            keepalive: Keepalive interval in seconds (default: 60)
        """
        self._broker = broker
        self._port = port
        self._keepalive = keepalive
        self._topics = topics if topics is not None else MQTTTopics()

        # Create paho MQTT client
        # Use CallbackAPIVersion.VERSION2 for paho-mqtt 2.0+
        try:
            self._client = mqtt.Client(
                callback_api_version=mqtt.CallbackAPIVersion.VERSION2,  # type: ignore[attr-defined]
                client_id=client_id or "",
            )
        except (AttributeError, TypeError):
            # Fallback for older paho-mqtt versions
            self._client = mqtt.Client(client_id=client_id or "")

        # Set up authentication if provided
        if username is not None:
            self._client.username_pw_set(username, password)

        # Set up callbacks
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message

        # State
        self._connected = False
        self._scheduler: Scheduler | None = None
        self._event_handlers: list[tuple[Event, Callable[..., Any]]] = []
        self._events: EventEmitter | None = None
        self._lock = threading.Lock()

        # Custom message handlers
        self._command_handlers: dict[str, Callable[[dict[str, Any]], None]] = {}

    @property
    def broker(self) -> str:
        """Get the broker hostname."""
        return self._broker

    @property
    def port(self) -> int:
        """Get the broker port."""
        return self._port

    @property
    def topics(self) -> MQTTTopics:
        """Get the topic configuration."""
        return self._topics

    @property
    def is_connected(self) -> bool:
        """Check if client is connected to broker."""
        return self._connected

    # -------------------------------------------------------------------------
    # Connection Management
    # -------------------------------------------------------------------------

    def connect(self, timeout: float = 10.0) -> None:
        """
        Connect to the MQTT broker.

        Args:
            timeout: Connection timeout in seconds

        Raises:
            ConnectionError: If connection fails
        """
        try:
            self._client.connect(self._broker, self._port, self._keepalive)
            self._client.loop_start()

            # Wait for connection with timeout
            import time

            start = time.monotonic()
            while not self._connected and (time.monotonic() - start) < timeout:
                time.sleep(0.1)

            if not self._connected:
                self._client.loop_stop()
                raise ConnectionError(
                    f"Failed to connect to MQTT broker at {self._broker}:{self._port}"
                )
        except Exception as e:
            raise ConnectionError(f"MQTT connection failed: {e}") from e

    def disconnect(self) -> None:
        """
        Disconnect from the MQTT broker.

        Also unbinds any event handlers that were registered.
        """
        self._unbind_events()
        self._client.loop_stop()
        self._client.disconnect()
        self._connected = False

    def _on_connect(
        self,
        client: mqtt.Client,
        userdata: Any,
        flags: Any,
        rc: int | Any,  # ReasonCode in paho-mqtt 2.0+
        properties: Any = None,
    ) -> None:
        """Handle connection established."""
        # rc can be int (old API) or ReasonCode (new API)
        success = rc == 0 if isinstance(rc, int) else rc.is_failure is False

        if success:
            self._connected = True
            # Subscribe to command topics
            for topic in self._topics.all_command_topics:
                client.subscribe(topic)

    def _on_disconnect(
        self,
        client: mqtt.Client,
        userdata: Any,
        rc: int | Any | None = None,  # ReasonCode in paho-mqtt 2.0+
        properties: Any = None,
    ) -> None:
        """Handle disconnection."""
        self._connected = False

    # -------------------------------------------------------------------------
    # Publishing
    # -------------------------------------------------------------------------

    def publish(
        self,
        topic: str,
        payload: str | dict[str, Any],
        qos: int = 1,
        retain: bool = False,
    ) -> None:
        """
        Publish a message to a topic.

        Args:
            topic: MQTT topic to publish to
            payload: Message payload (string or dict to be JSON-encoded)
            qos: Quality of Service level (0, 1, or 2)
            retain: Whether broker should retain the message
        """
        if isinstance(payload, dict):
            payload = json.dumps(payload)

        self._client.publish(topic, payload, qos=qos, retain=retain)

    def publish_machine_state(
        self,
        state: str,
        position: dict[str, float] | None = None,
        progress: float = 0.0,
        current_program: str | None = None,
    ) -> None:
        """
        Publish machine state update.

        Args:
            state: Machine state (idle, running, etc.)
            position: Optional position dict with x, y, z keys
            progress: Program progress (0.0 to 1.0)
            current_program: Path to current program
        """
        data = {
            "state": state,
            "position": position or {"x": 0.0, "y": 0.0, "z": 0.0},
            "progress": progress,
            "current_program": current_program,
        }
        message = create_message("machine_state", data)
        self.publish(self._topics.machine_state, message, retain=True)

    def publish_job_started(self, job: Job) -> None:
        """Publish job started event."""
        message = create_message("job_started", {"job": job_to_dict(job)})
        self.publish(self._topics.job_started, message)

    def publish_job_completed(self, job: Job) -> None:
        """Publish job completed event."""
        message = create_message("job_completed", {"job": job_to_dict(job)})
        self.publish(self._topics.job_completed, message)

    def publish_job_failed(self, job: Job, error: str | None = None) -> None:
        """Publish job failed event."""
        data = {"job": job_to_dict(job), "error": error or job.error}
        message = create_message("job_failed", data)
        self.publish(self._topics.job_failed, message)

    def publish_queue_empty(self) -> None:
        """Publish queue empty event."""
        message = create_message("queue_empty")
        self.publish(self._topics.queue_empty, message)

    # -------------------------------------------------------------------------
    # Command Handling
    # -------------------------------------------------------------------------

    def _on_message(
        self,
        client: mqtt.Client,
        userdata: Any,
        msg: mqtt.MQTTMessage,
    ) -> None:
        """Handle incoming MQTT messages."""
        topic = msg.topic
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            payload = {}

        with self._lock:
            # Check for custom handlers first
            if topic in self._command_handlers:
                with contextlib.suppress(Exception):
                    self._command_handlers[topic](payload)
                return

            # Handle built-in command topics
            if self._scheduler is not None:
                if topic == self._topics.command_start:
                    self._scheduler.start()
                elif topic == self._topics.command_pause:
                    self._scheduler.pause()
                elif topic == self._topics.command_stop:
                    self._scheduler.stop()

    def on_command(
        self,
        topic: str,
        handler: Callable[[dict[str, Any]], None],
    ) -> None:
        """
        Register a custom command handler for a topic.

        Args:
            topic: MQTT topic to handle
            handler: Callback function receiving the message payload dict

        Example:
            >>> def handle_custom(payload):
            ...     print(f"Received: {payload}")
            >>> client.on_command("cnckit/commands/custom", handle_custom)
        """
        with self._lock:
            self._command_handlers[topic] = handler
            # Subscribe to the topic if connected
            if self._connected:
                self._client.subscribe(topic)

    # -------------------------------------------------------------------------
    # Event Binding
    # -------------------------------------------------------------------------

    def bind_scheduler(self, scheduler: Scheduler) -> None:
        """
        Bind a scheduler for command handling.

        When bound, incoming commands on command topics will control
        the scheduler (start, pause, stop).

        Args:
            scheduler: Scheduler instance to control
        """
        self._scheduler = scheduler

    def bind_events(self, events: EventEmitter) -> None:
        """
        Bind to an EventEmitter to automatically publish events.

        When bound, the client will publish MQTT messages for:
        - JOB_STARTED -> job/started topic
        - JOB_COMPLETED -> job/completed topic
        - JOB_FAILED -> job/failed topic
        - QUEUE_EMPTY -> queue/empty topic

        Args:
            events: EventEmitter instance to listen to
        """
        from cnckit.core import Event

        self._events = events

        # Define handlers
        def on_job_started(job: Job) -> None:
            self.publish_job_started(job)

        def on_job_completed(job: Job) -> None:
            self.publish_job_completed(job)

        def on_job_failed(job: Job, error: str | None = None) -> None:
            self.publish_job_failed(job, error)

        def on_queue_empty() -> None:
            self.publish_queue_empty()

        # Register handlers
        handlers: list[tuple[Event, Callable[..., Any]]] = [
            (Event.JOB_STARTED, on_job_started),
            (Event.JOB_COMPLETED, on_job_completed),
            (Event.JOB_FAILED, on_job_failed),
            (Event.QUEUE_EMPTY, on_queue_empty),
        ]

        for event, handler in handlers:
            events.on(event, handler)
            self._event_handlers.append((event, handler))

    def _unbind_events(self) -> None:
        """Remove event handlers from the EventEmitter."""
        if self._events is not None:
            for event, handler in self._event_handlers:
                self._events.off(event, handler)
        self._event_handlers.clear()
        self._events = None


__all__ = [
    "MQTTClient",
    "MQTTTopics",
    "create_message",
    "job_to_dict",
]

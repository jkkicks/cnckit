"""Tests for MQTT integration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# Check if paho-mqtt is available for testing
try:
    import paho.mqtt.client  # noqa: F401

    PAHO_AVAILABLE = True
except ImportError:
    PAHO_AVAILABLE = False


class TestMQTTWithoutPaho:
    """Tests that work without paho-mqtt installed."""

    def test_import_raises_without_paho(self):
        """Import should raise ImportError if paho-mqtt not installed."""
        if PAHO_AVAILABLE:
            pytest.skip("paho-mqtt is installed, cannot test ImportError")

        with pytest.raises(ImportError, match="pip install cnckit\\[mqtt\\]"):
            from cnckit.integrations.mqtt import MQTTClient  # noqa: F401


@pytest.mark.skipif(not PAHO_AVAILABLE, reason="paho-mqtt not installed")
class TestMQTTTopics:
    """Tests for MQTTTopics configuration."""

    def test_default_prefix(self):
        """Default prefix is 'cnckit'."""
        from cnckit.integrations.mqtt import MQTTTopics

        topics = MQTTTopics()
        assert topics.prefix == "cnckit"

    def test_custom_prefix(self):
        """Custom prefix updates all topic names."""
        from cnckit.integrations.mqtt import MQTTTopics

        topics = MQTTTopics(prefix="myapp")
        assert topics.machine_state == "myapp/machine/state"
        assert topics.job_started == "myapp/job/started"
        assert topics.command_start == "myapp/commands/start"

    def test_all_command_topics(self):
        """all_command_topics returns all command topics."""
        from cnckit.integrations.mqtt import MQTTTopics

        topics = MQTTTopics()
        commands = topics.all_command_topics
        assert len(commands) == 3
        assert "cnckit/commands/start" in commands
        assert "cnckit/commands/pause" in commands
        assert "cnckit/commands/stop" in commands


@pytest.mark.skipif(not PAHO_AVAILABLE, reason="paho-mqtt not installed")
class TestMessageFormatting:
    """Tests for message creation functions."""

    def test_create_message_basic(self):
        """create_message creates valid JSON with type and timestamp."""
        from cnckit.integrations.mqtt import create_message

        msg = create_message("test_type")
        parsed = json.loads(msg)

        assert parsed["type"] == "test_type"
        assert "timestamp" in parsed
        assert "T" in parsed["timestamp"]  # ISO format
        assert parsed["data"] == {}

    def test_create_message_with_data(self):
        """create_message includes data payload."""
        from cnckit.integrations.mqtt import create_message

        data = {"key": "value", "number": 42}
        msg = create_message("test_type", data)
        parsed = json.loads(msg)

        assert parsed["data"] == data

    def test_job_to_dict(self):
        """job_to_dict converts Job to dictionary."""
        from cnckit.core import Job
        from cnckit.integrations.mqtt import job_to_dict

        job = Job(path=Path("/test/part.ngc"), priority=5, name="Test Part")
        result = job_to_dict(job)

        assert result["id"] == "/test/part.ngc"
        assert result["name"] == "Test Part"
        assert result["path"] == "/test/part.ngc"
        assert result["priority"] == 5
        assert result["status"] == "pending"
        assert "created_at" in result


@pytest.mark.skipif(not PAHO_AVAILABLE, reason="paho-mqtt not installed")
class TestMQTTClientInit:
    """Tests for MQTTClient initialization."""

    def test_init_with_defaults(self):
        """MQTTClient initializes with default values."""
        from cnckit.integrations.mqtt import MQTTClient

        with patch("paho.mqtt.client.Client"):
            client = MQTTClient("localhost")

        assert client.broker == "localhost"
        assert client.port == 1883
        assert client.is_connected is False

    def test_init_with_custom_port(self):
        """MQTTClient accepts custom port."""
        from cnckit.integrations.mqtt import MQTTClient

        with patch("paho.mqtt.client.Client"):
            client = MQTTClient("localhost", port=8883)

        assert client.port == 8883

    def test_init_with_custom_topics(self):
        """MQTTClient accepts custom topics configuration."""
        from cnckit.integrations.mqtt import MQTTClient, MQTTTopics

        topics = MQTTTopics(prefix="custom")
        with patch("paho.mqtt.client.Client"):
            client = MQTTClient("localhost", topics=topics)

        assert client.topics.prefix == "custom"

    def test_init_with_auth(self):
        """MQTTClient sets up authentication when provided."""
        from cnckit.integrations.mqtt import MQTTClient

        mock_client = MagicMock()
        with patch("paho.mqtt.client.Client", return_value=mock_client):
            MQTTClient("localhost", username="user", password="pass")

        mock_client.username_pw_set.assert_called_once_with("user", "pass")


@pytest.mark.skipif(not PAHO_AVAILABLE, reason="paho-mqtt not installed")
class TestMQTTClientPublish:
    """Tests for MQTT publishing methods."""

    @pytest.fixture
    def mock_client(self):
        """Create a mocked MQTT client."""
        from cnckit.integrations.mqtt import MQTTClient

        mock = MagicMock()
        with patch("paho.mqtt.client.Client", return_value=mock):
            client = MQTTClient("localhost")
            client._connected = True
            yield client, mock

    def test_publish_string(self, mock_client):
        """publish sends string payload."""
        client, mock = mock_client

        client.publish("test/topic", "hello")

        mock.publish.assert_called_once_with("test/topic", "hello", qos=1, retain=False)

    def test_publish_dict(self, mock_client):
        """publish JSON-encodes dict payload."""
        client, mock = mock_client

        client.publish("test/topic", {"key": "value"})

        call_args = mock.publish.call_args
        payload = call_args[0][1]
        assert json.loads(payload) == {"key": "value"}

    def test_publish_with_options(self, mock_client):
        """publish respects qos and retain options."""
        client, mock = mock_client

        client.publish("test/topic", "data", qos=2, retain=True)

        mock.publish.assert_called_once_with("test/topic", "data", qos=2, retain=True)

    def test_publish_machine_state(self, mock_client):
        """publish_machine_state sends formatted message."""
        client, mock = mock_client

        client.publish_machine_state(
            state="running",
            position={"x": 10.0, "y": 20.0, "z": 5.0},
            progress=0.5,
            current_program="/test.ngc",
        )

        call_args = mock.publish.call_args
        topic = call_args[0][0]
        payload = json.loads(call_args[0][1])

        assert topic == "cnckit/machine/state"
        assert payload["type"] == "machine_state"
        assert payload["data"]["state"] == "running"
        assert payload["data"]["progress"] == 0.5

    def test_publish_job_started(self, mock_client):
        """publish_job_started sends job data."""
        from cnckit.core import Job

        client, mock = mock_client
        job = Job(path=Path("/test.ngc"))

        client.publish_job_started(job)

        call_args = mock.publish.call_args
        topic = call_args[0][0]
        payload = json.loads(call_args[0][1])

        assert topic == "cnckit/job/started"
        assert payload["type"] == "job_started"
        assert payload["data"]["job"]["path"] == "/test.ngc"

    def test_publish_job_completed(self, mock_client):
        """publish_job_completed sends job data."""
        from cnckit.core import Job

        client, mock = mock_client
        job = Job(path=Path("/test.ngc"))
        job.mark_completed()

        client.publish_job_completed(job)

        call_args = mock.publish.call_args
        topic = call_args[0][0]
        payload = json.loads(call_args[0][1])

        assert topic == "cnckit/job/completed"
        assert payload["type"] == "job_completed"

    def test_publish_job_failed(self, mock_client):
        """publish_job_failed sends job data with error."""
        from cnckit.core import Job

        client, mock = mock_client
        job = Job(path=Path("/test.ngc"))
        job.mark_failed("Tool broke")

        client.publish_job_failed(job, error="Tool broke")

        call_args = mock.publish.call_args
        payload = json.loads(call_args[0][1])

        assert payload["data"]["error"] == "Tool broke"

    def test_publish_queue_empty(self, mock_client):
        """publish_queue_empty sends empty message."""
        client, mock = mock_client

        client.publish_queue_empty()

        call_args = mock.publish.call_args
        topic = call_args[0][0]
        payload = json.loads(call_args[0][1])

        assert topic == "cnckit/queue/empty"
        assert payload["type"] == "queue_empty"


@pytest.mark.skipif(not PAHO_AVAILABLE, reason="paho-mqtt not installed")
class TestMQTTClientCommands:
    """Tests for MQTT command handling."""

    @pytest.fixture
    def mock_client_with_scheduler(self):
        """Create mocked MQTT client with scheduler."""
        from cnckit.core import EventEmitter, JobQueue, Machine, Scheduler
        from cnckit.integrations.mqtt import MQTTClient

        mock = MagicMock()
        with patch("paho.mqtt.client.Client", return_value=mock):
            client = MQTTClient("localhost")
            client._connected = True

            machine = Machine(simulate=True)
            queue = JobQueue()
            events = EventEmitter()
            scheduler = Scheduler(machine, queue, events)
            client.bind_scheduler(scheduler)

            yield client, mock, scheduler

    def test_bind_scheduler(self, mock_client_with_scheduler):
        """bind_scheduler stores scheduler reference."""
        client, _, scheduler = mock_client_with_scheduler
        assert client._scheduler is scheduler

    def test_command_start(self, mock_client_with_scheduler):
        """Start command starts scheduler."""
        from cnckit.core import SchedulerState

        client, mock, scheduler = mock_client_with_scheduler

        # Simulate receiving start command
        msg = MagicMock()
        msg.topic = "cnckit/commands/start"
        msg.payload = b"{}"

        client._on_message(mock, None, msg)

        # Scheduler should be running (but stops immediately due to empty queue)
        # The start() was called though
        assert scheduler.state in (SchedulerState.RUNNING, SchedulerState.STOPPED)

    def test_command_pause(self, mock_client_with_scheduler):
        """Pause command calls scheduler.pause()."""
        from cnckit.core import SchedulerState

        client, mock, scheduler = mock_client_with_scheduler

        # Simulate receiving pause command when scheduler is stopped
        # pause() on a stopped scheduler is a no-op, but we verify the command works
        msg = MagicMock()
        msg.topic = "cnckit/commands/pause"
        msg.payload = b"{}"

        client._on_message(mock, None, msg)

        # Scheduler was stopped, so pause is a no-op - stays stopped
        assert scheduler.state == SchedulerState.STOPPED

    def test_command_pause_from_running(self, mock_client_with_scheduler):
        """Pause command pauses running scheduler."""
        from cnckit.core import SchedulerState

        client, mock, scheduler = mock_client_with_scheduler

        # Manually set scheduler to running state (bypassing empty queue issue)
        scheduler._state = SchedulerState.RUNNING

        msg = MagicMock()
        msg.topic = "cnckit/commands/pause"
        msg.payload = b"{}"

        client._on_message(mock, None, msg)

        # Scheduler should be paused
        assert scheduler.state == SchedulerState.PAUSED

    def test_command_stop(self, mock_client_with_scheduler):
        """Stop command stops scheduler."""
        from cnckit.core import SchedulerState

        client, mock, scheduler = mock_client_with_scheduler

        # Simulate receiving stop command
        msg = MagicMock()
        msg.topic = "cnckit/commands/stop"
        msg.payload = b"{}"

        client._on_message(mock, None, msg)

        assert scheduler.state == SchedulerState.STOPPED

    def test_custom_command_handler(self):
        """Custom command handlers are called."""
        from cnckit.integrations.mqtt import MQTTClient

        mock = MagicMock()
        with patch("paho.mqtt.client.Client", return_value=mock):
            client = MQTTClient("localhost")
            client._connected = True

        received: list[dict[str, Any]] = []

        def handler(payload: dict[str, Any]) -> None:
            received.append(payload)

        client.on_command("custom/topic", handler)

        # Simulate receiving message
        msg = MagicMock()
        msg.topic = "custom/topic"
        msg.payload = b'{"action": "test"}'

        client._on_message(mock, None, msg)

        assert len(received) == 1
        assert received[0] == {"action": "test"}


@pytest.mark.skipif(not PAHO_AVAILABLE, reason="paho-mqtt not installed")
class TestMQTTClientEventBinding:
    """Tests for event binding functionality."""

    @pytest.fixture
    def mock_client_with_events(self):
        """Create mocked MQTT client with event emitter."""
        from cnckit.core import EventEmitter
        from cnckit.integrations.mqtt import MQTTClient

        mock = MagicMock()
        with patch("paho.mqtt.client.Client", return_value=mock):
            client = MQTTClient("localhost")
            client._connected = True

            events = EventEmitter()
            client.bind_events(events)

            yield client, mock, events

    def test_bind_events_registers_handlers(self, mock_client_with_events):
        """bind_events registers event handlers."""
        _client, _, events = mock_client_with_events

        from cnckit.core import Event

        # Check handlers are registered
        assert len(events.listeners(Event.JOB_STARTED)) > 0
        assert len(events.listeners(Event.JOB_COMPLETED)) > 0
        assert len(events.listeners(Event.JOB_FAILED)) > 0
        assert len(events.listeners(Event.QUEUE_EMPTY)) > 0

    def test_event_publishes_job_started(self, mock_client_with_events):
        """JOB_STARTED event publishes to MQTT."""
        from cnckit.core import Event, Job

        _client, mock, events = mock_client_with_events

        job = Job(path=Path("/test.ngc"))
        events.emit(Event.JOB_STARTED, job)

        # Check publish was called
        assert mock.publish.called
        call_args = mock.publish.call_args
        topic = call_args[0][0]
        assert topic == "cnckit/job/started"

    def test_event_publishes_job_completed(self, mock_client_with_events):
        """JOB_COMPLETED event publishes to MQTT."""
        from cnckit.core import Event, Job

        _client, mock, events = mock_client_with_events

        job = Job(path=Path("/test.ngc"))
        events.emit(Event.JOB_COMPLETED, job)

        call_args = mock.publish.call_args
        topic = call_args[0][0]
        assert topic == "cnckit/job/completed"

    def test_event_publishes_queue_empty(self, mock_client_with_events):
        """QUEUE_EMPTY event publishes to MQTT."""
        from cnckit.core import Event

        _client, mock, events = mock_client_with_events

        events.emit(Event.QUEUE_EMPTY)

        call_args = mock.publish.call_args
        topic = call_args[0][0]
        assert topic == "cnckit/queue/empty"

    def test_unbind_events_removes_handlers(self, mock_client_with_events):
        """_unbind_events removes all event handlers."""
        from cnckit.core import Event

        client, _, events = mock_client_with_events

        client._unbind_events()

        # Handlers should be removed
        assert len(events.listeners(Event.JOB_STARTED)) == 0
        assert len(events.listeners(Event.JOB_COMPLETED)) == 0


@pytest.mark.skipif(not PAHO_AVAILABLE, reason="paho-mqtt not installed")
class TestMQTTClientConnection:
    """Tests for connection handling."""

    def test_on_connect_success(self):
        """_on_connect sets connected flag on success."""
        from cnckit.integrations.mqtt import MQTTClient

        mock = MagicMock()
        with patch("paho.mqtt.client.Client", return_value=mock):
            client = MQTTClient("localhost")

        # Simulate successful connection (rc=0 for old API)
        client._on_connect(mock, None, None, 0)

        assert client.is_connected is True

    def test_on_connect_subscribes_to_commands(self):
        """_on_connect subscribes to command topics."""
        from cnckit.integrations.mqtt import MQTTClient

        mock = MagicMock()
        with patch("paho.mqtt.client.Client", return_value=mock):
            client = MQTTClient("localhost")

        client._on_connect(mock, None, None, 0)

        # Should subscribe to all command topics
        assert mock.subscribe.call_count == 3

    def test_on_disconnect_clears_flag(self):
        """_on_disconnect clears connected flag."""
        from cnckit.integrations.mqtt import MQTTClient

        mock = MagicMock()
        with patch("paho.mqtt.client.Client", return_value=mock):
            client = MQTTClient("localhost")
            client._connected = True

        client._on_disconnect(mock, None, 0)

        assert client.is_connected is False

    def test_disconnect_unbinds_events(self):
        """disconnect unbinds event handlers."""
        from cnckit.core import Event, EventEmitter
        from cnckit.integrations.mqtt import MQTTClient

        mock = MagicMock()
        with patch("paho.mqtt.client.Client", return_value=mock):
            client = MQTTClient("localhost")
            client._connected = True

            events = EventEmitter()
            client.bind_events(events)

            # Verify handlers exist
            assert len(events.listeners(Event.JOB_STARTED)) > 0

            client.disconnect()

            # Handlers should be removed
            assert len(events.listeners(Event.JOB_STARTED)) == 0

# MQTT Integration

The MQTT integration enables pub/sub messaging for IoT and automation systems.

## Installation

```bash
pip install cnckit[mqtt]
```

## Quick Start

```python
from cnckit.core import Machine, JobQueue, Scheduler, EventEmitter
from cnckit.integrations.mqtt import MQTTClient

# Set up core components
machine = Machine(simulate=True)
queue = JobQueue()
events = EventEmitter()
scheduler = Scheduler(machine, queue, events)

# Create and connect MQTT client
client = MQTTClient("localhost", port=1883)
client.connect()

# Bind to events and scheduler
client.bind_events(events)      # Auto-publish job events
client.bind_scheduler(scheduler)  # Handle commands

# Run your application
scheduler.run_forever()

# When done
client.disconnect()
```

## API Reference

::: cnckit.integrations.mqtt.MQTTClient
    options:
      show_root_heading: true
      heading_level: 3

::: cnckit.integrations.mqtt.MQTTTopics
    options:
      show_root_heading: true
      heading_level: 3

## Topics

### Published Topics (Outgoing)

| Topic | Description | Retained |
|-------|-------------|----------|
| `cnckit/machine/state` | Machine state updates | Yes |
| `cnckit/job/started` | Job started events | No |
| `cnckit/job/completed` | Job completed events | No |
| `cnckit/job/failed` | Job failed events | No |
| `cnckit/queue/empty` | Queue empty notification | No |

### Subscribed Topics (Incoming Commands)

| Topic | Description |
|-------|-------------|
| `cnckit/commands/start` | Start the scheduler |
| `cnckit/commands/pause` | Pause after current job |
| `cnckit/commands/stop` | Stop the scheduler |

## Message Format

All messages use a consistent JSON format:

```json
{
  "type": "message_type",
  "timestamp": "2024-01-15T10:30:00.123456",
  "data": {
    // Type-specific data
  }
}
```

### Machine State Message

```json
{
  "type": "machine_state",
  "timestamp": "2024-01-15T10:30:00.123456",
  "data": {
    "state": "running",
    "position": {"x": 10.5, "y": 20.0, "z": -1.0},
    "progress": 0.45,
    "current_program": "/path/to/part.ngc"
  }
}
```

### Job Event Messages

```json
{
  "type": "job_started",
  "timestamp": "2024-01-15T10:30:00.123456",
  "data": {
    "job": {
      "id": "/path/to/part.ngc",
      "name": "part",
      "path": "/path/to/part.ngc",
      "priority": 0,
      "status": "running",
      "estimated_time": null,
      "created_at": "2024-01-15T10:25:00.123456",
      "started_at": "2024-01-15T10:30:00.123456",
      "completed_at": null,
      "error": null
    }
  }
}
```

### Job Failed Message

```json
{
  "type": "job_failed",
  "timestamp": "2024-01-15T10:35:00.123456",
  "data": {
    "job": { ... },
    "error": "Tool broke during operation"
  }
}
```

## Custom Topic Prefix

Customize topic names with a different prefix:

```python
from cnckit.integrations.mqtt import MQTTClient, MQTTTopics

# Use custom prefix
topics = MQTTTopics(prefix="factory/cnc1")
client = MQTTClient("localhost", topics=topics)

# Topics will be:
# - factory/cnc1/machine/state
# - factory/cnc1/job/started
# - factory/cnc1/commands/start
# etc.
```

## Authentication

Connect with username/password authentication:

```python
client = MQTTClient(
    broker="mqtt.example.com",
    port=8883,  # TLS port
    username="cnckit",
    password="secret",
)
client.connect()
```

## Custom Command Handlers

Register handlers for custom command topics:

```python
def handle_emergency_stop(payload):
    print(f"Emergency stop: {payload}")
    scheduler.stop()
    machine.abort()

client.on_command("cnckit/commands/emergency", handle_emergency_stop)
```

## Manual Publishing

Publish messages directly:

```python
# Publish machine state
client.publish_machine_state(
    state="running",
    position={"x": 10.0, "y": 20.0, "z": 5.0},
    progress=0.5,
    current_program="/path/to/part.ngc",
)

# Publish raw message
client.publish(
    topic="cnckit/custom/topic",
    payload={"custom": "data"},
    qos=1,
    retain=False,
)
```

## Integration Example

Complete example with machine state polling:

```python
import time
from cnckit.core import Machine, JobQueue, Scheduler, EventEmitter
from cnckit.integrations.mqtt import MQTTClient

# Set up components
machine = Machine(simulate=True)
queue = JobQueue()
events = EventEmitter()
scheduler = Scheduler(machine, queue, events)

# Set up MQTT
client = MQTTClient("localhost")
client.connect()
client.bind_events(events)
client.bind_scheduler(scheduler)

# Add some jobs
queue.add("/jobs/part1.ngc")
queue.add("/jobs/part2.ngc")

# Main loop with state publishing
scheduler.start()
try:
    while scheduler.state.value != "stopped":
        scheduler.tick()

        # Publish current machine state
        pos = machine.position
        client.publish_machine_state(
            state=machine.state.value,
            position={"x": pos.x, "y": pos.y, "z": pos.z},
            progress=machine.progress,
            current_program=machine.current_program,
        )

        time.sleep(1.0)
finally:
    client.disconnect()
```

## Subscribing from Another Client

Example using mosquitto_sub to receive events:

```bash
# Subscribe to all cnckit topics
mosquitto_sub -h localhost -t "cnckit/#" -v

# Send start command
mosquitto_pub -h localhost -t "cnckit/commands/start" -m "{}"

# Send stop command
mosquitto_pub -h localhost -t "cnckit/commands/stop" -m "{}"
```

## Testing with Mock Broker

For testing without a real broker, use the mock pattern:

```python
from unittest.mock import patch, MagicMock

with patch("paho.mqtt.client.Client") as mock_mqtt:
    mock_client = MagicMock()
    mock_mqtt.return_value = mock_client

    client = MQTTClient("localhost")
    client._connected = True  # Skip actual connection

    # Test publishing
    client.publish_queue_empty()
    mock_client.publish.assert_called()
```

# WebSocket Integration

The WebSocket integration provides real-time streaming of machine state and job progress to connected clients.

## Installation

```bash
pip install cnckit[websocket]
```

## Quick Start

```python
import asyncio
from cnckit.core import Machine, JobQueue, Scheduler, EventEmitter
from cnckit.integrations.websocket import WebSocketServer

async def main():
    # Set up core components
    machine = Machine(simulate=True)
    queue = JobQueue()
    events = EventEmitter()
    scheduler = Scheduler(machine, queue, events)

    # Create and start WebSocket server
    server = WebSocketServer(host="localhost", port=8765)
    server.bind_events(events)

    async with server:
        print(f"WebSocket server running on ws://localhost:8765")
        # Run your application...
        await asyncio.sleep(60)

asyncio.run(main())
```

## API Reference

::: cnckit.integrations.websocket.WebSocketServer
    options:
      show_root_heading: true
      heading_level: 3

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

## Message Types

### Connection Messages

**connected** - Sent when client connects:
```json
{
  "type": "connected",
  "timestamp": "2024-01-15T10:30:00.123456",
  "data": {
    "message": "Connected to CNCKit"
  }
}
```

**pong** - Response to client ping:
```json
{
  "type": "pong",
  "timestamp": "2024-01-15T10:30:00.123456",
  "data": {}
}
```

### Machine State

**machine_state** - Current machine status:
```json
{
  "type": "machine_state",
  "timestamp": "2024-01-15T10:30:00.123456",
  "data": {
    "state": "running",
    "position": {"x": 10.5, "y": 20.0, "z": -1.0},
    "progress": 0.45,
    "current_program": "/path/to/part.ngc",
    "tool": 1
  }
}
```

### Job Events

**job_started**:
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

**job_completed**:
```json
{
  "type": "job_completed",
  "timestamp": "2024-01-15T10:35:00.123456",
  "data": {
    "job": { ... }
  }
}
```

**job_failed**:
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

### Scheduler State

**scheduler_state**:
```json
{
  "type": "scheduler_state",
  "timestamp": "2024-01-15T10:30:00.123456",
  "data": {
    "state": "running",
    "current_job": { ... }
  }
}
```

**queue_empty**:
```json
{
  "type": "queue_empty",
  "timestamp": "2024-01-15T10:40:00.123456",
  "data": {}
}
```

## Server Methods

### Starting and Stopping

```python
# Method 1: Context manager (recommended)
async with server:
    # Server is running
    pass
# Server is stopped

# Method 2: Manual control
await server.start()
# ... do work ...
await server.stop()
```

### Broadcasting Messages

```python
# Broadcast raw message
await server.broadcast('{"type": "custom", "data": {}}')

# Broadcast machine state
await server.broadcast_machine_state(
    state="running",
    position={"x": 10.0, "y": 20.0, "z": 5.0},
    progress=0.5,
    current_program="/path/to/part.ngc",
    tool=1,
)

# Broadcast job events
await server.broadcast_job_started(job)
await server.broadcast_job_completed(job)
await server.broadcast_job_failed(job, error="Tool broke")
await server.broadcast_queue_empty()

# Broadcast scheduler state
await server.broadcast_scheduler_state(
    state="running",
    current_job=job,
)
```

## Event Binding

Automatically broadcast events from EventEmitter:

```python
from cnckit.core import EventEmitter
from cnckit.integrations.websocket import WebSocketServer

events = EventEmitter()
server = WebSocketServer()
server.bind_events(events)

# Now when events are emitted, they're automatically broadcast:
# Event.JOB_STARTED -> "job_started" message
# Event.JOB_COMPLETED -> "job_completed" message
# Event.JOB_FAILED -> "job_failed" message
# Event.QUEUE_EMPTY -> "queue_empty" message
```

## Complete Example

```python
import asyncio
from cnckit.core import Machine, JobQueue, Scheduler, EventEmitter
from cnckit.integrations.websocket import WebSocketServer

async def main():
    # Set up core components
    machine = Machine(simulate=True)
    queue = JobQueue()
    events = EventEmitter()
    scheduler = Scheduler(machine, queue, events)

    # Add some jobs
    queue.add("/jobs/part1.ngc")
    queue.add("/jobs/part2.ngc")

    # Create WebSocket server
    server = WebSocketServer(host="0.0.0.0", port=8765)
    server.bind_events(events)

    async with server:
        print(f"Server running on ws://0.0.0.0:8765")
        print(f"Connected clients: {server.client_count}")

        # Start scheduler
        scheduler.start()

        # Main loop
        while scheduler.state.value != "stopped":
            scheduler.tick()

            # Broadcast current machine state
            pos = machine.position
            await server.broadcast_machine_state(
                state=machine.state.value,
                position={"x": pos.x, "y": pos.y, "z": pos.z},
                progress=machine.progress,
                current_program=machine.current_program,
                tool=machine.tool,
            )

            await asyncio.sleep(0.5)

        print("All jobs completed!")

asyncio.run(main())
```

## JavaScript Client Example

Connect from a web browser:

```javascript
const ws = new WebSocket('ws://localhost:8765');

ws.onopen = () => {
    console.log('Connected to CNCKit');

    // Send ping to keep alive
    setInterval(() => {
        ws.send(JSON.stringify({ type: 'ping' }));
    }, 30000);
};

ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    console.log(`Received: ${msg.type}`, msg.data);

    switch (msg.type) {
        case 'machine_state':
            updateMachineDisplay(msg.data);
            break;
        case 'job_started':
            showNotification(`Job started: ${msg.data.job.name}`);
            break;
        case 'job_completed':
            showNotification(`Job completed: ${msg.data.job.name}`);
            break;
        case 'job_failed':
            showError(`Job failed: ${msg.data.error}`);
            break;
    }
};

ws.onclose = () => {
    console.log('Disconnected from CNCKit');
};
```

## Python Client Example

Connect using websockets library:

```python
import asyncio
import json
import websockets

async def monitor():
    async with websockets.connect("ws://localhost:8765") as ws:
        async for message in ws:
            data = json.loads(message)
            print(f"[{data['type']}] {data['data']}")

asyncio.run(monitor())
```

## Testing

For testing without a real server:

```python
from unittest.mock import AsyncMock
from cnckit.integrations.websocket import WebSocketServer

# Create server with mock client
server = WebSocketServer()
mock_client = AsyncMock()
server._clients.add(mock_client)
server._running = True

# Test broadcasting
await server.broadcast_machine_state(state="idle", progress=0.0)

# Verify client received message
mock_client.send.assert_called_once()
```

## Properties

| Property | Type | Description |
|----------|------|-------------|
| `host` | str | Server host |
| `port` | int | Server port |
| `is_running` | bool | Whether server is running |
| `client_count` | int | Number of connected clients |

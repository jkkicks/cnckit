# WebSocket Integration

The WebSocket integration provides real-time streaming of machine state and job progress.

## Installation

```bash
pip install cnckit[websocket]
```

## Quick Start

```python
from cnckit.integrations.websocket import WebSocketServer

server = WebSocketServer(host="localhost", port=8765)
await server.start()
```

## API Reference

::: cnckit.integrations.websocket.WebSocketServer
    options:
      show_root_heading: true
      heading_level: 3

## Message Format

!!! note "Coming in Phase 2"
    The WebSocket integration will be implemented in Phase 2.

Messages will be JSON-formatted:

```json
{
  "type": "machine_state",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "state": "running",
    "position": {"x": 10.5, "y": 20.0, "z": -1.0},
    "current_job": "part1.ngc"
  }
}
```

# REST API Integration

The REST API integration provides HTTP endpoints for remote monitoring and control of your CNC machine.

## Installation

```bash
pip install cnckit[api]
```

## Quick Start

```python
from cnckit.integrations.api import create_app
import uvicorn

# Create app with simulated machine (safe default)
app = create_app(simulate=True)

# Run the server
uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Using with Existing Components

```python
from cnckit.core import Machine, JobQueue, Scheduler, EventEmitter
from cnckit.integrations.api import create_app
import uvicorn

# Set up your components
machine = Machine(simulate=True)
queue = JobQueue()
events = EventEmitter()
scheduler = Scheduler(machine, queue, events)

# Create API with your components
app = create_app(
    machine=machine,
    queue=queue,
    scheduler=scheduler,
    events=events,
)

uvicorn.run(app, host="0.0.0.0", port=8000)
```

## API Reference

::: cnckit.integrations.api.create_app
    options:
      show_root_heading: true
      heading_level: 3

## Endpoints

### Dashboard

| Method | Path | Description |
|--------|------|-------------|
| GET | `/dashboard` | Web dashboard for monitoring and control |

The dashboard provides a real-time view of:

- **Machine Status**: Position (X, Y, Z), state, current tool, progress
- **Scheduler Controls**: Start, pause, stop buttons
- **Job Queue**: List of pending jobs with status
- **Event Log**: Real-time events from WebSocket (if running)

Access the dashboard at `http://localhost:8000/dashboard` when the server is running.

### Health

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check - returns service status and timestamp |

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.123456"
}
```

### Machine

| Method | Path | Description |
|--------|------|-------------|
| GET | `/machine/status` | Get current machine state, position, and program info |

**Response:**
```json
{
  "state": "idle",
  "position": {
    "x": 0.0,
    "y": 0.0,
    "z": 0.0,
    "a": null,
    "b": null,
    "c": null
  },
  "tool": 0,
  "current_program": null,
  "progress": 0.0,
  "simulate": true
}
```

**Machine States:**

- `disconnected` - Not connected to controller
- `idle` - Ready to run
- `running` - Program executing
- `paused` - Program paused mid-execution
- `error` - Error state, needs intervention
- `estop` - Emergency stop activated

### Queue

| Method | Path | Description |
|--------|------|-------------|
| GET | `/queue` | List all queued jobs |
| POST | `/queue` | Add a job to the queue |
| DELETE | `/queue/{job_id}` | Remove a job from the queue |

**GET /queue Response:**
```json
{
  "mode": "fifo",
  "count": 2,
  "jobs": [
    {
      "id": "/path/to/part1.ngc",
      "name": "part1",
      "path": "/path/to/part1.ngc",
      "priority": 0,
      "status": "pending",
      "estimated_time": null,
      "created_at": "2024-01-15T10:30:00.123456",
      "started_at": null,
      "completed_at": null,
      "error": null
    }
  ]
}
```

**POST /queue Request:**
```json
{
  "path": "/path/to/part.ngc",
  "priority": 5,
  "name": "My Custom Job Name"
}
```

**POST /queue Response (201 Created):**
```json
{
  "message": "Job added to queue",
  "job": {
    "id": "/path/to/part.ngc",
    "name": "My Custom Job Name",
    "path": "/path/to/part.ngc",
    "priority": 5,
    "status": "pending",
    "estimated_time": null,
    "created_at": "2024-01-15T10:30:00.123456",
    "started_at": null,
    "completed_at": null,
    "error": null
  }
}
```

**Job Statuses:**

- `pending` - Waiting in queue
- `running` - Currently executing
- `completed` - Finished successfully
- `failed` - Finished with error

### Scheduler

| Method | Path | Description |
|--------|------|-------------|
| GET | `/scheduler/status` | Get scheduler state and current job |
| POST | `/scheduler/start` | Start processing jobs |
| POST | `/scheduler/pause` | Pause after current job |
| POST | `/scheduler/stop` | Stop immediately |
| POST | `/scheduler/tick` | Manually trigger a scheduler tick |

**GET /scheduler/status Response:**
```json
{
  "state": "running",
  "current_job": {
    "id": "/path/to/part.ngc",
    "name": "part",
    "path": "/path/to/part.ngc",
    "priority": 0,
    "status": "running",
    "estimated_time": null,
    "created_at": "2024-01-15T10:30:00.123456",
    "started_at": "2024-01-15T10:31:00.123456",
    "completed_at": null,
    "error": null
  }
}
```

**Scheduler States:**

- `stopped` - Not processing jobs
- `running` - Actively processing queue
- `paused` - Paused, will not start next job

## Error Responses

All errors return a JSON response with a `detail` field:

```json
{
  "detail": "G-code file not found: /path/to/missing.ngc"
}
```

**HTTP Status Codes:**

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created (new resource) |
| 400 | Bad request |
| 404 | Resource not found |
| 500 | Internal server error |
| 503 | Service unavailable |

## Interactive Documentation

When the server is running, visit:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`

## Example: Complete Workflow

```python
import requests

BASE_URL = "http://localhost:8000"

# Check health
response = requests.get(f"{BASE_URL}/health")
print(response.json())

# Add jobs to queue
for gcode_file in ["part1.ngc", "part2.ngc", "part3.ngc"]:
    response = requests.post(
        f"{BASE_URL}/queue",
        json={"path": f"/jobs/{gcode_file}", "priority": 0}
    )
    print(f"Added: {response.json()['job']['name']}")

# Check queue
response = requests.get(f"{BASE_URL}/queue")
print(f"Queue has {response.json()['count']} jobs")

# Start scheduler
requests.post(f"{BASE_URL}/scheduler/start")

# Monitor progress
while True:
    status = requests.get(f"{BASE_URL}/scheduler/status").json()
    if status["state"] == "stopped":
        print("All jobs completed!")
        break

    if status["current_job"]:
        machine = requests.get(f"{BASE_URL}/machine/status").json()
        print(f"Running: {status['current_job']['name']} - {machine['progress']*100:.1f}%")

    time.sleep(1)
```

## Pydantic Models

The API uses Pydantic models for request/response validation. These are exported for use in type hints:

```python
from cnckit.integrations.api import (
    HealthResponse,
    MachineStatusResponse,
    PositionResponse,
    JobResponse,
    QueueResponse,
    AddJobRequest,
    AddJobResponse,
    SchedulerStatusResponse,
    MessageResponse,
    ErrorResponse,
)
```

## Using Dashboard with WebSocket

For the best experience, run both the REST API and WebSocket server together:

```python
import asyncio
from cnckit.core import Machine, JobQueue, Scheduler, EventEmitter
from cnckit.integrations.api import create_app
from cnckit.integrations.websocket import WebSocketServer
import uvicorn

async def main():
    # Set up components
    machine = Machine(simulate=True)
    queue = JobQueue()
    events = EventEmitter()
    scheduler = Scheduler(machine, queue, events)

    # Start WebSocket server for real-time updates
    ws_server = WebSocketServer(port=8765)
    ws_server.bind_events(events)

    # Create REST API
    app = create_app(
        machine=machine,
        queue=queue,
        scheduler=scheduler,
        events=events,
    )

    async with ws_server:
        # Run REST API (blocks)
        config = uvicorn.Config(app, host="0.0.0.0", port=8000)
        server = uvicorn.Server(config)
        await server.serve()

asyncio.run(main())
```

Then open `http://localhost:8000/dashboard` for real-time monitoring with both REST API controls and WebSocket event updates.

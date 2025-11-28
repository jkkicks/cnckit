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

app = create_app()
uvicorn.run(app, host="0.0.0.0", port=8000)
```

## API Reference

::: cnckit.integrations.api.create_app
    options:
      show_root_heading: true
      heading_level: 3

## Endpoints

!!! note "Coming in Phase 2"
    The REST API will be implemented in Phase 2.

Planned endpoints:

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/machine/status` | Machine state |
| GET | `/queue` | List queued jobs |
| POST | `/queue` | Add a job |
| DELETE | `/queue/{job_id}` | Remove a job |
| POST | `/scheduler/start` | Start scheduler |
| POST | `/scheduler/pause` | Pause scheduler |
| POST | `/scheduler/stop` | Stop scheduler |

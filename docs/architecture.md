# Architecture

This document describes the architectural vision and design philosophy of the project.

## Project Structure

```
cnckit/
├── src/cnckit/
│   ├── __init__.py          # Package root with quickstart()
│   ├── cli.py               # CLI entry point
│   ├── py.typed             # PEP 561 type marker
│   ├── core/                # Layer 1 - dependency-free
│   │   ├── machine.py       # LinuxCNC abstraction
│   │   ├── job.py           # Job metadata dataclass
│   │   ├── queue.py         # FIFO/LIFO/priority queue
│   │   ├── scheduler.py     # Job execution coordinator
│   │   ├── events.py        # Pub/sub event system
│   │   └── config.py        # YAML/TOML config loader
│   └── integrations/        # Layer 2 - optional modules
│       ├── api/             # FastAPI REST endpoints
│       ├── mqtt/            # MQTT client
│       ├── websocket/       # WebSocket server
│       └── robot/           # ROS2/TCP interfaces
├── tests/                   # Test suite (mirrors src structure)
├── docs/                    # MkDocs documentation
└── .github/workflows/       # CI/CD pipelines
```

## Design Philosophy

The package is built around a "building-block architecture":

- The **core** stays extremely small, stable, and dependency-free
- Optional **integrations** are available but never forced
- Users adopt only what they need
- The project remains accessible to non-technical LinuxCNC users
- Advanced users can layer on automation, APIs, and robotics

## Layer 1 — Core (no external dependencies)

Minimal, stable, and extremely lightweight.

**Core modules:**

- `machine.py` — abstraction over LinuxCNC's Python API
- `job.py` — metadata wrapper for gcode jobs
- `queue.py` — enqueue, dequeue, prioritization
- `scheduler.py` — job execution rules
- `config.py` — optional YAML/TOML loader (lazy import)
- `events.py` — simple callback/hook system

This layer is meant to remain extremely small and dependable. It provides all the base building blocks with "plain Python only."

## Layer 2 — Integrations (optional, modular)

Separate subpackages loaded **only on demand**, keeping the base install tiny.

**Modules under `integrations/`:**

- `api/fastapi_app.py`
- `mqtt/mqtt_client.py`
- `websocket/ws_server.py`
- `robot/ros2_interface.py`

**All optional integrations use lazy imports:**

```python
try:
    import fastapi
except ImportError:
    raise ImportError("Install with: pip install package[api]")
```

This avoids unnecessary dependencies and security concerns.

## Layer 3 — Experience Layer (Quality-of-Life)

High-level helpers and shortcuts intended for ease of use.

- `quickstart()` — 1-call setup that:
  - loads config
  - initializes Machine, Queue, Scheduler
  - optionally starts integrations

- Small CLI tools (e.g., `cnc-queue add file.ngc`)
- (Later) a simple local web dashboard

These tools never contain business logic themselves—they orchestrate the core.

## Why This Architecture Works

### Beginner-friendly

Someone with almost no Python experience can do:

```python
from package import quickstart
quickstart("/home/cnc/jobs/")
```

### Integration-friendly

Advanced users can build:

- API servers
- robot interfaces
- home automation
- dashboards
- industrial controllers

Without battling a monolithic architecture.

### Zero bloat by design

Nothing heavy is imported unless explicitly requested.

### AI/LLM-friendly

Modules are small, pure-purpose, and cleanly separated, making the package easy to extend automatically or programmatically.

## Development Goals

- Keep the core <2K LOC
- Make the default experience "just works"
- Provide rich extension points
- Support both small hobby CNC shops and larger automation environments

## Testing & Documentation Philosophy

Testing and documentation are not afterthoughts—they are cornerstones of every module.

### Testing Requirements

- **No code without tests.** Every module must have corresponding tests before it's considered complete.
- **Test-first mindset.** Write tests alongside (or before) implementation.
- **Coverage matters.** Aim for meaningful coverage of core logic, edge cases, and integration points.
- **Tests as documentation.** Tests should demonstrate how modules are intended to be used.

### Documentation Requirements

- **Document as you build.** Every public function, class, and module needs clear docstrings.
- **Examples are essential.** Show real usage, not just API signatures.
- **Keep docs in sync.** Documentation that drifts from code is worse than no documentation.
- **Explain the "why."** Don't just describe what code does—explain design decisions.

# cnckit

A lightweight, modular Python framework for job queuing, scheduling, and automation around LinuxCNC.

## Overview

cnckit provides a minimal core with optional integration modules, allowing you to adopt only the functionality you need. From simple local job queues to remote monitoring, API-based control, and more.

## Features

**Core (dependency-free):**

- Job queue with FIFO/LIFO/priority ordering
- Scheduler with start/stop/pause controls
- Machine state abstraction over LinuxCNC
- Event callbacks for job lifecycle
- Simulation mode for development

**Optional Integrations:**

- REST API for remote monitoring
- MQTT for messaging and automation
- WebSocket real-time streaming
- Robot interfaces (ROS2, TCP)

## Quick Start

```python
from cnckit.core import Machine, JobQueue, Scheduler

machine = Machine(simulate=True)  # or Machine() for real LinuxCNC
queue = JobQueue()
scheduler = Scheduler(machine, queue)

queue.add("part1.ngc")
queue.add("part2.ngc", priority=10)

scheduler.run_forever()
```

## Installation

```bash
pip install cnckit
```

With optional integrations:

```bash
pip install cnckit[api]      # REST API
pip install cnckit[mqtt]     # MQTT
pip install cnckit[all]      # Everything
```

## Documentation

- **[Quick Start](docs/getting-started/quickstart.md)** — Get up and running
- **[Architecture](docs/architecture.md)** — Design philosophy
- **[API Reference](docs/api/core/machine.md)** — Full API docs
- **[Roadmap](docs/roadmap.md)** — Planned features

## Development

```bash
git clone https://github.com/jacobm/cnckit.git
cd cnckit
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

See [Contributing](docs/contributing.md) for guidelines.

## License

MIT

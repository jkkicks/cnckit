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

## Design Philosophy

cnckit is built around a "building-block architecture":

- The **core** stays extremely small, stable, and dependency-free
- Optional **integrations** are available but never forced
- Users adopt only what they need
- The project remains accessible to non-technical LinuxCNC users
- Advanced users can layer on automation, APIs, and robotics

## Next Steps

- [Quick Start Guide](getting-started/quickstart.md) — Detailed setup instructions
- [Architecture](architecture.md) — Design philosophy and module structure
- [API Reference](api/core/machine.md) — Full API documentation
- [Roadmap](roadmap.md) — Planned features and phases

## License

MIT

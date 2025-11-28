# cnckit

A lightweight, modular Python framework for job queuing, scheduling, and automation around LinuxCNC.

## Overview

cnckit provides a minimal core with optional integration modules, allowing you to adopt only the functionality you need. From simple local job queues to remote monitoring, API-based control, and more.

## Features

**Core (dependency-free):**

- Job queue with FIFO/LIFO support and prioritization
- Scheduler with start/stop/pause controls
- Machine state abstraction over LinuxCNC's Python API
- Event callbacks for job completion, errors, and idle state

**Optional Integrations:**

- REST API for remote monitoring
- MQTT client for messaging and automation
- Websocket real-time streaming
- Robot interfaces (ROS2, TCP)

## Quick Start

```python
from cnckit import Machine, JobQueue, Scheduler

machine = Machine()
queue = JobQueue()
scheduler = Scheduler(machine, queue)

queue.add("part1.ngc")
scheduler.start()
```

Or use the one-liner:

```python
from cnckit import quickstart
quickstart("/home/cnc/jobs/")
```

## Installation

```bash
pip install cnckit
```

With optional integrations:

```bash
pip install cnckit[api]      # REST API support
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

## License

MIT

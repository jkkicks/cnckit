# Installation

## Requirements

- Python 3.10 or higher
- LinuxCNC (optional — simulation mode available for development)

## Basic Installation

Install cnckit with pip:

```bash
pip install cnckit
```

This installs the core package with no external dependencies.

## Optional Integrations

cnckit provides optional integrations that can be installed as extras:

### REST API

For remote monitoring via HTTP:

```bash
pip install cnckit[api]
```

Installs: FastAPI, Uvicorn

### MQTT

For IoT and automation messaging:

```bash
pip install cnckit[mqtt]
```

Installs: paho-mqtt

### WebSocket

For real-time streaming:

```bash
pip install cnckit[websocket]
```

Installs: websockets

### Everything

Install all optional integrations:

```bash
pip install cnckit[all]
```

## Development Installation

For contributing to cnckit:

```bash
git clone https://github.com/jkkicks/cnckit.git
cd cnckit
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

This installs all development dependencies including:

- pytest for testing
- ruff for linting
- mypy for type checking
- mkdocs for documentation
- pre-commit for git hooks

## Verifying Installation

```python
from cnckit.core import Machine, JobQueue, Scheduler

# Simulation mode - no LinuxCNC required
machine = Machine(simulate=True)
print(f"Machine state: {machine.state}")
```

## LinuxCNC Setup

For production use with real CNC hardware, LinuxCNC must be installed and running:

```python
from cnckit.core import Machine

# Connects to running LinuxCNC instance
machine = Machine()  # Raises error if LinuxCNC unavailable
```

For LinuxCNC installation, see the [official documentation](https://linuxcnc.org/docs/).

**Tip:** Use `Machine(simulate=True)` during development to test your automation logic without hardware.

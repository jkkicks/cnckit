# Installation

## Requirements

- Python 3.10 or higher
- LinuxCNC (for actual machine control)

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

For contributing to cnckit (using [uv](https://docs.astral.sh/uv/)):

```bash
git clone https://github.com/jacobm/cnckit.git
cd cnckit
uv sync --extra dev
source .venv/bin/activate
```

This installs all development dependencies including:

- pytest for testing
- ruff for linting
- mypy for type checking
- mkdocs for documentation
- pre-commit for git hooks

## Verifying Installation

```python
import cnckit
print(cnckit.__version__)
```

## LinuxCNC Setup

cnckit requires LinuxCNC to be installed and running for actual machine control. On systems without LinuxCNC, cnckit can be used in simulation mode (coming in Phase 3).

For LinuxCNC installation, see the [official documentation](https://linuxcnc.org/docs/).

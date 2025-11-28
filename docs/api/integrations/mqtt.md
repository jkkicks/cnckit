# MQTT Integration

The MQTT integration enables pub/sub messaging for IoT and automation systems.

## Installation

```bash
pip install cnckit[mqtt]
```

## Quick Start

```python
from cnckit.integrations.mqtt import MQTTClient

client = MQTTClient(broker="localhost", port=1883)
client.connect()
```

## API Reference

::: cnckit.integrations.mqtt.MQTTClient
    options:
      show_root_heading: true
      heading_level: 3

## Topics

!!! note "Coming in Phase 2"
    The MQTT integration will be implemented in Phase 2.

Planned topics:

| Topic | Direction | Description |
|-------|-----------|-------------|
| `cnckit/machine/state` | Publish | Machine state updates |
| `cnckit/job/started` | Publish | Job started events |
| `cnckit/job/completed` | Publish | Job completed events |
| `cnckit/job/failed` | Publish | Job failed events |
| `cnckit/commands/start` | Subscribe | Start command |
| `cnckit/commands/pause` | Subscribe | Pause command |
| `cnckit/commands/stop` | Subscribe | Stop command |

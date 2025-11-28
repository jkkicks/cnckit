# Robot Integration

The robot integration provides coordination between CNC machines and robotic systems.

## ROS2 Interface

### Installation

ROS2 must be installed separately. See [ROS2 documentation](https://docs.ros.org/).

### Quick Start

```python
from cnckit.integrations.robot import ROS2Interface

interface = ROS2Interface(node_name="cnckit")
interface.spin()
```

### API Reference

::: cnckit.integrations.robot.ROS2Interface
    options:
      show_root_heading: true
      heading_level: 4

## TCP Robot Client

For robots with simple TCP command interfaces.

### Quick Start

```python
from cnckit.integrations.robot import TCPRobotClient

robot = TCPRobotClient(host="192.168.1.100", port=10000)
robot.connect()
robot.send_command("MOVE X100 Y200")
```

### API Reference

::: cnckit.integrations.robot.TCPRobotClient
    options:
      show_root_heading: true
      heading_level: 4

## Use Cases

!!! note "Coming in Phase 2"
    Robot integration will be implemented in Phase 2.

Planned features:

- **Part Loading**: Signal robot to load/unload parts
- **Tool Changes**: Coordinate tool changes with robot arm
- **Quality Inspection**: Trigger robot-mounted inspection
- **Multi-Machine Coordination**: Orchestrate multiple CNC machines with robots

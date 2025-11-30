# Robot Integration

The Robot integration provides interfaces for coordinating CNC operations with robotic systems. Two interfaces are available:

- **TCPRobotClient**: Simple TCP socket client for robots with text-based protocols
- **ROS2Interface**: Full ROS2 node integration for ROS-based robots

## TCPRobotClient

### Quick Start

```python
from cnckit.integrations.robot import TCPRobotClient

# Connect to robot
robot = TCPRobotClient("192.168.1.100", port=10000)
robot.connect()

# Send commands
robot.home()
robot.load_part("part_001")
status = robot.get_status()
print(f"Robot ready: {status.ready}")

robot.disconnect()
```

### API Reference

::: cnckit.integrations.robot.TCPRobotClient
    options:
      show_root_heading: true
      heading_level: 3

### Connection Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `host` | str | required | Robot hostname or IP address |
| `port` | int | required | Robot TCP port |
| `timeout` | float | 10.0 | Socket timeout in seconds |
| `terminator` | str | "\n" | Message terminator string |
| `encoding` | str | "utf-8" | Character encoding |

### Standard Commands

```python
# Motion commands
robot.home()                      # Return to home position
robot.move_to(x=10.0, y=20.0, z=5.0)  # Move to position
robot.stop()                      # Emergency stop
robot.pause()                     # Pause motion
robot.resume()                    # Resume motion

# Part handling
robot.load_part()                 # Load part into CNC
robot.load_part("part_001")       # Load specific part
robot.unload_part()               # Unload part from CNC

# Tool operations
robot.tool_change(5)              # Change to tool 5
robot.inspect("visual")           # Trigger inspection
```

### Custom Commands

```python
# Send raw command
response = robot.send_command("CUSTOM_CMD arg1 arg2")

# Send JSON command
response = robot.send_json({
    "command": "move",
    "position": {"x": 10, "y": 20, "z": 5}
})
```

### Robot Status

```python
status = robot.get_status()

print(f"Connected: {status.connected}")
print(f"Ready: {status.ready}")
print(f"Busy: {status.busy}")
print(f"Error: {status.error}")
print(f"Position: {status.position}")
```

### Event Binding for CNC Coordination

Automatically coordinate robot actions with CNC events:

```python
from cnckit.core import EventEmitter
from cnckit.integrations.robot import TCPRobotClient

events = EventEmitter()
robot = TCPRobotClient("192.168.1.100", 10000)
robot.connect()

# Auto-load part when job starts, auto-unload when complete
robot.bind_events(events, auto_load=True, auto_unload=True)

# Now when scheduler emits JOB_STARTED, robot.load_part() is called
# When JOB_COMPLETED is emitted, robot.unload_part() is called
```

## ROS2Interface

The ROS2 interface requires ROS2 to be installed and sourced. It provides full pub/sub integration with ROS2 topics.

### Installation

1. Install ROS2 (see [ROS2 documentation](https://docs.ros.org/))
2. Source the ROS2 setup: `source /opt/ros/<distro>/setup.bash`

### Quick Start

```python
import rclpy
from cnckit.core import EventEmitter
from cnckit.integrations.robot import ROS2Interface

rclpy.init()

events = EventEmitter()
interface = ROS2Interface(node_name="cnckit_node")
interface.bind_events(events)

# Publish machine state
interface.publish_machine_state(
    state="running",
    position={"x": 10.0, "y": 20.0, "z": 5.0},
    progress=0.5,
)

# Run ROS2 event loop
rclpy.spin(interface.node)

rclpy.shutdown()
```

### API Reference

::: cnckit.integrations.robot.ROS2Interface
    options:
      show_root_heading: true
      heading_level: 3

### Published Topics

| Topic | Type | Description |
|-------|------|-------------|
| `/cnckit/machine_state` | std_msgs/String | Machine state updates (JSON) |
| `/cnckit/job_started` | std_msgs/String | Job started events (JSON) |
| `/cnckit/job_completed` | std_msgs/String | Job completed events (JSON) |
| `/cnckit/job_failed` | std_msgs/String | Job failed events (JSON) |
| `/cnckit/queue_empty` | std_msgs/String | Queue empty events (JSON) |

### Subscribed Topics

| Topic | Type | Description |
|-------|------|-------------|
| `/cnckit/commands` | std_msgs/String | Incoming commands |

### Message Format

All messages use JSON format:

```json
{
  "type": "machine_state",
  "timestamp": "2024-01-15T10:30:00.123456",
  "data": {
    "state": "running",
    "position": {"x": 10.0, "y": 20.0, "z": 5.0},
    "progress": 0.5
  }
}
```

### Command Handling

Register a callback for incoming commands:

```python
def handle_command(command: str):
    print(f"Received command: {command}")
    if command == "PAUSE":
        scheduler.pause()
    elif command == "RESUME":
        scheduler.start()

interface.on_command(handle_command)
```

### Event Binding

Automatically publish CNC events to ROS2 topics:

```python
events = EventEmitter()
interface = ROS2Interface()
interface.bind_events(events)

# Now when events are emitted, they're published to ROS2:
# Event.JOB_STARTED -> /cnckit/job_started
# Event.JOB_COMPLETED -> /cnckit/job_completed
# Event.JOB_FAILED -> /cnckit/job_failed
# Event.QUEUE_EMPTY -> /cnckit/queue_empty
```

## Complete Example: CNC-Robot Cell

```python
import asyncio
from cnckit.core import Machine, JobQueue, Scheduler, EventEmitter
from cnckit.integrations.robot import TCPRobotClient

async def main():
    # Set up CNC components
    machine = Machine(simulate=True)
    queue = JobQueue()
    events = EventEmitter()
    scheduler = Scheduler(machine, queue, events)

    # Connect to robot
    robot = TCPRobotClient("192.168.1.100", 10000)
    robot.connect()
    robot.bind_events(events, auto_load=True, auto_unload=True)

    # Add jobs
    queue.add("/jobs/part1.ngc")
    queue.add("/jobs/part2.ngc")

    # Run scheduler
    scheduler.start()
    while scheduler.state.value != "stopped":
        scheduler.tick()
        await asyncio.sleep(0.1)

    # Clean up
    robot.disconnect()
    print("All parts completed!")

asyncio.run(main())
```

## Helper Types

### RobotCommand

Enum of standard robot commands:

```python
from cnckit.integrations.robot import RobotCommand

RobotCommand.LOAD_PART    # "load_part"
RobotCommand.UNLOAD_PART  # "unload_part"
RobotCommand.TOOL_CHANGE  # "tool_change"
RobotCommand.INSPECT      # "inspect"
RobotCommand.HOME         # "home"
RobotCommand.PAUSE        # "pause"
RobotCommand.RESUME       # "resume"
RobotCommand.STOP         # "stop"
```

### RobotStatus

Dataclass for robot status:

```python
from cnckit.integrations.robot import RobotStatus

status = RobotStatus(
    connected=True,
    ready=True,
    busy=False,
    error=None,
    position={"x": 0.0, "y": 0.0, "z": 100.0}
)
```

## Properties

### TCPRobotClient

| Property | Type | Description |
|----------|------|-------------|
| `host` | str | Robot hostname |
| `port` | int | Robot port |
| `is_connected` | bool | Connection status |

### ROS2Interface

| Property | Type | Description |
|----------|------|-------------|
| `node` | Node | ROS2 node for spinning |
| `node_name` | str | Node name |

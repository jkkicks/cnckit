# Quick Start

Get started with cnckit in minutes.

## Basic Usage

### With LinuxCNC (Production)

```python
from cnckit.core import Machine, JobQueue, Scheduler

# Connect to LinuxCNC (requires LinuxCNC to be running)
machine = Machine()

# Create a job queue
queue = JobQueue()
queue.add("part1.ngc")
queue.add("part2.ngc")

# Create and start scheduler
scheduler = Scheduler(machine, queue)
scheduler.run_forever()  # Blocks until queue is empty
```

### Simulation Mode (Testing/Development)

```python
from cnckit.core import Machine, JobQueue, Scheduler

# Use simulation mode - no LinuxCNC required
machine = Machine(simulate=True)

queue = JobQueue()
queue.add("part1.ngc")

scheduler = Scheduler(machine, queue)
scheduler.start()

# Manual tick loop for more control
while scheduler.state.value == "running":
    scheduler.tick()
    time.sleep(1.0)
```

## Step-by-Step Setup

For more control, use the individual components:

```python
from cnckit.core import Machine, JobQueue, Scheduler, Event, EventEmitter

# Connect to LinuxCNC (or use simulate=True for testing)
machine = Machine(simulate=True)

# Create a job queue (FIFO by default)
queue = JobQueue()

# Create event emitter for callbacks
events = EventEmitter()

# Create a scheduler with event support
scheduler = Scheduler(machine, queue, events)

# Add jobs to the queue
queue.add("part1.ngc")
queue.add("part2.ngc", priority=10)  # Higher priority

# Start processing
scheduler.start()
```

## Queue Modes

cnckit supports different queue ordering strategies:

```python
from cnckit.core import JobQueue, QueueMode

# First in, first out (default)
fifo_queue = JobQueue(mode=QueueMode.FIFO)

# Last in, first out
lifo_queue = JobQueue(mode=QueueMode.LIFO)

# Priority-based (highest priority first)
priority_queue = JobQueue(mode=QueueMode.PRIORITY)
```

## Event Callbacks

React to job events:

```python
from cnckit.core import Machine, JobQueue, Scheduler, Event, EventEmitter

machine = Machine(simulate=True)
queue = JobQueue()
events = EventEmitter()

# Register callbacks for events
def on_complete(job):
    print(f"Finished: {job.name}")

def on_error(job, error):
    print(f"Error in {job.name}: {error}")

def on_started(job):
    print(f"Started: {job.name}")

events.on(Event.JOB_COMPLETED, on_complete)
events.on(Event.JOB_FAILED, on_error)
events.on(Event.JOB_STARTED, on_started)

scheduler = Scheduler(machine, queue, events)
```

## Scheduler Control

Control job execution:

```python
scheduler.start()   # Start processing jobs
scheduler.pause()   # Finish current job, then pause
scheduler.stop()    # Stop immediately (aborts current job)

# Check state
print(scheduler.state)  # SchedulerState.RUNNING, PAUSED, or STOPPED

# Get current job
if scheduler.current_job:
    print(f"Running: {scheduler.current_job.name}")
```

## Machine State

Monitor machine state:

```python
from cnckit.core import Machine, MachineState

machine = Machine(simulate=True)

# Check state
if machine.state == MachineState.IDLE:
    print("Machine is ready")

# Convenience methods
machine.is_idle()      # True if idle
machine.is_running()   # True if running a program
machine.is_ready()     # True if idle or paused

# Position and tool
print(f"Position: X={machine.position.x}, Y={machine.position.y}")
print(f"Tool: {machine.tool}")
```

## Next Steps

- [Architecture](../architecture.md) - Understand the design
- [API Reference](../api/core/machine.md) - Full API documentation
- [Integrations](../api/integrations/api.md) - Add REST API, MQTT, etc.

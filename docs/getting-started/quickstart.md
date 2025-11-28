# Quick Start

Get started with cnckit in minutes.

## Basic Usage

The simplest way to use cnckit is with the `quickstart` function:

```python
from cnckit import quickstart

# Start processing jobs from a directory
quickstart("/home/cnc/jobs/")
```

This will:

1. Initialize a connection to LinuxCNC
2. Create a job queue from `.ngc` files in the directory
3. Start a scheduler to process jobs

## Step-by-Step Setup

For more control, use the individual components:

```python
from cnckit import Machine, JobQueue, Scheduler

# Connect to LinuxCNC
machine = Machine()

# Create a job queue (FIFO by default)
queue = JobQueue()

# Create a scheduler
scheduler = Scheduler(machine, queue)

# Add jobs to the queue
queue.add("part1.ngc")
queue.add("part2.ngc", priority=10)  # Higher priority

# Start processing
scheduler.start()
```

## Queue Modes

cnckit supports different queue ordering strategies:

```python
from cnckit.core.queue import JobQueue, QueueMode

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
from cnckit import Machine, JobQueue, Scheduler, EventEmitter
from cnckit.core.events import Event

emitter = EventEmitter()

@emitter.on(Event.JOB_COMPLETED)
def on_complete(job):
    print(f"Finished: {job.name}")

@emitter.on(Event.JOB_FAILED)
def on_error(job, error):
    print(f"Error in {job.name}: {error}")

scheduler = Scheduler(machine, queue, events=emitter)
```

## Scheduler Control

Control job execution:

```python
scheduler.start()   # Start processing jobs
scheduler.pause()   # Finish current job, then pause
scheduler.stop()    # Stop immediately

print(scheduler.state)  # 'running', 'paused', or 'stopped'
```

## Next Steps

- [Architecture](../architecture.md) - Understand the design
- [API Reference](../api/core/machine.md) - Full API documentation
- [Integrations](../api/integrations/api.md) - Add REST API, MQTT, etc.

"""
Core modules - dependency-free building blocks for CNC automation.

This layer contains the minimal, stable foundation:
- Machine: abstraction over LinuxCNC's Python API
- Job: metadata wrapper for gcode jobs
- JobQueue: enqueue, dequeue, prioritization
- Scheduler: job execution rules
- EventEmitter: simple callback/hook system
- Config: configuration loader with defaults
"""

from cnckit.core.config import Config
from cnckit.core.events import Event, EventEmitter
from cnckit.core.job import Job, JobStatus
from cnckit.core.machine import Machine, MachineState, Position
from cnckit.core.queue import JobQueue, QueueMode
from cnckit.core.scheduler import Scheduler, SchedulerState

__all__ = [
    # Main classes
    "Config",
    "EventEmitter",
    "Job",
    "JobQueue",
    "Machine",
    "Scheduler",
    # Enums
    "Event",
    "JobStatus",
    "MachineState",
    "QueueMode",
    "SchedulerState",
    # Data classes
    "Position",
]

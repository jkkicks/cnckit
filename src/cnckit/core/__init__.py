"""
Core modules - dependency-free building blocks for CNC automation.

This layer contains the minimal, stable foundation:
- Machine: abstraction over LinuxCNC's Python API
- Job: metadata wrapper for gcode jobs
- JobQueue: enqueue, dequeue, prioritization
- Scheduler: job execution rules
- EventEmitter: simple callback/hook system
- Config: optional configuration loader
"""

from cnckit.core.events import EventEmitter
from cnckit.core.job import Job
from cnckit.core.machine import Machine
from cnckit.core.queue import JobQueue
from cnckit.core.scheduler import Scheduler

__all__ = ["EventEmitter", "Job", "JobQueue", "Machine", "Scheduler"]

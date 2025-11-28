"""
cnckit - A lightweight, modular Python framework for LinuxCNC automation.

This package provides job queuing, scheduling, and machine state management
for LinuxCNC with optional integrations for REST APIs, MQTT, WebSockets, and robotics.
"""

from typing import Any

from cnckit.core.events import EventEmitter
from cnckit.core.job import Job
from cnckit.core.machine import Machine
from cnckit.core.queue import JobQueue
from cnckit.core.scheduler import Scheduler

__version__ = "0.1.0"
__all__ = ["EventEmitter", "Job", "JobQueue", "Machine", "Scheduler", "quickstart"]


def quickstart(
    job_directory: str, **kwargs: Any
) -> tuple[Machine, JobQueue, Scheduler]:
    """
    One-call setup for simple CNC job automation.

    Args:
        job_directory: Path to directory containing .ngc files
        **kwargs: Additional configuration options

    Returns:
        Tuple of (Machine, JobQueue, Scheduler) instances
    """
    raise NotImplementedError("quickstart will be implemented in Phase 1")

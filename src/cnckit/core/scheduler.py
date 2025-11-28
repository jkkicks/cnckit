"""
Job scheduler with start/stop/pause controls.

This module provides a scheduler that coordinates between the
machine and job queue to execute jobs according to rules.
"""

from enum import Enum

from cnckit.core.machine import Machine
from cnckit.core.queue import JobQueue


class SchedulerState(Enum):
    """Scheduler operational state."""

    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"


class Scheduler:
    """
    Coordinates job execution between machine and queue.

    The scheduler pulls jobs from the queue and executes them
    on the machine, respecting start/stop/pause controls.

    Example:
        >>> scheduler = Scheduler(machine, queue)
        >>> scheduler.start()
        >>> scheduler.pause()  # Finish current job, don't start next
        >>> scheduler.stop()   # Stop immediately
    """

    def __init__(self, machine: Machine, queue: JobQueue):
        """
        Initialize the scheduler.

        Args:
            machine: Machine instance to execute jobs on
            queue: JobQueue to pull jobs from
        """
        raise NotImplementedError("Scheduler will be implemented in Phase 1")

    def start(self) -> None:
        """Start processing jobs from the queue."""
        raise NotImplementedError("Scheduler will be implemented in Phase 1")

    def stop(self) -> None:
        """Stop the scheduler immediately."""
        raise NotImplementedError("Scheduler will be implemented in Phase 1")

    def pause(self) -> None:
        """Pause after current job completes."""
        raise NotImplementedError("Scheduler will be implemented in Phase 1")

    @property
    def state(self) -> SchedulerState:
        """Current scheduler state."""
        raise NotImplementedError("Scheduler will be implemented in Phase 1")

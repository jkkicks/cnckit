"""
Job queue with FIFO/LIFO support and prioritization.

This module provides a flexible job queue that supports different
ordering strategies and priority-based scheduling.
"""

from enum import Enum
from typing import Any

from cnckit.core.job import Job


class QueueMode(Enum):
    """Queue ordering mode."""

    FIFO = "fifo"  # First in, first out
    LIFO = "lifo"  # Last in, first out
    PRIORITY = "priority"  # Highest priority first


class JobQueue:
    """
    A flexible job queue with configurable ordering.

    Supports FIFO, LIFO, and priority-based ordering. Jobs can be
    added, removed, and reordered dynamically.

    Example:
        >>> queue = JobQueue(mode=QueueMode.PRIORITY)
        >>> queue.add("part1.ngc", priority=5)
        >>> queue.add("urgent.ngc", priority=10)
        >>> queue.next()  # Returns urgent.ngc
    """

    def __init__(self, mode: QueueMode = QueueMode.FIFO):
        """
        Initialize the job queue.

        Args:
            mode: Queue ordering mode (FIFO, LIFO, or PRIORITY)
        """
        raise NotImplementedError("JobQueue will be implemented in Phase 1")

    def add(self, path: str, priority: int = 0, **kwargs: Any) -> Job:
        """Add a job to the queue."""
        raise NotImplementedError("JobQueue will be implemented in Phase 1")

    def next(self) -> Job | None:
        """Get the next job without removing it."""
        raise NotImplementedError("JobQueue will be implemented in Phase 1")

    def pop(self) -> Job | None:
        """Remove and return the next job."""
        raise NotImplementedError("JobQueue will be implemented in Phase 1")

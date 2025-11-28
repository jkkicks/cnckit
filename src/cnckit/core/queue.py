"""
Job queue with FIFO/LIFO support and prioritization.

This module provides a flexible job queue that supports different
ordering strategies and priority-based scheduling.
"""

from collections.abc import Iterator
from enum import Enum
from pathlib import Path
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
        >>> job = queue.next()  # Peek at urgent.ngc (priority 10)
        >>> job = queue.pop()   # Remove and return urgent.ngc
    """

    def __init__(self, mode: QueueMode = QueueMode.FIFO) -> None:
        """
        Initialize the job queue.

        Args:
            mode: Queue ordering mode (FIFO, LIFO, or PRIORITY)
        """
        self._mode = mode
        self._jobs: list[Job] = []

    @property
    def mode(self) -> QueueMode:
        """Get the queue ordering mode."""
        return self._mode

    def add(self, path: str | Path, priority: int = 0, **kwargs: Any) -> Job:
        """
        Add a job to the queue.

        Args:
            path: Path to the G-code file
            priority: Job priority (higher = more urgent, used in PRIORITY mode)
            **kwargs: Additional arguments passed to Job constructor

        Returns:
            The created Job instance
        """
        job = Job(path=Path(path), priority=priority, **kwargs)
        self._jobs.append(job)
        return job

    def add_job(self, job: Job) -> None:
        """
        Add an existing Job instance to the queue.

        Args:
            job: Job instance to add
        """
        self._jobs.append(job)

    def _get_next_index(self) -> int | None:
        """Get the index of the next job based on queue mode."""
        if not self._jobs:
            return None

        if self._mode == QueueMode.FIFO:
            return 0
        elif self._mode == QueueMode.LIFO:
            return len(self._jobs) - 1
        else:  # PRIORITY - highest priority first
            return max(range(len(self._jobs)), key=lambda i: self._jobs[i].priority)

    def next(self) -> Job | None:
        """
        Get the next job without removing it (peek).

        Returns:
            The next Job based on queue mode, or None if queue is empty
        """
        idx = self._get_next_index()
        if idx is None:
            return None
        return self._jobs[idx]

    def pop(self) -> Job | None:
        """
        Remove and return the next job.

        Returns:
            The next Job based on queue mode, or None if queue is empty
        """
        idx = self._get_next_index()
        if idx is None:
            return None
        return self._jobs.pop(idx)

    def remove(self, job: Job) -> bool:
        """
        Remove a specific job from the queue.

        Args:
            job: The Job instance to remove

        Returns:
            True if job was removed, False if not found
        """
        try:
            self._jobs.remove(job)
            return True
        except ValueError:
            return False

    def clear(self) -> None:
        """Remove all jobs from the queue."""
        self._jobs.clear()

    def jobs(self) -> list[Job]:
        """
        Get all jobs in the queue (in insertion order).

        Returns:
            List of jobs (copy, not the internal list)
        """
        return self._jobs.copy()

    def __len__(self) -> int:
        """Return the number of jobs in the queue."""
        return len(self._jobs)

    def __iter__(self) -> Iterator[Job]:
        """Iterate over jobs in insertion order."""
        return iter(self._jobs.copy())

    def __bool__(self) -> bool:
        """Return True if queue has jobs, False if empty."""
        return len(self._jobs) > 0

    def __contains__(self, job: Job) -> bool:
        """Check if a job is in the queue."""
        return job in self._jobs

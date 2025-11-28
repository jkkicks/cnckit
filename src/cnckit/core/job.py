"""
Job metadata wrapper for G-code programs.

This module provides a Job class that wraps G-code files with
metadata like priority, estimated time, and required tools.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class JobStatus(Enum):
    """Status of a job in the queue/scheduler."""

    PENDING = "pending"  # Waiting in queue
    RUNNING = "running"  # Currently executing
    COMPLETED = "completed"  # Finished successfully
    FAILED = "failed"  # Finished with error


@dataclass
class Job:
    """
    Metadata wrapper for a G-code job.

    Attributes:
        path: Path to the .ngc file
        priority: Job priority (higher = more urgent)
        name: Human-readable job name (defaults to filename without extension)
        status: Current job status
        estimated_time: Estimated runtime in seconds
        tools_required: List of tool numbers needed
        created_at: When the job was queued
        started_at: When the job started running
        completed_at: When the job finished
        error: Error message if job failed
        metadata: Additional user-defined metadata

    Example:
        >>> job = Job(path=Path("part1.ngc"))
        >>> job.name
        'part1'
        >>> job.status
        <JobStatus.PENDING: 'pending'>
    """

    path: Path
    priority: int = 0
    name: str | None = None
    status: JobStatus = JobStatus.PENDING
    estimated_time: float | None = None
    tools_required: list[int] | None = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        """Set defaults after initialization."""
        # Convert string path to Path object
        if isinstance(self.path, str):
            self.path = Path(self.path)

        # Auto-derive name from filename if not provided
        if self.name is None:
            self.name = self.path.stem

    def mark_running(self) -> None:
        """Mark the job as currently running."""
        self.status = JobStatus.RUNNING
        self.started_at = datetime.now()

    def mark_completed(self) -> None:
        """Mark the job as successfully completed."""
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.now()

    def mark_failed(self, error: str) -> None:
        """
        Mark the job as failed with an error message.

        Args:
            error: Description of what went wrong
        """
        self.status = JobStatus.FAILED
        self.completed_at = datetime.now()
        self.error = error

    @property
    def is_finished(self) -> bool:
        """Check if the job has finished (completed or failed)."""
        return self.status in (JobStatus.COMPLETED, JobStatus.FAILED)

    @property
    def duration(self) -> float | None:
        """
        Get the job duration in seconds.

        Returns:
            Duration if job has started and finished, None otherwise.
        """
        if self.started_at is None or self.completed_at is None:
            return None
        return (self.completed_at - self.started_at).total_seconds()

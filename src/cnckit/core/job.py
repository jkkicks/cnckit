"""
Job metadata wrapper for G-code programs.

This module provides a Job class that wraps G-code files with
metadata like priority, estimated time, and required tools.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class Job:
    """
    Metadata wrapper for a G-code job.

    Attributes:
        path: Path to the .ngc file
        priority: Job priority (higher = more urgent)
        name: Human-readable job name
        estimated_time: Estimated runtime in seconds
        tools_required: List of tool numbers needed
        created_at: When the job was queued
        metadata: Additional user-defined metadata

    Example:
        >>> job = Job(path=Path("part1.ngc"), priority=10)
        >>> job.name
        'part1'
    """

    path: Path
    priority: int = 0
    name: str | None = None
    estimated_time: float | None = None
    tools_required: list[int] | None = None
    created_at: datetime = None  # type: ignore[assignment]
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        """Set defaults after initialization."""
        raise NotImplementedError("Job will be implemented in Phase 1")

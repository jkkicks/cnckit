"""
Simple callback/hook system for event handling.

This module provides an event emitter that allows registering
callbacks for various system events like job completion, errors, etc.
"""

from collections.abc import Callable
from enum import Enum
from typing import Any


class Event(Enum):
    """Standard events emitted by the system."""

    JOB_STARTED = "job_started"
    JOB_COMPLETED = "job_completed"
    JOB_FAILED = "job_failed"
    QUEUE_EMPTY = "queue_empty"
    MACHINE_ERROR = "machine_error"
    MACHINE_IDLE = "machine_idle"


class EventEmitter:
    """
    Simple pub/sub event system.

    Register callbacks for events and emit events to trigger them.
    Supports both enum-based and string-based event names.

    Example:
        >>> emitter = EventEmitter()
        >>> emitter.on(Event.JOB_COMPLETED, lambda job: print(f"Done: {job}"))
        >>> emitter.emit(Event.JOB_COMPLETED, job)
    """

    def __init__(self) -> None:
        """Initialize the event emitter."""
        raise NotImplementedError("EventEmitter will be implemented in Phase 1")

    def on(self, event: Event | str, callback: Callable[..., Any]) -> None:
        """
        Register a callback for an event.

        Args:
            event: Event to listen for
            callback: Function to call when event occurs
        """
        raise NotImplementedError("EventEmitter will be implemented in Phase 1")

    def off(self, event: Event | str, callback: Callable[..., Any]) -> None:
        """Remove a callback for an event."""
        raise NotImplementedError("EventEmitter will be implemented in Phase 1")

    def emit(self, event: Event | str, *args: Any, **kwargs: Any) -> None:
        """Emit an event, calling all registered callbacks."""
        raise NotImplementedError("EventEmitter will be implemented in Phase 1")

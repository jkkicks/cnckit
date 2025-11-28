"""
Simple callback/hook system for event handling.

This module provides an event emitter that allows registering
callbacks for various system events like job completion, errors, etc.
"""

from collections.abc import Callable
from collections import defaultdict
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
    MACHINE_CONNECTED = "machine_connected"
    MACHINE_DISCONNECTED = "machine_disconnected"


class EventEmitter:
    """
    Simple pub/sub event system.

    Register callbacks for events and emit events to trigger them.
    Supports both enum-based and string-based event names.

    Example:
        >>> emitter = EventEmitter()
        >>> emitter.on(Event.JOB_COMPLETED, lambda job: print(f"Done: {job}"))
        >>> emitter.emit(Event.JOB_COMPLETED, job)

        >>> # Using string event names for custom events
        >>> emitter.on("custom_event", my_handler)
        >>> emitter.emit("custom_event", data)
    """

    def __init__(self) -> None:
        """Initialize the event emitter."""
        self._listeners: dict[str, list[Callable[..., Any]]] = defaultdict(list)

    def _normalize_event(self, event: Event | str) -> str:
        """Convert Event enum to string key."""
        if isinstance(event, Event):
            return event.value
        return event

    def on(self, event: Event | str, callback: Callable[..., Any]) -> None:
        """
        Register a callback for an event.

        Args:
            event: Event to listen for (Event enum or string)
            callback: Function to call when event occurs

        Example:
            >>> emitter.on(Event.JOB_COMPLETED, lambda job: print(job.name))
            >>> emitter.on("custom", my_handler)
        """
        key = self._normalize_event(event)
        self._listeners[key].append(callback)

    def off(self, event: Event | str, callback: Callable[..., Any]) -> None:
        """
        Remove a callback for an event.

        Args:
            event: Event to stop listening for
            callback: The callback function to remove

        Note:
            If the callback is not registered, this is a no-op.
        """
        key = self._normalize_event(event)
        if key in self._listeners:
            try:
                self._listeners[key].remove(callback)
            except ValueError:
                pass  # Callback not in list, ignore

    def emit(self, event: Event | str, *args: Any, **kwargs: Any) -> None:
        """
        Emit an event, calling all registered callbacks.

        Args:
            event: Event to emit
            *args: Positional arguments to pass to callbacks
            **kwargs: Keyword arguments to pass to callbacks

        Note:
            Callbacks are called in the order they were registered.
            If a callback raises an exception, subsequent callbacks
            are still called, and the exception is re-raised after
            all callbacks have been invoked.

        Example:
            >>> emitter.emit(Event.JOB_COMPLETED, job)
            >>> emitter.emit(Event.JOB_FAILED, job, error="Tool broke")
        """
        key = self._normalize_event(event)
        callbacks = self._listeners.get(key, [])

        errors: list[Exception] = []
        for callback in callbacks:
            try:
                callback(*args, **kwargs)
            except Exception as e:
                errors.append(e)

        # Re-raise the first error after all callbacks have run
        if errors:
            raise errors[0]

    def listeners(self, event: Event | str) -> list[Callable[..., Any]]:
        """
        Get all listeners for an event.

        Args:
            event: Event to get listeners for

        Returns:
            List of callback functions (copy, not the internal list)
        """
        key = self._normalize_event(event)
        return self._listeners.get(key, []).copy()

    def clear(self, event: Event | str | None = None) -> None:
        """
        Clear listeners for an event, or all listeners if no event specified.

        Args:
            event: Event to clear listeners for, or None to clear all
        """
        if event is None:
            self._listeners.clear()
        else:
            key = self._normalize_event(event)
            if key in self._listeners:
                del self._listeners[key]

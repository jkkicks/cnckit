"""Tests for the EventEmitter class."""

import pytest

from cnckit.core.events import Event, EventEmitter


class TestEvent:
    """Tests for Event enum."""

    def test_standard_events_exist(self):
        """All standard events are defined."""
        assert Event.JOB_STARTED.value == "job_started"
        assert Event.JOB_COMPLETED.value == "job_completed"
        assert Event.JOB_FAILED.value == "job_failed"
        assert Event.QUEUE_EMPTY.value == "queue_empty"
        assert Event.MACHINE_ERROR.value == "machine_error"
        assert Event.MACHINE_IDLE.value == "machine_idle"
        assert Event.MACHINE_CONNECTED.value == "machine_connected"
        assert Event.MACHINE_DISCONNECTED.value == "machine_disconnected"


class TestEventEmitterBasics:
    """Tests for basic EventEmitter functionality."""

    def test_emitter_creation(self):
        """EventEmitter can be created."""
        emitter = EventEmitter()
        assert emitter is not None

    def test_on_registers_callback(self):
        """on() registers a callback for an event."""
        emitter = EventEmitter()

        def callback() -> None:
            pass

        emitter.on(Event.JOB_COMPLETED, callback)
        assert callback in emitter.listeners(Event.JOB_COMPLETED)

    def test_multiple_callbacks(self):
        """Multiple callbacks can be registered for same event."""
        emitter = EventEmitter()

        def callback1() -> None:
            pass

        def callback2() -> None:
            pass

        emitter.on(Event.JOB_COMPLETED, callback1)
        emitter.on(Event.JOB_COMPLETED, callback2)
        listeners = emitter.listeners(Event.JOB_COMPLETED)
        assert callback1 in listeners
        assert callback2 in listeners
        assert len(listeners) == 2


class TestEventEmitterEmit:
    """Tests for emit() method."""

    def test_emit_calls_callback(self):
        """Emitting an event calls registered callbacks."""
        emitter = EventEmitter()
        results = []
        emitter.on(Event.JOB_COMPLETED, lambda: results.append("called"))
        emitter.emit(Event.JOB_COMPLETED)
        assert results == ["called"]

    def test_emit_passes_args(self):
        """emit() passes positional arguments to callbacks."""
        emitter = EventEmitter()
        results = []
        emitter.on(Event.JOB_COMPLETED, lambda job: results.append(job))
        emitter.emit(Event.JOB_COMPLETED, "my_job")
        assert results == ["my_job"]

    def test_emit_passes_kwargs(self):
        """emit() passes keyword arguments to callbacks."""
        emitter = EventEmitter()
        results = []
        emitter.on(Event.JOB_FAILED, lambda job, error: results.append((job, error)))
        emitter.emit(Event.JOB_FAILED, "my_job", error="broke")
        assert results == [("my_job", "broke")]

    def test_emit_calls_callbacks_in_order(self):
        """Callbacks are called in registration order."""
        emitter = EventEmitter()
        results = []
        emitter.on(Event.JOB_COMPLETED, lambda: results.append(1))
        emitter.on(Event.JOB_COMPLETED, lambda: results.append(2))
        emitter.on(Event.JOB_COMPLETED, lambda: results.append(3))
        emitter.emit(Event.JOB_COMPLETED)
        assert results == [1, 2, 3]

    def test_emit_no_listeners_is_noop(self):
        """emit() with no listeners doesn't raise."""
        emitter = EventEmitter()
        emitter.emit(Event.JOB_COMPLETED)  # Should not raise


class TestEventEmitterOff:
    """Tests for off() method."""

    def test_off_removes_callback(self):
        """off() removes a registered callback."""
        emitter = EventEmitter()

        def callback() -> None:
            pass

        emitter.on(Event.JOB_COMPLETED, callback)
        emitter.off(Event.JOB_COMPLETED, callback)
        assert callback not in emitter.listeners(Event.JOB_COMPLETED)

    def test_off_nonexistent_callback_is_noop(self):
        """off() with unregistered callback doesn't raise."""
        emitter = EventEmitter()

        def callback() -> None:
            pass

        emitter.off(Event.JOB_COMPLETED, callback)  # Should not raise

    def test_off_nonexistent_event_is_noop(self):
        """off() with unregistered event doesn't raise."""
        emitter = EventEmitter()
        emitter.off("never_registered", lambda: None)  # Should not raise

    def test_removed_callback_not_called(self):
        """Removed callback is not called on emit."""
        emitter = EventEmitter()
        results: list[str] = []

        def callback() -> None:
            results.append("called")

        emitter.on(Event.JOB_COMPLETED, callback)
        emitter.off(Event.JOB_COMPLETED, callback)
        emitter.emit(Event.JOB_COMPLETED)
        assert results == []


class TestEventEmitterStringEvents:
    """Tests for string-based event names."""

    def test_string_event_registration(self):
        """Can register callbacks with string event names."""
        emitter = EventEmitter()

        def callback() -> None:
            pass

        emitter.on("custom_event", callback)
        assert callback in emitter.listeners("custom_event")

    def test_string_event_emit(self):
        """Can emit string event names."""
        emitter = EventEmitter()
        results = []
        emitter.on("custom_event", lambda: results.append("called"))
        emitter.emit("custom_event")
        assert results == ["called"]

    def test_enum_and_string_are_equivalent(self):
        """Event enum and its string value are treated the same."""
        emitter = EventEmitter()
        results = []
        emitter.on(Event.JOB_COMPLETED, lambda: results.append("enum"))
        emitter.on("job_completed", lambda: results.append("string"))
        emitter.emit(Event.JOB_COMPLETED)
        assert results == ["enum", "string"]


class TestEventEmitterClear:
    """Tests for clear() method."""

    def test_clear_specific_event(self):
        """clear(event) removes all listeners for that event."""
        emitter = EventEmitter()
        emitter.on(Event.JOB_COMPLETED, lambda: None)
        emitter.on(Event.JOB_COMPLETED, lambda: None)
        emitter.on(Event.JOB_FAILED, lambda: None)

        emitter.clear(Event.JOB_COMPLETED)

        assert len(emitter.listeners(Event.JOB_COMPLETED)) == 0
        assert len(emitter.listeners(Event.JOB_FAILED)) == 1

    def test_clear_all_events(self):
        """clear() with no args removes all listeners."""
        emitter = EventEmitter()
        emitter.on(Event.JOB_COMPLETED, lambda: None)
        emitter.on(Event.JOB_FAILED, lambda: None)
        emitter.on("custom", lambda: None)

        emitter.clear()

        assert len(emitter.listeners(Event.JOB_COMPLETED)) == 0
        assert len(emitter.listeners(Event.JOB_FAILED)) == 0
        assert len(emitter.listeners("custom")) == 0


class TestEventEmitterErrorHandling:
    """Tests for error handling in emit()."""

    def test_error_in_callback_still_calls_others(self):
        """If one callback raises, others are still called."""
        emitter = EventEmitter()
        results = []

        def good_callback():
            results.append("good")

        def bad_callback():
            raise ValueError("oops")

        emitter.on(Event.JOB_COMPLETED, good_callback)
        emitter.on(Event.JOB_COMPLETED, bad_callback)
        emitter.on(Event.JOB_COMPLETED, good_callback)

        with pytest.raises(ValueError, match="oops"):
            emitter.emit(Event.JOB_COMPLETED)

        # Both good callbacks should have been called
        assert results == ["good", "good"]

    def test_first_error_is_raised(self):
        """First error is raised after all callbacks run."""
        emitter = EventEmitter()

        def error1():
            raise ValueError("first")

        def error2():
            raise TypeError("second")

        emitter.on(Event.JOB_COMPLETED, error1)
        emitter.on(Event.JOB_COMPLETED, error2)

        with pytest.raises(ValueError, match="first"):
            emitter.emit(Event.JOB_COMPLETED)


class TestEventEmitterListeners:
    """Tests for listeners() method."""

    def test_listeners_returns_copy(self):
        """listeners() returns a copy, not the internal list."""
        emitter = EventEmitter()

        def callback() -> None:
            pass

        emitter.on(Event.JOB_COMPLETED, callback)

        listeners = emitter.listeners(Event.JOB_COMPLETED)
        listeners.clear()

        # Internal list should be unchanged
        assert len(emitter.listeners(Event.JOB_COMPLETED)) == 1

    def test_listeners_empty_for_unregistered_event(self):
        """listeners() returns empty list for unregistered events."""
        emitter = EventEmitter()
        assert emitter.listeners(Event.JOB_COMPLETED) == []
        assert emitter.listeners("never_registered") == []

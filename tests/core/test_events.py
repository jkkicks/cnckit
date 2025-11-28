"""Tests for the EventEmitter class."""

import pytest

from cnckit.core.events import Event, EventEmitter


class TestEventEmitter:
    """Tests for EventEmitter."""

    def test_emitter_creation_raises_not_implemented(self):
        """EventEmitter creation should raise NotImplementedError until Phase 1."""
        with pytest.raises(NotImplementedError):
            EventEmitter()

    # === Tests to be enabled in Phase 1 ===
    #
    # def test_register_callback(self):
    #     """Can register a callback for an event."""
    #     emitter = EventEmitter()
    #     callback = lambda: None
    #     emitter.on(Event.JOB_COMPLETED, callback)
    #     # Should not raise
    #
    # def test_emit_calls_callback(self):
    #     """Emitting an event calls registered callbacks."""
    #     emitter = EventEmitter()
    #     results = []
    #     emitter.on(Event.JOB_COMPLETED, lambda job: results.append(job))
    #     emitter.emit(Event.JOB_COMPLETED, "test_job")
    #     assert results == ["test_job"]
    #
    # def test_string_event_names(self):
    #     """Can use string event names."""
    #     emitter = EventEmitter()
    #     results = []
    #     emitter.on("custom_event", lambda: results.append(True))
    #     emitter.emit("custom_event")
    #     assert results == [True]


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

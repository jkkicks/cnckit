"""Tests for the Scheduler class."""

import pytest

from cnckit.core.scheduler import Scheduler, SchedulerState


class TestScheduler:
    """Tests for Scheduler."""

    def test_scheduler_creation_raises_not_implemented(self):
        """Scheduler creation should raise NotImplementedError until Phase 1."""
        # Can't even create Machine and JobQueue yet
        with pytest.raises(NotImplementedError):
            from cnckit.core.machine import Machine
            from cnckit.core.queue import JobQueue

            machine = Machine()
            queue = JobQueue()
            Scheduler(machine, queue)

    # === Tests to be enabled in Phase 1 ===
    #
    # def test_scheduler_initial_state_is_stopped(self, machine, queue):
    #     """Scheduler should start in stopped state."""
    #     scheduler = Scheduler(machine, queue)
    #     assert scheduler.state == SchedulerState.STOPPED
    #
    # def test_start_changes_state_to_running(self, machine, queue):
    #     """Starting scheduler changes state to running."""
    #     scheduler = Scheduler(machine, queue)
    #     scheduler.start()
    #     assert scheduler.state == SchedulerState.RUNNING
    #
    # def test_pause_changes_state_to_paused(self, machine, queue):
    #     """Pausing scheduler changes state to paused."""
    #     scheduler = Scheduler(machine, queue)
    #     scheduler.start()
    #     scheduler.pause()
    #     assert scheduler.state == SchedulerState.PAUSED


class TestSchedulerState:
    """Tests for SchedulerState enum."""

    def test_stopped_state_value(self):
        """STOPPED state has correct value."""
        assert SchedulerState.STOPPED.value == "stopped"

    def test_running_state_value(self):
        """RUNNING state has correct value."""
        assert SchedulerState.RUNNING.value == "running"

    def test_paused_state_value(self):
        """PAUSED state has correct value."""
        assert SchedulerState.PAUSED.value == "paused"

"""Tests for the JobQueue class."""

import pytest

from cnckit.core.queue import JobQueue, QueueMode


class TestJobQueue:
    """Tests for JobQueue."""

    def test_queue_creation_raises_not_implemented(self):
        """Queue creation should raise NotImplementedError until Phase 1."""
        with pytest.raises(NotImplementedError):
            JobQueue()

    def test_queue_with_mode_raises_not_implemented(self):
        """Queue with mode should raise NotImplementedError until Phase 1."""
        with pytest.raises(NotImplementedError):
            JobQueue(mode=QueueMode.PRIORITY)

    # === Tests to be enabled in Phase 1 ===
    #
    # def test_fifo_order(self, sample_gcode_file):
    #     """FIFO queue should return jobs in order added."""
    #     queue = JobQueue(mode=QueueMode.FIFO)
    #     queue.add("first.ngc")
    #     queue.add("second.ngc")
    #     assert queue.next().name == "first"
    #
    # def test_lifo_order(self, sample_gcode_file):
    #     """LIFO queue should return most recently added job."""
    #     queue = JobQueue(mode=QueueMode.LIFO)
    #     queue.add("first.ngc")
    #     queue.add("second.ngc")
    #     assert queue.next().name == "second"
    #
    # def test_priority_order(self, sample_gcode_file):
    #     """Priority queue should return highest priority first."""
    #     queue = JobQueue(mode=QueueMode.PRIORITY)
    #     queue.add("low.ngc", priority=1)
    #     queue.add("high.ngc", priority=10)
    #     queue.add("medium.ngc", priority=5)
    #     assert queue.next().name == "high"


class TestQueueMode:
    """Tests for QueueMode enum."""

    def test_fifo_mode_value(self):
        """FIFO mode has correct value."""
        assert QueueMode.FIFO.value == "fifo"

    def test_lifo_mode_value(self):
        """LIFO mode has correct value."""
        assert QueueMode.LIFO.value == "lifo"

    def test_priority_mode_value(self):
        """PRIORITY mode has correct value."""
        assert QueueMode.PRIORITY.value == "priority"

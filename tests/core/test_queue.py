"""Tests for the JobQueue class."""

from pathlib import Path

import pytest

from cnckit.core.job import Job
from cnckit.core.queue import JobQueue, QueueMode


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


class TestJobQueueCreation:
    """Tests for JobQueue creation."""

    def test_default_mode_is_fifo(self):
        """Default queue mode is FIFO."""
        queue = JobQueue()
        assert queue.mode == QueueMode.FIFO

    def test_create_with_mode(self):
        """Can create queue with specific mode."""
        queue = JobQueue(mode=QueueMode.PRIORITY)
        assert queue.mode == QueueMode.PRIORITY

    def test_empty_queue(self):
        """New queue is empty."""
        queue = JobQueue()
        assert len(queue) == 0
        assert not queue


class TestJobQueueAdd:
    """Tests for add() method."""

    def test_add_creates_job(self):
        """add() creates and returns a Job."""
        queue = JobQueue()
        job = queue.add("part1.ngc")
        assert isinstance(job, Job)
        assert job.path == Path("part1.ngc")

    def test_add_with_priority(self):
        """add() accepts priority argument."""
        queue = JobQueue()
        job = queue.add("urgent.ngc", priority=10)
        assert job.priority == 10

    def test_add_with_kwargs(self):
        """add() passes kwargs to Job constructor."""
        queue = JobQueue()
        job = queue.add("part.ngc", name="Custom Name", estimated_time=120.0)
        assert job.name == "Custom Name"
        assert job.estimated_time == 120.0

    def test_add_increases_length(self):
        """add() increases queue length."""
        queue = JobQueue()
        queue.add("job1.ngc")
        assert len(queue) == 1
        queue.add("job2.ngc")
        assert len(queue) == 2

    def test_add_job_instance(self):
        """add_job() adds existing Job instance."""
        queue = JobQueue()
        job = Job(path=Path("test.ngc"))
        queue.add_job(job)
        assert job in queue
        assert len(queue) == 1


class TestJobQueueFIFO:
    """Tests for FIFO mode."""

    def test_fifo_order(self):
        """FIFO returns jobs in order added."""
        queue = JobQueue(mode=QueueMode.FIFO)
        queue.add("first.ngc")
        queue.add("second.ngc")
        queue.add("third.ngc")

        assert queue.pop().name == "first"
        assert queue.pop().name == "second"
        assert queue.pop().name == "third"

    def test_fifo_next_does_not_remove(self):
        """next() peeks without removing in FIFO."""
        queue = JobQueue(mode=QueueMode.FIFO)
        queue.add("first.ngc")
        queue.add("second.ngc")

        assert queue.next().name == "first"
        assert queue.next().name == "first"  # Still first
        assert len(queue) == 2


class TestJobQueueLIFO:
    """Tests for LIFO mode."""

    def test_lifo_order(self):
        """LIFO returns most recently added job."""
        queue = JobQueue(mode=QueueMode.LIFO)
        queue.add("first.ngc")
        queue.add("second.ngc")
        queue.add("third.ngc")

        assert queue.pop().name == "third"
        assert queue.pop().name == "second"
        assert queue.pop().name == "first"

    def test_lifo_next_does_not_remove(self):
        """next() peeks without removing in LIFO."""
        queue = JobQueue(mode=QueueMode.LIFO)
        queue.add("first.ngc")
        queue.add("second.ngc")

        assert queue.next().name == "second"
        assert queue.next().name == "second"  # Still second
        assert len(queue) == 2


class TestJobQueuePriority:
    """Tests for PRIORITY mode."""

    def test_priority_order(self):
        """PRIORITY returns highest priority first."""
        queue = JobQueue(mode=QueueMode.PRIORITY)
        queue.add("low.ngc", priority=1)
        queue.add("high.ngc", priority=10)
        queue.add("medium.ngc", priority=5)

        assert queue.pop().name == "high"
        assert queue.pop().name == "medium"
        assert queue.pop().name == "low"

    def test_priority_same_priority_fifo(self):
        """Same priority jobs are returned in FIFO order."""
        queue = JobQueue(mode=QueueMode.PRIORITY)
        queue.add("first.ngc", priority=5)
        queue.add("second.ngc", priority=5)
        queue.add("third.ngc", priority=5)

        # With same priority, should get first added
        # (max returns first occurrence of max value)
        assert queue.pop().name == "first"

    def test_priority_next_does_not_remove(self):
        """next() peeks without removing in PRIORITY."""
        queue = JobQueue(mode=QueueMode.PRIORITY)
        queue.add("low.ngc", priority=1)
        queue.add("high.ngc", priority=10)

        assert queue.next().name == "high"
        assert queue.next().name == "high"  # Still high
        assert len(queue) == 2


class TestJobQueueEmptyOperations:
    """Tests for operations on empty queue."""

    def test_next_empty_returns_none(self):
        """next() on empty queue returns None."""
        queue = JobQueue()
        assert queue.next() is None

    def test_pop_empty_returns_none(self):
        """pop() on empty queue returns None."""
        queue = JobQueue()
        assert queue.pop() is None


class TestJobQueueRemove:
    """Tests for remove() method."""

    def test_remove_existing_job(self):
        """remove() removes and returns True for existing job."""
        queue = JobQueue()
        job = queue.add("test.ngc")
        assert queue.remove(job) is True
        assert job not in queue
        assert len(queue) == 0

    def test_remove_nonexistent_job(self):
        """remove() returns False for nonexistent job."""
        queue = JobQueue()
        job = Job(path=Path("test.ngc"))
        assert queue.remove(job) is False

    def test_remove_middle_job(self):
        """Can remove job from middle of queue."""
        queue = JobQueue()
        job1 = queue.add("first.ngc")
        job2 = queue.add("second.ngc")
        job3 = queue.add("third.ngc")

        queue.remove(job2)

        assert len(queue) == 2
        assert queue.pop().name == "first"
        assert queue.pop().name == "third"


class TestJobQueueClear:
    """Tests for clear() method."""

    def test_clear_empties_queue(self):
        """clear() removes all jobs."""
        queue = JobQueue()
        queue.add("job1.ngc")
        queue.add("job2.ngc")
        queue.add("job3.ngc")

        queue.clear()

        assert len(queue) == 0
        assert not queue

    def test_clear_empty_queue(self):
        """clear() on empty queue is safe."""
        queue = JobQueue()
        queue.clear()  # Should not raise
        assert len(queue) == 0


class TestJobQueueJobs:
    """Tests for jobs() method."""

    def test_jobs_returns_all(self):
        """jobs() returns all jobs in insertion order."""
        queue = JobQueue()
        job1 = queue.add("first.ngc")
        job2 = queue.add("second.ngc")
        job3 = queue.add("third.ngc")

        jobs = queue.jobs()

        assert len(jobs) == 3
        assert jobs[0] is job1
        assert jobs[1] is job2
        assert jobs[2] is job3

    def test_jobs_returns_copy(self):
        """jobs() returns a copy, not internal list."""
        queue = JobQueue()
        queue.add("test.ngc")

        jobs = queue.jobs()
        jobs.clear()

        assert len(queue) == 1


class TestJobQueueDunderMethods:
    """Tests for __len__, __iter__, __bool__, __contains__."""

    def test_len(self):
        """__len__ returns correct count."""
        queue = JobQueue()
        assert len(queue) == 0
        queue.add("job.ngc")
        assert len(queue) == 1

    def test_bool_empty(self):
        """Empty queue is falsy."""
        queue = JobQueue()
        assert not queue
        assert bool(queue) is False

    def test_bool_not_empty(self):
        """Non-empty queue is truthy."""
        queue = JobQueue()
        queue.add("job.ngc")
        assert queue
        assert bool(queue) is True

    def test_iter(self):
        """Can iterate over queue."""
        queue = JobQueue()
        job1 = queue.add("first.ngc")
        job2 = queue.add("second.ngc")

        jobs = list(queue)

        assert jobs == [job1, job2]

    def test_contains(self):
        """'in' operator works."""
        queue = JobQueue()
        job = queue.add("test.ngc")
        other_job = Job(path=Path("other.ngc"))

        assert job in queue
        assert other_job not in queue

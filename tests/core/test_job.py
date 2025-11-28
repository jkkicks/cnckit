"""Tests for the Job class."""

import time
from datetime import datetime
from pathlib import Path

import pytest

from cnckit.core.job import Job, JobStatus


class TestJobCreation:
    """Tests for Job creation and defaults."""

    def test_job_creation_with_path(self):
        """Job can be created with just a path."""
        job = Job(path=Path("part1.ngc"))
        assert job.path == Path("part1.ngc")
        assert job.priority == 0
        assert job.status == JobStatus.PENDING

    def test_job_creation_with_string_path(self):
        """Job converts string path to Path object."""
        job = Job(path="part1.ngc")  # type: ignore[arg-type]
        assert job.path == Path("part1.ngc")
        assert isinstance(job.path, Path)

    def test_job_name_defaults_to_filename(self):
        """Job name should default to the filename without extension."""
        job = Job(path=Path("/home/cnc/jobs/my_part.ngc"))
        assert job.name == "my_part"

    def test_job_name_can_be_overridden(self):
        """Job name can be explicitly set."""
        job = Job(path=Path("part1.ngc"), name="Custom Name")
        assert job.name == "Custom Name"

    def test_job_created_at_is_set(self):
        """Job should have created_at timestamp set on creation."""
        before = datetime.now()
        job = Job(path=Path("part1.ngc"))
        after = datetime.now()

        assert job.created_at is not None
        assert before <= job.created_at <= after

    def test_job_with_priority(self):
        """Job can be created with priority."""
        job = Job(path=Path("urgent.ngc"), priority=10)
        assert job.priority == 10

    def test_job_with_all_fields(self):
        """Job can be created with all optional fields."""
        job = Job(
            path=Path("part.ngc"),
            priority=5,
            name="Test Part",
            estimated_time=120.5,
            tools_required=[1, 2, 5],
            metadata={"material": "aluminum", "quantity": 10},
        )
        assert job.priority == 5
        assert job.name == "Test Part"
        assert job.estimated_time == 120.5
        assert job.tools_required == [1, 2, 5]
        assert job.metadata == {"material": "aluminum", "quantity": 10}


class TestJobStatus:
    """Tests for JobStatus enum."""

    def test_status_values(self):
        """All status values exist with correct strings."""
        assert JobStatus.PENDING.value == "pending"
        assert JobStatus.RUNNING.value == "running"
        assert JobStatus.COMPLETED.value == "completed"
        assert JobStatus.FAILED.value == "failed"

    def test_initial_status_is_pending(self):
        """New jobs start with PENDING status."""
        job = Job(path=Path("test.ngc"))
        assert job.status == JobStatus.PENDING


class TestJobStateTransitions:
    """Tests for job state transition methods."""

    def test_mark_running(self):
        """mark_running() sets status and started_at."""
        job = Job(path=Path("test.ngc"))
        assert job.started_at is None

        before = datetime.now()
        job.mark_running()
        after = datetime.now()

        assert job.status == JobStatus.RUNNING
        assert job.started_at is not None
        assert before <= job.started_at <= after

    def test_mark_completed(self):
        """mark_completed() sets status and completed_at."""
        job = Job(path=Path("test.ngc"))
        job.mark_running()
        assert job.completed_at is None

        before = datetime.now()
        job.mark_completed()
        after = datetime.now()

        assert job.status == JobStatus.COMPLETED
        assert job.completed_at is not None
        assert before <= job.completed_at <= after
        assert job.error is None

    def test_mark_failed(self):
        """mark_failed() sets status, completed_at, and error."""
        job = Job(path=Path("test.ngc"))
        job.mark_running()

        before = datetime.now()
        job.mark_failed("Tool broke")
        after = datetime.now()

        assert job.status == JobStatus.FAILED
        assert job.completed_at is not None
        assert before <= job.completed_at <= after
        assert job.error == "Tool broke"


class TestJobIsFinished:
    """Tests for is_finished property."""

    def test_pending_is_not_finished(self):
        """PENDING jobs are not finished."""
        job = Job(path=Path("test.ngc"))
        assert job.is_finished is False

    def test_running_is_not_finished(self):
        """RUNNING jobs are not finished."""
        job = Job(path=Path("test.ngc"))
        job.mark_running()
        assert job.is_finished is False

    def test_completed_is_finished(self):
        """COMPLETED jobs are finished."""
        job = Job(path=Path("test.ngc"))
        job.mark_running()
        job.mark_completed()
        assert job.is_finished is True

    def test_failed_is_finished(self):
        """FAILED jobs are finished."""
        job = Job(path=Path("test.ngc"))
        job.mark_running()
        job.mark_failed("Error")
        assert job.is_finished is True


class TestJobDuration:
    """Tests for duration property."""

    def test_duration_none_when_not_started(self):
        """Duration is None when job hasn't started."""
        job = Job(path=Path("test.ngc"))
        assert job.duration is None

    def test_duration_none_when_running(self):
        """Duration is None when job is still running."""
        job = Job(path=Path("test.ngc"))
        job.mark_running()
        assert job.duration is None

    def test_duration_calculated_when_completed(self):
        """Duration is calculated when job completes."""
        job = Job(path=Path("test.ngc"))
        job.mark_running()
        time.sleep(0.01)  # Small delay to ensure measurable duration
        job.mark_completed()

        assert job.duration is not None
        assert job.duration >= 0.01

    def test_duration_calculated_when_failed(self):
        """Duration is calculated when job fails."""
        job = Job(path=Path("test.ngc"))
        job.mark_running()
        time.sleep(0.01)
        job.mark_failed("Error")

        assert job.duration is not None
        assert job.duration >= 0.01

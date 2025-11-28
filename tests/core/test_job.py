"""Tests for the Job class."""

from pathlib import Path

import pytest

from cnckit.core.job import Job


class TestJob:
    """Tests for Job dataclass."""

    def test_job_creation_raises_not_implemented(self):
        """Job creation should raise NotImplementedError until Phase 1."""
        with pytest.raises(NotImplementedError):
            Job(path=Path("test.ngc"))

    def test_job_with_priority_raises_not_implemented(self):
        """Job with priority should raise NotImplementedError until Phase 1."""
        with pytest.raises(NotImplementedError):
            Job(path=Path("test.ngc"), priority=10)

    # === Tests to be enabled in Phase 1 ===
    #
    # def test_job_creation_with_path(self, sample_gcode_file):
    #     """Job can be created with just a path."""
    #     job = Job(path=Path(sample_gcode_file))
    #     assert job.path == Path(sample_gcode_file)
    #     assert job.priority == 0
    #
    # def test_job_name_defaults_to_filename(self, sample_gcode_file):
    #     """Job name should default to the filename without extension."""
    #     job = Job(path=Path(sample_gcode_file))
    #     assert job.name == "test_part"
    #
    # def test_job_created_at_is_set(self, sample_gcode_file):
    #     """Job should have created_at timestamp set on creation."""
    #     job = Job(path=Path(sample_gcode_file))
    #     assert job.created_at is not None

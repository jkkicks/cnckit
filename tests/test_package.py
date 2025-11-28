"""Tests for package-level imports and quickstart."""

import pytest

import cnckit


class TestPackageImports:
    """Tests for package imports."""

    def test_version_is_defined(self):
        """Package version should be defined."""
        assert hasattr(cnckit, "__version__")
        assert cnckit.__version__ == "0.1.0"

    def test_core_classes_importable(self):
        """Core classes should be importable from package root."""
        assert hasattr(cnckit, "Machine")
        assert hasattr(cnckit, "Job")
        assert hasattr(cnckit, "JobQueue")
        assert hasattr(cnckit, "Scheduler")
        assert hasattr(cnckit, "EventEmitter")

    def test_quickstart_importable(self):
        """quickstart function should be importable."""
        assert hasattr(cnckit, "quickstart")
        assert callable(cnckit.quickstart)


class TestQuickstart:
    """Tests for quickstart helper."""

    def test_quickstart_raises_not_implemented(self):
        """quickstart should raise NotImplementedError until Phase 1."""
        with pytest.raises(NotImplementedError):
            cnckit.quickstart("/some/path")

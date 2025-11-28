"""Tests for REST API integration."""

import pytest


class TestAPIIntegration:
    """Tests for FastAPI integration."""

    def test_create_app_raises_without_fastapi(self):
        """create_app should raise ImportError if fastapi not installed."""
        # This test will pass in CI without [api] extras
        # and be skipped when fastapi is available
        try:
            import fastapi  # noqa: F401

            pytest.skip("fastapi is installed, cannot test ImportError")
        except ImportError:
            from cnckit.integrations.api import create_app

            with pytest.raises(ImportError, match="pip install cnckit\\[api\\]"):
                create_app()

    # === Tests to be enabled in Phase 2 ===
    #
    # @pytest.mark.integration
    # def test_app_has_health_endpoint(self):
    #     """API should have a /health endpoint."""
    #     from cnckit.integrations.api import create_app
    #     from fastapi.testclient import TestClient
    #
    #     app = create_app()
    #     client = TestClient(app)
    #     response = client.get("/health")
    #     assert response.status_code == 200

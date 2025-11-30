"""Tests for REST API integration."""

import pytest

# Check if fastapi is available for testing
try:
    from fastapi.testclient import TestClient

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False


class TestAPIWithoutFastAPI:
    """Tests that work without FastAPI installed."""

    def test_import_raises_without_fastapi(self):
        """Import should raise ImportError if fastapi not installed."""
        if FASTAPI_AVAILABLE:
            pytest.skip("fastapi is installed, cannot test ImportError")

        with pytest.raises(ImportError, match="pip install cnckit\\[api\\]"):
            from cnckit.integrations.api import create_app  # noqa: F401


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not installed")
class TestHealthEndpoint:
    """Tests for /health endpoint."""

    def test_health_returns_200(self):
        """Health endpoint returns 200 OK."""
        from cnckit.integrations.api import create_app

        app = create_app(simulate=True)
        client = TestClient(app)

        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_health_includes_iso_timestamp(self):
        """Health response includes ISO format timestamp."""
        from cnckit.integrations.api import create_app

        app = create_app(simulate=True)
        client = TestClient(app)

        response = client.get("/health")
        data = response.json()

        # Should be valid ISO format
        assert "T" in data["timestamp"]


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not installed")
class TestDashboardEndpoint:
    """Tests for /dashboard endpoint."""

    def test_dashboard_returns_200(self):
        """Dashboard endpoint returns 200 OK."""
        from cnckit.integrations.api import create_app

        app = create_app(simulate=True)
        client = TestClient(app)

        response = client.get("/dashboard")

        assert response.status_code == 200

    def test_dashboard_returns_html(self):
        """Dashboard returns HTML content."""
        from cnckit.integrations.api import create_app

        app = create_app(simulate=True)
        client = TestClient(app)

        response = client.get("/dashboard")

        assert "text/html" in response.headers["content-type"]
        assert "<!DOCTYPE html>" in response.text

    def test_dashboard_contains_cnckit_title(self):
        """Dashboard HTML contains CNCKit title."""
        from cnckit.integrations.api import create_app

        app = create_app(simulate=True)
        client = TestClient(app)

        response = client.get("/dashboard")

        assert "CNCKit Dashboard" in response.text


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not installed")
class TestMachineEndpoint:
    """Tests for /machine/status endpoint."""

    def test_machine_status_returns_200(self):
        """Machine status endpoint returns 200 OK."""
        from cnckit.integrations.api import create_app

        app = create_app(simulate=True)
        client = TestClient(app)

        response = client.get("/machine/status")

        assert response.status_code == 200

    def test_machine_status_includes_state(self):
        """Machine status includes state field."""
        from cnckit.integrations.api import create_app

        app = create_app(simulate=True)
        client = TestClient(app)

        response = client.get("/machine/status")
        data = response.json()

        assert "state" in data
        assert data["state"] == "idle"  # Simulated machine starts idle

    def test_machine_status_includes_position(self):
        """Machine status includes position with x, y, z coordinates."""
        from cnckit.integrations.api import create_app

        app = create_app(simulate=True)
        client = TestClient(app)

        response = client.get("/machine/status")
        data = response.json()

        assert "position" in data
        pos = data["position"]
        assert "x" in pos
        assert "y" in pos
        assert "z" in pos

    def test_machine_status_includes_simulate_flag(self):
        """Machine status includes simulate flag."""
        from cnckit.integrations.api import create_app

        app = create_app(simulate=True)
        client = TestClient(app)

        response = client.get("/machine/status")
        data = response.json()

        assert data["simulate"] is True

    def test_machine_status_with_custom_machine(self):
        """Machine status works with custom machine instance."""
        from cnckit.core import Machine
        from cnckit.integrations.api import create_app

        machine = Machine(simulate=True)
        app = create_app(machine=machine)
        client = TestClient(app)

        response = client.get("/machine/status")
        data = response.json()

        assert data["state"] == "idle"


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not installed")
class TestQueueEndpoints:
    """Tests for /queue endpoints."""

    def test_get_queue_empty(self):
        """Empty queue returns correctly."""
        from cnckit.integrations.api import create_app

        app = create_app(simulate=True)
        client = TestClient(app)

        response = client.get("/queue")

        assert response.status_code == 200
        data = response.json()
        assert data["mode"] == "fifo"
        assert data["count"] == 0
        assert data["jobs"] == []

    def test_add_job_success(self, sample_gcode_file):
        """Adding a valid job returns 201."""
        from cnckit.integrations.api import create_app

        app = create_app(simulate=True)
        client = TestClient(app)

        response = client.post(
            "/queue",
            json={"path": sample_gcode_file, "priority": 5},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "Job added to queue"
        assert data["job"]["path"] == sample_gcode_file
        assert data["job"]["priority"] == 5

    def test_add_job_file_not_found(self):
        """Adding nonexistent file returns 404."""
        from cnckit.integrations.api import create_app

        app = create_app(simulate=True)
        client = TestClient(app)

        response = client.post(
            "/queue",
            json={"path": "/nonexistent/file.ngc"},
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_add_job_with_name(self, sample_gcode_file):
        """Adding job with custom name sets the name."""
        from cnckit.integrations.api import create_app

        app = create_app(simulate=True)
        client = TestClient(app)

        response = client.post(
            "/queue",
            json={"path": sample_gcode_file, "name": "My Custom Job"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["job"]["name"] == "My Custom Job"

    def test_get_queue_with_jobs(self, sample_gcode_file):
        """Queue with jobs returns all jobs."""
        from cnckit.integrations.api import create_app

        app = create_app(simulate=True)
        client = TestClient(app)

        # Add two jobs
        client.post("/queue", json={"path": sample_gcode_file, "priority": 1})
        client.post("/queue", json={"path": sample_gcode_file, "priority": 2})

        response = client.get("/queue")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        assert len(data["jobs"]) == 2

    def test_remove_job_success(self, sample_gcode_file):
        """Removing existing job returns success."""
        from cnckit.integrations.api import create_app

        app = create_app(simulate=True)
        client = TestClient(app)

        # Add a job
        add_response = client.post(
            "/queue",
            json={"path": sample_gcode_file},
        )
        job_id = add_response.json()["job"]["id"]

        # Remove it
        response = client.delete(f"/queue/{job_id}")

        assert response.status_code == 200
        assert "removed" in response.json()["message"].lower()

        # Verify queue is empty
        queue_response = client.get("/queue")
        assert queue_response.json()["count"] == 0

    def test_remove_job_not_found(self):
        """Removing nonexistent job returns 404."""
        from cnckit.integrations.api import create_app

        app = create_app(simulate=True)
        client = TestClient(app)

        response = client.delete("/queue/nonexistent.ngc")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not installed")
class TestSchedulerEndpoints:
    """Tests for /scheduler endpoints."""

    def test_get_scheduler_status(self):
        """Scheduler status returns correctly."""
        from cnckit.integrations.api import create_app

        app = create_app(simulate=True)
        client = TestClient(app)

        response = client.get("/scheduler/status")

        assert response.status_code == 200
        data = response.json()
        assert data["state"] == "stopped"  # Default state
        assert data["current_job"] is None

    def test_start_scheduler(self):
        """Starting scheduler changes state."""
        from cnckit.integrations.api import create_app

        app = create_app(simulate=True)
        client = TestClient(app)

        response = client.post("/scheduler/start")

        assert response.status_code == 200
        assert "started" in response.json()["message"].lower()

    def test_pause_scheduler(self):
        """Pausing scheduler returns success message."""
        from cnckit.integrations.api import create_app

        app = create_app(simulate=True)
        client = TestClient(app)

        # Start first
        client.post("/scheduler/start")

        response = client.post("/scheduler/pause")

        assert response.status_code == 200
        assert "paus" in response.json()["message"].lower()

    def test_stop_scheduler(self):
        """Stopping scheduler changes state to stopped."""
        from cnckit.integrations.api import create_app

        app = create_app(simulate=True)
        client = TestClient(app)

        # Start first
        client.post("/scheduler/start")

        response = client.post("/scheduler/stop")

        assert response.status_code == 200
        assert "stopped" in response.json()["message"].lower()

        # Verify state
        status_response = client.get("/scheduler/status")
        assert status_response.json()["state"] == "stopped"

    def test_tick_scheduler(self, sample_gcode_file):
        """Tick scheduler advances state."""
        from cnckit.integrations.api import create_app

        app = create_app(simulate=True)
        client = TestClient(app)

        # Add a job and start scheduler
        client.post("/queue", json={"path": sample_gcode_file})
        client.post("/scheduler/start")

        response = client.post("/scheduler/tick")

        assert response.status_code == 200
        data = response.json()
        assert "state" in data

    def test_scheduler_runs_job(self, sample_gcode_file):
        """Scheduler executes a job through ticks."""
        from cnckit.integrations.api import create_app

        app = create_app(simulate=True)
        client = TestClient(app)

        # Add a job
        client.post("/queue", json={"path": sample_gcode_file})

        # Start scheduler
        client.post("/scheduler/start")

        # Should have picked up the job
        status = client.get("/scheduler/status").json()
        assert status["current_job"] is not None
        assert status["current_job"]["status"] == "running"


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not installed")
class TestAppStateManagement:
    """Tests for application state management."""

    def test_create_app_with_defaults(self):
        """create_app works with default arguments."""
        from cnckit.integrations.api import create_app

        app = create_app()

        assert app is not None
        assert app.title == "CNCKit API"

    def test_create_app_with_custom_components(self):
        """create_app accepts custom core components."""
        from cnckit.core import EventEmitter, JobQueue, Machine, Scheduler
        from cnckit.integrations.api import create_app

        machine = Machine(simulate=True)
        queue = JobQueue()
        events = EventEmitter()
        scheduler = Scheduler(machine, queue, events)

        app = create_app(
            machine=machine,
            queue=queue,
            scheduler=scheduler,
            events=events,
        )

        assert app is not None

    def test_state_shared_across_requests(self, sample_gcode_file):
        """State is shared across multiple requests."""
        from cnckit.integrations.api import create_app

        app = create_app(simulate=True)
        client = TestClient(app)

        # Add job via API
        client.post("/queue", json={"path": sample_gcode_file})

        # Verify via separate request
        response = client.get("/queue")
        assert response.json()["count"] == 1


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not installed")
class TestOpenAPIDocumentation:
    """Tests for API documentation."""

    def test_openapi_schema_available(self):
        """OpenAPI schema is generated."""
        from cnckit.integrations.api import create_app

        app = create_app(simulate=True)
        client = TestClient(app)

        response = client.get("/openapi.json")

        assert response.status_code == 200
        schema = response.json()
        assert schema["info"]["title"] == "CNCKit API"
        assert "/health" in schema["paths"]
        assert "/machine/status" in schema["paths"]
        assert "/queue" in schema["paths"]

    def test_docs_available(self):
        """Swagger UI docs are available."""
        from cnckit.integrations.api import create_app

        app = create_app(simulate=True)
        client = TestClient(app)

        response = client.get("/docs")

        assert response.status_code == 200

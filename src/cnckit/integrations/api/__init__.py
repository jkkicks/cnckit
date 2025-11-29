"""
REST API integration using FastAPI.

Provides HTTP endpoints for remote monitoring and control.
Requires: pip install cnckit[api]
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

# Validate FastAPI is available on import
try:
    from fastapi import Depends, FastAPI, HTTPException, status
    from fastapi.responses import HTMLResponse, JSONResponse
    from pydantic import BaseModel, Field
except ImportError:
    raise ImportError(
        "FastAPI is required for the REST API integration. "
        "Install with: pip install cnckit[api]"
    ) from None

# Path to static files
_STATIC_DIR = Path(__file__).parent / "static"

if TYPE_CHECKING:
    from cnckit.core import EventEmitter, JobQueue, Machine, Scheduler


# =============================================================================
# Pydantic Models
# =============================================================================


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(description="Service status")
    timestamp: str = Field(description="ISO format timestamp")


class PositionResponse(BaseModel):
    """Machine position response."""

    x: float
    y: float
    z: float
    a: float | None = None
    b: float | None = None
    c: float | None = None


class MachineStatusResponse(BaseModel):
    """Machine status response."""

    state: str = Field(description="Machine state (idle, running, etc.)")
    position: PositionResponse
    tool: int = Field(description="Current tool number")
    current_program: str | None = Field(description="Path to loaded program")
    progress: float = Field(description="Program progress (0.0 to 1.0)")
    simulate: bool = Field(description="Whether machine is in simulation mode")


class JobResponse(BaseModel):
    """Job information response."""

    id: str = Field(description="Job identifier (path-based)")
    name: str = Field(description="Human-readable job name")
    path: str = Field(description="Path to G-code file")
    priority: int = Field(description="Job priority")
    status: str = Field(description="Job status")
    estimated_time: float | None = Field(description="Estimated runtime in seconds")
    created_at: str = Field(description="ISO format creation timestamp")
    started_at: str | None = Field(description="ISO format start timestamp")
    completed_at: str | None = Field(description="ISO format completion timestamp")
    error: str | None = Field(description="Error message if failed")


class QueueResponse(BaseModel):
    """Queue status response."""

    mode: str = Field(description="Queue mode (fifo, lifo, priority)")
    count: int = Field(description="Number of jobs in queue")
    jobs: list[JobResponse] = Field(description="List of queued jobs")


class AddJobRequest(BaseModel):
    """Request to add a job to the queue."""

    path: str = Field(description="Path to G-code file")
    priority: int = Field(default=0, description="Job priority (higher = more urgent)")
    name: str | None = Field(default=None, description="Optional human-readable name")


class AddJobResponse(BaseModel):
    """Response after adding a job."""

    message: str
    job: JobResponse


class SchedulerStatusResponse(BaseModel):
    """Scheduler status response."""

    state: str = Field(description="Scheduler state (stopped, running, paused)")
    current_job: JobResponse | None = Field(description="Currently executing job")


class MessageResponse(BaseModel):
    """Simple message response."""

    message: str


class ErrorResponse(BaseModel):
    """Error response."""

    detail: str


# =============================================================================
# Application State
# =============================================================================


@dataclass
class AppState:
    """
    Holds references to cnckit core components.

    This allows the API to interact with an existing machine/queue/scheduler
    setup, or create new instances if none are provided.
    """

    machine: Machine | None = None
    queue: JobQueue | None = None
    scheduler: Scheduler | None = None
    events: EventEmitter | None = None
    _initialized: bool = field(default=False, init=False)

    def initialize(
        self,
        machine: Machine | None = None,
        queue: JobQueue | None = None,
        scheduler: Scheduler | None = None,
        events: EventEmitter | None = None,
        simulate: bool = True,
    ) -> None:
        """
        Initialize or update the application state.

        Args:
            machine: Machine instance (creates simulated if not provided)
            queue: JobQueue instance (creates new if not provided)
            scheduler: Scheduler instance (creates new if not provided)
            events: EventEmitter instance (creates new if not provided)
            simulate: If creating new machine, use simulation mode
        """
        from cnckit.core import EventEmitter as EE
        from cnckit.core import JobQueue, Machine, Scheduler

        self.events = events if events is not None else EE()
        self.machine = machine if machine is not None else Machine(simulate=simulate)
        self.queue = queue if queue is not None else JobQueue()
        self.scheduler = (
            scheduler
            if scheduler is not None
            else Scheduler(self.machine, self.queue, self.events)
        )
        self._initialized = True

    @property
    def is_initialized(self) -> bool:
        """Check if the app state has been initialized."""
        return self._initialized


# Global app state - will be initialized when create_app() is called
_app_state = AppState()


def get_state() -> AppState:
    """Dependency to get the application state."""
    if not _app_state.is_initialized:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Application not initialized. Call initialize() first.",
        )
    return _app_state


# =============================================================================
# Helper Functions
# =============================================================================


def job_to_response(job: Any) -> JobResponse:
    """Convert a Job instance to a JobResponse."""
    return JobResponse(
        id=str(job.path),
        name=job.name or job.path.stem,
        path=str(job.path),
        priority=job.priority,
        status=job.status.value,
        estimated_time=job.estimated_time,
        created_at=job.created_at.isoformat(),
        started_at=job.started_at.isoformat() if job.started_at else None,
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
        error=job.error,
    )


# =============================================================================
# API Routes
# =============================================================================


def create_app(
    machine: Machine | None = None,
    queue: JobQueue | None = None,
    scheduler: Scheduler | None = None,
    events: EventEmitter | None = None,
    simulate: bool = True,
) -> FastAPI:
    """
    Create a FastAPI application for cnckit.

    Args:
        machine: Optional Machine instance to use. If not provided,
                creates a new one based on the simulate parameter.
        queue: Optional JobQueue instance to use. If not provided,
              creates a new FIFO queue.
        scheduler: Optional Scheduler instance to use. If not provided,
                  creates a new scheduler with the machine and queue.
        events: Optional EventEmitter instance to use for events.
        simulate: If True and no machine provided, create a simulated machine.
                 Defaults to True for safety.

    Returns:
        FastAPI application instance configured with all endpoints.

    Example:
        >>> from cnckit.integrations.api import create_app
        >>> import uvicorn
        >>>
        >>> app = create_app(simulate=True)
        >>> uvicorn.run(app, host="0.0.0.0", port=8000)

        Or with existing components:
        >>> from cnckit.core import Machine, JobQueue, Scheduler
        >>> machine = Machine(simulate=True)
        >>> queue = JobQueue()
        >>> scheduler = Scheduler(machine, queue)
        >>> app = create_app(machine=machine, queue=queue, scheduler=scheduler)
    """
    # Initialize the global app state
    _app_state.initialize(
        machine=machine,
        queue=queue,
        scheduler=scheduler,
        events=events,
        simulate=simulate,
    )

    app = FastAPI(
        title="CNCKit API",
        description="REST API for CNC machine monitoring and control",
        version="0.1.0",
        responses={
            503: {"model": ErrorResponse, "description": "Service unavailable"},
        },
    )

    # -------------------------------------------------------------------------
    # Health Endpoint
    # -------------------------------------------------------------------------

    @app.get(
        "/health",
        response_model=HealthResponse,
        tags=["Health"],
        summary="Health check",
        description="Check if the API service is running.",
    )
    def health() -> HealthResponse:
        return HealthResponse(
            status="healthy",
            timestamp=datetime.now().isoformat(),
        )

    # -------------------------------------------------------------------------
    # Dashboard
    # -------------------------------------------------------------------------

    @app.get(
        "/dashboard",
        response_class=HTMLResponse,
        tags=["Dashboard"],
        summary="Web dashboard",
        description="Simple web dashboard for monitoring and control.",
    )
    def dashboard() -> HTMLResponse:
        dashboard_path = _STATIC_DIR / "dashboard.html"
        if not dashboard_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dashboard not found",
            )
        return HTMLResponse(content=dashboard_path.read_text())

    # -------------------------------------------------------------------------
    # Machine Endpoints
    # -------------------------------------------------------------------------

    @app.get(
        "/machine/status",
        response_model=MachineStatusResponse,
        tags=["Machine"],
        summary="Get machine status",
        description="Get the current machine state, position, and program info.",
    )
    def get_machine_status(
        state: AppState = Depends(get_state),
    ) -> MachineStatusResponse:
        machine = state.machine
        assert machine is not None  # Guaranteed by get_state
        pos = machine.position
        return MachineStatusResponse(
            state=machine.state.value,
            position=PositionResponse(
                x=pos.x,
                y=pos.y,
                z=pos.z,
                a=pos.a,
                b=pos.b,
                c=pos.c,
            ),
            tool=machine.tool,
            current_program=machine.current_program,
            progress=machine.progress,
            simulate=machine.simulate,
        )

    # -------------------------------------------------------------------------
    # Queue Endpoints
    # -------------------------------------------------------------------------

    @app.get(
        "/queue",
        response_model=QueueResponse,
        tags=["Queue"],
        summary="List queued jobs",
        description="Get all jobs currently in the queue.",
    )
    def get_queue(state: AppState = Depends(get_state)) -> QueueResponse:
        queue = state.queue
        assert queue is not None
        return QueueResponse(
            mode=queue.mode.value,
            count=len(queue),
            jobs=[job_to_response(job) for job in queue.jobs()],
        )

    @app.post(
        "/queue",
        response_model=AddJobResponse,
        status_code=status.HTTP_201_CREATED,
        tags=["Queue"],
        summary="Add a job",
        description="Add a new job to the queue.",
        responses={
            400: {"model": ErrorResponse, "description": "Invalid request"},
            404: {"model": ErrorResponse, "description": "File not found"},
        },
    )
    def add_job(
        request: AddJobRequest,
        state: AppState = Depends(get_state),
    ) -> AddJobResponse:
        queue = state.queue
        assert queue is not None

        # Validate the file exists
        path = Path(request.path)
        if not path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"G-code file not found: {request.path}",
            )

        # Add to queue
        job = queue.add(
            path=request.path,
            priority=request.priority,
            name=request.name,
        )

        return AddJobResponse(
            message="Job added to queue",
            job=job_to_response(job),
        )

    @app.delete(
        "/queue/{job_id:path}",
        response_model=MessageResponse,
        tags=["Queue"],
        summary="Remove a job",
        description="Remove a job from the queue by its ID (path).",
        responses={
            404: {"model": ErrorResponse, "description": "Job not found"},
        },
    )
    def remove_job(
        job_id: str,
        state: AppState = Depends(get_state),
    ) -> MessageResponse:
        queue = state.queue
        assert queue is not None

        # Find the job by path
        for job in queue.jobs():
            if str(job.path) == job_id:
                queue.remove(job)
                return MessageResponse(message=f"Job removed: {job_id}")

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job not found: {job_id}",
        )

    # -------------------------------------------------------------------------
    # Scheduler Endpoints
    # -------------------------------------------------------------------------

    @app.get(
        "/scheduler/status",
        response_model=SchedulerStatusResponse,
        tags=["Scheduler"],
        summary="Get scheduler status",
        description="Get the current scheduler state and running job.",
    )
    def get_scheduler_status(
        state: AppState = Depends(get_state),
    ) -> SchedulerStatusResponse:
        scheduler = state.scheduler
        assert scheduler is not None
        current_job = scheduler.current_job
        return SchedulerStatusResponse(
            state=scheduler.state.value,
            current_job=job_to_response(current_job) if current_job else None,
        )

    @app.post(
        "/scheduler/start",
        response_model=MessageResponse,
        tags=["Scheduler"],
        summary="Start scheduler",
        description="Start processing jobs from the queue.",
    )
    def start_scheduler(
        state: AppState = Depends(get_state),
    ) -> MessageResponse:
        scheduler = state.scheduler
        assert scheduler is not None
        scheduler.start()
        return MessageResponse(message="Scheduler started")

    @app.post(
        "/scheduler/pause",
        response_model=MessageResponse,
        tags=["Scheduler"],
        summary="Pause scheduler",
        description="Pause after the current job completes.",
    )
    def pause_scheduler(
        state: AppState = Depends(get_state),
    ) -> MessageResponse:
        scheduler = state.scheduler
        assert scheduler is not None
        scheduler.pause()
        return MessageResponse(message="Scheduler pausing after current job")

    @app.post(
        "/scheduler/stop",
        response_model=MessageResponse,
        tags=["Scheduler"],
        summary="Stop scheduler",
        description="Stop the scheduler immediately.",
    )
    def stop_scheduler(
        state: AppState = Depends(get_state),
    ) -> MessageResponse:
        scheduler = state.scheduler
        assert scheduler is not None
        scheduler.stop()
        return MessageResponse(message="Scheduler stopped")

    @app.post(
        "/scheduler/tick",
        response_model=SchedulerStatusResponse,
        tags=["Scheduler"],
        summary="Tick scheduler",
        description="Manually trigger a scheduler tick for step-by-step control.",
    )
    def tick_scheduler(
        state: AppState = Depends(get_state),
    ) -> SchedulerStatusResponse:
        scheduler = state.scheduler
        assert scheduler is not None
        scheduler.tick()
        current_job = scheduler.current_job
        return SchedulerStatusResponse(
            state=scheduler.state.value,
            current_job=job_to_response(current_job) if current_job else None,
        )

    # -------------------------------------------------------------------------
    # Exception Handlers
    # -------------------------------------------------------------------------

    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Any,  # noqa: ARG001
        exc: Exception,
    ) -> JSONResponse:
        """Handle unexpected exceptions."""
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": str(exc)},
        )

    return app


__all__ = [
    "AddJobRequest",
    "AddJobResponse",
    "AppState",
    "ErrorResponse",
    "HealthResponse",
    "JobResponse",
    "MachineStatusResponse",
    "MessageResponse",
    "PositionResponse",
    "QueueResponse",
    "SchedulerStatusResponse",
    "create_app",
]

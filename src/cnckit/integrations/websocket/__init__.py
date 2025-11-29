"""
WebSocket server for real-time status streaming.

Provides live updates of machine state and job progress.
Requires: pip install cnckit[websocket]
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import TYPE_CHECKING, Any

# Validate websockets is available on import
try:
    import websockets
    from websockets import serve
except ImportError:
    raise ImportError(
        "websockets is required for WebSocket integration. "
        "Install with: pip install cnckit[websocket]"
    ) from None

if TYPE_CHECKING:
    from collections.abc import Callable

    from cnckit.core import Event, EventEmitter, Job


# =============================================================================
# Message Formatting
# =============================================================================


def job_to_dict(job: Job) -> dict[str, Any]:
    """Convert a Job instance to a dictionary for JSON serialization."""
    return {
        "id": str(job.path),
        "name": job.name or job.path.stem,
        "path": str(job.path),
        "priority": job.priority,
        "status": job.status.value,
        "estimated_time": job.estimated_time,
        "created_at": job.created_at.isoformat(),
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "error": job.error,
    }


def create_message(
    msg_type: str,
    data: dict[str, Any] | None = None,
) -> str:
    """
    Create a JSON message with standard format.

    Args:
        msg_type: Message type identifier
        data: Optional data payload

    Returns:
        JSON string with type, timestamp, and data
    """
    message = {
        "type": msg_type,
        "timestamp": datetime.now().isoformat(),
        "data": data or {},
    }
    return json.dumps(message)


# =============================================================================
# WebSocket Server
# =============================================================================


class WebSocketServer:
    """
    WebSocket server for real-time cnckit updates.

    Streams machine state, job progress, and events to connected clients.
    Supports multiple concurrent client connections.

    The server integrates with cnckit's EventEmitter to automatically
    broadcast events to all connected clients.

    Example:
        >>> import asyncio
        >>> from cnckit.core import Machine, JobQueue, Scheduler, EventEmitter
        >>> from cnckit.integrations.websocket import WebSocketServer
        >>>
        >>> async def main():
        ...     # Set up core components
        ...     machine = Machine(simulate=True)
        ...     queue = JobQueue()
        ...     events = EventEmitter()
        ...     scheduler = Scheduler(machine, queue, events)
        ...
        ...     # Create and start WebSocket server
        ...     server = WebSocketServer(host="localhost", port=8765)
        ...     server.bind_events(events)
        ...
        ...     async with server:
        ...         # Run scheduler in background
        ...         queue.add("part1.ngc")
        ...         scheduler.start()
        ...         while scheduler.state.value != "stopped":
        ...             scheduler.tick()
        ...             # Broadcast machine state
        ...             await server.broadcast_machine_state(
        ...                 state=machine.state.value,
        ...                 position={"x": machine.position.x, "y": machine.position.y},
        ...                 progress=machine.progress,
        ...             )
        ...             await asyncio.sleep(1.0)
        >>>
        >>> asyncio.run(main())
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8765,
    ) -> None:
        """
        Initialize WebSocket server.

        Args:
            host: Host to bind to (default: "localhost")
            port: Port to listen on (default: 8765)
        """
        self._host = host
        self._port = port
        self._server: Any | None = None
        self._clients: set[Any] = set()  # WebSocket connections
        self._running = False
        self._lock = asyncio.Lock()

        # Event binding
        self._events: EventEmitter | None = None
        self._event_handlers: list[tuple[Event, Callable[..., Any]]] = []

    @property
    def host(self) -> str:
        """Get the server host."""
        return self._host

    @property
    def port(self) -> int:
        """Get the server port."""
        return self._port

    @property
    def is_running(self) -> bool:
        """Check if server is running."""
        return self._running

    @property
    def client_count(self) -> int:
        """Get number of connected clients."""
        return len(self._clients)

    # -------------------------------------------------------------------------
    # Server Lifecycle
    # -------------------------------------------------------------------------

    async def start(self) -> None:
        """
        Start the WebSocket server.

        The server will accept connections and handle messages until
        stop() is called.

        Raises:
            RuntimeError: If server is already running
        """
        if self._running:
            raise RuntimeError("Server is already running")

        self._server = await serve(
            self._handle_client,
            self._host,
            self._port,
        )
        self._running = True

    async def stop(self) -> None:
        """
        Stop the WebSocket server.

        Closes all client connections and stops accepting new ones.
        """
        if not self._running:
            return

        self._running = False

        # Close all client connections
        async with self._lock:
            for client in self._clients.copy():
                await client.close()
            self._clients.clear()

        # Stop the server
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            self._server = None

        # Unbind events
        self._unbind_events()

    async def __aenter__(self) -> WebSocketServer:
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Async context manager exit."""
        await self.stop()

    # -------------------------------------------------------------------------
    # Client Handling
    # -------------------------------------------------------------------------

    async def _handle_client(self, websocket: Any) -> None:
        """Handle a client connection."""
        async with self._lock:
            self._clients.add(websocket)

        try:
            # Send welcome message
            await websocket.send(
                create_message("connected", {"message": "Connected to CNCKit"})
            )

            # Keep connection alive and handle incoming messages
            async for message in websocket:
                await self._handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            async with self._lock:
                self._clients.discard(websocket)

    async def _handle_message(
        self,
        websocket: Any,
        message: str | bytes,
    ) -> None:
        """
        Handle incoming message from client.

        Override this method to add custom message handling.

        Args:
            websocket: The client connection
            message: The received message
        """
        # Default: echo back a pong for ping messages
        try:
            if isinstance(message, bytes):
                message = message.decode("utf-8")
            data = json.loads(message)
            if data.get("type") == "ping":
                await websocket.send(create_message("pong"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass

    # -------------------------------------------------------------------------
    # Broadcasting
    # -------------------------------------------------------------------------

    async def broadcast(self, message: str) -> None:
        """
        Broadcast a message to all connected clients.

        Args:
            message: JSON message string to broadcast
        """
        if not self._clients:
            return

        async with self._lock:
            # Send to all clients, removing any that fail
            disconnected: set[Any] = set()
            for client in self._clients:
                try:
                    await client.send(message)
                except websockets.exceptions.ConnectionClosed:
                    disconnected.add(client)

            self._clients -= disconnected

    async def broadcast_machine_state(
        self,
        state: str,
        position: dict[str, float] | None = None,
        progress: float = 0.0,
        current_program: str | None = None,
        tool: int = 0,
    ) -> None:
        """
        Broadcast machine state update to all clients.

        Args:
            state: Machine state (idle, running, etc.)
            position: Position dict with x, y, z keys
            progress: Program progress (0.0 to 1.0)
            current_program: Path to current program
            tool: Current tool number
        """
        data = {
            "state": state,
            "position": position or {"x": 0.0, "y": 0.0, "z": 0.0},
            "progress": progress,
            "current_program": current_program,
            "tool": tool,
        }
        await self.broadcast(create_message("machine_state", data))

    async def broadcast_job_started(self, job: Job) -> None:
        """Broadcast job started event to all clients."""
        await self.broadcast(create_message("job_started", {"job": job_to_dict(job)}))

    async def broadcast_job_completed(self, job: Job) -> None:
        """Broadcast job completed event to all clients."""
        await self.broadcast(create_message("job_completed", {"job": job_to_dict(job)}))

    async def broadcast_job_failed(self, job: Job, error: str | None = None) -> None:
        """Broadcast job failed event to all clients."""
        data = {"job": job_to_dict(job), "error": error or job.error}
        await self.broadcast(create_message("job_failed", data))

    async def broadcast_queue_empty(self) -> None:
        """Broadcast queue empty event to all clients."""
        await self.broadcast(create_message("queue_empty"))

    async def broadcast_scheduler_state(
        self,
        state: str,
        current_job: Job | None = None,
    ) -> None:
        """
        Broadcast scheduler state update to all clients.

        Args:
            state: Scheduler state (stopped, running, paused)
            current_job: Currently executing job, if any
        """
        data = {
            "state": state,
            "current_job": job_to_dict(current_job) if current_job else None,
        }
        await self.broadcast(create_message("scheduler_state", data))

    # -------------------------------------------------------------------------
    # Event Binding
    # -------------------------------------------------------------------------

    def bind_events(self, events: EventEmitter) -> None:
        """
        Bind to an EventEmitter to automatically broadcast events.

        When bound, the server will broadcast messages for:
        - JOB_STARTED -> job_started message
        - JOB_COMPLETED -> job_completed message
        - JOB_FAILED -> job_failed message
        - QUEUE_EMPTY -> queue_empty message

        Note: Event handlers schedule broadcasts as async tasks since
        EventEmitter callbacks are synchronous.

        Args:
            events: EventEmitter instance to listen to
        """
        from cnckit.core import Event

        self._events = events

        def get_loop() -> asyncio.AbstractEventLoop | None:
            """Get the running event loop, or None if not running."""
            try:
                return asyncio.get_running_loop()
            except RuntimeError:
                return None

        # Define handlers that schedule async broadcasts
        def on_job_started(job: Job) -> None:
            loop = get_loop()
            if loop is not None:
                loop.create_task(self.broadcast_job_started(job))

        def on_job_completed(job: Job) -> None:
            loop = get_loop()
            if loop is not None:
                loop.create_task(self.broadcast_job_completed(job))

        def on_job_failed(job: Job, error: str | None = None) -> None:
            loop = get_loop()
            if loop is not None:
                loop.create_task(self.broadcast_job_failed(job, error))

        def on_queue_empty() -> None:
            loop = get_loop()
            if loop is not None:
                loop.create_task(self.broadcast_queue_empty())

        # Register handlers
        handlers: list[tuple[Event, Callable[..., Any]]] = [
            (Event.JOB_STARTED, on_job_started),
            (Event.JOB_COMPLETED, on_job_completed),
            (Event.JOB_FAILED, on_job_failed),
            (Event.QUEUE_EMPTY, on_queue_empty),
        ]

        for event, handler in handlers:
            events.on(event, handler)
            self._event_handlers.append((event, handler))

    def _unbind_events(self) -> None:
        """Remove event handlers from the EventEmitter."""
        if self._events is not None:
            for event, handler in self._event_handlers:
                self._events.off(event, handler)
        self._event_handlers.clear()
        self._events = None


__all__ = [
    "WebSocketServer",
    "create_message",
    "job_to_dict",
]

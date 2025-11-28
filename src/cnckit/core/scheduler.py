"""
Job scheduler with start/stop/pause controls.

This module provides a scheduler that coordinates between the
machine and job queue to execute jobs according to rules.
"""

from __future__ import annotations

import time
from enum import Enum

from cnckit.core.events import Event, EventEmitter
from cnckit.core.job import Job  # noqa: TC001
from cnckit.core.machine import Machine, MachineState
from cnckit.core.queue import JobQueue  # noqa: TC001


class SchedulerState(Enum):
    """Scheduler operational state."""

    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"


class Scheduler:
    """
    Coordinates job execution between machine and queue.

    The scheduler pulls jobs from the queue and executes them
    on the machine, respecting start/stop/pause controls.

    Uses a tick-based polling model where you call tick() periodically
    to check machine state and handle job transitions.

    Example:
        >>> machine = Machine(simulate=True)
        >>> queue = JobQueue()
        >>> queue.add("part1.ngc")
        >>> queue.add("part2.ngc")
        >>>
        >>> scheduler = Scheduler(machine, queue)
        >>> scheduler.start()
        >>> while scheduler.state == SchedulerState.RUNNING:
        ...     scheduler.tick()
        ...     time.sleep(1.0)

    Or use the convenience blocking loop:
        >>> scheduler.run_forever(poll_interval=1.0)
    """

    def __init__(
        self,
        machine: Machine,
        queue: JobQueue,
        events: EventEmitter | None = None,
    ) -> None:
        """
        Initialize the scheduler.

        Args:
            machine: Machine instance to execute jobs on
            queue: JobQueue to pull jobs from
            events: Optional EventEmitter for job/machine events.
                   If not provided, creates a new one.
        """
        self._machine = machine
        self._queue = queue
        self._events = events if events is not None else EventEmitter()
        self._state = SchedulerState.STOPPED
        self._current_job: Job | None = None
        self._pause_after_current = False

    @property
    def state(self) -> SchedulerState:
        """Current scheduler state."""
        return self._state

    @property
    def current_job(self) -> Job | None:
        """Currently executing job, if any."""
        return self._current_job

    @property
    def events(self) -> EventEmitter:
        """Event emitter for scheduler events."""
        return self._events

    def start(self) -> None:
        """
        Start processing jobs from the queue.

        Sets scheduler to RUNNING state and begins processing the
        first job if the queue is not empty.
        """
        if self._state == SchedulerState.RUNNING:
            return

        self._state = SchedulerState.RUNNING
        self._pause_after_current = False

        # If no job is currently running, start the next one
        if self._current_job is None:
            self._process_next()

    def stop(self) -> None:
        """
        Stop the scheduler immediately.

        If a job is currently running on the machine, it continues
        to run but the scheduler won't process any more jobs.
        The current job is marked as failed if interrupted.
        """
        if self._state == SchedulerState.STOPPED:
            return

        self._state = SchedulerState.STOPPED
        self._pause_after_current = False

        # If there's a running job, mark it as failed
        if self._current_job is not None and self._machine.is_running():
            self._machine.abort()
            self._current_job.mark_failed("Scheduler stopped")
            self._events.emit(Event.JOB_FAILED, self._current_job, "Scheduler stopped")
            self._current_job = None

    def pause(self) -> None:
        """
        Pause after current job completes.

        The scheduler will finish the current job (if any) and then
        enter PAUSED state instead of starting the next job.
        """
        if self._state == SchedulerState.STOPPED:
            return

        if self._current_job is None:
            # No job running, pause immediately
            self._state = SchedulerState.PAUSED
        else:
            # Set flag to pause after current job
            self._pause_after_current = True

    def tick(self) -> None:
        """
        Check machine state and handle transitions.

        Call this method periodically (e.g., every 1 second) to:
        - Poll the machine for state updates
        - Detect job completion
        - Handle errors
        - Start the next job when ready

        This is the main polling method that drives the scheduler.
        """
        if self._state == SchedulerState.STOPPED:
            return

        # Poll machine to update state
        try:
            self._machine.poll()
        except Exception as e:
            self._handle_machine_error(e)
            return

        # Check for machine errors
        if self._machine.state == MachineState.ERROR:
            self._handle_machine_error(RuntimeError("Machine in error state"))
            return

        if self._machine.state == MachineState.ESTOP:
            self._handle_machine_error(RuntimeError("Machine in E-STOP"))
            return

        # Check if current job completed
        if self._current_job is not None and self._machine.is_idle():
            # Job completed
            self._current_job.mark_completed()
            self._events.emit(Event.JOB_COMPLETED, self._current_job)
            self._current_job = None

            # Check if we should pause
            if self._pause_after_current:
                self._state = SchedulerState.PAUSED
                self._pause_after_current = False
                return

            # Process next job
            if self._state == SchedulerState.RUNNING:
                self._process_next()

    def run_forever(self, poll_interval: float = 1.0) -> None:
        """
        Convenience blocking loop that runs until stopped or queue empty.

        Args:
            poll_interval: Time in seconds between tick() calls

        This method:
        1. Calls start() if not already running
        2. Calls tick() in a loop
        3. Sleeps for poll_interval between ticks
        4. Returns when state is no longer RUNNING
        """
        if self._state != SchedulerState.RUNNING:
            self.start()

        while self._state == SchedulerState.RUNNING:
            self.tick()
            time.sleep(poll_interval)

    def _process_next(self) -> None:
        """Pop next job from queue and start it on the machine."""
        if self._state != SchedulerState.RUNNING:
            return

        job = self._queue.pop()
        if job is None:
            self._events.emit(Event.QUEUE_EMPTY)
            self._state = SchedulerState.STOPPED
            return

        self._current_job = job

        try:
            job.mark_running()
            self._machine.load_program(str(job.path))
            self._machine.cycle_start()
            self._events.emit(Event.JOB_STARTED, job)
        except FileNotFoundError as e:
            job.mark_failed(str(e))
            self._events.emit(Event.JOB_FAILED, job, str(e))
            self._current_job = None
            # Try next job
            self._process_next()
        except Exception as e:
            job.mark_failed(str(e))
            self._events.emit(Event.JOB_FAILED, job, str(e))
            self._handle_machine_error(e)

    def _handle_machine_error(self, error: Exception) -> None:
        """Handle machine errors by stopping scheduler and failing current job."""
        self._state = SchedulerState.STOPPED
        self._events.emit(Event.MACHINE_ERROR, error)

        if self._current_job is not None:
            self._current_job.mark_failed(str(error))
            self._events.emit(Event.JOB_FAILED, self._current_job, str(error))
            self._current_job = None

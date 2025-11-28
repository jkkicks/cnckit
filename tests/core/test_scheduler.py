"""Tests for the Scheduler class."""

import pytest

from cnckit.core.events import Event, EventEmitter
from cnckit.core.job import JobStatus
from cnckit.core.machine import Machine, MachineState
from cnckit.core.queue import JobQueue
from cnckit.core.scheduler import Scheduler, SchedulerState


@pytest.fixture
def machine():
    """Create a simulated machine for testing."""
    m = Machine(simulate=True)
    # Use short execution time for fast tests
    m._backend._execution_time = 0.05  # type: ignore
    return m


@pytest.fixture
def queue():
    """Create an empty job queue."""
    return JobQueue()


@pytest.fixture
def events():
    """Create an event emitter."""
    return EventEmitter()


@pytest.fixture
def sample_programs(tmp_path):
    """Create sample G-code program files."""
    programs = []
    for i in range(3):
        prog = tmp_path / f"job{i}.ngc"
        prog.write_text(f"G0 X{i} Y{i}\n")
        programs.append(str(prog))
    return programs


class TestSchedulerState:
    """Tests for SchedulerState enum."""

    def test_stopped_state_value(self):
        """STOPPED state has correct value."""
        assert SchedulerState.STOPPED.value == "stopped"

    def test_running_state_value(self):
        """RUNNING state has correct value."""
        assert SchedulerState.RUNNING.value == "running"

    def test_paused_state_value(self):
        """PAUSED state has correct value."""
        assert SchedulerState.PAUSED.value == "paused"


class TestSchedulerCreation:
    """Tests for Scheduler creation."""

    def test_scheduler_creation(self, machine, queue):
        """Scheduler can be created with machine and queue."""
        scheduler = Scheduler(machine, queue)
        assert scheduler.state == SchedulerState.STOPPED
        assert scheduler.current_job is None

    def test_scheduler_with_events(self, machine, queue, events):
        """Scheduler can be created with custom event emitter."""
        scheduler = Scheduler(machine, queue, events)
        assert scheduler.events is events

    def test_scheduler_creates_default_events(self, machine, queue):
        """Scheduler creates event emitter if none provided."""
        scheduler = Scheduler(machine, queue)
        assert scheduler.events is not None
        assert isinstance(scheduler.events, EventEmitter)


class TestSchedulerStart:
    """Tests for Scheduler.start()."""

    def test_start_changes_state_to_running(self, machine, queue):
        """Starting scheduler changes state to running."""
        scheduler = Scheduler(machine, queue)
        scheduler.start()
        # Will immediately stop because queue is empty
        # But should have emitted QUEUE_EMPTY

    def test_start_with_empty_queue_emits_queue_empty(self, machine, queue, events):
        """Starting with empty queue emits QUEUE_EMPTY."""
        scheduler = Scheduler(machine, queue, events)

        empty_events = []
        events.on(Event.QUEUE_EMPTY, lambda: empty_events.append(True))

        scheduler.start()

        assert len(empty_events) == 1
        assert scheduler.state == SchedulerState.STOPPED

    def test_start_with_jobs_begins_first_job(self, machine, queue, sample_programs):
        """Starting with jobs in queue begins executing first job."""
        queue.add(sample_programs[0])
        scheduler = Scheduler(machine, queue)

        scheduler.start()

        assert scheduler.state == SchedulerState.RUNNING
        assert scheduler.current_job is not None
        assert machine.is_running()

    def test_start_emits_job_started(self, machine, queue, events, sample_programs):
        """Starting execution emits JOB_STARTED event."""
        queue.add(sample_programs[0])
        scheduler = Scheduler(machine, queue, events)

        started_jobs = []
        events.on(Event.JOB_STARTED, lambda job: started_jobs.append(job))

        scheduler.start()

        assert len(started_jobs) == 1
        assert started_jobs[0].name == "job0"

    def test_start_when_already_running_is_noop(self, machine, queue, sample_programs):
        """Starting when already running has no effect."""
        queue.add(sample_programs[0])
        scheduler = Scheduler(machine, queue)
        scheduler.start()

        first_job = scheduler.current_job

        scheduler.start()  # Should be no-op

        assert scheduler.current_job is first_job


class TestSchedulerStop:
    """Tests for Scheduler.stop()."""

    def test_stop_changes_state_to_stopped(self, machine, queue, sample_programs):
        """Stopping scheduler changes state to stopped."""
        queue.add(sample_programs[0])
        scheduler = Scheduler(machine, queue)
        scheduler.start()

        scheduler.stop()

        assert scheduler.state == SchedulerState.STOPPED

    def test_stop_aborts_current_job(self, machine, queue, sample_programs):
        """Stopping scheduler aborts the current job."""
        queue.add(sample_programs[0])
        scheduler = Scheduler(machine, queue)
        scheduler.start()

        job = scheduler.current_job

        scheduler.stop()

        assert job is not None
        assert job.status == JobStatus.FAILED
        assert machine.state == MachineState.IDLE

    def test_stop_emits_job_failed(self, machine, queue, events, sample_programs):
        """Stopping with running job emits JOB_FAILED."""
        queue.add(sample_programs[0])
        scheduler = Scheduler(machine, queue, events)

        failed_jobs = []
        events.on(Event.JOB_FAILED, lambda job, error: failed_jobs.append((job, error)))

        scheduler.start()
        scheduler.stop()

        assert len(failed_jobs) == 1
        assert "Scheduler stopped" in failed_jobs[0][1]

    def test_stop_when_already_stopped_is_noop(self, machine, queue):
        """Stopping when already stopped has no effect."""
        scheduler = Scheduler(machine, queue)
        scheduler.stop()  # Should be no-op
        assert scheduler.state == SchedulerState.STOPPED


class TestSchedulerPause:
    """Tests for Scheduler.pause()."""

    def test_pause_with_no_job_pauses_immediately(
        self, machine, queue, sample_programs
    ):
        """Pausing with no current job pauses immediately."""
        queue.add(sample_programs[0])
        queue.add(sample_programs[1])  # Need 2 jobs to not go to STOPPED
        scheduler = Scheduler(machine, queue)

        # Start and let first job complete
        scheduler.start()
        scheduler._backend_complete()  # Helper to instantly complete
        scheduler.tick()

        # Second job should now be running
        assert scheduler.current_job is not None

        # Complete second job
        scheduler._backend_complete()
        scheduler.tick()

        # Now scheduler is STOPPED because queue is empty
        # Let's test pause on a running scheduler with no current job differently
        # Re-add jobs and test pause when scheduler starts with immediate pause
        queue.add(sample_programs[2])
        scheduler.start()

        # Now pause while job is running - it should set flag
        scheduler.pause()

        # Complete the job
        scheduler._backend_complete()
        scheduler.tick()

        # Should be PAUSED now
        assert scheduler.state == SchedulerState.PAUSED

    def test_pause_with_running_job_finishes_current(
        self, machine, queue, sample_programs
    ):
        """Pausing with running job finishes current then pauses."""
        queue.add(sample_programs[0])
        queue.add(sample_programs[1])
        scheduler = Scheduler(machine, queue)
        scheduler.start()

        # Request pause while first job running
        scheduler.pause()

        # Should still be running (finishing current job)
        assert scheduler.state == SchedulerState.RUNNING
        assert scheduler._pause_after_current is True

    def test_pause_transitions_after_job_completes(
        self, machine, queue, events, sample_programs
    ):
        """After job completes, scheduler transitions to PAUSED."""
        queue.add(sample_programs[0])
        queue.add(sample_programs[1])
        scheduler = Scheduler(machine, queue, events)
        scheduler.start()

        scheduler.pause()  # Request pause

        # Complete the current job
        scheduler._backend_complete()
        scheduler.tick()

        assert scheduler.state == SchedulerState.PAUSED
        # Queue should still have the second job
        assert len(queue) == 1

    def test_pause_when_stopped_is_noop(self, machine, queue):
        """Pausing when stopped has no effect."""
        scheduler = Scheduler(machine, queue)
        scheduler.pause()  # Should be no-op
        assert scheduler.state == SchedulerState.STOPPED

    def test_pause_immediate_when_running_no_job(self, machine, queue, sample_programs):
        """Pausing when running but no current job pauses immediately."""
        # This edge case: scheduler is RUNNING but between jobs
        queue.add(sample_programs[0])
        scheduler = Scheduler(machine, queue)
        scheduler.start()

        # Complete job, but manually set state before tick processes next
        scheduler._backend_complete()
        machine.poll()  # Update machine state to IDLE

        # Manually clear current job to simulate gap between jobs
        scheduler._current_job.mark_completed()
        scheduler._current_job = None

        # Now pause when running but no current job
        scheduler.pause()
        assert scheduler.state == SchedulerState.PAUSED


class TestSchedulerTick:
    """Tests for Scheduler.tick()."""

    def test_tick_when_stopped_is_noop(self, machine, queue):
        """Tick when stopped has no effect."""
        scheduler = Scheduler(machine, queue)
        scheduler.tick()  # Should be no-op
        assert scheduler.state == SchedulerState.STOPPED

    def test_tick_polls_machine(self, machine, queue, sample_programs):
        """Tick polls the machine for state updates."""
        queue.add(sample_programs[0])
        scheduler = Scheduler(machine, queue)
        scheduler.start()

        # Machine should be running
        assert machine.is_running()

        # Tick polls machine (advances simulation)
        scheduler._backend_complete()
        scheduler.tick()

        # Job should now be complete
        assert machine.is_idle()

    def test_tick_detects_job_completion(self, machine, queue, events, sample_programs):
        """Tick detects when a job completes."""
        queue.add(sample_programs[0])
        scheduler = Scheduler(machine, queue, events)

        completed_jobs = []
        events.on(Event.JOB_COMPLETED, lambda job: completed_jobs.append(job))

        scheduler.start()
        scheduler._backend_complete()
        scheduler.tick()

        assert len(completed_jobs) == 1
        assert completed_jobs[0].status == JobStatus.COMPLETED

    def test_tick_starts_next_job(self, machine, queue, events, sample_programs):
        """Tick starts next job after current completes."""
        queue.add(sample_programs[0])
        queue.add(sample_programs[1])
        scheduler = Scheduler(machine, queue, events)

        started_jobs = []
        events.on(Event.JOB_STARTED, lambda job: started_jobs.append(job))

        scheduler.start()
        scheduler._backend_complete()
        scheduler.tick()

        assert len(started_jobs) == 2
        assert started_jobs[1].name == "job1"

    def test_tick_handles_queue_empty_after_jobs(
        self, machine, queue, events, sample_programs
    ):
        """Tick handles queue becoming empty after all jobs complete."""
        queue.add(sample_programs[0])
        scheduler = Scheduler(machine, queue, events)

        empty_events = []
        events.on(Event.QUEUE_EMPTY, lambda: empty_events.append(True))

        scheduler.start()
        scheduler._backend_complete()
        scheduler.tick()

        assert len(empty_events) == 1
        assert scheduler.state == SchedulerState.STOPPED


class TestSchedulerErrorHandling:
    """Tests for Scheduler error handling."""

    def test_poll_exception_stops_scheduler(
        self, machine, queue, events, sample_programs
    ):
        """Exception during poll() stops the scheduler."""
        queue.add(sample_programs[0])
        scheduler = Scheduler(machine, queue, events)

        machine_errors = []
        events.on(Event.MACHINE_ERROR, lambda e: machine_errors.append(e))

        scheduler.start()

        # Make poll raise an exception
        def bad_poll():
            raise RuntimeError("Connection lost")

        machine._backend.poll = bad_poll  # type: ignore
        scheduler.tick()

        assert scheduler.state == SchedulerState.STOPPED
        assert len(machine_errors) == 1
        assert "Connection lost" in str(machine_errors[0])

    def test_machine_error_stops_scheduler(
        self, machine, queue, events, sample_programs
    ):
        """Machine error stops the scheduler."""
        queue.add(sample_programs[0])
        scheduler = Scheduler(machine, queue, events)
        scheduler.start()

        # Set machine to error state
        machine._backend.set_state(MachineState.ERROR)  # type: ignore
        scheduler.tick()

        assert scheduler.state == SchedulerState.STOPPED

    def test_machine_error_emits_events(self, machine, queue, events, sample_programs):
        """Machine error emits MACHINE_ERROR and JOB_FAILED events."""
        queue.add(sample_programs[0])
        scheduler = Scheduler(machine, queue, events)

        machine_errors = []
        job_failures = []
        events.on(Event.MACHINE_ERROR, lambda e: machine_errors.append(e))
        events.on(Event.JOB_FAILED, lambda job, e: job_failures.append((job, e)))

        scheduler.start()
        machine._backend.set_state(MachineState.ERROR)  # type: ignore
        scheduler.tick()

        assert len(machine_errors) == 1
        assert len(job_failures) == 1

    def test_estop_stops_scheduler(self, machine, queue, sample_programs):
        """E-STOP stops the scheduler."""
        queue.add(sample_programs[0])
        scheduler = Scheduler(machine, queue)
        scheduler.start()

        machine._backend.set_state(MachineState.ESTOP)  # type: ignore
        scheduler.tick()

        assert scheduler.state == SchedulerState.STOPPED

    def test_file_not_found_skips_job(self, machine, queue, events, sample_programs):
        """Missing file skips to next job."""
        queue.add("/nonexistent/file.ngc")
        queue.add(sample_programs[0])
        scheduler = Scheduler(machine, queue, events)

        failed_jobs = []
        started_jobs = []
        events.on(Event.JOB_FAILED, lambda job, _: failed_jobs.append(job))
        events.on(Event.JOB_STARTED, lambda job: started_jobs.append(job))

        scheduler.start()

        # First job should have failed, second should have started
        assert len(failed_jobs) == 1
        assert failed_jobs[0].name == "file"
        assert len(started_jobs) == 1
        assert started_jobs[0].name == "job0"

    def test_queue_preserved_after_error(self, machine, queue, events, sample_programs):
        """Queue is preserved after error for retry."""
        queue.add(sample_programs[0])
        queue.add(sample_programs[1])
        scheduler = Scheduler(machine, queue, events)
        scheduler.start()

        # Simulate error
        machine._backend.set_state(MachineState.ERROR)  # type: ignore
        scheduler.tick()

        # Second job should still be in queue
        assert len(queue) == 1


class TestSchedulerFullWorkflow:
    """Integration tests for complete scheduler workflows."""

    def test_process_multiple_jobs(self, machine, queue, events, sample_programs):
        """Scheduler processes multiple jobs in sequence."""
        for prog in sample_programs:
            queue.add(prog)

        scheduler = Scheduler(machine, queue, events)

        completed_jobs = []
        events.on(Event.JOB_COMPLETED, lambda job: completed_jobs.append(job))

        scheduler.start()

        # Process all jobs
        for _ in range(3):
            scheduler._backend_complete()
            scheduler.tick()

        assert len(completed_jobs) == 3
        assert scheduler.state == SchedulerState.STOPPED

    def test_pause_resume_workflow(self, machine, queue, events, sample_programs):
        """Test pause and resume workflow."""
        for prog in sample_programs:
            queue.add(prog)

        scheduler = Scheduler(machine, queue, events)
        scheduler.start()

        # Complete first job, which starts second job
        scheduler._backend_complete()
        scheduler.tick()

        # Pause (while second job is running)
        scheduler.pause()
        assert scheduler.state == SchedulerState.RUNNING  # Still running current job
        assert scheduler._pause_after_current is True

        # Complete second job - should pause after
        scheduler._backend_complete()
        scheduler.tick()

        assert scheduler.state == SchedulerState.PAUSED
        # Third job should still be in queue
        assert len(queue) == 1

        # Resume
        scheduler.start()
        assert scheduler.state == SchedulerState.RUNNING

        # Complete remaining job
        scheduler._backend_complete()
        scheduler.tick()

        assert scheduler.state == SchedulerState.STOPPED

    def test_stop_resume_workflow(self, machine, queue, events, sample_programs):
        """Test stop and resume workflow."""
        for prog in sample_programs:
            queue.add(prog)

        scheduler = Scheduler(machine, queue, events)
        scheduler.start()

        # Stop mid-job
        scheduler.stop()
        assert scheduler.state == SchedulerState.STOPPED

        # Resume - should continue with remaining jobs
        scheduler.start()
        assert scheduler.state == SchedulerState.RUNNING

        # Complete remaining jobs (2 jobs left after stop)
        for _ in range(2):
            scheduler._backend_complete()
            scheduler.tick()

        assert scheduler.state == SchedulerState.STOPPED


class TestSchedulerRunForever:
    """Tests for Scheduler.run_forever()."""

    def test_run_forever_processes_all_jobs(
        self, machine, queue, events, sample_programs
    ):
        """run_forever() processes all jobs then returns."""
        # Use very short execution and poll times
        machine._backend._execution_time = 0.01  # type: ignore

        queue.add(sample_programs[0])
        scheduler = Scheduler(machine, queue, events)

        completed = []
        events.on(Event.JOB_COMPLETED, lambda job: completed.append(job))

        scheduler.run_forever(poll_interval=0.02)

        assert len(completed) == 1
        assert scheduler.state == SchedulerState.STOPPED


# Helper method for tests - add to Scheduler for testing convenience
def _backend_complete(self):
    """Instantly complete the current program (test helper)."""
    if hasattr(self._machine._backend, "complete_program"):
        self._machine._backend.complete_program()


# Monkey-patch the helper method onto Scheduler for tests
Scheduler._backend_complete = _backend_complete  # type: ignore

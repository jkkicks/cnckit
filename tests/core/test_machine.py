"""Tests for the Machine class and related components."""

import time
from pathlib import Path

import pytest

from cnckit.core.machine import (
    Machine,
    MachineBackend,
    MachineState,
    Position,
    SimulatedBackend,
)


class TestMachineState:
    """Tests for MachineState enum."""

    def test_state_values(self):
        """All state values exist with correct strings."""
        assert MachineState.DISCONNECTED.value == "disconnected"
        assert MachineState.IDLE.value == "idle"
        assert MachineState.RUNNING.value == "running"
        assert MachineState.PAUSED.value == "paused"
        assert MachineState.ERROR.value == "error"
        assert MachineState.ESTOP.value == "estop"

    def test_all_states_exist(self):
        """All expected states are defined."""
        states = [s.value for s in MachineState]
        assert "disconnected" in states
        assert "idle" in states
        assert "running" in states
        assert "paused" in states
        assert "error" in states
        assert "estop" in states


class TestPosition:
    """Tests for Position dataclass."""

    def test_default_position(self):
        """Position defaults to origin."""
        pos = Position()
        assert pos.x == 0.0
        assert pos.y == 0.0
        assert pos.z == 0.0
        assert pos.a is None
        assert pos.b is None
        assert pos.c is None

    def test_position_with_xyz(self):
        """Position can be created with XYZ values."""
        pos = Position(x=10.5, y=20.0, z=-5.0)
        assert pos.x == 10.5
        assert pos.y == 20.0
        assert pos.z == -5.0

    def test_position_with_rotary_axes(self):
        """Position can include rotary axes."""
        pos = Position(x=0, y=0, z=0, a=45.0, b=90.0, c=180.0)
        assert pos.a == 45.0
        assert pos.b == 90.0
        assert pos.c == 180.0

    def test_position_equality(self):
        """Positions with same values are equal."""
        pos1 = Position(x=1.0, y=2.0, z=3.0)
        pos2 = Position(x=1.0, y=2.0, z=3.0)
        assert pos1 == pos2


class TestSimulatedBackend:
    """Tests for SimulatedBackend class."""

    def test_initial_state_is_idle(self):
        """Backend starts in IDLE state."""
        backend = SimulatedBackend()
        assert backend.state == MachineState.IDLE

    def test_initial_position_is_origin(self):
        """Backend starts at origin."""
        backend = SimulatedBackend()
        assert backend.position == Position()

    def test_initial_tool_is_zero(self):
        """Backend starts with tool 0."""
        backend = SimulatedBackend()
        assert backend.tool == 0

    def test_initial_program_is_none(self):
        """Backend starts with no program loaded."""
        backend = SimulatedBackend()
        assert backend.current_program is None

    def test_initial_progress_is_zero(self):
        """Backend starts with 0 progress."""
        backend = SimulatedBackend()
        assert backend.progress == 0.0


class TestSimulatedBackendLoadProgram:
    """Tests for SimulatedBackend.load_program()."""

    def test_load_program_sets_current_program(self, tmp_path):
        """load_program() sets the current program path."""
        backend = SimulatedBackend()
        program = tmp_path / "test.ngc"
        program.write_text("G0 X0 Y0")

        backend.load_program(str(program))
        assert backend.current_program == str(program)

    def test_load_program_resets_progress(self, tmp_path):
        """load_program() resets progress to 0."""
        backend = SimulatedBackend()
        program = tmp_path / "test.ngc"
        program.write_text("G0 X0 Y0")

        backend.load_program(str(program))
        assert backend.progress == 0.0

    def test_load_program_requires_idle_state(self, tmp_path):
        """load_program() fails if machine is not idle."""
        backend = SimulatedBackend()
        program = tmp_path / "test.ngc"
        program.write_text("G0 X0 Y0")
        backend.load_program(str(program))
        backend.cycle_start()

        program2 = tmp_path / "test2.ngc"
        program2.write_text("G0 X1 Y1")

        with pytest.raises(RuntimeError, match="must be idle"):
            backend.load_program(str(program2))

    def test_load_program_file_not_found(self):
        """load_program() raises FileNotFoundError for missing files."""
        backend = SimulatedBackend()

        with pytest.raises(FileNotFoundError, match="not found"):
            backend.load_program("/nonexistent/path/file.ngc")


class TestSimulatedBackendExecution:
    """Tests for SimulatedBackend program execution."""

    def test_cycle_start_requires_program(self):
        """cycle_start() fails if no program is loaded."""
        backend = SimulatedBackend()

        with pytest.raises(RuntimeError, match="No program loaded"):
            backend.cycle_start()

    def test_cycle_start_changes_state_to_running(self, tmp_path):
        """cycle_start() changes state to RUNNING."""
        backend = SimulatedBackend()
        program = tmp_path / "test.ngc"
        program.write_text("G0 X0 Y0")
        backend.load_program(str(program))

        backend.cycle_start()
        assert backend.state == MachineState.RUNNING

    def test_cycle_start_requires_idle_or_paused(self, tmp_path):
        """cycle_start() only works from IDLE or PAUSED state."""
        backend = SimulatedBackend()
        program = tmp_path / "test.ngc"
        program.write_text("G0 X0 Y0")
        backend.load_program(str(program))
        backend.set_state(MachineState.ERROR)

        with pytest.raises(RuntimeError, match="must be idle or paused"):
            backend.cycle_start()

    def test_stop_pauses_execution(self, tmp_path):
        """stop() pauses running program."""
        backend = SimulatedBackend()
        program = tmp_path / "test.ngc"
        program.write_text("G0 X0 Y0")
        backend.load_program(str(program))
        backend.cycle_start()

        backend.stop()
        assert backend.state == MachineState.PAUSED

    def test_resume_from_paused(self, tmp_path):
        """cycle_start() resumes from paused state."""
        backend = SimulatedBackend()
        program = tmp_path / "test.ngc"
        program.write_text("G0 X0 Y0")
        backend.load_program(str(program))
        backend.cycle_start()
        backend.stop()
        assert backend.state == MachineState.PAUSED

        backend.cycle_start()
        assert backend.state == MachineState.RUNNING

    def test_abort_stops_and_clears(self, tmp_path):
        """abort() stops program and clears state."""
        backend = SimulatedBackend()
        program = tmp_path / "test.ngc"
        program.write_text("G0 X0 Y0")
        backend.load_program(str(program))
        backend.cycle_start()

        backend.abort()
        assert backend.state == MachineState.IDLE
        assert backend.current_program is None
        assert backend.progress == 0.0


class TestSimulatedBackendPoll:
    """Tests for SimulatedBackend.poll() simulation timing."""

    def test_poll_advances_progress(self, tmp_path):
        """poll() advances progress over time."""
        backend = SimulatedBackend(execution_time=0.1)
        program = tmp_path / "test.ngc"
        program.write_text("G0 X0 Y0")
        backend.load_program(str(program))
        backend.cycle_start()

        # Wait a bit and poll
        time.sleep(0.05)
        backend.poll()

        assert backend.progress > 0.0
        assert backend.progress < 1.0

    def test_poll_completes_program(self, tmp_path):
        """poll() completes program after execution time."""
        backend = SimulatedBackend(execution_time=0.05)
        program = tmp_path / "test.ngc"
        program.write_text("G0 X0 Y0")
        backend.load_program(str(program))
        backend.cycle_start()

        # Wait for completion
        time.sleep(0.1)
        backend.poll()

        assert backend.progress == 1.0
        assert backend.state == MachineState.IDLE

    def test_poll_updates_position(self, tmp_path):
        """poll() updates simulated position."""
        backend = SimulatedBackend(execution_time=0.1)
        program = tmp_path / "test.ngc"
        program.write_text("G0 X0 Y0")
        backend.load_program(str(program))
        backend.cycle_start()

        initial_pos = backend.position

        time.sleep(0.05)
        backend.poll()

        # Position should have changed
        assert backend.position.x >= initial_pos.x

    def test_poll_noop_when_not_running(self, tmp_path):
        """poll() does nothing when not running."""
        backend = SimulatedBackend()
        program = tmp_path / "test.ngc"
        program.write_text("G0 X0 Y0")
        backend.load_program(str(program))

        backend.poll()
        assert backend.progress == 0.0
        assert backend.state == MachineState.IDLE


class TestSimulatedBackendTestHelpers:
    """Tests for SimulatedBackend test helper methods."""

    def test_set_state(self):
        """set_state() allows manually setting state."""
        backend = SimulatedBackend()
        backend.set_state(MachineState.ERROR)
        assert backend.state == MachineState.ERROR

    def test_set_position(self):
        """set_position() allows manually setting position."""
        backend = SimulatedBackend()
        new_pos = Position(x=100, y=200, z=50)
        backend.set_position(new_pos)
        assert backend.position == new_pos

    def test_set_tool(self):
        """set_tool() allows manually setting tool number."""
        backend = SimulatedBackend()
        backend.set_tool(5)
        assert backend.tool == 5

    def test_complete_program(self, tmp_path):
        """complete_program() instantly finishes running program."""
        backend = SimulatedBackend(execution_time=100)  # Long execution
        program = tmp_path / "test.ngc"
        program.write_text("G0 X0 Y0")
        backend.load_program(str(program))
        backend.cycle_start()

        backend.complete_program()
        assert backend.progress == 1.0
        assert backend.state == MachineState.IDLE


class TestMachine:
    """Tests for Machine class."""

    def test_machine_simulate_true(self):
        """Machine(simulate=True) creates simulated machine."""
        machine = Machine(simulate=True)
        assert machine.simulate is True
        assert machine.state == MachineState.IDLE

    def test_machine_simulate_false_without_linuxcnc(self):
        """Machine(simulate=False) raises if LinuxCNC unavailable."""
        with pytest.raises(RuntimeError, match="LinuxCNC"):
            Machine(simulate=False)

    def test_machine_state_property(self):
        """Machine.state returns backend state."""
        machine = Machine(simulate=True)
        assert machine.state == MachineState.IDLE

    def test_machine_position_property(self):
        """Machine.position returns backend position."""
        machine = Machine(simulate=True)
        assert machine.position == Position()

    def test_machine_tool_property(self):
        """Machine.tool returns backend tool."""
        machine = Machine(simulate=True)
        assert machine.tool == 0

    def test_machine_current_program_property(self):
        """Machine.current_program returns backend program."""
        machine = Machine(simulate=True)
        assert machine.current_program is None

    def test_machine_progress_property(self):
        """Machine.progress returns backend progress."""
        machine = Machine(simulate=True)
        assert machine.progress == 0.0


class TestMachineOperations:
    """Tests for Machine operation methods."""

    def test_load_program(self, tmp_path):
        """Machine.load_program() loads program via backend."""
        machine = Machine(simulate=True)
        program = tmp_path / "test.ngc"
        program.write_text("G0 X0 Y0")

        machine.load_program(str(program))
        assert machine.current_program == str(program)

    def test_cycle_start(self, tmp_path):
        """Machine.cycle_start() starts program via backend."""
        machine = Machine(simulate=True)
        program = tmp_path / "test.ngc"
        program.write_text("G0 X0 Y0")
        machine.load_program(str(program))

        machine.cycle_start()
        assert machine.state == MachineState.RUNNING

    def test_stop(self, tmp_path):
        """Machine.stop() stops program via backend."""
        machine = Machine(simulate=True)
        program = tmp_path / "test.ngc"
        program.write_text("G0 X0 Y0")
        machine.load_program(str(program))
        machine.cycle_start()

        machine.stop()
        assert machine.state == MachineState.PAUSED

    def test_abort(self, tmp_path):
        """Machine.abort() aborts program via backend."""
        machine = Machine(simulate=True)
        program = tmp_path / "test.ngc"
        program.write_text("G0 X0 Y0")
        machine.load_program(str(program))
        machine.cycle_start()

        machine.abort()
        assert machine.state == MachineState.IDLE
        assert machine.current_program is None

    def test_poll(self, tmp_path):
        """Machine.poll() calls backend poll."""
        machine = Machine(simulate=True)
        program = tmp_path / "test.ngc"
        program.write_text("G0 X0 Y0")
        machine.load_program(str(program))
        machine.cycle_start()

        # Access backend to set short execution time
        machine._backend._execution_time = 0.05  # type: ignore

        time.sleep(0.1)
        machine.poll()
        assert machine.state == MachineState.IDLE


class TestMachineConvenienceMethods:
    """Tests for Machine convenience methods."""

    def test_is_idle_when_idle(self):
        """is_idle() returns True when idle."""
        machine = Machine(simulate=True)
        assert machine.is_idle() is True

    def test_is_idle_when_running(self, tmp_path):
        """is_idle() returns False when running."""
        machine = Machine(simulate=True)
        program = tmp_path / "test.ngc"
        program.write_text("G0 X0 Y0")
        machine.load_program(str(program))
        machine.cycle_start()

        assert machine.is_idle() is False

    def test_is_running_when_running(self, tmp_path):
        """is_running() returns True when running."""
        machine = Machine(simulate=True)
        program = tmp_path / "test.ngc"
        program.write_text("G0 X0 Y0")
        machine.load_program(str(program))
        machine.cycle_start()

        assert machine.is_running() is True

    def test_is_running_when_idle(self):
        """is_running() returns False when idle."""
        machine = Machine(simulate=True)
        assert machine.is_running() is False

    def test_is_ready_when_idle(self):
        """is_ready() returns True when idle."""
        machine = Machine(simulate=True)
        assert machine.is_ready() is True

    def test_is_ready_when_paused(self, tmp_path):
        """is_ready() returns True when paused."""
        machine = Machine(simulate=True)
        program = tmp_path / "test.ngc"
        program.write_text("G0 X0 Y0")
        machine.load_program(str(program))
        machine.cycle_start()
        machine.stop()

        assert machine.is_ready() is True

    def test_is_ready_when_running(self, tmp_path):
        """is_ready() returns False when running."""
        machine = Machine(simulate=True)
        program = tmp_path / "test.ngc"
        program.write_text("G0 X0 Y0")
        machine.load_program(str(program))
        machine.cycle_start()

        assert machine.is_ready() is False


class TestMachineBackendProtocol:
    """Tests for MachineBackend protocol."""

    def test_simulated_backend_implements_protocol(self):
        """SimulatedBackend implements MachineBackend protocol."""
        backend = SimulatedBackend()
        assert isinstance(backend, MachineBackend)


class TestMachineFullWorkflow:
    """Integration tests for complete machine workflows."""

    def test_load_start_complete_workflow(self, tmp_path):
        """Test complete workflow: load → start → poll → complete."""
        machine = Machine(simulate=True)
        machine._backend._execution_time = 0.05  # type: ignore

        program = tmp_path / "test.ngc"
        program.write_text("G0 X0 Y0\nG1 X10 Y10 F100")

        # Load program
        machine.load_program(str(program))
        assert machine.current_program == str(program)
        assert machine.state == MachineState.IDLE

        # Start execution
        machine.cycle_start()
        assert machine.state == MachineState.RUNNING

        # Poll until complete
        time.sleep(0.1)
        machine.poll()

        assert machine.state == MachineState.IDLE
        assert machine.progress == 1.0

    def test_load_start_pause_resume_workflow(self, tmp_path):
        """Test workflow with pause/resume."""
        machine = Machine(simulate=True)
        machine._backend._execution_time = 1.0  # type: ignore

        program = tmp_path / "test.ngc"
        program.write_text("G0 X0 Y0")

        machine.load_program(str(program))
        machine.cycle_start()
        assert machine.state == MachineState.RUNNING

        # Pause
        machine.stop()
        assert machine.state == MachineState.PAUSED

        # Resume
        machine.cycle_start()
        assert machine.state == MachineState.RUNNING

    def test_abort_mid_program(self, tmp_path):
        """Test aborting during program execution."""
        machine = Machine(simulate=True)
        machine._backend._execution_time = 10.0  # type: ignore

        program = tmp_path / "test.ngc"
        program.write_text("G0 X0 Y0")

        machine.load_program(str(program))
        machine.cycle_start()

        # Let it run a bit
        time.sleep(0.05)
        machine.poll()
        assert machine.progress > 0.0

        # Abort
        machine.abort()
        assert machine.state == MachineState.IDLE
        assert machine.current_program is None
        assert machine.progress == 0.0

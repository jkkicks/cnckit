"""
Machine state abstraction over LinuxCNC's Python API.

This module provides a clean interface to LinuxCNC, hiding the complexity
of the underlying API and providing a consistent state model.
"""

import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Protocol, runtime_checkable


class MachineState(Enum):
    """Machine operational state."""

    DISCONNECTED = "disconnected"  # Not connected to controller
    IDLE = "idle"  # Connected, ready to run
    RUNNING = "running"  # Program executing
    PAUSED = "paused"  # Program paused mid-execution
    ERROR = "error"  # Error state, needs intervention
    ESTOP = "estop"  # Emergency stop activated


@dataclass
class Position:
    """
    Machine position in work coordinates.

    Attributes:
        x: X-axis position
        y: Y-axis position
        z: Z-axis position
        a: A-axis position (rotary, optional)
        b: B-axis position (rotary, optional)
        c: C-axis position (rotary, optional)
    """

    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    a: float | None = None
    b: float | None = None
    c: float | None = None


@runtime_checkable
class MachineBackend(Protocol):
    """
    Protocol defining the interface for machine backends.

    This allows swapping between LinuxCNC and simulated backends
    without changing the Machine class.
    """

    @property
    def state(self) -> MachineState:
        """Get current machine state."""
        ...

    @property
    def position(self) -> Position:
        """Get current machine position."""
        ...

    @property
    def tool(self) -> int:
        """Get current tool number."""
        ...

    @property
    def current_program(self) -> str | None:
        """Get path to currently loaded program."""
        ...

    @property
    def progress(self) -> float:
        """Get program progress (0.0 to 1.0)."""
        ...

    def load_program(self, path: str) -> None:
        """Load a G-code program."""
        ...

    def cycle_start(self) -> None:
        """Start program execution."""
        ...

    def stop(self) -> None:
        """Stop program execution (controlled stop)."""
        ...

    def abort(self) -> None:
        """Abort program execution (emergency stop)."""
        ...

    def poll(self) -> None:
        """Poll the backend to update state. Called by tick()."""
        ...


class SimulatedBackend:
    """
    Simulated machine backend for testing without hardware.

    Simulates program execution with configurable timing.
    Useful for testing, development, and demonstrations.
    """

    def __init__(self, execution_time: float = 5.0) -> None:
        """
        Initialize the simulated backend.

        Args:
            execution_time: Time in seconds to "execute" each program
        """
        self._state = MachineState.IDLE
        self._position = Position()
        self._tool = 0
        self._current_program: str | None = None
        self._progress = 0.0
        self._execution_time = execution_time

        # Timing for simulation
        self._start_time: float | None = None

    @property
    def state(self) -> MachineState:
        """Get current machine state."""
        return self._state

    @property
    def position(self) -> Position:
        """Get current machine position."""
        return self._position

    @property
    def tool(self) -> int:
        """Get current tool number."""
        return self._tool

    @property
    def current_program(self) -> str | None:
        """Get path to currently loaded program."""
        return self._current_program

    @property
    def progress(self) -> float:
        """Get program progress (0.0 to 1.0)."""
        return self._progress

    def load_program(self, path: str) -> None:
        """
        Load a G-code program.

        Args:
            path: Path to the G-code file

        Raises:
            RuntimeError: If machine is not in IDLE state
            FileNotFoundError: If the program file doesn't exist
        """
        if self._state != MachineState.IDLE:
            raise RuntimeError(
                f"Cannot load program in {self._state.value} state, must be idle"
            )

        # Verify file exists
        if not Path(path).exists():
            raise FileNotFoundError(f"Program file not found: {path}")

        self._current_program = path
        self._progress = 0.0

    def cycle_start(self) -> None:
        """
        Start program execution.

        Raises:
            RuntimeError: If no program is loaded or machine not idle
        """
        if self._current_program is None:
            raise RuntimeError("No program loaded")

        if self._state == MachineState.PAUSED:
            # Resume from pause
            self._state = MachineState.RUNNING
            return

        if self._state != MachineState.IDLE:
            raise RuntimeError(
                f"Cannot start in {self._state.value} state, must be idle or paused"
            )

        self._state = MachineState.RUNNING
        self._start_time = time.monotonic()
        self._progress = 0.0

    def stop(self) -> None:
        """Stop program execution (controlled stop)."""
        if self._state == MachineState.RUNNING:
            self._state = MachineState.PAUSED

    def abort(self) -> None:
        """Abort program execution (emergency stop)."""
        self._state = MachineState.IDLE
        self._current_program = None
        self._progress = 0.0
        self._start_time = None

    def poll(self) -> None:
        """
        Poll the backend to update state.

        For simulation, this advances the program progress based on elapsed time.
        """
        if self._state != MachineState.RUNNING:
            return

        if self._start_time is None:
            return

        elapsed = time.monotonic() - self._start_time
        self._progress = min(1.0, elapsed / self._execution_time)

        # Simulate position changes
        self._position = Position(
            x=self._progress * 100,
            y=self._progress * 50,
            z=0.0,
        )

        # Check if program completed
        if self._progress >= 1.0:
            self._state = MachineState.IDLE
            self._progress = 1.0

    # --- Simulation-specific methods ---

    def set_state(self, state: MachineState) -> None:
        """Set machine state (for testing)."""
        self._state = state

    def set_position(self, position: Position) -> None:
        """Set machine position (for testing)."""
        self._position = position

    def set_tool(self, tool: int) -> None:
        """Set current tool (for testing)."""
        self._tool = tool

    def complete_program(self) -> None:
        """Instantly complete the current program (for testing)."""
        if self._state == MachineState.RUNNING:
            self._progress = 1.0
            self._state = MachineState.IDLE


class LinuxCNCBackend:
    """
    LinuxCNC backend for controlling real CNC hardware.

    This backend communicates with LinuxCNC via its Python interface.
    Requires LinuxCNC to be installed and running.
    """

    def __init__(self) -> None:
        """
        Initialize the LinuxCNC backend.

        Raises:
            RuntimeError: If LinuxCNC is not available
        """
        # Try to import linuxcnc
        try:
            import linuxcnc  # noqa: PLC0415

            self._linuxcnc = linuxcnc
            self._stat = linuxcnc.stat()
            self._command = linuxcnc.command()
            self._error = linuxcnc.error_channel()
            self._stat.poll()
        except ImportError:
            raise RuntimeError(
                "LinuxCNC Python module not available. "
                "Use Machine(simulate=True) for testing without hardware."
            ) from None
        except Exception as e:
            raise RuntimeError(f"Failed to connect to LinuxCNC: {e}") from e

        self._current_program: str | None = None

    @property
    def state(self) -> MachineState:  # noqa: PLR0911
        """Get current machine state from LinuxCNC."""
        self._stat.poll()

        # Check for estop first
        if self._stat.estop:
            return MachineState.ESTOP

        # Check task state
        if self._stat.task_state == self._linuxcnc.STATE_ESTOP:
            return MachineState.ESTOP
        elif self._stat.task_state == self._linuxcnc.STATE_ESTOP_RESET:
            return MachineState.IDLE
        elif self._stat.task_state == self._linuxcnc.STATE_OFF:
            return MachineState.DISCONNECTED
        elif self._stat.task_state == self._linuxcnc.STATE_ON:
            # Check interpreter state for more detail
            if self._stat.interp_state == self._linuxcnc.INTERP_IDLE:
                return MachineState.IDLE
            elif self._stat.interp_state == self._linuxcnc.INTERP_READING:
                return MachineState.RUNNING
            elif self._stat.interp_state == self._linuxcnc.INTERP_PAUSED:
                return MachineState.PAUSED
            elif self._stat.interp_state == self._linuxcnc.INTERP_WAITING:
                return MachineState.RUNNING

        return MachineState.IDLE

    @property
    def position(self) -> Position:
        """Get current machine position from LinuxCNC."""
        self._stat.poll()
        pos = self._stat.actual_position
        return Position(
            x=pos[0],
            y=pos[1],
            z=pos[2],
            a=pos[3] if len(pos) > 3 else None,
            b=pos[4] if len(pos) > 4 else None,
            c=pos[5] if len(pos) > 5 else None,
        )

    @property
    def tool(self) -> int:
        """Get current tool number from LinuxCNC."""
        self._stat.poll()
        return int(self._stat.tool_in_spindle)

    @property
    def current_program(self) -> str | None:
        """Get path to currently loaded program."""
        return self._current_program

    @property
    def progress(self) -> float:
        """
        Get program progress (0.0 to 1.0).

        Note: LinuxCNC doesn't provide direct progress. This uses
        current line / total lines as an approximation.
        """
        self._stat.poll()
        if self._stat.file == "":
            return 0.0

        total_lines: int = (
            self._stat.line_count if hasattr(self._stat, "line_count") else 0
        )
        current_line: int = self._stat.current_line

        if total_lines <= 0:
            return 0.0

        return float(min(1.0, current_line / total_lines))

    def load_program(self, path: str) -> None:
        """
        Load a G-code program into LinuxCNC.

        Args:
            path: Path to the G-code file

        Raises:
            RuntimeError: If program cannot be loaded
            FileNotFoundError: If program file doesn't exist
        """
        if not Path(path).exists():
            raise FileNotFoundError(f"Program file not found: {path}")

        # Set to auto mode for program execution
        self._command.mode(self._linuxcnc.MODE_AUTO)
        self._command.wait_complete()

        # Load the program
        self._command.program_open(str(Path(path).absolute()))
        self._command.wait_complete()

        self._current_program = path

    def cycle_start(self) -> None:
        """Start or resume program execution."""
        self._stat.poll()

        if self._stat.interp_state == self._linuxcnc.INTERP_PAUSED:
            self._command.auto(self._linuxcnc.AUTO_RESUME)
        else:
            self._command.auto(self._linuxcnc.AUTO_RUN, 0)

    def stop(self) -> None:
        """Pause program execution."""
        self._command.auto(self._linuxcnc.AUTO_PAUSE)

    def abort(self) -> None:
        """Abort program execution."""
        self._command.abort()
        self._command.wait_complete()

    def poll(self) -> None:
        """Poll LinuxCNC to update state."""
        self._stat.poll()

        # Check error channel
        error = self._error.poll()
        if error:
            kind, text = error
            if kind in (
                self._linuxcnc.NML_ERROR,
                self._linuxcnc.OPERATOR_ERROR,
            ):
                raise RuntimeError(f"LinuxCNC error: {text}")


class Machine:
    """
    Abstraction over LinuxCNC's Python API.

    Provides a simplified interface for:
    - Querying machine state (idle, running, error)
    - Loading and executing G-code programs
    - Monitoring position and status

    Example:
        >>> # Simulation mode for testing
        >>> machine = Machine(simulate=True)
        >>> machine.state
        <MachineState.IDLE: 'idle'>

        >>> # Production mode (requires LinuxCNC)
        >>> machine = Machine()  # Raises if LinuxCNC unavailable
        >>> machine.load_program("part1.ngc")
        >>> machine.cycle_start()
    """

    def __init__(self, simulate: bool = False) -> None:
        """
        Initialize machine connection.

        Args:
            simulate: If True, use simulated backend. If False, connect
                     to real LinuxCNC (raises error if unavailable).

        Raises:
            RuntimeError: If simulate=False and LinuxCNC is not available
        """
        self._simulate = simulate

        if simulate:
            self._backend: MachineBackend = SimulatedBackend()
        else:
            self._backend = LinuxCNCBackend()

    @property
    def simulate(self) -> bool:
        """Check if machine is running in simulation mode."""
        return self._simulate

    @property
    def state(self) -> MachineState:
        """Get current machine state."""
        return self._backend.state

    @property
    def position(self) -> Position:
        """Get current machine position."""
        return self._backend.position

    @property
    def tool(self) -> int:
        """Get current tool number."""
        return self._backend.tool

    @property
    def current_program(self) -> str | None:
        """Get path to currently loaded program."""
        return self._backend.current_program

    @property
    def progress(self) -> float:
        """Get program progress (0.0 to 1.0)."""
        return self._backend.progress

    def load_program(self, path: str) -> None:
        """
        Load a G-code program.

        Args:
            path: Path to the G-code file

        Raises:
            RuntimeError: If machine is not in IDLE state
            FileNotFoundError: If program file doesn't exist
        """
        self._backend.load_program(path)

    def cycle_start(self) -> None:
        """
        Start or resume program execution.

        Raises:
            RuntimeError: If no program is loaded or machine not ready
        """
        self._backend.cycle_start()

    def stop(self) -> None:
        """Stop/pause program execution (controlled stop)."""
        self._backend.stop()

    def abort(self) -> None:
        """Abort program execution (emergency stop)."""
        self._backend.abort()

    def poll(self) -> None:
        """
        Poll the machine to update state.

        Call this periodically (e.g., in a tick loop) to update
        machine state and detect completion/errors.
        """
        self._backend.poll()

    # --- Convenience methods ---

    def is_idle(self) -> bool:
        """Check if machine is idle and ready for a new program."""
        return self.state == MachineState.IDLE

    def is_running(self) -> bool:
        """Check if machine is currently executing a program."""
        return self.state == MachineState.RUNNING

    def is_ready(self) -> bool:
        """Check if machine is ready to accept commands (idle or paused)."""
        return self.state in (MachineState.IDLE, MachineState.PAUSED)

"""Tests for the Machine class."""

import pytest

from cnckit.core.machine import Machine


class TestMachine:
    """Tests for Machine abstraction."""

    def test_machine_creation_raises_not_implemented(self):
        """Machine creation should raise NotImplementedError until Phase 1."""
        with pytest.raises(NotImplementedError):
            Machine()

    # === Tests to be enabled in Phase 1 ===
    #
    # def test_machine_initial_state_is_idle(self):
    #     """Machine should start in idle state."""
    #     machine = Machine()
    #     assert machine.state == "idle"
    #
    # def test_load_program(self, sample_gcode_file):
    #     """Machine can load a G-code program."""
    #     machine = Machine()
    #     machine.load_program(sample_gcode_file)
    #     assert machine.current_program == sample_gcode_file

"""
Machine state abstraction over LinuxCNC's Python API.

This module provides a clean interface to LinuxCNC, hiding the complexity
of the underlying API and providing a consistent state model.
"""


class Machine:
    """
    Abstraction over LinuxCNC's Python API.

    Provides a simplified interface for:
    - Querying machine state (idle, running, error)
    - Loading and executing G-code programs
    - Monitoring position and status

    Example:
        >>> machine = Machine()
        >>> machine.state
        'idle'
        >>> machine.load_program("part1.ngc")
        >>> machine.run()
    """

    def __init__(self) -> None:
        """Initialize machine connection."""
        raise NotImplementedError("Machine will be implemented in Phase 1")

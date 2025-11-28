"""
Pytest configuration and shared fixtures.
"""

import pytest


@pytest.fixture
def sample_gcode_content() -> str:
    """Sample G-code content for testing."""
    return """
G21 ; metric
G90 ; absolute positioning
G0 X0 Y0 Z10
G1 Z-1 F100
G1 X50 Y0 F200
G1 X50 Y50
G1 X0 Y50
G1 X0 Y0
G0 Z10
M30
""".strip()


@pytest.fixture
def sample_gcode_file(tmp_path, sample_gcode_content) -> str:
    """Create a temporary G-code file for testing."""
    gcode_file = tmp_path / "test_part.ngc"
    gcode_file.write_text(sample_gcode_content)
    return str(gcode_file)

"""
REST API integration using FastAPI.

Provides HTTP endpoints for remote monitoring and control.
Requires: pip install cnckit[api]
"""

from typing import Any


def create_app() -> Any:
    """
    Create a FastAPI application for cnckit.

    Returns:
        FastAPI application instance

    Raises:
        ImportError: If fastapi is not installed
    """
    try:
        import fastapi  # noqa: F401
    except ImportError:
        raise ImportError(
            "FastAPI is required for the REST API integration. "
            "Install with: pip install cnckit[api]"
        )

    raise NotImplementedError("API integration will be implemented in Phase 2")

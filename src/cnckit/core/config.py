"""
Optional configuration loader supporting YAML and TOML.

This module provides lazy-loaded configuration parsing to avoid
requiring external dependencies unless actually used.
"""

from pathlib import Path
from typing import Any


class Config:
    """
    Configuration loader with lazy dependency imports.

    Supports YAML and TOML files. Dependencies are only imported
    when actually loading a file of that type.

    Example:
        >>> config = Config.from_file("cnckit.yaml")
        >>> config["queue"]["mode"]
        'priority'
    """

    def __init__(self, data: dict[str, Any]):
        """
        Initialize with configuration data.

        Args:
            data: Configuration dictionary
        """
        raise NotImplementedError("Config will be implemented in Phase 1")

    @classmethod
    def from_file(cls, path: str | Path) -> "Config":
        """
        Load configuration from a YAML or TOML file.

        Args:
            path: Path to configuration file

        Returns:
            Config instance with loaded data

        Raises:
            ImportError: If required parser is not installed
            FileNotFoundError: If file doesn't exist
        """
        raise NotImplementedError("Config will be implemented in Phase 1")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value with optional default."""
        raise NotImplementedError("Config will be implemented in Phase 1")

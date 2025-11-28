"""
Configuration loader with defaults and YAML override support.

This module provides configuration management where all settings have
sensible defaults, and users can override only what they need via YAML.
"""

import copy
from pathlib import Path
from typing import Any

# Default configuration - all settings have values here
DEFAULTS: dict[str, Any] = {
    "machine": {
        "simulate": False,
        "poll_interval": 1.0,
    },
    "queue": {
        "mode": "fifo",  # fifo, lifo, priority
    },
    "scheduler": {
        "auto_start": False,
    },
}


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """
    Deep merge override into base, returning a new dict.

    Values in override take precedence. Nested dicts are merged recursively.
    """
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


class Config:
    """
    Configuration manager with defaults and file-based overrides.

    All settings have sensible defaults. Load a YAML file to override
    only the settings you want to change.

    Example:
        >>> config = Config()  # All defaults
        >>> config.get("machine.simulate")
        False

        >>> config = Config.from_file("config.yml")  # With overrides
        >>> config.get("machine.simulate")
        True

        >>> config.get("nonexistent.key", "fallback")
        'fallback'
    """

    def __init__(self, data: dict[str, Any] | None = None) -> None:
        """
        Initialize config with optional override data.

        Args:
            data: Override data to merge with defaults. If None, only defaults are used.
        """
        if data is None:
            self._data = copy.deepcopy(DEFAULTS)
        else:
            self._data = _deep_merge(copy.deepcopy(DEFAULTS), data)

    @classmethod
    def from_file(cls, path: str | Path) -> "Config":
        """
        Load configuration from a YAML file, merged with defaults.

        Args:
            path: Path to YAML configuration file

        Returns:
            Config instance with defaults + file overrides

        Raises:
            FileNotFoundError: If file doesn't exist
            ImportError: If PyYAML is not installed
        """
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")

        # Lazy import - only require PyYAML when actually loading a file
        try:
            import yaml  # type: ignore[import-untyped]  # noqa: PLC0415
        except ImportError:
            raise ImportError(
                "PyYAML is required to load configuration files. "
                "Install with: pip install pyyaml"
            ) from None

        with path.open() as f:
            file_data = yaml.safe_load(f)

        # Handle empty files (yaml.safe_load returns None)
        if file_data is None:
            file_data = {}

        return cls(file_data)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.

        Args:
            key: Dot-separated key path (e.g., "machine.simulate")
            default: Value to return if key doesn't exist

        Returns:
            The configuration value, or default if not found

        Example:
            >>> config.get("machine.simulate")
            False
            >>> config.get("machine.poll_interval")
            1.0
            >>> config.get("unknown.key", "fallback")
            'fallback'
        """
        keys = key.split(".")
        value: Any = self._data

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def __getitem__(self, key: str) -> Any:
        """
        Get a top-level configuration section.

        Args:
            key: Top-level key (e.g., "machine")

        Returns:
            The configuration section dict

        Raises:
            KeyError: If key doesn't exist
        """
        return self._data[key]

    def __contains__(self, key: str) -> bool:
        """Check if a top-level key exists."""
        return key in self._data

    def to_dict(self) -> dict[str, Any]:
        """Return the full configuration as a dictionary (deep copy)."""
        return copy.deepcopy(self._data)

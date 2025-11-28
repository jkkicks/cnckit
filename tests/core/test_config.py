"""Tests for the Config class."""

import pytest

from cnckit.core.config import DEFAULTS, Config, _deep_merge


class TestDeepMerge:
    """Tests for the _deep_merge helper function."""

    def test_empty_override(self):
        """Empty override returns base unchanged."""
        base = {"a": 1, "b": {"c": 2}}
        result = _deep_merge(base, {})
        assert result == base

    def test_simple_override(self):
        """Simple values are overridden."""
        base = {"a": 1, "b": 2}
        override = {"b": 3}
        result = _deep_merge(base, override)
        assert result == {"a": 1, "b": 3}

    def test_nested_override(self):
        """Nested dicts are merged recursively."""
        base = {"a": {"b": 1, "c": 2}}
        override = {"a": {"c": 3}}
        result = _deep_merge(base, override)
        assert result == {"a": {"b": 1, "c": 3}}

    def test_new_keys_added(self):
        """New keys in override are added."""
        base = {"a": 1}
        override = {"b": 2}
        result = _deep_merge(base, override)
        assert result == {"a": 1, "b": 2}

    def test_does_not_mutate_base(self):
        """Original base dict is not modified."""
        base = {"a": {"b": 1}}
        override = {"a": {"b": 2}}
        _deep_merge(base, override)
        assert base == {"a": {"b": 1}}


class TestConfigDefaults:
    """Tests for Config default values."""

    def test_defaults_exist(self):
        """DEFAULTS contains expected top-level keys."""
        assert "machine" in DEFAULTS
        assert "queue" in DEFAULTS
        assert "scheduler" in DEFAULTS

    def test_config_without_data_uses_defaults(self):
        """Config() with no args uses all defaults."""
        config = Config()
        assert config.get("machine.simulate") is False
        assert config.get("machine.poll_interval") == 1.0
        assert config.get("queue.mode") == "fifo"
        assert config.get("scheduler.auto_start") is False

    def test_config_with_empty_dict_uses_defaults(self):
        """Config({}) uses all defaults."""
        config = Config({})
        assert config.get("machine.simulate") is False


class TestConfigOverrides:
    """Tests for Config override behavior."""

    def test_partial_override(self):
        """Overriding one value preserves other defaults."""
        config = Config({"machine": {"simulate": True}})
        assert config.get("machine.simulate") is True
        assert config.get("machine.poll_interval") == 1.0  # Default preserved

    def test_full_section_override(self):
        """Can override entire section while preserving others."""
        config = Config({"queue": {"mode": "priority"}})
        assert config.get("queue.mode") == "priority"
        assert config.get("machine.simulate") is False  # Other section preserved


class TestConfigGet:
    """Tests for Config.get() method."""

    def test_dot_notation_single_level(self):
        """Single-level key access works."""
        config = Config({"machine": {"simulate": True}})
        # Note: "machine" returns the dict, need dot notation for nested
        assert config.get("machine.simulate") is True

    def test_dot_notation_nested(self):
        """Nested dot notation works."""
        config = Config()
        assert config.get("machine.poll_interval") == 1.0

    def test_missing_key_returns_default(self):
        """Missing key returns provided default."""
        config = Config()
        assert config.get("nonexistent.key", "fallback") == "fallback"

    def test_missing_key_returns_none_by_default(self):
        """Missing key returns None if no default provided."""
        config = Config()
        assert config.get("nonexistent.key") is None

    def test_partial_path_missing(self):
        """Partial path missing returns default."""
        config = Config()
        assert config.get("machine.nonexistent.deep", "nope") == "nope"


class TestConfigGetitem:
    """Tests for Config[] access."""

    def test_getitem_returns_section(self):
        """config['key'] returns the section dict."""
        config = Config()
        machine = config["machine"]
        assert isinstance(machine, dict)
        assert machine["simulate"] is False

    def test_getitem_missing_raises(self):
        """config['missing'] raises KeyError."""
        config = Config()
        with pytest.raises(KeyError):
            _ = config["nonexistent"]


class TestConfigContains:
    """Tests for 'in' operator."""

    def test_contains_existing_key(self):
        """'machine' in config returns True."""
        config = Config()
        assert "machine" in config

    def test_contains_missing_key(self):
        """'nonexistent' in config returns False."""
        config = Config()
        assert "nonexistent" not in config


class TestConfigToDict:
    """Tests for Config.to_dict() method."""

    def test_to_dict_returns_copy(self):
        """to_dict() returns a copy, not the internal dict."""
        config = Config()
        d = config.to_dict()
        d["machine"]["simulate"] = True
        # Original should be unchanged
        assert config.get("machine.simulate") is False


class TestConfigFromFile:
    """Tests for Config.from_file() method."""

    def test_load_yaml_file(self, tmp_path):
        """Can load a YAML config file."""
        config_file = tmp_path / "config.yml"
        config_file.write_text("machine:\n  simulate: true\n")

        config = Config.from_file(config_file)
        assert config.get("machine.simulate") is True
        assert config.get("machine.poll_interval") == 1.0  # Default preserved

    def test_load_empty_yaml_file(self, tmp_path):
        """Empty YAML file uses all defaults."""
        config_file = tmp_path / "config.yml"
        config_file.write_text("")

        config = Config.from_file(config_file)
        assert config.get("machine.simulate") is False

    def test_load_yaml_with_comments_only(self, tmp_path):
        """YAML file with only comments uses defaults."""
        config_file = tmp_path / "config.yml"
        config_file.write_text("# This is a comment\n# Another comment\n")

        config = Config.from_file(config_file)
        assert config.get("machine.simulate") is False

    def test_file_not_found_raises(self, tmp_path):
        """Missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            Config.from_file(tmp_path / "nonexistent.yml")

    def test_load_partial_config(self, tmp_path):
        """Partial config merges with defaults."""
        config_file = tmp_path / "config.yml"
        config_file.write_text("queue:\n  mode: priority\n")

        config = Config.from_file(config_file)
        assert config.get("queue.mode") == "priority"
        assert config.get("machine.simulate") is False  # Default
        assert config.get("scheduler.auto_start") is False  # Default

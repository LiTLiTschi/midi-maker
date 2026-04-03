"""Tests for app config loading and validation."""

import json
from pathlib import Path

import pytest

from midi_maker.app.config import ConfigError, load_app_config
from midi_maker.core.enums import RecordingMode


def fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / "config" / name


def test_load_valid_config_parses_required_and_optional_fields() -> None:
    cfg = load_app_config(fixture_path("valid-config.json"))

    assert cfg.ports.trigger_input == "Drum Pedal"
    assert cfg.ports.cc_source_input == "MIDI Controller"
    assert cfg.default_recording_mode == RecordingMode.TOGGLE
    assert cfg.default_channel_mappings[0] == "pattern-id-a"
    assert cfg.default_channel_mappings[1] == "pattern-id-b"
    assert set(cfg.default_channel_mappings.keys()) == {0, 1}
    assert cfg.library_path == (
        fixture_path("valid-config.json").parent / "patterns" / "library.json"
    ).resolve()


def test_load_config_applies_optional_defaults(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "ports": {
                    "trigger_input": "Drum Pedal",
                    "cc_source_input": "MIDI Controller",
                    "sequencer_input": "MPD232",
                    "daw_output": "To DAW",
                },
                "library_path": "patterns/library.json",
            }
        ),
        encoding="utf-8",
    )
    cfg = load_app_config(config_path)

    assert cfg.default_recording_mode == RecordingMode.TOGGLE
    assert cfg.default_channel_mappings == {}


def test_missing_required_keys_raise_config_error() -> None:
    with pytest.raises(ConfigError, match="missing required keys") as exc_info:
        load_app_config(fixture_path("missing-keys.json"))

    assert "library_path" in str(exc_info.value)
    assert "ports.cc_source_input" in str(exc_info.value)


def test_invalid_channel_mapping_keys_raise_config_error() -> None:
    with pytest.raises(ConfigError, match="channel keys must be 0-15"):
        load_app_config(fixture_path("invalid-mappings.json"))


def test_channel_mapping_keys_with_whitespace_raise_config_error(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "ports": {
                    "trigger_input": "Drum Pedal",
                    "cc_source_input": "MIDI Controller",
                    "sequencer_input": "MPD232",
                    "daw_output": "To DAW",
                },
                "library_path": "patterns/library.json",
                "default_channel_mappings": {
                    " 5": "pattern-id-a",
                },
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="channel keys must be 0-15"):
        load_app_config(config_path)


def test_malformed_json_raises_config_error(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("{not valid json", encoding="utf-8")

    with pytest.raises(ConfigError, match="invalid JSON"):
        load_app_config(bad)


def test_unreadable_json_raises_config_error(tmp_path: Path) -> None:
    unreadable = tmp_path / "config-dir"
    unreadable.mkdir()

    with pytest.raises(ConfigError, match="Could not read config file"):
        load_app_config(unreadable)

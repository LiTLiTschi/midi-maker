"""Application configuration loading and validation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Dict, Mapping

from midi_maker.core import RecordingMode


class ConfigError(Exception):
    """Raised when app configuration cannot be loaded or validated."""


@dataclass(frozen=True)
class PortConfig:
    """Configured MIDI port names used by the runtime."""

    trigger_input: str
    cc_source_input: str
    sequencer_input: str
    daw_output: str


@dataclass(frozen=True)
class AppConfig:
    """Parsed and validated app configuration."""

    ports: PortConfig
    library_path: Path
    default_recording_mode: RecordingMode
    default_channel_mappings: Mapping[int, str]
    config_dir: Path


_REQUIRED_PORT_KEYS = (
    "trigger_input",
    "cc_source_input",
    "sequencer_input",
    "daw_output",
)


def load_app_config(path: Path) -> AppConfig:
    """Load and validate application configuration from JSON."""
    config_path = Path(path)

    try:
        raw = config_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError(
            f"Could not read config file '{config_path}': {exc.strerror or exc}"
        ) from exc

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ConfigError(
            "invalid JSON in config file "
            f"'{config_path}' at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc

    if not isinstance(payload, dict):
        raise ConfigError(f"Config file '{config_path}' must contain a JSON object")

    missing_keys = _find_missing_required_keys(payload)
    if missing_keys:
        listed = ", ".join(missing_keys)
        raise ConfigError(
            f"Config file '{config_path}' is missing required keys: {listed}"
        )

    ports_raw = payload["ports"]
    if not isinstance(ports_raw, dict):
        raise ConfigError("Config key 'ports' must be an object")

    ports = PortConfig(
        trigger_input=_require_non_empty_string(ports_raw, "trigger_input", "ports"),
        cc_source_input=_require_non_empty_string(ports_raw, "cc_source_input", "ports"),
        sequencer_input=_require_non_empty_string(ports_raw, "sequencer_input", "ports"),
        daw_output=_require_non_empty_string(ports_raw, "daw_output", "ports"),
    )

    library_path_value = _require_non_empty_string(payload, "library_path")
    library_path = _resolve_library_path(config_path, library_path_value)

    default_recording_mode = _parse_recording_mode(payload)
    default_channel_mappings = _parse_channel_mappings(payload)

    return AppConfig(
        ports=ports,
        library_path=library_path,
        default_recording_mode=default_recording_mode,
        default_channel_mappings=default_channel_mappings,
        config_dir=config_path.resolve().parent,
    )


def _find_missing_required_keys(payload: Mapping[str, object]) -> list[str]:
    missing_keys: list[str] = []

    ports_raw = payload.get("ports")
    if ports_raw is None:
        missing_keys.append("ports")
        missing_keys.extend(f"ports.{key}" for key in _REQUIRED_PORT_KEYS)
    elif isinstance(ports_raw, dict):
        for key in _REQUIRED_PORT_KEYS:
            if key not in ports_raw:
                missing_keys.append(f"ports.{key}")
    else:
        missing_keys.append("ports")

    if "library_path" not in payload:
        missing_keys.append("library_path")

    return missing_keys


def _require_non_empty_string(
    payload: Mapping[str, object], key: str, parent: str | None = None
) -> str:
    value = payload.get(key)
    key_name = f"{parent}.{key}" if parent else key
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"Config key '{key_name}' must be a non-empty string")
    return value


def _parse_recording_mode(payload: Mapping[str, object]) -> RecordingMode:
    mode_value = payload.get("default_recording_mode", RecordingMode.TOGGLE.name)
    if not isinstance(mode_value, str):
        raise ConfigError(
            "Config key 'default_recording_mode' must be one of HOLD or TOGGLE"
        )

    normalized = mode_value.upper()
    try:
        return RecordingMode[normalized]
    except KeyError as exc:
        raise ConfigError(
            "Config key 'default_recording_mode' must be one of HOLD or TOGGLE"
        ) from exc


def _parse_channel_mappings(payload: Mapping[str, object]) -> Mapping[int, str]:
    mappings_value = payload.get("default_channel_mappings", {})
    if not isinstance(mappings_value, dict):
        raise ConfigError("Config key 'default_channel_mappings' must be an object")

    mappings: Dict[int, str] = {}
    for channel_key, pattern_id in mappings_value.items():
        if not isinstance(channel_key, str):
            raise ConfigError(
                "Config key 'default_channel_mappings' channel keys must be strings 0-15"
            )

        try:
            channel = int(channel_key)
        except ValueError as exc:
            raise ConfigError(
                "Config key 'default_channel_mappings' channel keys must be 0-15"
            ) from exc

        if channel_key != str(channel) or not 0 <= channel <= 15:
            raise ConfigError(
                "Config key 'default_channel_mappings' channel keys must be 0-15"
            )

        if not isinstance(pattern_id, str) or not pattern_id.strip():
            raise ConfigError(
                f"Config mapping for channel {channel} must be a non-empty pattern id"
            )

        mappings[channel] = pattern_id

    return MappingProxyType(mappings)


def _resolve_library_path(config_path: Path, library_path: str) -> Path:
    path = Path(library_path)
    if path.is_absolute():
        return path.resolve()
    return (config_path.resolve().parent / path).resolve()

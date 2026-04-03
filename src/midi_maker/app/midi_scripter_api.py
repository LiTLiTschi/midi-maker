"""Adapter boundary around optional midi-scripter dependency."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Callable

_MISSING_DEP_MESSAGE = (
    "midi-scripter is required to run the GUI app. "
    "Install it with `pip install midi-scripter`."
)

try:
    import midi_scripter as _midi_scripter
except ModuleNotFoundError as _midi_scripter_import_error:  # pragma: no cover - env-dependent
    _midi_scripter = None
else:
    _midi_scripter_import_error = None


def _raise_missing_dependency() -> None:
    raise RuntimeError(_MISSING_DEP_MESSAGE) from _midi_scripter_import_error


if _midi_scripter is None:  # pragma: no cover - env-dependent
    class _UnavailableMidiType:
        NOTE_ON = "NOTE_ON"
        NOTE_OFF = "NOTE_OFF"
        CONTROL_CHANGE = "CONTROL_CHANGE"

    class MidiIn:  # type: ignore[no-redef]
        """Stub type that raises clear install guidance when instantiated."""

        def __init__(self, *, name: str) -> None:
            _ = name
            _raise_missing_dependency()

    class MidiOut:  # type: ignore[no-redef]
        """Stub type that raises clear install guidance when instantiated."""

        def __init__(self, *, name: str) -> None:
            _ = name
            _raise_missing_dependency()

    MidiType = _UnavailableMidiType  # type: ignore[assignment]

    def start_gui() -> None:
        """Raise clear guidance when GUI runtime dependency is missing."""
        _raise_missing_dependency()

else:
    MidiIn = _midi_scripter.MidiIn
    MidiOut = _midi_scripter.MidiOut
    MidiType = _midi_scripter.MidiType
    start_gui = _midi_scripter.start_gui


def list_input_ports() -> list[str]:
    """Return available input ports, or [] when listing is unavailable."""
    return _list_ports(
        module_names=("list_input_ports", "get_input_ports", "input_ports"),
        class_obj=MidiIn,
        class_names=("list_ports", "ports"),
    )


def list_output_ports() -> list[str]:
    """Return available output ports, or [] when listing is unavailable."""
    return _list_ports(
        module_names=("list_output_ports", "get_output_ports", "output_ports"),
        class_obj=MidiOut,
        class_names=("list_ports", "ports"),
    )


def _list_ports(
    *,
    module_names: tuple[str, ...],
    class_obj: Any,
    class_names: tuple[str, ...],
) -> list[str]:
    if _midi_scripter is None:
        return []

    for name in module_names:
        result = _coerce_port_names(getattr(_midi_scripter, name, None))
        if result is not None:
            return result

    for name in class_names:
        result = _coerce_port_names(getattr(class_obj, name, None))
        if result is not None:
            return result

    return []


def _coerce_port_names(candidate: Any) -> list[str] | None:
    if candidate is None:
        return None

    try:
        value = candidate() if callable(candidate) else candidate
    except Exception:
        return []

    if value is None:
        return []

    if isinstance(value, str):
        return [value]

    if isinstance(value, Iterable):
        return [str(item) for item in value]

    return []


__all__ = [
    "MidiIn",
    "MidiOut",
    "MidiType",
    "start_gui",
    "list_input_ports",
    "list_output_ports",
]

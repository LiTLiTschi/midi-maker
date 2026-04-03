"""Recording panel adapter that owns widgets and delegates recorder actions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Protocol

from midi_maker.core import RecordingMode, RecordingState


class CCRecorderLike(Protocol):
    """Subset of recorder behavior used by RecordingPanel."""

    recording_mode: RecordingMode

    def set_recording_mode(self, mode: RecordingMode) -> None:
        """Set recorder mode."""


class TextWidgetLike(Protocol):
    """Text widget adapter protocol."""

    text: str

    def set_text(self, text: str) -> None:
        """Set rendered text."""


class ModeSelectorWidgetLike(Protocol):
    """Mode selector widget adapter protocol."""

    selected: str | None

    def set_selected(self, value: str) -> None:
        """Set selected label."""

    def set_on_change(self, callback: Callable[[str], None]) -> None:
        """Register change callback."""


class ValueWidgetLike(Protocol):
    """Value widget adapter protocol for level indicators."""

    value: float

    def set_value(self, value: float) -> None:
        """Set numeric widget value."""


@dataclass(frozen=True)
class RecordingPanelWidgets:
    """Injected widget facades for the recording panel."""

    status: TextWidgetLike
    mode: ModeSelectorWidgetLike
    level: ValueWidgetLike


class RecordingPanel:
    """Widget-owner adapter for recording panel UI concerns."""

    def __init__(self, cc_recorder: CCRecorderLike, widgets: RecordingPanelWidgets) -> None:
        self.cc_recorder = cc_recorder
        self.status_widget = widgets.status
        self.mode_widget = widgets.mode
        self.level_widget = widgets.level

        self.recording_status = RecordingState.IDLE
        self.input_level = 0

        mode = getattr(cc_recorder, "recording_mode", RecordingMode.TOGGLE)
        self.selected_mode_label = self._mode_to_label(mode)

        self.status_widget.set_text(self.recording_status.name)
        self.mode_widget.set_selected(self.selected_mode_label)
        self.mode_widget.set_on_change(self._on_mode_changed)
        self.level_widget.set_value(self.input_level)

    def update_recording_status(self, status: RecordingState) -> None:
        """Update status indicator from runtime state."""
        self.recording_status = status
        self.status_widget.set_text(status.name)

    def update_input_level(self, cc_value: int) -> None:
        """Update recent-event level indicator using MIDI range clamping."""
        normalized_value = max(0, min(127, int(cc_value)))
        self.input_level = normalized_value
        self.level_widget.set_value(normalized_value)

    def _on_mode_changed(self, selected_label: str) -> None:
        mode = self._label_to_mode(selected_label)
        if mode is None:
            return

        self.selected_mode_label = mode.name
        setter = getattr(self.cc_recorder, "set_recording_mode", None)
        if callable(setter):
            setter(mode)

    @staticmethod
    def _mode_to_label(mode: Any) -> str:
        mode_name = getattr(mode, "name", RecordingMode.TOGGLE.name)
        if mode_name in (RecordingMode.HOLD.name, RecordingMode.TOGGLE.name):
            return mode_name
        return RecordingMode.TOGGLE.name

    @staticmethod
    def _label_to_mode(label: str) -> RecordingMode | None:
        if label == RecordingMode.HOLD.name:
            return RecordingMode.HOLD
        if label == RecordingMode.TOGGLE.name:
            return RecordingMode.TOGGLE
        return None


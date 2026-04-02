"""Dependency-free recording panel state model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from midi_maker.core import RecordingMode, RecordingState


class CCRecorderLike(Protocol):
    """CCRecorder-compatible interface used by RecordingPanel."""

    recording_mode: RecordingMode


@dataclass(frozen=True)
class ModeSelectionState:
    """UI state for the recording mode selector."""

    labels: tuple[str, str] = ("HOLD", "TOGGLE")
    selected_label: str = "TOGGLE"


class RecordingPanel:
    """Simple state container for recording interface data."""

    def __init__(self, cc_recorder: CCRecorderLike) -> None:
        """Store recorder reference and initialize default panel state."""
        self.cc_recorder = cc_recorder
        self.recording_status = RecordingState.IDLE
        self.recording_indicator_text = RecordingState.IDLE.name
        self.input_level = 0

        default_mode_label = getattr(cc_recorder, "recording_mode", RecordingMode.TOGGLE).name
        if default_mode_label not in ModeSelectionState().labels:
            default_mode_label = "TOGGLE"

        self.mode_selection = ModeSelectionState(selected_label=default_mode_label)
        self.mode_labels = self.mode_selection.labels
        self.selected_mode_label = self.mode_selection.selected_label

    def update_recording_status(self, status: RecordingState) -> None:
        """Update recording state and text indicator."""
        self.recording_status = status
        self.recording_indicator_text = status.name

    def update_input_level(self, cc_value: int) -> None:
        """Normalize incoming CC value to MIDI range and store it."""
        normalized_value = max(0, min(127, int(cc_value)))
        self.input_level = normalized_value

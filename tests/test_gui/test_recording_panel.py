"""Tests for RecordingPanel GUI widget adapter behavior."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

from midi_maker.core import RecordingMode, RecordingState
from midi_maker.gui.recording_panel import RecordingPanel

sys.path.append(str(Path(__file__).parent))
from fakes import FakeButtonSelectorH, FakeGuiText, FakeProgressBarH


@dataclass
class RecordingWidgets:
    status: FakeGuiText
    mode: FakeButtonSelectorH
    level: FakeProgressBarH


class FakeRecorder:
    def __init__(self, mode: RecordingMode = RecordingMode.TOGGLE) -> None:
        self.recording_mode = mode
        self.set_mode_calls: list[RecordingMode] = []

    def set_recording_mode(self, mode: RecordingMode) -> None:
        self.recording_mode = mode
        self.set_mode_calls.append(mode)


def make_widgets() -> RecordingWidgets:
    return RecordingWidgets(
        status=FakeGuiText(),
        mode=FakeButtonSelectorH(options=("HOLD", "TOGGLE"), selected="TOGGLE"),
        level=FakeProgressBarH(),
    )


def test_recording_panel_updates_status_widget() -> None:
    recorder = FakeRecorder()
    widgets = make_widgets()
    panel = RecordingPanel(cc_recorder=recorder, widgets=widgets)

    panel.update_recording_status(RecordingState.RECORDING)

    assert panel.recording_status == RecordingState.RECORDING
    assert widgets.status.text == "RECORDING"


def test_recording_panel_updates_recent_level_indicator() -> None:
    panel = RecordingPanel(cc_recorder=FakeRecorder(), widgets=make_widgets())

    panel.update_input_level(96)

    assert panel.input_level == 96
    assert panel.level_widget.value == 96


def test_recording_panel_clamps_recent_level_indicator() -> None:
    panel = RecordingPanel(cc_recorder=FakeRecorder(), widgets=make_widgets())

    panel.update_input_level(255)
    assert panel.level_widget.value == 127

    panel.update_input_level(-2)
    assert panel.level_widget.value == 0


def test_recording_panel_defaults_mode_selector_from_recorder() -> None:
    widgets = make_widgets()
    panel = RecordingPanel(cc_recorder=FakeRecorder(RecordingMode.HOLD), widgets=widgets)

    assert panel.selected_mode_label == "HOLD"
    assert widgets.mode.selected == "HOLD"


def test_recording_panel_handles_hold_toggle_mode_changes() -> None:
    recorder = FakeRecorder()
    widgets = make_widgets()
    panel = RecordingPanel(cc_recorder=recorder, widgets=widgets)

    widgets.mode.trigger_change("HOLD")

    assert panel.selected_mode_label == "HOLD"
    assert recorder.recording_mode == RecordingMode.HOLD
    assert recorder.set_mode_calls == [RecordingMode.HOLD]


def test_recording_panel_ignores_unknown_mode_changes() -> None:
    recorder = FakeRecorder()
    widgets = make_widgets()
    panel = RecordingPanel(cc_recorder=recorder, widgets=widgets)

    widgets.mode.trigger_change("LATCH")

    assert panel.selected_mode_label == "TOGGLE"
    assert recorder.set_mode_calls == []

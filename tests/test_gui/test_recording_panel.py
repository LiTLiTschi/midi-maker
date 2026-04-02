"""Tests for dependency-free RecordingPanel state model."""

from midi_maker.core import RecordingState
from midi_maker.gui.recording_panel import RecordingPanel


class DummyRecorder:
    """Minimal CCRecorder-compatible stub for panel tests."""


class TestRecordingPanelInit:
    """Tests for RecordingPanel initialization."""

    def test_init_stores_recorder_and_defaults(self) -> None:
        """Panel stores recorder and initializes default visual state."""
        recorder = DummyRecorder()

        panel = RecordingPanel(recorder)

        assert panel.cc_recorder is recorder
        assert panel.recording_status == RecordingState.IDLE
        assert panel.recording_indicator_text == "IDLE"
        assert panel.input_level == 0

    def test_init_has_mode_selection_labels(self) -> None:
        """Panel exposes HOLD/TOGGLE mode labels and default selection."""
        panel = RecordingPanel(DummyRecorder())

        assert panel.mode_labels == ("HOLD", "TOGGLE")
        assert panel.selected_mode_label == "TOGGLE"


class TestRecordingPanelStatusUpdates:
    """Tests for status text updates."""

    def test_update_recording_status_updates_state_and_text(self) -> None:
        """Status updates replace current state and status label."""
        panel = RecordingPanel(DummyRecorder())

        panel.update_recording_status(RecordingState.RECORDING)

        assert panel.recording_status == RecordingState.RECORDING
        assert panel.recording_indicator_text == "RECORDING"

    def test_update_recording_status_handles_stopped(self) -> None:
        """STOPPED state maps to STOPPED indicator text."""
        panel = RecordingPanel(DummyRecorder())

        panel.update_recording_status(RecordingState.STOPPED)

        assert panel.recording_indicator_text == "STOPPED"


class TestRecordingPanelInputLevel:
    """Tests for input level normalization and clamping."""

    def test_update_input_level_keeps_value_within_range(self) -> None:
        """Values within MIDI range are stored unchanged."""
        panel = RecordingPanel(DummyRecorder())

        panel.update_input_level(64)

        assert panel.input_level == 64

    def test_update_input_level_clamps_below_zero(self) -> None:
        """Values below 0 are clamped to 0."""
        panel = RecordingPanel(DummyRecorder())

        panel.update_input_level(-15)

        assert panel.input_level == 0

    def test_update_input_level_clamps_above_127(self) -> None:
        """Values above 127 are clamped to 127."""
        panel = RecordingPanel(DummyRecorder())

        panel.update_input_level(255)

        assert panel.input_level == 127

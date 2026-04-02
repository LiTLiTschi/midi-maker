"""Tests for exports from the ``midi_maker.gui`` package."""

from midi_maker.gui import PatternBrowser, PlaybackControls, RecordingPanel


def test_gui_package_exports_public_components() -> None:
    """GUI package exposes key panel/control classes."""
    assert RecordingPanel.__name__ == "RecordingPanel"
    assert PatternBrowser.__name__ == "PatternBrowser"
    assert PlaybackControls.__name__ == "PlaybackControls"

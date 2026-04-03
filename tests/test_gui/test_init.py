"""Tests for exports from the ``midi_maker.gui`` package."""

from midi_maker.gui import (
    PatternBrowser,
    PlaybackControls,
    RecordingPanel,
    RecordingPanelWidgets,
    PatternBrowserWidgets,
    PlaybackControlsWidgets,
)


def test_gui_package_exports_public_components() -> None:
    """GUI package exposes key panel/control classes."""
    assert RecordingPanel.__name__ == "RecordingPanel"
    assert PatternBrowser.__name__ == "PatternBrowser"
    assert PlaybackControls.__name__ == "PlaybackControls"
    assert RecordingPanelWidgets.__name__ == "RecordingPanelWidgets"
    assert PatternBrowserWidgets.__name__ == "PatternBrowserWidgets"
    assert PlaybackControlsWidgets.__name__ == "PlaybackControlsWidgets"


def test_gui_package_all_matches_public_component_names() -> None:
    """GUI package __all__ only exposes supported public component names."""
    from midi_maker import gui

    assert set(gui.__all__) == {
        "RecordingPanel",
        "PatternBrowser",
        "PlaybackControls",
        "RecordingPanelWidgets",
        "PatternBrowserWidgets",
        "PlaybackControlsWidgets",
    }

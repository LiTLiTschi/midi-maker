"""Tests for PatternBrowser placeholder GUI model."""

from midi_maker.automation import AutomationPattern, PatternLibrary
from midi_maker.core import CCEvent
from midi_maker.gui.pattern_browser import PatternBrowser


def make_pattern() -> AutomationPattern:
    """Create a pattern fixture with attack/decay and metadata."""
    events = [
        CCEvent(cc_number=74, value=0, channel=0, timestamp=0.0),
        CCEvent(cc_number=74, value=127, channel=0, timestamp=0.5),
        CCEvent(cc_number=74, value=32, channel=0, timestamp=1.0),
    ]
    pattern = AutomationPattern(
        pattern_id="sweep-1",
        name="Filter Sweep",
        cc_events=events,
        duration=1.25,
        metadata={"source": "pedal", "cc_number": 74},
    )
    pattern.analyze_attack_decay()
    return pattern


def test_init_stores_library_and_initializes_state() -> None:
    """PatternBrowser keeps library reference and default state values."""
    library = PatternLibrary()

    browser = PatternBrowser(library)

    assert browser.pattern_library is library
    assert browser.pattern_list == []
    assert browser.selected_pattern is None
    assert browser.info_text == ""
    assert browser.play_button_label == "▶ Play"


def test_refresh_pattern_list_updates_state_from_library() -> None:
    """Pattern list state mirrors library IDs after refresh."""
    library = PatternLibrary()
    library.add_pattern(make_pattern())
    library.add_pattern(
        AutomationPattern(
            pattern_id="alpha",
            name="Alpha",
            cc_events=[],
            duration=0.0,
        )
    )
    browser = PatternBrowser(library)

    browser.refresh_pattern_list()

    assert browser.pattern_list == ["alpha", "sweep-1"]


def test_show_pattern_details_renders_concise_metadata_text() -> None:
    """Details text includes key pattern metadata and statistics."""
    library = PatternLibrary()
    library.add_pattern(make_pattern())
    browser = PatternBrowser(library)

    browser.show_pattern_details("sweep-1")

    assert browser.selected_pattern == "sweep-1"
    expected = (
        "sweep-1: Filter Sweep\n"
        "Duration: 1.25s | Events: 3 | Attack: 2 | Decay: 1\n"
        "Metadata: cc_number=74, source=pedal"
    )
    assert browser.info_text == expected


def test_show_pattern_details_uses_none_for_empty_metadata() -> None:
    """Details text renders metadata as none when metadata is empty."""
    library = PatternLibrary()
    library.add_pattern(
        AutomationPattern(
            pattern_id="plain",
            name="Plain",
            cc_events=[],
            duration=0.0,
        )
    )
    browser = PatternBrowser(library)

    browser.show_pattern_details("plain")

    assert browser.info_text.endswith("Metadata: none")

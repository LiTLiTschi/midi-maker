"""Tests for PatternBrowser GUI widget adapter behavior."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

from midi_maker.automation import AutomationPattern
from midi_maker.core import CCEvent
from midi_maker.gui.pattern_browser import PatternBrowser

sys.path.append(str(Path(__file__).parent))
from fakes import FakeButton, FakeGuiText, FakeListSelector


@dataclass
class PatternWidgets:
    pattern_list: FakeListSelector
    info_text: FakeGuiText
    save_button: FakeButton
    load_button: FakeButton


class FakePatternLibrary:
    def __init__(self) -> None:
        self.patterns: dict[str, AutomationPattern] = {}
        self.load_calls = 0
        self.save_calls = 0

    def add_pattern(self, pattern: AutomationPattern) -> None:
        self.patterns[pattern.pattern_id] = pattern

    def list_patterns(self) -> list[str]:
        return sorted(self.patterns.keys())

    def get_pattern(self, pattern_id: str) -> AutomationPattern:
        return self.patterns[pattern_id]

    def save_library(self) -> None:
        self.save_calls += 1

    def load_library(self) -> None:
        self.load_calls += 1


def make_pattern(pattern_id: str = "pat-a", name: str = "Pattern A") -> AutomationPattern:
    pattern = AutomationPattern(
        pattern_id=pattern_id,
        name=name,
        cc_events=[CCEvent(cc_number=74, value=64, channel=0, timestamp=0.0)],
        duration=0.5,
    )
    pattern.analyze_attack_decay()
    return pattern


def make_widgets() -> PatternWidgets:
    return PatternWidgets(
        pattern_list=FakeListSelector(),
        info_text=FakeGuiText(),
        save_button=FakeButton(),
        load_button=FakeButton(),
    )


def test_pattern_browser_refreshes_selector_from_library() -> None:
    library = FakePatternLibrary()
    library.add_pattern(make_pattern("alpha"))
    library.add_pattern(make_pattern("beta"))
    browser = PatternBrowser(pattern_library=library, widgets=make_widgets())

    browser.refresh_pattern_list()

    assert browser.pattern_list_widget.items == ["alpha", "beta"]


def test_pattern_browser_select_surfaces_pattern_details() -> None:
    library = FakePatternLibrary()
    library.add_pattern(make_pattern("sweep", "Filter Sweep"))
    browser = PatternBrowser(pattern_library=library, widgets=make_widgets())

    browser.pattern_list_widget.select("sweep")

    assert browser.selected_pattern == "sweep"
    assert "Filter Sweep" in browser.info_widget.text
    assert "Duration:" in browser.info_widget.text


def test_pattern_browser_save_surface_calls_library_save() -> None:
    library = FakePatternLibrary()
    browser = PatternBrowser(pattern_library=library, widgets=make_widgets())

    browser.save_button.click()

    assert library.save_calls == 1


def test_pattern_browser_load_surface_calls_library_load_and_refreshes() -> None:
    library = FakePatternLibrary()
    widgets = make_widgets()
    browser = PatternBrowser(pattern_library=library, widgets=widgets)
    library.add_pattern(make_pattern("loaded"))

    browser.load_button.click()

    assert library.load_calls == 1
    assert widgets.pattern_list.items == ["loaded"]

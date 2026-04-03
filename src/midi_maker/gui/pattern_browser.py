"""Pattern browser adapter that owns widgets and delegates library operations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol

from midi_maker.automation import AutomationPattern


class PatternLibraryLike(Protocol):
    """Subset of pattern library behavior used by PatternBrowser."""

    def list_patterns(self) -> list[str]:
        """List known pattern IDs."""

    def get_pattern(self, pattern_id: str) -> AutomationPattern:
        """Resolve a pattern by ID."""

    def save_library(self) -> None:
        """Persist current library state."""

    def load_library(self) -> None:
        """Reload library state."""


class ListSelectorWidgetLike(Protocol):
    """List selector widget protocol."""

    items: list[str]
    selected: str | None

    def set_items(self, items: list[str]) -> None:
        """Replace selectable items."""

    def set_selected(self, value: str | None) -> None:
        """Update selection."""

    def set_on_change(self, callback: Callable[[str], None]) -> None:
        """Register selection callback."""


class TextWidgetLike(Protocol):
    """Text widget protocol."""

    text: str

    def set_text(self, text: str) -> None:
        """Update text content."""


class ButtonWidgetLike(Protocol):
    """Button widget protocol."""

    def set_on_click(self, callback: Callable[[], object]) -> None:
        """Register click callback."""


@dataclass(frozen=True)
class PatternBrowserWidgets:
    """Injected widget facades for pattern browser."""

    pattern_list: ListSelectorWidgetLike
    info_text: TextWidgetLike
    save_button: ButtonWidgetLike
    load_button: ButtonWidgetLike


class PatternBrowser:
    """Widget-owner adapter for pattern management GUI."""

    def __init__(self, pattern_library: PatternLibraryLike, widgets: PatternBrowserWidgets) -> None:
        self.pattern_library = pattern_library
        self.pattern_list_widget = widgets.pattern_list
        self.info_widget = widgets.info_text
        self.save_button = widgets.save_button
        self.load_button = widgets.load_button
        self.selected_pattern: str | None = None

        self.pattern_list_widget.set_items([])
        self.pattern_list_widget.set_selected(None)
        self.info_widget.set_text("")
        self.pattern_list_widget.set_on_change(self.show_pattern_details)
        self.save_button.set_on_click(self.save_patterns)
        self.load_button.set_on_click(self.load_patterns)

    def refresh_pattern_list(self) -> None:
        """Surface current pattern IDs in the selector widget."""
        pattern_ids = list(self.pattern_library.list_patterns())
        self.pattern_list_widget.set_items(pattern_ids)
        if self.selected_pattern and self.selected_pattern not in pattern_ids:
            self.selected_pattern = None
            self.pattern_list_widget.set_selected(None)

    def show_pattern_details(self, pattern_id: str) -> None:
        """Surface selected pattern metadata and timing details."""
        pattern = self.pattern_library.get_pattern(pattern_id)
        self.selected_pattern = pattern_id
        self.pattern_list_widget.set_selected(pattern_id)
        self.info_widget.set_text(self._format_pattern_info(pattern))

    def save_patterns(self) -> None:
        """Delegate save action to pattern library service."""
        self.pattern_library.save_library()

    def load_patterns(self) -> None:
        """Delegate load action and refresh available pattern IDs."""
        self.pattern_library.load_library()
        self.refresh_pattern_list()

    @staticmethod
    def _format_pattern_info(pattern: AutomationPattern) -> str:
        metadata = pattern.metadata or {}
        metadata_text = (
            ", ".join(f"{key}={metadata[key]}" for key in sorted(metadata)) if metadata else "none"
        )
        return (
            f"{pattern.pattern_id}: {pattern.name}\n"
            f"Duration: {pattern.duration:.2f}s | "
            f"Events: {len(pattern.cc_events)} | "
            f"Attack: {len(pattern.attack_events)} | "
            f"Decay: {len(pattern.decay_events)}\n"
            f"Metadata: {metadata_text}"
        )


"""Dependency-free pattern browser model for placeholder GUI state."""

from typing import Any, List, Optional


class PatternBrowser:
    """Library management model for browsing stored automation patterns."""

    def __init__(self, pattern_library: Any):
        """Store the pattern library and initialize placeholder UI state."""
        self.pattern_library = pattern_library
        self.pattern_list: List[str] = []
        self.selected_pattern: Optional[str] = None
        self.info_text = ""
        self.play_button_label = "▶ Play"

    def refresh_pattern_list(self) -> None:
        """Update internal pattern list from the library."""
        self.pattern_list = list(self.pattern_library.list_patterns())

    def show_pattern_details(self, pattern_id: str) -> None:
        """Load a pattern by ID and render concise details text."""
        pattern = self.pattern_library.get_pattern(pattern_id)
        self.selected_pattern = pattern_id

        metadata = pattern.metadata or {}
        if metadata:
            metadata_text = ", ".join(
                f"{key}={metadata[key]}" for key in sorted(metadata)
            )
        else:
            metadata_text = "none"

        self.info_text = (
            f"{pattern.pattern_id}: {pattern.name}\n"
            f"Duration: {pattern.duration:.2f}s | "
            f"Events: {len(pattern.cc_events)} | "
            f"Attack: {len(pattern.attack_events)} | "
            f"Decay: {len(pattern.decay_events)}\n"
            f"Metadata: {metadata_text}"
        )

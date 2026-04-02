"""Pattern library for managing collections of automation patterns.

This module provides the PatternLibrary class for storing, retrieving,
and persisting AutomationPattern collections to JSON files.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

from .patterns import AutomationPattern


class PatternNotFoundError(KeyError):
    """Raised when a requested pattern does not exist in the library."""

    pass


class PatternLibrary:
    """Manages collections of automation patterns with JSON persistence.

    Provides methods to add, retrieve, list, save, and load automation
    patterns. Patterns are stored in-memory and can be persisted to a
    JSON file.

    Attributes:
        patterns: Dictionary mapping pattern IDs to AutomationPattern objects.
        library_path: Path to the JSON file for persistence.
    """

    def __init__(self, library_path: str = "patterns.json"):
        """Initialize a new PatternLibrary.

        Args:
            library_path: Path to the JSON file for storing patterns.
                         Defaults to "patterns.json" in the current directory.
        """
        self.patterns: Dict[str, AutomationPattern] = {}
        self.library_path = library_path

    def add_pattern(self, pattern: AutomationPattern) -> None:
        """Add a pattern to the library.

        If a pattern with the same ID already exists, it will be overwritten.

        Args:
            pattern: The AutomationPattern to add.
        """
        self.patterns[pattern.pattern_id] = pattern

    def get_pattern(self, pattern_id: str) -> AutomationPattern:
        """Retrieve a pattern by its ID.

        Args:
            pattern_id: The unique identifier of the pattern.

        Returns:
            The AutomationPattern with the given ID.

        Raises:
            PatternNotFoundError: If no pattern exists with the given ID.
        """
        if pattern_id not in self.patterns:
            raise PatternNotFoundError(f"Pattern not found: {pattern_id}")
        return self.patterns[pattern_id]

    def remove_pattern(self, pattern_id: str) -> None:
        """Remove a pattern from the library.

        Args:
            pattern_id: The unique identifier of the pattern to remove.

        Raises:
            PatternNotFoundError: If no pattern exists with the given ID.
        """
        if pattern_id not in self.patterns:
            raise PatternNotFoundError(f"Pattern not found: {pattern_id}")
        del self.patterns[pattern_id]

    def list_patterns(self) -> List[str]:
        """Get all pattern IDs in the library.

        Returns:
            List of pattern IDs, sorted alphabetically.
        """
        return sorted(self.patterns.keys())

    def __len__(self) -> int:
        """Return the number of patterns in the library."""
        return len(self.patterns)

    def __contains__(self, pattern_id: str) -> bool:
        """Check if a pattern ID exists in the library."""
        return pattern_id in self.patterns

    def save_library(self, path: Optional[str] = None) -> None:
        """Persist the library to a JSON file.

        Args:
            path: Optional alternative path to save to. If not provided,
                  uses self.library_path.

        Raises:
            OSError: If the file cannot be written.
        """
        save_path = Path(path or self.library_path)
        data = {
            "patterns": {
                pattern_id: pattern.to_dict()
                for pattern_id, pattern in self.patterns.items()
            }
        }
        save_path.write_text(json.dumps(data, indent=2))

    def load_library(self, path: Optional[str] = None) -> None:
        """Load patterns from a JSON file.

        Replaces any existing patterns in the library with those from the file.

        Args:
            path: Optional alternative path to load from. If not provided,
                  uses self.library_path.

        Raises:
            FileNotFoundError: If the library file does not exist.
            json.JSONDecodeError: If the file contains invalid JSON.
            KeyError: If the file structure is invalid.
        """
        load_path = Path(path or self.library_path)
        data = json.loads(load_path.read_text())
        self.patterns = {
            pattern_id: AutomationPattern.from_dict(pattern_data)
            for pattern_id, pattern_data in data["patterns"].items()
        }

    def clear(self) -> None:
        """Remove all patterns from the library."""
        self.patterns.clear()

"""Tests for PatternLibrary class."""

import json
from pathlib import Path

import pytest

from midi_maker.automation import AutomationPattern, PatternLibrary
from midi_maker.automation.library import PatternNotFoundError
from midi_maker.core import CCEvent


def make_pattern(pattern_id: str, name: str = "Test Pattern") -> AutomationPattern:
    """Create a simple AutomationPattern for testing."""
    events = [
        CCEvent(cc_number=74, value=64, channel=0, timestamp=0.0),
        CCEvent(cc_number=74, value=127, channel=0, timestamp=0.5),
    ]
    return AutomationPattern(
        pattern_id=pattern_id,
        name=name,
        cc_events=events,
        duration=1.0,
    )


class TestPatternLibraryInit:
    """Tests for PatternLibrary initialization."""

    def test_default_path(self) -> None:
        """Test default library path is patterns.json."""
        library = PatternLibrary()
        assert library.library_path == "patterns.json"

    def test_custom_path(self) -> None:
        """Test custom library path."""
        library = PatternLibrary("/custom/path/library.json")
        assert library.library_path == "/custom/path/library.json"

    def test_starts_empty(self) -> None:
        """Test library starts with no patterns."""
        library = PatternLibrary()
        assert len(library) == 0
        assert library.list_patterns() == []


class TestAddPattern:
    """Tests for add_pattern method."""

    def test_add_single_pattern(self) -> None:
        """Test adding a single pattern."""
        library = PatternLibrary()
        pattern = make_pattern("test-1")

        library.add_pattern(pattern)

        assert len(library) == 1
        assert "test-1" in library

    def test_add_multiple_patterns(self) -> None:
        """Test adding multiple patterns."""
        library = PatternLibrary()

        library.add_pattern(make_pattern("pattern-a"))
        library.add_pattern(make_pattern("pattern-b"))
        library.add_pattern(make_pattern("pattern-c"))

        assert len(library) == 3
        assert library.list_patterns() == ["pattern-a", "pattern-b", "pattern-c"]

    def test_add_overwrites_existing(self) -> None:
        """Test that adding a pattern with existing ID overwrites it."""
        library = PatternLibrary()
        pattern1 = make_pattern("same-id", name="First")
        pattern2 = make_pattern("same-id", name="Second")

        library.add_pattern(pattern1)
        library.add_pattern(pattern2)

        assert len(library) == 1
        assert library.get_pattern("same-id").name == "Second"


class TestGetPattern:
    """Tests for get_pattern method."""

    def test_get_existing_pattern(self) -> None:
        """Test retrieving an existing pattern."""
        library = PatternLibrary()
        pattern = make_pattern("test-1", name="My Pattern")
        library.add_pattern(pattern)

        result = library.get_pattern("test-1")

        assert result.pattern_id == "test-1"
        assert result.name == "My Pattern"

    def test_get_nonexistent_raises(self) -> None:
        """Test that getting a nonexistent pattern raises error."""
        library = PatternLibrary()

        with pytest.raises(PatternNotFoundError, match="Pattern not found: missing"):
            library.get_pattern("missing")

    def test_get_returns_same_object(self) -> None:
        """Test that get_pattern returns the same object instance."""
        library = PatternLibrary()
        pattern = make_pattern("test-1")
        library.add_pattern(pattern)

        result = library.get_pattern("test-1")

        assert result is pattern


class TestRemovePattern:
    """Tests for remove_pattern method."""

    def test_remove_existing_pattern(self) -> None:
        """Test removing an existing pattern."""
        library = PatternLibrary()
        library.add_pattern(make_pattern("to-remove"))
        library.add_pattern(make_pattern("to-keep"))

        library.remove_pattern("to-remove")

        assert len(library) == 1
        assert "to-remove" not in library
        assert "to-keep" in library

    def test_remove_nonexistent_raises(self) -> None:
        """Test that removing a nonexistent pattern raises error."""
        library = PatternLibrary()

        with pytest.raises(PatternNotFoundError, match="Pattern not found: missing"):
            library.remove_pattern("missing")


class TestListPatterns:
    """Tests for list_patterns method."""

    def test_empty_library(self) -> None:
        """Test list_patterns on empty library."""
        library = PatternLibrary()
        assert library.list_patterns() == []

    def test_returns_sorted_ids(self) -> None:
        """Test that pattern IDs are returned sorted."""
        library = PatternLibrary()
        library.add_pattern(make_pattern("zebra"))
        library.add_pattern(make_pattern("alpha"))
        library.add_pattern(make_pattern("middle"))

        result = library.list_patterns()

        assert result == ["alpha", "middle", "zebra"]


class TestContains:
    """Tests for __contains__ method."""

    def test_contains_existing(self) -> None:
        """Test 'in' operator for existing pattern."""
        library = PatternLibrary()
        library.add_pattern(make_pattern("exists"))

        assert "exists" in library

    def test_not_contains_missing(self) -> None:
        """Test 'in' operator for missing pattern."""
        library = PatternLibrary()

        assert "missing" not in library


class TestClear:
    """Tests for clear method."""

    def test_clear_removes_all(self) -> None:
        """Test that clear removes all patterns."""
        library = PatternLibrary()
        library.add_pattern(make_pattern("a"))
        library.add_pattern(make_pattern("b"))
        library.add_pattern(make_pattern("c"))

        library.clear()

        assert len(library) == 0
        assert library.list_patterns() == []


class TestSaveLibrary:
    """Tests for save_library method."""

    def test_save_to_default_path(self, tmp_path: Path) -> None:
        """Test saving to the default library path."""
        library_file = tmp_path / "patterns.json"
        library = PatternLibrary(str(library_file))
        library.add_pattern(make_pattern("saved-pattern"))

        library.save_library()

        assert library_file.exists()
        data = json.loads(library_file.read_text())
        assert "patterns" in data
        assert "saved-pattern" in data["patterns"]

    def test_save_to_custom_path(self, tmp_path: Path) -> None:
        """Test saving to a custom path."""
        default_file = tmp_path / "default.json"
        custom_file = tmp_path / "custom.json"
        library = PatternLibrary(str(default_file))
        library.add_pattern(make_pattern("test"))

        library.save_library(str(custom_file))

        assert custom_file.exists()
        assert not default_file.exists()

    def test_save_empty_library(self, tmp_path: Path) -> None:
        """Test saving an empty library."""
        library_file = tmp_path / "empty.json"
        library = PatternLibrary(str(library_file))

        library.save_library()

        data = json.loads(library_file.read_text())
        assert data == {"patterns": {}}

    def test_save_multiple_patterns(self, tmp_path: Path) -> None:
        """Test saving multiple patterns."""
        library_file = tmp_path / "multi.json"
        library = PatternLibrary(str(library_file))
        library.add_pattern(make_pattern("first"))
        library.add_pattern(make_pattern("second"))
        library.add_pattern(make_pattern("third"))

        library.save_library()

        data = json.loads(library_file.read_text())
        assert len(data["patterns"]) == 3

    def test_save_preserves_pattern_data(self, tmp_path: Path) -> None:
        """Test that save preserves all pattern data."""
        library_file = tmp_path / "data.json"
        library = PatternLibrary(str(library_file))
        events = [
            CCEvent(cc_number=74, value=0, channel=1, timestamp=0.0),
            CCEvent(cc_number=74, value=127, channel=1, timestamp=0.5),
        ]
        pattern = AutomationPattern(
            pattern_id="detailed",
            name="Detailed Pattern",
            cc_events=events,
            duration=2.5,
            metadata={"source": "test"},
        )
        pattern.analyze_attack_decay()
        library.add_pattern(pattern)

        library.save_library()

        data = json.loads(library_file.read_text())
        saved = data["patterns"]["detailed"]
        assert saved["name"] == "Detailed Pattern"
        assert saved["duration"] == 2.5
        assert saved["metadata"] == {"source": "test"}
        assert len(saved["cc_events"]) == 2
        assert len(saved["attack_events"]) == 2
        assert len(saved["decay_events"]) == 0


class TestLoadLibrary:
    """Tests for load_library method."""

    def test_load_from_default_path(self, tmp_path: Path) -> None:
        """Test loading from the default library path."""
        library_file = tmp_path / "patterns.json"
        data = {
            "patterns": {
                "loaded-pattern": {
                    "pattern_id": "loaded-pattern",
                    "name": "Loaded",
                    "cc_events": [],
                    "duration": 1.0,
                }
            }
        }
        library_file.write_text(json.dumps(data))
        library = PatternLibrary(str(library_file))

        library.load_library()

        assert len(library) == 1
        assert "loaded-pattern" in library
        assert library.get_pattern("loaded-pattern").name == "Loaded"

    def test_load_from_custom_path(self, tmp_path: Path) -> None:
        """Test loading from a custom path."""
        default_file = tmp_path / "default.json"
        custom_file = tmp_path / "custom.json"
        data = {
            "patterns": {
                "custom": {
                    "pattern_id": "custom",
                    "name": "Custom",
                    "cc_events": [],
                    "duration": 0.0,
                }
            }
        }
        custom_file.write_text(json.dumps(data))
        library = PatternLibrary(str(default_file))

        library.load_library(str(custom_file))

        assert "custom" in library

    def test_load_replaces_existing(self, tmp_path: Path) -> None:
        """Test that loading replaces existing patterns."""
        library_file = tmp_path / "replace.json"
        data = {
            "patterns": {
                "new": {
                    "pattern_id": "new",
                    "name": "New Pattern",
                    "cc_events": [],
                    "duration": 0.0,
                }
            }
        }
        library_file.write_text(json.dumps(data))

        library = PatternLibrary(str(library_file))
        library.add_pattern(make_pattern("existing"))

        library.load_library()

        assert len(library) == 1
        assert "new" in library
        assert "existing" not in library

    def test_load_nonexistent_raises(self, tmp_path: Path) -> None:
        """Test that loading nonexistent file raises error."""
        library = PatternLibrary(str(tmp_path / "nonexistent.json"))

        with pytest.raises(FileNotFoundError):
            library.load_library()

    def test_load_invalid_json_raises(self, tmp_path: Path) -> None:
        """Test that loading invalid JSON raises error."""
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("not valid json{}")
        library = PatternLibrary(str(invalid_file))

        with pytest.raises(json.JSONDecodeError):
            library.load_library()

    def test_load_preserves_pattern_data(self, tmp_path: Path) -> None:
        """Test that load preserves all pattern data including events."""
        library_file = tmp_path / "full.json"
        data = {
            "patterns": {
                "full": {
                    "pattern_id": "full",
                    "name": "Full Pattern",
                    "cc_events": [
                        {"cc_number": 74, "value": 64, "channel": 1, "timestamp": 0.25}
                    ],
                    "duration": 3.0,
                    "attack_events": [
                        {"cc_number": 74, "value": 64, "channel": 1, "timestamp": 0.25}
                    ],
                    "decay_events": [],
                    "metadata": {"loaded": True},
                }
            }
        }
        library_file.write_text(json.dumps(data))
        library = PatternLibrary(str(library_file))

        library.load_library()

        pattern = library.get_pattern("full")
        assert pattern.name == "Full Pattern"
        assert pattern.duration == 3.0
        assert pattern.metadata == {"loaded": True}
        assert len(pattern.cc_events) == 1
        assert pattern.cc_events[0].cc_number == 74
        assert pattern.cc_events[0].value == 64


class TestRoundtrip:
    """Tests for save and load roundtrip."""

    def test_save_load_roundtrip(self, tmp_path: Path) -> None:
        """Test that patterns survive save/load cycle."""
        library_file = tmp_path / "roundtrip.json"

        # Create and populate library
        library1 = PatternLibrary(str(library_file))
        events = [
            CCEvent(cc_number=1, value=0, channel=0, timestamp=0.0),
            CCEvent(cc_number=1, value=127, channel=0, timestamp=0.5),
            CCEvent(cc_number=1, value=64, channel=0, timestamp=1.0),
        ]
        pattern = AutomationPattern(
            pattern_id="roundtrip-test",
            name="Roundtrip Test",
            cc_events=events,
            duration=1.0,
            metadata={"test": True, "count": 42},
        )
        pattern.analyze_attack_decay()
        library1.add_pattern(pattern)

        # Save
        library1.save_library()

        # Load into new library
        library2 = PatternLibrary(str(library_file))
        library2.load_library()

        # Verify
        assert len(library2) == 1
        loaded = library2.get_pattern("roundtrip-test")
        assert loaded.name == "Roundtrip Test"
        assert loaded.duration == 1.0
        assert loaded.metadata == {"test": True, "count": 42}
        assert len(loaded.cc_events) == 3
        assert len(loaded.attack_events) == 2
        assert len(loaded.decay_events) == 1

    def test_multiple_patterns_roundtrip(self, tmp_path: Path) -> None:
        """Test roundtrip with multiple patterns."""
        library_file = tmp_path / "multi.json"

        # Create patterns
        library1 = PatternLibrary(str(library_file))
        for i in range(5):
            pattern = make_pattern(f"pattern-{i}", name=f"Pattern {i}")
            library1.add_pattern(pattern)

        library1.save_library()

        # Load and verify
        library2 = PatternLibrary(str(library_file))
        library2.load_library()

        assert len(library2) == 5
        for i in range(5):
            assert f"pattern-{i}" in library2
            assert library2.get_pattern(f"pattern-{i}").name == f"Pattern {i}"

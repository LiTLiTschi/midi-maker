"""Tests for AutomationPattern dataclass."""

import json

import pytest

from midi_maker.automation import AutomationPattern
from midi_maker.core import CCEvent


class TestAutomationPatternInit:
    """Tests for AutomationPattern initialization and validation."""

    def test_basic_creation(self) -> None:
        """Test creating a pattern with minimal required fields."""
        events = [CCEvent(cc_number=1, value=64, channel=0, timestamp=0.0)]
        pattern = AutomationPattern(
            pattern_id="test-1",
            name="Test Pattern",
            cc_events=events,
            duration=1.0,
        )

        assert pattern.pattern_id == "test-1"
        assert pattern.name == "Test Pattern"
        assert pattern.cc_events == events
        assert pattern.duration == 1.0
        assert pattern.attack_events == []
        assert pattern.decay_events == []
        assert pattern.metadata == {}

    def test_creation_with_all_fields(self) -> None:
        """Test creating a pattern with all fields specified."""
        events = [CCEvent(cc_number=1, value=64, channel=0, timestamp=0.0)]
        attack = [CCEvent(cc_number=1, value=64, channel=0, timestamp=0.0)]
        decay = [CCEvent(cc_number=1, value=32, channel=0, timestamp=0.5)]
        metadata = {"source_cc": 74, "created": "2026-04-02"}

        pattern = AutomationPattern(
            pattern_id="test-2",
            name="Full Pattern",
            cc_events=events,
            duration=1.0,
            attack_events=attack,
            decay_events=decay,
            metadata=metadata,
        )

        assert pattern.attack_events == attack
        assert pattern.decay_events == decay
        assert pattern.metadata == metadata

    def test_empty_pattern_id_raises(self) -> None:
        """Test that empty pattern_id raises ValueError."""
        with pytest.raises(ValueError, match="pattern_id cannot be empty"):
            AutomationPattern(
                pattern_id="",
                name="Test",
                cc_events=[],
                duration=0.0,
            )

    def test_empty_name_raises(self) -> None:
        """Test that empty name raises ValueError."""
        with pytest.raises(ValueError, match="name cannot be empty"):
            AutomationPattern(
                pattern_id="test-1",
                name="",
                cc_events=[],
                duration=0.0,
            )

    def test_negative_duration_raises(self) -> None:
        """Test that negative duration raises ValueError."""
        with pytest.raises(ValueError, match="duration must be >= 0"):
            AutomationPattern(
                pattern_id="test-1",
                name="Test",
                cc_events=[],
                duration=-1.0,
            )


class TestAnalyzeAttackDecay:
    """Tests for the analyze_attack_decay method."""

    def test_empty_events(self) -> None:
        """Test analysis with no events."""
        pattern = AutomationPattern(
            pattern_id="test-1",
            name="Empty",
            cc_events=[],
            duration=0.0,
        )

        pattern.analyze_attack_decay()

        assert pattern.attack_events == []
        assert pattern.decay_events == []

    def test_single_event(self) -> None:
        """Test analysis with single event (peak is the only event)."""
        event = CCEvent(cc_number=1, value=100, channel=0, timestamp=0.0)
        pattern = AutomationPattern(
            pattern_id="test-1",
            name="Single",
            cc_events=[event],
            duration=0.1,
        )

        pattern.analyze_attack_decay()

        assert pattern.attack_events == [event]
        assert pattern.decay_events == []

    def test_ascending_sequence(self) -> None:
        """Test ascending values (peak at end)."""
        events = [
            CCEvent(cc_number=1, value=0, channel=0, timestamp=0.0),
            CCEvent(cc_number=1, value=64, channel=0, timestamp=0.5),
            CCEvent(cc_number=1, value=127, channel=0, timestamp=1.0),
        ]
        pattern = AutomationPattern(
            pattern_id="test-1",
            name="Ascending",
            cc_events=events,
            duration=1.0,
        )

        pattern.analyze_attack_decay()

        assert pattern.attack_events == events  # All events are attack
        assert pattern.decay_events == []

    def test_descending_sequence(self) -> None:
        """Test descending values (peak at start)."""
        events = [
            CCEvent(cc_number=1, value=127, channel=0, timestamp=0.0),
            CCEvent(cc_number=1, value=64, channel=0, timestamp=0.5),
            CCEvent(cc_number=1, value=0, channel=0, timestamp=1.0),
        ]
        pattern = AutomationPattern(
            pattern_id="test-1",
            name="Descending",
            cc_events=events,
            duration=1.0,
        )

        pattern.analyze_attack_decay()

        assert pattern.attack_events == [events[0]]
        assert pattern.decay_events == events[1:]

    def test_attack_decay_envelope(self) -> None:
        """Test typical attack-decay envelope (rise then fall)."""
        events = [
            CCEvent(cc_number=1, value=0, channel=0, timestamp=0.0),
            CCEvent(cc_number=1, value=64, channel=0, timestamp=0.25),
            CCEvent(cc_number=1, value=127, channel=0, timestamp=0.5),
            CCEvent(cc_number=1, value=64, channel=0, timestamp=0.75),
            CCEvent(cc_number=1, value=0, channel=0, timestamp=1.0),
        ]
        pattern = AutomationPattern(
            pattern_id="test-1",
            name="Envelope",
            cc_events=events,
            duration=1.0,
        )

        pattern.analyze_attack_decay()

        assert pattern.attack_events == events[:3]  # 0 -> 64 -> 127
        assert pattern.decay_events == events[3:]  # 64 -> 0

    def test_multiple_peaks_uses_first(self) -> None:
        """Test that first peak occurrence is used when multiple exist."""
        events = [
            CCEvent(cc_number=1, value=0, channel=0, timestamp=0.0),
            CCEvent(cc_number=1, value=127, channel=0, timestamp=0.25),
            CCEvent(cc_number=1, value=64, channel=0, timestamp=0.5),
            CCEvent(cc_number=1, value=127, channel=0, timestamp=0.75),
            CCEvent(cc_number=1, value=0, channel=0, timestamp=1.0),
        ]
        pattern = AutomationPattern(
            pattern_id="test-1",
            name="Multi-peak",
            cc_events=events,
            duration=1.0,
        )

        pattern.analyze_attack_decay()

        # First 127 is at index 1
        assert pattern.attack_events == events[:2]  # 0 -> 127 (first)
        assert pattern.decay_events == events[2:]  # 64 -> 127 -> 0


class TestSerialization:
    """Tests for to_dict and from_dict methods."""

    def test_to_dict_basic(self) -> None:
        """Test serialization to dictionary."""
        events = [
            CCEvent(cc_number=74, value=100, channel=1, timestamp=0.5),
        ]
        pattern = AutomationPattern(
            pattern_id="filter-sweep-1",
            name="Filter Sweep",
            cc_events=events,
            duration=2.0,
            metadata={"source": "recording"},
        )

        result = pattern.to_dict()

        assert result["pattern_id"] == "filter-sweep-1"
        assert result["name"] == "Filter Sweep"
        assert result["duration"] == 2.0
        assert result["metadata"] == {"source": "recording"}
        assert len(result["cc_events"]) == 1
        assert result["cc_events"][0] == {
            "cc_number": 74,
            "value": 100,
            "channel": 1,
            "timestamp": 0.5,
        }

    def test_to_dict_with_attack_decay(self) -> None:
        """Test serialization includes attack and decay events."""
        events = [
            CCEvent(cc_number=1, value=0, channel=0, timestamp=0.0),
            CCEvent(cc_number=1, value=127, channel=0, timestamp=0.5),
            CCEvent(cc_number=1, value=0, channel=0, timestamp=1.0),
        ]
        pattern = AutomationPattern(
            pattern_id="test-1",
            name="Test",
            cc_events=events,
            duration=1.0,
        )
        pattern.analyze_attack_decay()

        result = pattern.to_dict()

        assert len(result["attack_events"]) == 2
        assert len(result["decay_events"]) == 1

    def test_from_dict_basic(self) -> None:
        """Test deserialization from dictionary."""
        data = {
            "pattern_id": "test-1",
            "name": "Test Pattern",
            "cc_events": [
                {"cc_number": 74, "value": 100, "channel": 1, "timestamp": 0.5}
            ],
            "duration": 2.0,
            "metadata": {"key": "value"},
        }

        pattern = AutomationPattern.from_dict(data)

        assert pattern.pattern_id == "test-1"
        assert pattern.name == "Test Pattern"
        assert pattern.duration == 2.0
        assert len(pattern.cc_events) == 1
        assert pattern.cc_events[0].cc_number == 74
        assert pattern.cc_events[0].value == 100
        assert pattern.metadata == {"key": "value"}

    def test_from_dict_with_attack_decay(self) -> None:
        """Test deserialization preserves attack and decay events."""
        data = {
            "pattern_id": "test-1",
            "name": "Test",
            "cc_events": [
                {"cc_number": 1, "value": 127, "channel": 0, "timestamp": 0.5}
            ],
            "duration": 1.0,
            "attack_events": [
                {"cc_number": 1, "value": 0, "channel": 0, "timestamp": 0.0},
                {"cc_number": 1, "value": 127, "channel": 0, "timestamp": 0.5},
            ],
            "decay_events": [
                {"cc_number": 1, "value": 0, "channel": 0, "timestamp": 1.0}
            ],
        }

        pattern = AutomationPattern.from_dict(data)

        assert len(pattern.attack_events) == 2
        assert len(pattern.decay_events) == 1

    def test_roundtrip_serialization(self) -> None:
        """Test that to_dict -> from_dict preserves all data."""
        events = [
            CCEvent(cc_number=74, value=0, channel=0, timestamp=0.0),
            CCEvent(cc_number=74, value=127, channel=0, timestamp=0.5),
            CCEvent(cc_number=74, value=64, channel=0, timestamp=1.0),
        ]
        original = AutomationPattern(
            pattern_id="roundtrip-test",
            name="Roundtrip Test",
            cc_events=events,
            duration=1.0,
            metadata={"test": True, "count": 42},
        )
        original.analyze_attack_decay()

        # Roundtrip
        data = original.to_dict()
        restored = AutomationPattern.from_dict(data)

        assert restored.pattern_id == original.pattern_id
        assert restored.name == original.name
        assert restored.duration == original.duration
        assert restored.metadata == original.metadata
        assert len(restored.cc_events) == len(original.cc_events)
        assert len(restored.attack_events) == len(original.attack_events)
        assert len(restored.decay_events) == len(original.decay_events)

        # Verify individual events
        for orig, rest in zip(original.cc_events, restored.cc_events):
            assert orig.cc_number == rest.cc_number
            assert orig.value == rest.value
            assert orig.channel == rest.channel
            assert orig.timestamp == rest.timestamp

    def test_json_compatibility(self) -> None:
        """Test that to_dict output is JSON-serializable."""
        events = [
            CCEvent(cc_number=1, value=64, channel=0, timestamp=0.5),
        ]
        pattern = AutomationPattern(
            pattern_id="json-test",
            name="JSON Test",
            cc_events=events,
            duration=1.0,
        )

        # Should not raise
        json_str = json.dumps(pattern.to_dict())
        data = json.loads(json_str)
        restored = AutomationPattern.from_dict(data)

        assert restored.pattern_id == pattern.pattern_id

    def test_from_dict_missing_optional_fields(self) -> None:
        """Test deserialization handles missing optional fields."""
        data = {
            "pattern_id": "minimal-test",
            "name": "Minimal",
            "cc_events": [],
            "duration": 0.0,
            # attack_events, decay_events, metadata omitted
        }

        pattern = AutomationPattern.from_dict(data)

        assert pattern.attack_events == []
        assert pattern.decay_events == []
        assert pattern.metadata == {}

    def test_from_dict_missing_required_field_raises(self) -> None:
        """Test deserialization raises on missing required fields."""
        data = {
            "pattern_id": "test-1",
            # name is missing
            "cc_events": [],
            "duration": 0.0,
        }

        with pytest.raises(KeyError):
            AutomationPattern.from_dict(data)

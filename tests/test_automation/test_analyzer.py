"""Tests for PatternAnalyzer static methods."""

import pytest

from midi_maker.automation import PatternAnalyzer
from midi_maker.core import CCAutomationType, CCEvent


class TestSplitAttackDecay:
    """Tests for the split_attack_decay static method."""

    def test_empty_events(self) -> None:
        """Test splitting with no events."""
        attack, decay = PatternAnalyzer.split_attack_decay([])

        assert attack == []
        assert decay == []

    def test_single_event(self) -> None:
        """Test splitting with single event."""
        event = CCEvent(cc_number=1, value=100, channel=0, timestamp=0.0)

        attack, decay = PatternAnalyzer.split_attack_decay([event])

        assert attack == [event]
        assert decay == []

    def test_ascending_sequence(self) -> None:
        """Test ascending values (peak at end)."""
        events = [
            CCEvent(cc_number=1, value=0, channel=0, timestamp=0.0),
            CCEvent(cc_number=1, value=64, channel=0, timestamp=0.5),
            CCEvent(cc_number=1, value=127, channel=0, timestamp=1.0),
        ]

        attack, decay = PatternAnalyzer.split_attack_decay(events)

        assert attack == events  # All events are attack
        assert decay == []

    def test_descending_sequence(self) -> None:
        """Test descending values (peak at start)."""
        events = [
            CCEvent(cc_number=1, value=127, channel=0, timestamp=0.0),
            CCEvent(cc_number=1, value=64, channel=0, timestamp=0.5),
            CCEvent(cc_number=1, value=0, channel=0, timestamp=1.0),
        ]

        attack, decay = PatternAnalyzer.split_attack_decay(events)

        assert attack == [events[0]]
        assert decay == events[1:]

    def test_attack_decay_envelope(self) -> None:
        """Test typical attack-decay envelope (rise then fall)."""
        events = [
            CCEvent(cc_number=1, value=0, channel=0, timestamp=0.0),
            CCEvent(cc_number=1, value=64, channel=0, timestamp=0.25),
            CCEvent(cc_number=1, value=127, channel=0, timestamp=0.5),
            CCEvent(cc_number=1, value=64, channel=0, timestamp=0.75),
            CCEvent(cc_number=1, value=0, channel=0, timestamp=1.0),
        ]

        attack, decay = PatternAnalyzer.split_attack_decay(events)

        assert attack == events[:3]  # 0 -> 64 -> 127
        assert decay == events[3:]  # 64 -> 0

    def test_multiple_peaks_uses_first(self) -> None:
        """Test that first peak occurrence is used when multiple exist."""
        events = [
            CCEvent(cc_number=1, value=0, channel=0, timestamp=0.0),
            CCEvent(cc_number=1, value=127, channel=0, timestamp=0.25),
            CCEvent(cc_number=1, value=64, channel=0, timestamp=0.5),
            CCEvent(cc_number=1, value=127, channel=0, timestamp=0.75),
            CCEvent(cc_number=1, value=0, channel=0, timestamp=1.0),
        ]

        attack, decay = PatternAnalyzer.split_attack_decay(events)

        # First 127 is at index 1
        assert attack == events[:2]  # 0 -> 127 (first)
        assert decay == events[2:]  # 64 -> 127 -> 0


class TestDetectCCType:
    """Tests for the detect_cc_type static method."""

    def test_empty_events_returns_custom(self) -> None:
        """Test that empty events return CUSTOM type."""
        result = PatternAnalyzer.detect_cc_type([])

        assert result == CCAutomationType.CUSTOM

    def test_filter_cutoff_cc74(self) -> None:
        """Test detection of filter sweep on CC 74."""
        events = [
            CCEvent(cc_number=74, value=0, channel=0, timestamp=0.0),
            CCEvent(cc_number=74, value=127, channel=0, timestamp=1.0),
        ]

        result = PatternAnalyzer.detect_cc_type(events)

        assert result == CCAutomationType.FILTER_SWEEP

    def test_volume_cc7(self) -> None:
        """Test detection of volume fade on CC 7."""
        events = [
            CCEvent(cc_number=7, value=127, channel=0, timestamp=0.0),
            CCEvent(cc_number=7, value=0, channel=0, timestamp=1.0),
        ]

        result = PatternAnalyzer.detect_cc_type(events)

        assert result == CCAutomationType.VOLUME_FADE

    def test_expression_cc11(self) -> None:
        """Test detection of volume fade on CC 11 (expression)."""
        events = [
            CCEvent(cc_number=11, value=0, channel=0, timestamp=0.0),
            CCEvent(cc_number=11, value=127, channel=0, timestamp=1.0),
        ]

        result = PatternAnalyzer.detect_cc_type(events)

        assert result == CCAutomationType.VOLUME_FADE

    def test_pan_cc10(self) -> None:
        """Test detection of pan sweep on CC 10."""
        events = [
            CCEvent(cc_number=10, value=0, channel=0, timestamp=0.0),
            CCEvent(cc_number=10, value=127, channel=0, timestamp=1.0),
        ]

        result = PatternAnalyzer.detect_cc_type(events)

        assert result == CCAutomationType.PAN_SWEEP

    def test_resonance_cc71_small_range(self) -> None:
        """Test detection of resonance on CC 71 with small value range."""
        events = [
            CCEvent(cc_number=71, value=60, channel=0, timestamp=0.0),
            CCEvent(cc_number=71, value=80, channel=0, timestamp=1.0),
        ]

        result = PatternAnalyzer.detect_cc_type(events)

        assert result == CCAutomationType.RESONANCE

    def test_filter_sweep_cc71_large_range(self) -> None:
        """Test detection of filter sweep on CC 71 with large value range."""
        events = [
            CCEvent(cc_number=71, value=0, channel=0, timestamp=0.0),
            CCEvent(cc_number=71, value=127, channel=0, timestamp=1.0),
        ]

        result = PatternAnalyzer.detect_cc_type(events)

        assert result == CCAutomationType.FILTER_SWEEP

    def test_unknown_cc_returns_custom(self) -> None:
        """Test that unknown CC numbers return CUSTOM type."""
        events = [
            CCEvent(cc_number=99, value=0, channel=0, timestamp=0.0),
            CCEvent(cc_number=99, value=127, channel=0, timestamp=1.0),
        ]

        result = PatternAnalyzer.detect_cc_type(events)

        assert result == CCAutomationType.CUSTOM

    def test_mixed_cc_uses_most_common(self) -> None:
        """Test that the most common CC number determines type."""
        events = [
            CCEvent(cc_number=74, value=0, channel=0, timestamp=0.0),
            CCEvent(cc_number=74, value=64, channel=0, timestamp=0.25),
            CCEvent(cc_number=74, value=127, channel=0, timestamp=0.5),
            CCEvent(cc_number=7, value=100, channel=0, timestamp=0.75),
        ]

        result = PatternAnalyzer.detect_cc_type(events)

        assert result == CCAutomationType.FILTER_SWEEP


class TestOptimizeEvents:
    """Tests for the optimize_events static method."""

    def test_empty_events(self) -> None:
        """Test optimizing empty list."""
        result = PatternAnalyzer.optimize_events([])

        assert result == []

    def test_no_redundant_events(self) -> None:
        """Test that unique events are preserved."""
        events = [
            CCEvent(cc_number=1, value=0, channel=0, timestamp=0.0),
            CCEvent(cc_number=1, value=64, channel=0, timestamp=0.5),
            CCEvent(cc_number=1, value=127, channel=0, timestamp=1.0),
        ]

        result = PatternAnalyzer.optimize_events(events)

        assert result == events

    def test_removes_consecutive_same_values(self) -> None:
        """Test that consecutive events with same value are removed."""
        events = [
            CCEvent(cc_number=1, value=64, channel=0, timestamp=0.0),
            CCEvent(cc_number=1, value=64, channel=0, timestamp=0.1),
            CCEvent(cc_number=1, value=64, channel=0, timestamp=0.2),
            CCEvent(cc_number=1, value=127, channel=0, timestamp=0.3),
        ]

        result = PatternAnalyzer.optimize_events(events)

        assert len(result) == 2
        assert result[0].value == 64
        assert result[0].timestamp == 0.0  # Keeps first occurrence
        assert result[1].value == 127

    def test_different_cc_numbers_not_redundant(self) -> None:
        """Test that same value on different CCs is not redundant."""
        events = [
            CCEvent(cc_number=1, value=64, channel=0, timestamp=0.0),
            CCEvent(cc_number=2, value=64, channel=0, timestamp=0.1),
        ]

        result = PatternAnalyzer.optimize_events(events)

        assert result == events

    def test_different_channels_not_redundant(self) -> None:
        """Test that same value on different channels is not redundant."""
        events = [
            CCEvent(cc_number=1, value=64, channel=0, timestamp=0.0),
            CCEvent(cc_number=1, value=64, channel=1, timestamp=0.1),
        ]

        result = PatternAnalyzer.optimize_events(events)

        assert result == events

    def test_preserves_order(self) -> None:
        """Test that event order is preserved after optimization."""
        events = [
            CCEvent(cc_number=1, value=0, channel=0, timestamp=0.0),
            CCEvent(cc_number=1, value=0, channel=0, timestamp=0.1),
            CCEvent(cc_number=2, value=64, channel=0, timestamp=0.2),
            CCEvent(cc_number=1, value=127, channel=0, timestamp=0.3),
            CCEvent(cc_number=2, value=64, channel=0, timestamp=0.4),
        ]

        result = PatternAnalyzer.optimize_events(events)

        assert len(result) == 3
        assert result[0].timestamp == 0.0
        assert result[1].timestamp == 0.2
        assert result[2].timestamp == 0.3


class TestCalculateDuration:
    """Tests for the calculate_duration static method."""

    def test_empty_events(self) -> None:
        """Test duration of empty list."""
        result = PatternAnalyzer.calculate_duration([])

        assert result == 0.0

    def test_single_event(self) -> None:
        """Test duration of single event."""
        events = [CCEvent(cc_number=1, value=64, channel=0, timestamp=0.5)]

        result = PatternAnalyzer.calculate_duration(events)

        assert result == 0.0

    def test_multiple_events(self) -> None:
        """Test duration calculation from first to last event."""
        events = [
            CCEvent(cc_number=1, value=0, channel=0, timestamp=0.5),
            CCEvent(cc_number=1, value=64, channel=0, timestamp=1.0),
            CCEvent(cc_number=1, value=127, channel=0, timestamp=2.5),
        ]

        result = PatternAnalyzer.calculate_duration(events)

        assert result == 2.0  # 2.5 - 0.5


class TestFindPeakEvent:
    """Tests for the find_peak_event static method."""

    def test_empty_events(self) -> None:
        """Test finding peak in empty list."""
        result = PatternAnalyzer.find_peak_event([])

        assert result is None

    def test_single_event(self) -> None:
        """Test finding peak with single event."""
        event = CCEvent(cc_number=1, value=64, channel=0, timestamp=0.0)

        result = PatternAnalyzer.find_peak_event([event])

        assert result == event

    def test_finds_highest_value(self) -> None:
        """Test that highest value event is returned."""
        events = [
            CCEvent(cc_number=1, value=0, channel=0, timestamp=0.0),
            CCEvent(cc_number=1, value=127, channel=0, timestamp=0.5),
            CCEvent(cc_number=1, value=64, channel=0, timestamp=1.0),
        ]

        result = PatternAnalyzer.find_peak_event(events)

        assert result is not None
        assert result.value == 127

    def test_returns_first_peak_when_tied(self) -> None:
        """Test that first occurrence is returned when multiple peaks exist."""
        events = [
            CCEvent(cc_number=1, value=127, channel=0, timestamp=0.0),
            CCEvent(cc_number=1, value=64, channel=0, timestamp=0.5),
            CCEvent(cc_number=1, value=127, channel=0, timestamp=1.0),
        ]

        result = PatternAnalyzer.find_peak_event(events)

        assert result is not None
        assert result.value == 127
        assert result.timestamp == 0.0  # First occurrence


class TestGetValueRange:
    """Tests for the get_value_range static method."""

    def test_empty_events(self) -> None:
        """Test value range of empty list."""
        result = PatternAnalyzer.get_value_range([])

        assert result == (0, 0)

    def test_single_event(self) -> None:
        """Test value range of single event."""
        events = [CCEvent(cc_number=1, value=64, channel=0, timestamp=0.0)]

        result = PatternAnalyzer.get_value_range(events)

        assert result == (64, 64)

    def test_multiple_events(self) -> None:
        """Test value range calculation."""
        events = [
            CCEvent(cc_number=1, value=20, channel=0, timestamp=0.0),
            CCEvent(cc_number=1, value=100, channel=0, timestamp=0.5),
            CCEvent(cc_number=1, value=50, channel=0, timestamp=1.0),
        ]

        result = PatternAnalyzer.get_value_range(events)

        assert result == (20, 100)

    def test_full_range(self) -> None:
        """Test full MIDI range."""
        events = [
            CCEvent(cc_number=1, value=0, channel=0, timestamp=0.0),
            CCEvent(cc_number=1, value=127, channel=0, timestamp=1.0),
        ]

        result = PatternAnalyzer.get_value_range(events)

        assert result == (0, 127)

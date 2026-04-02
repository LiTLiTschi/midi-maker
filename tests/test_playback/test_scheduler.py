"""Tests for PlaybackScheduler functionality."""

import time
from typing import List, Tuple
from unittest.mock import Mock

import pytest

from midi_maker.automation import AutomationPattern
from midi_maker.core import CCEvent, PlaybackMode
from midi_maker.playback import PlaybackScheduler


@pytest.fixture
def simple_pattern() -> AutomationPattern:
    """Create a simple automation pattern for testing."""
    events = [
        CCEvent(cc_number=74, value=0, channel=0, timestamp=0.0),
        CCEvent(cc_number=74, value=64, channel=0, timestamp=0.05),
        CCEvent(cc_number=74, value=127, channel=0, timestamp=0.1),
        CCEvent(cc_number=74, value=64, channel=0, timestamp=0.15),
        CCEvent(cc_number=74, value=0, channel=0, timestamp=0.2),
    ]

    pattern = AutomationPattern(
        pattern_id="test-pattern",
        name="Test Pattern",
        cc_events=events,
        duration=0.2,
    )

    # Set attack and decay for testing
    pattern.attack_events = events[:3]
    pattern.decay_events = events[3:]

    return pattern


@pytest.fixture
def multi_cc_pattern() -> AutomationPattern:
    """Create a pattern with multiple CC numbers."""
    events = [
        CCEvent(cc_number=74, value=127, channel=0, timestamp=0.0),
        CCEvent(cc_number=71, value=100, channel=0, timestamp=0.05),
        CCEvent(cc_number=74, value=64, channel=0, timestamp=0.1),
    ]

    return AutomationPattern(
        pattern_id="multi-cc",
        name="Multi CC Pattern",
        cc_events=events,
        duration=0.1,
    )


class TestPlaybackSchedulerInit:
    """Tests for PlaybackScheduler initialization."""

    def test_init_without_output_port(self) -> None:
        """Scheduler can be created without an output port."""
        scheduler = PlaybackScheduler()
        assert scheduler.output_port is None
        assert len(scheduler.active_playbacks) == 0

    def test_init_with_output_port(self) -> None:
        """Scheduler accepts an output port."""
        mock_port = Mock()
        scheduler = PlaybackScheduler(output_port=mock_port)
        assert scheduler.output_port is mock_port


class TestStartPatternPlayback:
    """Tests for starting pattern playback."""

    def test_returns_playback_id(self, simple_pattern: AutomationPattern) -> None:
        """start_pattern_playback returns a unique ID."""
        scheduler = PlaybackScheduler()
        playback_id = scheduler.start_pattern_playback(
            simple_pattern, PlaybackMode.FULL_SEQUENCE
        )
        assert isinstance(playback_id, str)
        assert len(playback_id) > 0

    def test_playback_id_is_unique(self, simple_pattern: AutomationPattern) -> None:
        """Each playback gets a unique ID."""
        scheduler = PlaybackScheduler()
        id1 = scheduler.start_pattern_playback(
            simple_pattern, PlaybackMode.FULL_SEQUENCE
        )
        id2 = scheduler.start_pattern_playback(
            simple_pattern, PlaybackMode.FULL_SEQUENCE
        )
        assert id1 != id2

    def test_adds_to_active_playbacks(self, simple_pattern: AutomationPattern) -> None:
        """Started playback is tracked in active_playbacks."""
        scheduler = PlaybackScheduler()
        playback_id = scheduler.start_pattern_playback(
            simple_pattern, PlaybackMode.FULL_SEQUENCE
        )
        assert playback_id in scheduler.active_playbacks

    def test_playback_runs_asynchronously(
        self, simple_pattern: AutomationPattern
    ) -> None:
        """Playback runs in background without blocking."""
        scheduler = PlaybackScheduler()
        start_time = time.time()
        scheduler.start_pattern_playback(simple_pattern, PlaybackMode.FULL_SEQUENCE)
        elapsed = time.time() - start_time

        # Should return immediately (well under the 0.2s pattern duration)
        assert elapsed < 0.1


class TestStopPatternPlayback:
    """Tests for stopping pattern playback."""

    def test_removes_from_active_playbacks(
        self, simple_pattern: AutomationPattern
    ) -> None:
        """Stopping a playback removes it from active_playbacks."""
        scheduler = PlaybackScheduler()
        playback_id = scheduler.start_pattern_playback(
            simple_pattern, PlaybackMode.FULL_SEQUENCE
        )

        scheduler.stop_pattern_playback(playback_id)
        assert playback_id not in scheduler.active_playbacks

    def test_raises_on_invalid_id(self) -> None:
        """Stopping non-existent playback raises KeyError."""
        scheduler = PlaybackScheduler()

        with pytest.raises(KeyError):
            scheduler.stop_pattern_playback("invalid-id")

    def test_can_stop_playback_early(self, simple_pattern: AutomationPattern) -> None:
        """Playback can be stopped before completion."""
        scheduler = PlaybackScheduler()
        playback_id = scheduler.start_pattern_playback(
            simple_pattern, PlaybackMode.FULL_SEQUENCE
        )

        # Stop almost immediately
        time.sleep(0.05)
        scheduler.stop_pattern_playback(playback_id)

        # Should be removed from active playbacks
        assert playback_id not in scheduler.active_playbacks


class TestStopAllPlaybacks:
    """Tests for stopping all playbacks."""

    def test_stops_all_active_playbacks(
        self, simple_pattern: AutomationPattern
    ) -> None:
        """stop_all_playbacks clears all active playbacks."""
        scheduler = PlaybackScheduler()

        # Start multiple playbacks
        scheduler.start_pattern_playback(simple_pattern, PlaybackMode.FULL_SEQUENCE)
        scheduler.start_pattern_playback(simple_pattern, PlaybackMode.ATTACK_ONLY)
        scheduler.start_pattern_playback(simple_pattern, PlaybackMode.DECAY_ONLY)

        assert len(scheduler.active_playbacks) == 3

        scheduler.stop_all_playbacks()
        assert len(scheduler.active_playbacks) == 0

    def test_stop_all_on_empty_scheduler(self) -> None:
        """stop_all_playbacks works when no playbacks are active."""
        scheduler = PlaybackScheduler()
        scheduler.stop_all_playbacks()  # Should not raise
        assert len(scheduler.active_playbacks) == 0


class TestScheduleCCEvent:
    """Tests for scheduling individual CC events."""

    def test_sends_cc_event_immediately(self) -> None:
        """CC event with zero delay is sent immediately."""
        mock_port = Mock()
        scheduler = PlaybackScheduler(output_port=mock_port)

        event = CCEvent(cc_number=74, value=100, channel=0, timestamp=0.0)
        scheduler.schedule_cc_event(event, delay_ms=0)

        # Give thread a moment to execute
        time.sleep(0.05)

        mock_port.send_cc.assert_called_once_with(74, 100, 0)

    def test_sends_cc_event_after_delay(self) -> None:
        """CC event is delayed by the specified amount."""
        mock_port = Mock()
        scheduler = PlaybackScheduler(output_port=mock_port)

        event = CCEvent(cc_number=71, value=50, channel=1, timestamp=0.0)
        start_time = time.time()
        scheduler.schedule_cc_event(event, delay_ms=100)

        # Wait for event to be sent
        time.sleep(0.15)
        elapsed = time.time() - start_time

        # Should have been delayed by ~100ms
        assert elapsed >= 0.1
        mock_port.send_cc.assert_called_once_with(71, 50, 1)

    def test_multiple_scheduled_events(self) -> None:
        """Multiple CC events can be scheduled independently."""
        mock_port = Mock()
        scheduler = PlaybackScheduler(output_port=mock_port)

        event1 = CCEvent(cc_number=74, value=10, channel=0, timestamp=0.0)
        event2 = CCEvent(cc_number=71, value=20, channel=0, timestamp=0.0)

        scheduler.schedule_cc_event(event1, delay_ms=0)
        scheduler.schedule_cc_event(event2, delay_ms=0)

        time.sleep(0.05)

        assert mock_port.send_cc.call_count == 2


class TestPlaybackModes:
    """Tests for different playback modes."""

    def test_full_sequence_mode(self, simple_pattern: AutomationPattern) -> None:
        """FULL_SEQUENCE mode plays all events."""
        received: List[Tuple[int, int, int]] = []

        # Use a player with callback instead of mock port for this test
        from midi_maker.playback.player import AutomationPlayer

        mock_port = Mock()
        scheduler = PlaybackScheduler(output_port=mock_port)

        playback_id = scheduler.start_pattern_playback(
            simple_pattern, PlaybackMode.FULL_SEQUENCE
        )

        # Wait for playback to complete
        time.sleep(0.3)

        # Should have sent all 5 events
        assert mock_port.send_cc.call_count == 5

    def test_attack_only_mode(self, simple_pattern: AutomationPattern) -> None:
        """ATTACK_ONLY mode plays only attack events."""
        mock_port = Mock()
        scheduler = PlaybackScheduler(output_port=mock_port)

        scheduler.start_pattern_playback(simple_pattern, PlaybackMode.ATTACK_ONLY)

        # Wait for playback to complete
        time.sleep(0.3)

        # Should have sent only attack events (3)
        assert mock_port.send_cc.call_count == 3

    def test_decay_only_mode(self, simple_pattern: AutomationPattern) -> None:
        """DECAY_ONLY mode plays only decay events."""
        mock_port = Mock()
        scheduler = PlaybackScheduler(output_port=mock_port)

        scheduler.start_pattern_playback(simple_pattern, PlaybackMode.DECAY_ONLY)

        # Wait for playback to complete
        time.sleep(0.3)

        # Should have sent only decay events (2)
        assert mock_port.send_cc.call_count == 2

    def test_snapshot_mode(self, multi_cc_pattern: AutomationPattern) -> None:
        """SNAPSHOT mode sends all CC values immediately."""
        mock_port = Mock()
        scheduler = PlaybackScheduler(output_port=mock_port)

        scheduler.start_pattern_playback(multi_cc_pattern, PlaybackMode.SNAPSHOT)

        # Wait briefly for snapshot to be sent
        time.sleep(0.05)

        # Should have sent CC values immediately (one for each unique CC number)
        # CC74: 127 -> 64 (last is 64)
        # CC71: 100 (only one)
        assert mock_port.send_cc.call_count == 2

    def test_attack_decay_mode(self, simple_pattern: AutomationPattern) -> None:
        """ATTACK_DECAY mode plays full sequence (gate control not yet implemented)."""
        mock_port = Mock()
        scheduler = PlaybackScheduler(output_port=mock_port)

        scheduler.start_pattern_playback(simple_pattern, PlaybackMode.ATTACK_DECAY)

        # Wait for playback to complete
        time.sleep(0.3)

        # Currently falls back to full sequence
        assert mock_port.send_cc.call_count == 5


class TestConcurrentPlaybacks:
    """Tests for multiple concurrent playbacks."""

    def test_multiple_patterns_play_concurrently(
        self, simple_pattern: AutomationPattern
    ) -> None:
        """Multiple patterns can play at the same time."""
        mock_port = Mock()
        scheduler = PlaybackScheduler(output_port=mock_port)

        # Start three concurrent playbacks
        id1 = scheduler.start_pattern_playback(
            simple_pattern, PlaybackMode.FULL_SEQUENCE
        )
        id2 = scheduler.start_pattern_playback(simple_pattern, PlaybackMode.ATTACK_ONLY)
        id3 = scheduler.start_pattern_playback(simple_pattern, PlaybackMode.DECAY_ONLY)

        # All should be tracked
        assert len(scheduler.active_playbacks) == 3
        assert id1 in scheduler.active_playbacks
        assert id2 in scheduler.active_playbacks
        assert id3 in scheduler.active_playbacks

        # Wait for playbacks to complete
        time.sleep(0.3)

        # Should have sent events from all three (5 + 3 + 2 = 10)
        assert mock_port.send_cc.call_count == 10

    def test_playbacks_complete_independently(
        self, simple_pattern: AutomationPattern
    ) -> None:
        """Playbacks finish independently without affecting each other."""
        scheduler = PlaybackScheduler()

        # Start two playbacks
        id1 = scheduler.start_pattern_playback(
            simple_pattern, PlaybackMode.FULL_SEQUENCE
        )
        id2 = scheduler.start_pattern_playback(
            simple_pattern, PlaybackMode.FULL_SEQUENCE
        )

        # Stop one
        scheduler.stop_pattern_playback(id1)

        # The other should still be active
        assert id1 not in scheduler.active_playbacks
        assert id2 in scheduler.active_playbacks


class TestThreadSafety:
    """Tests for thread-safe operations."""

    def test_concurrent_start_and_stop(
        self, simple_pattern: AutomationPattern
    ) -> None:
        """Starting and stopping playbacks concurrently is safe."""
        scheduler = PlaybackScheduler()

        # Start and immediately stop multiple times
        for _ in range(10):
            playback_id = scheduler.start_pattern_playback(
                simple_pattern, PlaybackMode.FULL_SEQUENCE
            )
            scheduler.stop_pattern_playback(playback_id)

        # Should complete without errors
        assert len(scheduler.active_playbacks) == 0

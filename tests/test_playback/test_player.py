"""Tests for AutomationPlayer playback functionality."""

import time
from typing import List, Tuple
from unittest.mock import Mock

import pytest

from midi_maker.automation import AutomationPattern
from midi_maker.core import CCEvent
from midi_maker.playback import AutomationPlayer


class TestAutomationPlayerInit:
    """Tests for AutomationPlayer initialization."""

    def test_init_without_output_port(self) -> None:
        """Player can be created without an output port."""
        player = AutomationPlayer()
        assert player.output_port is None

    def test_init_with_output_port(self) -> None:
        """Player accepts an output port."""
        mock_port = Mock()
        player = AutomationPlayer(output_port=mock_port)
        assert player.output_port is mock_port


class TestCCOutputCallback:
    """Tests for the callback mechanism."""

    def test_set_callback(self) -> None:
        """Callback can be set."""
        player = AutomationPlayer()
        callback = Mock()
        player.set_cc_output_callback(callback)
        assert player._cc_output_callback is callback

    def test_clear_callback(self) -> None:
        """Callback can be cleared by setting to None."""
        player = AutomationPlayer()
        callback = Mock()
        player.set_cc_output_callback(callback)
        player.set_cc_output_callback(None)
        assert player._cc_output_callback is None

    def test_callback_receives_cc_values(self) -> None:
        """Callback is invoked with correct CC values."""
        player = AutomationPlayer()
        received: List[Tuple[int, int, int]] = []
        player.set_cc_output_callback(lambda cc, val, ch: received.append((cc, val, ch)))

        player._send_cc(74, 100, 0)

        assert received == [(74, 100, 0)]

    def test_callback_and_port_both_receive(self) -> None:
        """Both callback and port receive CC messages."""
        mock_port = Mock()
        player = AutomationPlayer(output_port=mock_port)
        received: List[Tuple[int, int, int]] = []
        player.set_cc_output_callback(lambda cc, val, ch: received.append((cc, val, ch)))

        player._send_cc(74, 100, 0)

        mock_port.send_cc.assert_called_once_with(74, 100, 0)
        assert received == [(74, 100, 0)]


class TestPlayCCSnapshot:
    """Tests for playing CC snapshots."""

    def test_snapshot_sends_all_values(self) -> None:
        """Snapshot sends all provided CC values."""
        player = AutomationPlayer()
        received: List[Tuple[int, int, int]] = []
        player.set_cc_output_callback(lambda cc, val, ch: received.append((cc, val, ch)))

        player.play_cc_snapshot({74: 100, 71: 50, 1: 127})

        assert len(received) == 3
        assert (74, 100, 0) in received
        assert (71, 50, 0) in received
        assert (1, 127, 0) in received

    def test_snapshot_uses_specified_channel(self) -> None:
        """Snapshot sends on the specified channel."""
        player = AutomationPlayer()
        received: List[Tuple[int, int, int]] = []
        player.set_cc_output_callback(lambda cc, val, ch: received.append((cc, val, ch)))

        player.play_cc_snapshot({74: 100}, channel=5)

        assert received == [(74, 100, 5)]

    def test_snapshot_empty_dict(self) -> None:
        """Snapshot with empty dict sends nothing."""
        player = AutomationPlayer()
        received: List[Tuple[int, int, int]] = []
        player.set_cc_output_callback(lambda cc, val, ch: received.append((cc, val, ch)))

        player.play_cc_snapshot({})

        assert received == []


class TestPlayEvents:
    """Tests for playing event sequences."""

    def test_play_empty_events(self) -> None:
        """Playing empty event list does nothing."""
        player = AutomationPlayer()
        received: List[Tuple[int, int, int]] = []
        player.set_cc_output_callback(lambda cc, val, ch: received.append((cc, val, ch)))

        player._play_events([])

        assert received == []

    def test_play_single_event(self) -> None:
        """Single event is sent correctly."""
        player = AutomationPlayer()
        received: List[Tuple[int, int, int]] = []
        player.set_cc_output_callback(lambda cc, val, ch: received.append((cc, val, ch)))

        event = CCEvent(cc_number=74, value=100, channel=0, timestamp=0.0)
        player._play_events([event])

        assert received == [(74, 100, 0)]

    def test_play_multiple_events_order(self) -> None:
        """Events are sent in order."""
        player = AutomationPlayer()
        received: List[Tuple[int, int, int]] = []
        player.set_cc_output_callback(lambda cc, val, ch: received.append((cc, val, ch)))

        events = [
            CCEvent(cc_number=74, value=50, channel=0, timestamp=0.0),
            CCEvent(cc_number=74, value=100, channel=0, timestamp=0.001),
            CCEvent(cc_number=74, value=75, channel=0, timestamp=0.002),
        ]
        player._play_events(events)

        assert received == [(74, 50, 0), (74, 100, 0), (74, 75, 0)]

    def test_play_respects_timing(self) -> None:
        """Events are delayed based on timestamps."""
        player = AutomationPlayer()
        timestamps: List[float] = []
        start_time = time.time()
        player.set_cc_output_callback(
            lambda cc, val, ch: timestamps.append(time.time() - start_time)
        )

        events = [
            CCEvent(cc_number=74, value=50, channel=0, timestamp=0.0),
            CCEvent(cc_number=74, value=100, channel=0, timestamp=0.05),
            CCEvent(cc_number=74, value=75, channel=0, timestamp=0.1),
        ]

        player._play_events(events)

        # First event should be immediate (within tolerance)
        assert timestamps[0] < 0.02

        # Second event should be ~50ms after first
        assert 0.03 < timestamps[1] < 0.08

        # Third event should be ~100ms after first
        assert 0.08 < timestamps[2] < 0.15


class TestPlayFullSequence:
    """Tests for playing full automation patterns."""

    def test_play_full_sequence(self) -> None:
        """Full sequence plays all events."""
        player = AutomationPlayer()
        received: List[Tuple[int, int, int]] = []
        player.set_cc_output_callback(lambda cc, val, ch: received.append((cc, val, ch)))

        events = [
            CCEvent(cc_number=74, value=50, channel=0, timestamp=0.0),
            CCEvent(cc_number=74, value=100, channel=0, timestamp=0.001),
            CCEvent(cc_number=74, value=75, channel=0, timestamp=0.002),
        ]
        pattern = AutomationPattern(
            pattern_id="test-1",
            name="Test Pattern",
            cc_events=events,
            duration=0.002,
        )

        player.play_full_sequence(pattern)

        assert len(received) == 3
        assert received[0] == (74, 50, 0)
        assert received[1] == (74, 100, 0)
        assert received[2] == (74, 75, 0)

    def test_play_empty_pattern(self) -> None:
        """Empty pattern plays nothing."""
        player = AutomationPlayer()
        received: List[Tuple[int, int, int]] = []
        player.set_cc_output_callback(lambda cc, val, ch: received.append((cc, val, ch)))

        pattern = AutomationPattern(
            pattern_id="empty",
            name="Empty Pattern",
            cc_events=[],
            duration=0.0,
        )

        player.play_full_sequence(pattern)

        assert received == []


class TestPlayAttackPhase:
    """Tests for playing attack phases."""

    def test_play_attack_events(self) -> None:
        """Attack events are played correctly."""
        player = AutomationPlayer()
        received: List[Tuple[int, int, int]] = []
        player.set_cc_output_callback(lambda cc, val, ch: received.append((cc, val, ch)))

        attack_events = [
            CCEvent(cc_number=74, value=50, channel=0, timestamp=0.0),
            CCEvent(cc_number=74, value=75, channel=0, timestamp=0.001),
            CCEvent(cc_number=74, value=100, channel=0, timestamp=0.002),
        ]

        player.play_attack_phase(attack_events)

        assert len(received) == 3
        assert received == [(74, 50, 0), (74, 75, 0), (74, 100, 0)]


class TestPlayDecayPhase:
    """Tests for playing decay phases."""

    def test_play_decay_events(self) -> None:
        """Decay events are played correctly."""
        player = AutomationPlayer()
        received: List[Tuple[int, int, int]] = []
        player.set_cc_output_callback(lambda cc, val, ch: received.append((cc, val, ch)))

        decay_events = [
            CCEvent(cc_number=74, value=90, channel=1, timestamp=0.003),
            CCEvent(cc_number=74, value=60, channel=1, timestamp=0.004),
            CCEvent(cc_number=74, value=30, channel=1, timestamp=0.005),
        ]

        player.play_decay_phase(decay_events)

        assert len(received) == 3
        assert received == [(74, 90, 1), (74, 60, 1), (74, 30, 1)]


class TestWithMockPort:
    """Tests using mock MIDI output port."""

    def test_port_receives_cc(self) -> None:
        """Output port's send_cc is called."""
        mock_port = Mock()
        player = AutomationPlayer(output_port=mock_port)

        player.play_cc_snapshot({74: 100})

        mock_port.send_cc.assert_called_once_with(74, 100, 0)

    def test_full_sequence_through_port(self) -> None:
        """Full sequence sends all events through port."""
        mock_port = Mock()
        player = AutomationPlayer(output_port=mock_port)

        events = [
            CCEvent(cc_number=1, value=64, channel=0, timestamp=0.0),
            CCEvent(cc_number=2, value=127, channel=1, timestamp=0.001),
        ]
        pattern = AutomationPattern(
            pattern_id="test",
            name="Test",
            cc_events=events,
            duration=0.001,
        )

        player.play_full_sequence(pattern)

        assert mock_port.send_cc.call_count == 2
        mock_port.send_cc.assert_any_call(1, 64, 0)
        mock_port.send_cc.assert_any_call(2, 127, 1)


class TestNoOutput:
    """Tests for player with no output configured."""

    def test_no_output_no_error(self) -> None:
        """Player without output or callback doesn't error."""
        player = AutomationPlayer()

        # Should not raise
        player.play_cc_snapshot({74: 100})
        player._play_events([CCEvent(cc_number=74, value=50, channel=0, timestamp=0.0)])

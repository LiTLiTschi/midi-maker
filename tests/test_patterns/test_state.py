"""Tests for GateStateMachine."""

import pytest

from midi_maker.core import GateState
from midi_maker.patterns.state import (
    GateStateMachine,
    GateTransition,
    GateEvent,
    ChannelGateInfo,
)


class TestGateTransitionEnum:
    """Tests for GateTransition enum."""

    def test_transition_values_exist(self):
        """Test all expected transition types exist."""
        assert GateTransition.OPENED is not None
        assert GateTransition.CLOSED is not None
        assert GateTransition.NO_CHANGE is not None

    def test_transitions_are_distinct(self):
        """Test that all transitions have unique values."""
        values = [t.value for t in GateTransition]
        assert len(values) == len(set(values))


class TestGateEventDataclass:
    """Tests for GateEvent dataclass."""

    def test_create_gate_event(self):
        """Test creating a GateEvent."""
        event = GateEvent(channel=0, state=GateState.OPEN, timestamp=1.5)
        
        assert event.channel == 0
        assert event.state == GateState.OPEN
        assert event.timestamp == 1.5

    def test_gate_event_equality(self):
        """Test GateEvent equality."""
        event1 = GateEvent(channel=0, state=GateState.OPEN, timestamp=1.5)
        event2 = GateEvent(channel=0, state=GateState.OPEN, timestamp=1.5)
        
        assert event1 == event2


class TestChannelGateInfoDataclass:
    """Tests for ChannelGateInfo dataclass."""

    def test_default_values(self):
        """Test default values for ChannelGateInfo."""
        info = ChannelGateInfo()
        
        assert info.state == GateState.CLOSED
        assert info.open_timestamp == 0.0
        assert info.open_count == 0


class TestGateStateMachineInit:
    """Tests for GateStateMachine initialization."""

    def test_init_default_history_size(self):
        """Test initialization with default history size."""
        gsm = GateStateMachine()
        assert len(gsm.get_history()) == 0

    def test_init_custom_history_size(self):
        """Test initialization with custom history size."""
        gsm = GateStateMachine(history_size=10)
        # Fill history beyond capacity
        for i in range(15):
            gsm.update_gate_state(channel=0, gate_on=(i % 2 == 0))
        
        assert len(gsm.get_history()) == 10


class TestGateStateMachineTransitions:
    """Tests for gate state transitions."""

    def test_gate_on_from_closed(self):
        """Test gate-on when gate is closed returns OPENED."""
        gsm = GateStateMachine()
        transition = gsm.update_gate_state(channel=0, gate_on=True)
        
        assert transition == GateTransition.OPENED
        assert gsm.get_current_state(0) == GateState.OPEN

    def test_gate_off_from_open(self):
        """Test gate-off when gate is open returns CLOSED."""
        gsm = GateStateMachine()
        gsm.update_gate_state(channel=0, gate_on=True)
        transition = gsm.update_gate_state(channel=0, gate_on=False)
        
        assert transition == GateTransition.CLOSED
        assert gsm.get_current_state(0) == GateState.CLOSED

    def test_gate_on_when_already_open(self):
        """Test gate-on when gate is already open returns NO_CHANGE."""
        gsm = GateStateMachine()
        gsm.update_gate_state(channel=0, gate_on=True)
        transition = gsm.update_gate_state(channel=0, gate_on=True)
        
        assert transition == GateTransition.NO_CHANGE
        assert gsm.get_current_state(0) == GateState.OPEN

    def test_gate_off_when_already_closed(self):
        """Test gate-off when gate is already closed returns NO_CHANGE."""
        gsm = GateStateMachine()
        transition = gsm.update_gate_state(channel=0, gate_on=False)
        
        assert transition == GateTransition.NO_CHANGE
        assert gsm.get_current_state(0) == GateState.CLOSED

    def test_multiple_channels_independent(self):
        """Test that channels are tracked independently."""
        gsm = GateStateMachine()
        
        gsm.update_gate_state(channel=0, gate_on=True)
        gsm.update_gate_state(channel=1, gate_on=True)
        gsm.update_gate_state(channel=0, gate_on=False)
        
        assert gsm.get_current_state(0) == GateState.CLOSED
        assert gsm.get_current_state(1) == GateState.OPEN


class TestGateStateMachineOverlapping:
    """Tests for overlapping gate detection."""

    def test_no_overlap_initially(self):
        """Test no overlap on fresh channel."""
        gsm = GateStateMachine()
        assert gsm.has_overlapping_gates(0) is False

    def test_no_overlap_single_gate(self):
        """Test no overlap with single gate-on."""
        gsm = GateStateMachine()
        gsm.update_gate_state(channel=0, gate_on=True)
        
        assert gsm.has_overlapping_gates(0) is False

    def test_overlap_detected_on_second_gate_on(self):
        """Test overlap detected when second gate-on without gate-off."""
        gsm = GateStateMachine()
        gsm.update_gate_state(channel=0, gate_on=True)
        gsm.update_gate_state(channel=0, gate_on=True)
        
        assert gsm.has_overlapping_gates(0) is True
        assert gsm.get_open_count(0) == 2

    def test_overlap_resolved_on_gate_off(self):
        """Test overlap resolved when gate-off reduces count."""
        gsm = GateStateMachine()
        gsm.update_gate_state(channel=0, gate_on=True)
        gsm.update_gate_state(channel=0, gate_on=True)
        gsm.update_gate_state(channel=0, gate_on=False)
        
        assert gsm.has_overlapping_gates(0) is False
        assert gsm.get_open_count(0) == 1
        assert gsm.get_current_state(0) == GateState.OPEN

    def test_fully_closed_after_all_gate_offs(self):
        """Test gate closes only after all overlapping gates are released."""
        gsm = GateStateMachine()
        gsm.update_gate_state(channel=0, gate_on=True)
        gsm.update_gate_state(channel=0, gate_on=True)
        gsm.update_gate_state(channel=0, gate_on=True)
        
        assert gsm.get_open_count(0) == 3
        
        gsm.update_gate_state(channel=0, gate_on=False)
        assert gsm.get_current_state(0) == GateState.OPEN
        
        gsm.update_gate_state(channel=0, gate_on=False)
        assert gsm.get_current_state(0) == GateState.OPEN
        
        transition = gsm.update_gate_state(channel=0, gate_on=False)
        assert gsm.get_current_state(0) == GateState.CLOSED
        assert transition == GateTransition.CLOSED


class TestGateStateMachineDuration:
    """Tests for gate duration calculation."""

    def test_duration_zero_when_closed(self):
        """Test duration is 0 when gate is closed."""
        gsm = GateStateMachine()
        assert gsm.get_gate_duration(0) == 0.0

    def test_duration_positive_when_open(self):
        """Test duration is positive when gate is open."""
        gsm = GateStateMachine()
        # Mock time function for deterministic tests
        mock_time = [1.0]
        gsm._time_func = lambda: mock_time[0]
        
        gsm.update_gate_state(channel=0, gate_on=True)
        
        mock_time[0] = 1.5
        duration = gsm.get_gate_duration(0)
        
        assert duration == pytest.approx(0.5)

    def test_duration_after_reopen(self):
        """Test duration resets when gate reopens."""
        gsm = GateStateMachine()
        mock_time = [1.0]
        gsm._time_func = lambda: mock_time[0]
        
        gsm.update_gate_state(channel=0, gate_on=True)
        mock_time[0] = 2.0
        gsm.update_gate_state(channel=0, gate_on=False)
        
        mock_time[0] = 3.0
        gsm.update_gate_state(channel=0, gate_on=True)
        
        mock_time[0] = 3.25
        duration = gsm.get_gate_duration(0)
        
        assert duration == pytest.approx(0.25)


class TestGateStateMachineHistory:
    """Tests for gate event history."""

    def test_history_records_events(self):
        """Test that events are recorded in history."""
        gsm = GateStateMachine()
        gsm.update_gate_state(channel=0, gate_on=True)
        gsm.update_gate_state(channel=0, gate_on=False)
        
        history = gsm.get_history()
        
        assert len(history) == 2
        assert history[0].channel == 0
        assert history[0].state == GateState.OPEN
        assert history[1].channel == 0
        assert history[1].state == GateState.CLOSED

    def test_history_limits_size(self):
        """Test that history respects max size."""
        gsm = GateStateMachine(history_size=5)
        
        for i in range(10):
            gsm.update_gate_state(channel=0, gate_on=(i % 2 == 0))
        
        history = gsm.get_history()
        assert len(history) == 5


class TestGateStateMachineClear:
    """Tests for clearing state."""

    def test_clear_channel(self):
        """Test clearing a single channel."""
        gsm = GateStateMachine()
        gsm.update_gate_state(channel=0, gate_on=True)
        gsm.update_gate_state(channel=1, gate_on=True)
        
        gsm.clear_channel(0)
        
        assert gsm.get_current_state(0) == GateState.CLOSED
        assert gsm.get_current_state(1) == GateState.OPEN

    def test_clear_all(self):
        """Test clearing all channels and history."""
        gsm = GateStateMachine()
        gsm.update_gate_state(channel=0, gate_on=True)
        gsm.update_gate_state(channel=1, gate_on=True)
        
        gsm.clear_all()
        
        assert gsm.get_current_state(0) == GateState.CLOSED
        assert gsm.get_current_state(1) == GateState.CLOSED
        assert len(gsm.get_history()) == 0

    def test_clear_nonexistent_channel_is_safe(self):
        """Test clearing a channel that was never used."""
        gsm = GateStateMachine()
        gsm.clear_channel(99)  # Should not raise


class TestGateStateMachineEdgeCases:
    """Tests for edge cases."""

    def test_high_channel_numbers(self):
        """Test handling of high channel numbers."""
        gsm = GateStateMachine()
        transition = gsm.update_gate_state(channel=15, gate_on=True)
        
        assert transition == GateTransition.OPENED
        assert gsm.get_current_state(15) == GateState.OPEN

    def test_open_count_does_not_go_negative(self):
        """Test that open_count doesn't go below zero."""
        gsm = GateStateMachine()
        # Send multiple gate-offs without gate-ons
        gsm.update_gate_state(channel=0, gate_on=False)
        gsm.update_gate_state(channel=0, gate_on=False)
        gsm.update_gate_state(channel=0, gate_on=False)
        
        assert gsm.get_open_count(0) == 0

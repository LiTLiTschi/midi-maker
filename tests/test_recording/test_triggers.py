"""Tests for TriggerHandler class."""

import pytest

from midi_maker.core import RecordingMode, RecordingState
from midi_maker.recording import TriggerHandler


class TestTriggerHandlerInit:
    """Tests for TriggerHandler initialization."""
    
    def test_init_without_trigger_port(self) -> None:
        """TriggerHandler can be created without a trigger port."""
        handler = TriggerHandler()
        assert handler.trigger_port is None
        assert handler.recording_state == RecordingState.IDLE
        assert handler.mode == RecordingMode.TOGGLE
    
    def test_init_with_trigger_port(self) -> None:
        """TriggerHandler can be created with a trigger port."""
        mock_port = object()
        handler = TriggerHandler(trigger_port=mock_port)
        assert handler.trigger_port is mock_port
    
    def test_default_state_is_idle(self) -> None:
        """Handler starts in IDLE state."""
        handler = TriggerHandler()
        assert handler.get_state() == RecordingState.IDLE
    
    def test_default_mode_is_toggle(self) -> None:
        """Handler defaults to TOGGLE mode."""
        handler = TriggerHandler()
        assert handler.mode == RecordingMode.TOGGLE


class TestTriggerHandlerToggleMode:
    """Tests for TOGGLE mode behavior."""
    
    def test_toggle_idle_to_recording(self) -> None:
        """In TOGGLE mode, press starts recording from IDLE."""
        handler = TriggerHandler()
        handler.set_mode(RecordingMode.TOGGLE)
        
        handler.handle_trigger_on()
        
        assert handler.get_state() == RecordingState.RECORDING
    
    def test_toggle_recording_to_stopped(self) -> None:
        """In TOGGLE mode, press stops recording from RECORDING."""
        handler = TriggerHandler()
        handler.set_mode(RecordingMode.TOGGLE)
        handler.handle_trigger_on()  # IDLE -> RECORDING
        
        handler.handle_trigger_on()  # RECORDING -> STOPPED
        
        assert handler.get_state() == RecordingState.STOPPED
    
    def test_toggle_stopped_to_recording(self) -> None:
        """In TOGGLE mode, press starts new recording from STOPPED."""
        handler = TriggerHandler()
        handler.set_mode(RecordingMode.TOGGLE)
        handler.handle_trigger_on()  # IDLE -> RECORDING
        handler.handle_trigger_on()  # RECORDING -> STOPPED
        
        handler.handle_trigger_on()  # STOPPED -> RECORDING
        
        assert handler.get_state() == RecordingState.RECORDING
    
    def test_toggle_release_does_nothing(self) -> None:
        """In TOGGLE mode, release does not change state."""
        handler = TriggerHandler()
        handler.set_mode(RecordingMode.TOGGLE)
        handler.handle_trigger_on()  # IDLE -> RECORDING
        
        handler.handle_trigger_off()
        
        # Still recording
        assert handler.get_state() == RecordingState.RECORDING
    
    def test_toggle_release_when_idle(self) -> None:
        """In TOGGLE mode, release when IDLE does nothing."""
        handler = TriggerHandler()
        handler.set_mode(RecordingMode.TOGGLE)
        
        handler.handle_trigger_off()
        
        assert handler.get_state() == RecordingState.IDLE
    
    def test_toggle_full_cycle(self) -> None:
        """Test complete toggle cycle: idle -> recording -> stopped -> recording."""
        handler = TriggerHandler()
        handler.set_mode(RecordingMode.TOGGLE)
        
        assert handler.get_state() == RecordingState.IDLE
        
        handler.handle_trigger_on()
        assert handler.get_state() == RecordingState.RECORDING
        
        handler.handle_trigger_off()  # No effect in toggle mode
        assert handler.get_state() == RecordingState.RECORDING
        
        handler.handle_trigger_on()
        assert handler.get_state() == RecordingState.STOPPED
        
        handler.handle_trigger_on()
        assert handler.get_state() == RecordingState.RECORDING


class TestTriggerHandlerHoldMode:
    """Tests for HOLD mode behavior."""
    
    def test_hold_press_starts_recording(self) -> None:
        """In HOLD mode, press starts recording from IDLE."""
        handler = TriggerHandler()
        handler.set_mode(RecordingMode.HOLD)
        
        handler.handle_trigger_on()
        
        assert handler.get_state() == RecordingState.RECORDING
    
    def test_hold_release_stops_recording(self) -> None:
        """In HOLD mode, release stops recording."""
        handler = TriggerHandler()
        handler.set_mode(RecordingMode.HOLD)
        handler.handle_trigger_on()  # Start recording
        
        handler.handle_trigger_off()
        
        assert handler.get_state() == RecordingState.STOPPED
    
    def test_hold_press_after_stopped_starts_new_recording(self) -> None:
        """In HOLD mode, press starts new recording from STOPPED."""
        handler = TriggerHandler()
        handler.set_mode(RecordingMode.HOLD)
        handler.handle_trigger_on()
        handler.handle_trigger_off()  # STOPPED
        
        handler.handle_trigger_on()
        
        assert handler.get_state() == RecordingState.RECORDING
    
    def test_hold_release_when_idle(self) -> None:
        """In HOLD mode, release when IDLE does nothing."""
        handler = TriggerHandler()
        handler.set_mode(RecordingMode.HOLD)
        
        handler.handle_trigger_off()
        
        assert handler.get_state() == RecordingState.IDLE
    
    def test_hold_press_while_recording_does_nothing(self) -> None:
        """In HOLD mode, press while recording does not change state."""
        handler = TriggerHandler()
        handler.set_mode(RecordingMode.HOLD)
        handler.handle_trigger_on()  # Start recording
        
        handler.handle_trigger_on()  # Second press
        
        assert handler.get_state() == RecordingState.RECORDING
    
    def test_hold_full_cycle(self) -> None:
        """Test complete hold cycle: idle -> recording -> stopped -> recording."""
        handler = TriggerHandler()
        handler.set_mode(RecordingMode.HOLD)
        
        assert handler.get_state() == RecordingState.IDLE
        
        handler.handle_trigger_on()
        assert handler.get_state() == RecordingState.RECORDING
        
        handler.handle_trigger_off()
        assert handler.get_state() == RecordingState.STOPPED
        
        handler.handle_trigger_on()
        assert handler.get_state() == RecordingState.RECORDING
        
        handler.handle_trigger_off()
        assert handler.get_state() == RecordingState.STOPPED


class TestTriggerHandlerSetMode:
    """Tests for set_mode method."""
    
    def test_set_mode_to_hold(self) -> None:
        """set_mode can switch to HOLD mode."""
        handler = TriggerHandler()
        
        handler.set_mode(RecordingMode.HOLD)
        
        assert handler.mode == RecordingMode.HOLD
    
    def test_set_mode_to_toggle(self) -> None:
        """set_mode can switch to TOGGLE mode."""
        handler = TriggerHandler()
        handler.set_mode(RecordingMode.HOLD)
        
        handler.set_mode(RecordingMode.TOGGLE)
        
        assert handler.mode == RecordingMode.TOGGLE
    
    def test_set_mode_invalid_type_raises(self) -> None:
        """set_mode raises TypeError for invalid type."""
        handler = TriggerHandler()
        
        with pytest.raises(TypeError, match="must be RecordingMode"):
            handler.set_mode("toggle")  # type: ignore
    
    def test_mode_change_mid_recording(self) -> None:
        """Mode can be changed while recording (state preserved)."""
        handler = TriggerHandler()
        handler.set_mode(RecordingMode.TOGGLE)
        handler.handle_trigger_on()  # RECORDING
        
        handler.set_mode(RecordingMode.HOLD)
        
        assert handler.mode == RecordingMode.HOLD
        assert handler.get_state() == RecordingState.RECORDING
        
        # Now release should stop (HOLD mode)
        handler.handle_trigger_off()
        assert handler.get_state() == RecordingState.STOPPED


class TestTriggerHandlerReset:
    """Tests for reset method."""
    
    def test_reset_from_recording(self) -> None:
        """reset returns to IDLE from RECORDING."""
        handler = TriggerHandler()
        handler.handle_trigger_on()
        
        handler.reset()
        
        assert handler.get_state() == RecordingState.IDLE
    
    def test_reset_from_stopped(self) -> None:
        """reset returns to IDLE from STOPPED."""
        handler = TriggerHandler()
        handler.handle_trigger_on()
        handler.handle_trigger_on()  # STOPPED
        
        handler.reset()
        
        assert handler.get_state() == RecordingState.IDLE
    
    def test_reset_from_idle(self) -> None:
        """reset when already IDLE stays IDLE."""
        handler = TriggerHandler()
        
        handler.reset()
        
        assert handler.get_state() == RecordingState.IDLE


class TestTriggerHandlerProperties:
    """Tests for property accessors."""
    
    def test_is_recording_true(self) -> None:
        """is_recording is True when RECORDING."""
        handler = TriggerHandler()
        handler.handle_trigger_on()
        
        assert handler.is_recording is True
    
    def test_is_recording_false_when_idle(self) -> None:
        """is_recording is False when IDLE."""
        handler = TriggerHandler()
        
        assert handler.is_recording is False
    
    def test_is_recording_false_when_stopped(self) -> None:
        """is_recording is False when STOPPED."""
        handler = TriggerHandler()
        handler.handle_trigger_on()
        handler.handle_trigger_on()
        
        assert handler.is_recording is False
    
    def test_is_idle_true(self) -> None:
        """is_idle is True when IDLE."""
        handler = TriggerHandler()
        
        assert handler.is_idle is True
    
    def test_is_idle_false_when_recording(self) -> None:
        """is_idle is False when RECORDING."""
        handler = TriggerHandler()
        handler.handle_trigger_on()
        
        assert handler.is_idle is False
    
    def test_is_stopped_true(self) -> None:
        """is_stopped is True when STOPPED."""
        handler = TriggerHandler()
        handler.handle_trigger_on()
        handler.handle_trigger_on()
        
        assert handler.is_stopped is True
    
    def test_is_stopped_false_when_idle(self) -> None:
        """is_stopped is False when IDLE."""
        handler = TriggerHandler()
        
        assert handler.is_stopped is False


class TestTriggerHandlerStateChangeCallback:
    """Tests for state change callback functionality."""
    
    def test_callback_called_on_state_change(self) -> None:
        """Callback is invoked when state changes."""
        handler = TriggerHandler()
        changes: list[tuple[RecordingState, RecordingState]] = []
        
        handler.set_on_state_change(lambda old, new: changes.append((old, new)))
        handler.handle_trigger_on()
        
        assert len(changes) == 1
        assert changes[0] == (RecordingState.IDLE, RecordingState.RECORDING)
    
    def test_callback_not_called_when_no_change(self) -> None:
        """Callback is not invoked when state doesn't change."""
        handler = TriggerHandler()
        handler.set_mode(RecordingMode.TOGGLE)
        handler.handle_trigger_on()  # RECORDING
        
        changes: list[tuple[RecordingState, RecordingState]] = []
        handler.set_on_state_change(lambda old, new: changes.append((old, new)))
        
        handler.handle_trigger_off()  # No change in TOGGLE mode
        
        assert len(changes) == 0
    
    def test_callback_multiple_transitions(self) -> None:
        """Callback tracks multiple state transitions."""
        handler = TriggerHandler()
        changes: list[tuple[RecordingState, RecordingState]] = []
        
        handler.set_on_state_change(lambda old, new: changes.append((old, new)))
        
        handler.handle_trigger_on()  # IDLE -> RECORDING
        handler.handle_trigger_on()  # RECORDING -> STOPPED
        handler.handle_trigger_on()  # STOPPED -> RECORDING
        
        assert len(changes) == 3
        assert changes[0] == (RecordingState.IDLE, RecordingState.RECORDING)
        assert changes[1] == (RecordingState.RECORDING, RecordingState.STOPPED)
        assert changes[2] == (RecordingState.STOPPED, RecordingState.RECORDING)
    
    def test_callback_on_reset(self) -> None:
        """Callback is invoked on reset."""
        handler = TriggerHandler()
        handler.handle_trigger_on()  # RECORDING
        
        changes: list[tuple[RecordingState, RecordingState]] = []
        handler.set_on_state_change(lambda old, new: changes.append((old, new)))
        
        handler.reset()
        
        assert len(changes) == 1
        assert changes[0] == (RecordingState.RECORDING, RecordingState.IDLE)
    
    def test_remove_callback(self) -> None:
        """Callback can be removed by setting to None."""
        handler = TriggerHandler()
        changes: list[tuple[RecordingState, RecordingState]] = []
        
        handler.set_on_state_change(lambda old, new: changes.append((old, new)))
        handler.handle_trigger_on()  # Callback invoked
        
        handler.set_on_state_change(None)
        handler.handle_trigger_on()  # Callback not invoked
        
        assert len(changes) == 1


class TestTriggerHandlerWithMidiMsg:
    """Tests verifying msg parameter is accepted but optional."""
    
    def test_handle_trigger_on_with_msg(self) -> None:
        """handle_trigger_on accepts a MIDI message."""
        handler = TriggerHandler()
        mock_msg = {"type": "note_on", "note": 64}
        
        handler.handle_trigger_on(mock_msg)
        
        assert handler.get_state() == RecordingState.RECORDING
    
    def test_handle_trigger_off_with_msg(self) -> None:
        """handle_trigger_off accepts a MIDI message."""
        handler = TriggerHandler()
        handler.set_mode(RecordingMode.HOLD)
        handler.handle_trigger_on()
        
        mock_msg = {"type": "note_off", "note": 64}
        handler.handle_trigger_off(mock_msg)
        
        assert handler.get_state() == RecordingState.STOPPED
    
    def test_handle_trigger_on_with_none(self) -> None:
        """handle_trigger_on works with None msg."""
        handler = TriggerHandler()
        
        handler.handle_trigger_on(None)
        
        assert handler.get_state() == RecordingState.RECORDING
    
    def test_handle_trigger_off_with_none(self) -> None:
        """handle_trigger_off works with None msg."""
        handler = TriggerHandler()
        handler.set_mode(RecordingMode.HOLD)
        handler.handle_trigger_on(None)
        
        handler.handle_trigger_off(None)
        
        assert handler.get_state() == RecordingState.STOPPED

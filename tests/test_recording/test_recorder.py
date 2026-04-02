"""Tests for CCRecorder class."""

import pytest
import time

from midi_maker.automation import AutomationPattern
from midi_maker.core import RecordingMode, RecordingState
from midi_maker.recording import CCRecorder


class TestCCRecorderInit:
    """Tests for CCRecorder initialization."""
    
    def test_init_without_ports(self) -> None:
        """CCRecorder can be created without MIDI ports."""
        recorder = CCRecorder()
        assert recorder.trigger_handler is not None
        assert recorder.stream_capture is not None
        assert recorder.recording_mode == RecordingMode.TOGGLE
        assert recorder.current_pattern_id is None
    
    def test_init_with_ports(self) -> None:
        """CCRecorder can be created with MIDI ports."""
        mock_trigger = object()
        mock_source = object()
        recorder = CCRecorder(trigger_port=mock_trigger, source_port=mock_source)
        assert recorder.trigger_handler.trigger_port is mock_trigger
        assert recorder.stream_capture.source_port is mock_source
    
    def test_default_mode_is_toggle(self) -> None:
        """Recorder defaults to TOGGLE mode."""
        recorder = CCRecorder()
        assert recorder.recording_mode == RecordingMode.TOGGLE
    
    def test_initial_state_is_idle(self) -> None:
        """Recorder starts in IDLE state."""
        recorder = CCRecorder()
        assert recorder.get_state() == RecordingState.IDLE
        assert recorder.is_idle is True


class TestCCRecorderStartRecording:
    """Tests for start_recording method."""
    
    def test_start_recording_returns_pattern_id(self) -> None:
        """start_recording returns a pattern ID."""
        recorder = CCRecorder()
        pattern_id = recorder.start_recording()
        assert pattern_id is not None
        assert isinstance(pattern_id, str)
        assert len(pattern_id) > 0
    
    def test_start_recording_with_custom_id(self) -> None:
        """start_recording accepts custom pattern ID."""
        recorder = CCRecorder()
        custom_id = "my-custom-pattern"
        pattern_id = recorder.start_recording(pattern_id=custom_id)
        assert pattern_id == custom_id
        assert recorder.current_pattern_id == custom_id
    
    def test_start_recording_sets_is_recording(self) -> None:
        """start_recording sets is_recording to True."""
        recorder = CCRecorder()
        recorder.start_recording()
        assert recorder.is_recording is True
    
    def test_start_recording_sets_current_pattern_id(self) -> None:
        """start_recording sets current_pattern_id."""
        recorder = CCRecorder()
        pattern_id = recorder.start_recording()
        assert recorder.current_pattern_id == pattern_id
    
    def test_start_recording_raises_if_already_recording(self) -> None:
        """start_recording raises RuntimeError if already recording."""
        recorder = CCRecorder()
        recorder.start_recording()
        
        with pytest.raises(RuntimeError, match="Already recording"):
            recorder.start_recording()
    
    def test_start_recording_unique_ids(self) -> None:
        """Each recording gets a unique ID."""
        recorder = CCRecorder()
        
        id1 = recorder.start_recording()
        recorder.stop_recording()
        recorder.reset()
        
        id2 = recorder.start_recording()
        
        assert id1 != id2


class TestCCRecorderStopRecording:
    """Tests for stop_recording method."""
    
    def test_stop_recording_returns_pattern(self) -> None:
        """stop_recording returns an AutomationPattern."""
        recorder = CCRecorder()
        recorder.start_recording()
        
        pattern = recorder.stop_recording()
        
        assert isinstance(pattern, AutomationPattern)
    
    def test_stop_recording_pattern_has_correct_id(self) -> None:
        """Pattern has the ID from start_recording."""
        recorder = CCRecorder()
        pattern_id = recorder.start_recording()
        
        pattern = recorder.stop_recording()
        
        assert pattern.pattern_id == pattern_id
    
    def test_stop_recording_with_custom_name(self) -> None:
        """stop_recording accepts custom pattern name."""
        recorder = CCRecorder()
        recorder.start_recording()
        
        pattern = recorder.stop_recording(name="My Filter Sweep")
        
        assert pattern.name == "My Filter Sweep"
    
    def test_stop_recording_default_name(self) -> None:
        """stop_recording generates default name."""
        recorder = CCRecorder()
        pattern_id = recorder.start_recording()
        
        pattern = recorder.stop_recording()
        
        assert pattern.name.startswith("Pattern ")
        assert pattern_id[:8] in pattern.name
    
    def test_stop_recording_sets_is_recording_false(self) -> None:
        """stop_recording sets is_recording to False."""
        recorder = CCRecorder()
        recorder.start_recording()
        
        recorder.stop_recording()
        
        assert recorder.is_recording is False
    
    def test_stop_recording_clears_current_pattern_id(self) -> None:
        """stop_recording clears current_pattern_id."""
        recorder = CCRecorder()
        recorder.start_recording()
        
        recorder.stop_recording()
        
        assert recorder.current_pattern_id is None
    
    def test_stop_recording_raises_if_not_recording(self) -> None:
        """stop_recording raises RuntimeError if not recording."""
        recorder = CCRecorder()
        
        with pytest.raises(RuntimeError, match="Not recording"):
            recorder.stop_recording()
    
    def test_stop_recording_empty_pattern(self) -> None:
        """stop_recording works with no captured events."""
        recorder = CCRecorder()
        recorder.start_recording()
        
        pattern = recorder.stop_recording()
        
        assert pattern.cc_events == []
        assert pattern.duration == 0.0


class TestCCRecorderCaptureCC:
    """Tests for capture_cc method."""
    
    def test_capture_cc_adds_event(self) -> None:
        """capture_cc adds event to buffer."""
        recorder = CCRecorder()
        recorder.start_recording()
        
        recorder.capture_cc(cc_number=1, value=64, channel=0)
        
        assert recorder.event_count == 1
    
    def test_capture_cc_multiple_events(self) -> None:
        """Multiple capture_cc calls accumulate events."""
        recorder = CCRecorder()
        recorder.start_recording()
        
        recorder.capture_cc(cc_number=1, value=64)
        recorder.capture_cc(cc_number=1, value=80)
        recorder.capture_cc(cc_number=1, value=100)
        
        assert recorder.event_count == 3
    
    def test_capture_cc_event_values(self) -> None:
        """Captured events have correct values."""
        recorder = CCRecorder()
        recorder.start_recording()
        
        recorder.capture_cc(cc_number=74, value=127, channel=5)
        
        events = recorder.get_events()
        assert events[0].cc_number == 74
        assert events[0].value == 127
        assert events[0].channel == 5
    
    def test_capture_cc_raises_if_not_recording(self) -> None:
        """capture_cc raises if not recording."""
        recorder = CCRecorder()
        
        with pytest.raises(RuntimeError):
            recorder.capture_cc(cc_number=1, value=64)
    
    def test_capture_cc_in_pattern(self) -> None:
        """Captured events appear in final pattern."""
        recorder = CCRecorder()
        recorder.start_recording()
        
        recorder.capture_cc(cc_number=1, value=64)
        recorder.capture_cc(cc_number=1, value=127)
        
        pattern = recorder.stop_recording()
        
        assert len(pattern.cc_events) == 2
        assert pattern.cc_events[0].value == 64
        assert pattern.cc_events[1].value == 127


class TestCCRecorderSetRecordingMode:
    """Tests for set_recording_mode method."""
    
    def test_set_mode_to_hold(self) -> None:
        """set_recording_mode can switch to HOLD."""
        recorder = CCRecorder()
        
        recorder.set_recording_mode(RecordingMode.HOLD)
        
        assert recorder.recording_mode == RecordingMode.HOLD
        assert recorder.trigger_handler.mode == RecordingMode.HOLD
    
    def test_set_mode_to_toggle(self) -> None:
        """set_recording_mode can switch to TOGGLE."""
        recorder = CCRecorder()
        recorder.set_recording_mode(RecordingMode.HOLD)
        
        recorder.set_recording_mode(RecordingMode.TOGGLE)
        
        assert recorder.recording_mode == RecordingMode.TOGGLE
        assert recorder.trigger_handler.mode == RecordingMode.TOGGLE
    
    def test_set_mode_invalid_type_raises(self) -> None:
        """set_recording_mode raises TypeError for invalid type."""
        recorder = CCRecorder()
        
        with pytest.raises(TypeError, match="must be RecordingMode"):
            recorder.set_recording_mode("hold")  # type: ignore
    
    def test_mode_synced_with_trigger_handler(self) -> None:
        """Mode changes propagate to trigger handler."""
        recorder = CCRecorder()
        
        recorder.set_recording_mode(RecordingMode.HOLD)
        
        assert recorder.trigger_handler.mode == RecordingMode.HOLD


class TestCCRecorderReset:
    """Tests for reset method."""
    
    def test_reset_clears_recording(self) -> None:
        """reset stops active recording."""
        recorder = CCRecorder()
        recorder.start_recording()
        recorder.capture_cc(cc_number=1, value=64)
        
        recorder.reset()
        
        assert recorder.is_recording is False
        assert recorder.current_pattern_id is None
    
    def test_reset_clears_events(self) -> None:
        """reset clears captured events."""
        recorder = CCRecorder()
        recorder.start_recording()
        recorder.capture_cc(cc_number=1, value=64)
        recorder.stop_recording()
        
        recorder.reset()
        
        assert recorder.event_count == 0
    
    def test_reset_to_idle_state(self) -> None:
        """reset returns to IDLE state."""
        recorder = CCRecorder()
        recorder.start_recording()
        
        recorder.reset()
        
        assert recorder.get_state() == RecordingState.IDLE
        assert recorder.is_idle is True
    
    def test_reset_when_idle(self) -> None:
        """reset when already idle does nothing harmful."""
        recorder = CCRecorder()
        
        recorder.reset()  # Should not raise
        
        assert recorder.is_idle is True


class TestCCRecorderGetState:
    """Tests for get_state method."""
    
    def test_get_state_idle(self) -> None:
        """get_state returns IDLE initially."""
        recorder = CCRecorder()
        assert recorder.get_state() == RecordingState.IDLE
    
    def test_get_state_recording(self) -> None:
        """get_state returns RECORDING while recording."""
        recorder = CCRecorder()
        recorder.start_recording()
        assert recorder.get_state() == RecordingState.RECORDING
    
    def test_get_state_stopped(self) -> None:
        """get_state returns STOPPED after stop."""
        recorder = CCRecorder()
        recorder.start_recording()
        recorder.stop_recording()
        assert recorder.get_state() == RecordingState.STOPPED


class TestCCRecorderGetEvents:
    """Tests for get_events method."""
    
    def test_get_events_empty(self) -> None:
        """get_events returns empty list when no events."""
        recorder = CCRecorder()
        recorder.start_recording()
        
        events = recorder.get_events()
        
        assert events == []
    
    def test_get_events_returns_copy(self) -> None:
        """get_events returns a copy of events."""
        recorder = CCRecorder()
        recorder.start_recording()
        recorder.capture_cc(cc_number=1, value=64)
        
        events1 = recorder.get_events()
        events2 = recorder.get_events()
        
        assert events1 is not events2
        assert events1 == events2


class TestCCRecorderProperties:
    """Tests for property accessors."""
    
    def test_is_recording_true(self) -> None:
        """is_recording is True when recording."""
        recorder = CCRecorder()
        recorder.start_recording()
        assert recorder.is_recording is True
    
    def test_is_recording_false_when_idle(self) -> None:
        """is_recording is False when idle."""
        recorder = CCRecorder()
        assert recorder.is_recording is False
    
    def test_is_recording_false_when_stopped(self) -> None:
        """is_recording is False when stopped."""
        recorder = CCRecorder()
        recorder.start_recording()
        recorder.stop_recording()
        assert recorder.is_recording is False
    
    def test_is_idle_true(self) -> None:
        """is_idle is True when idle."""
        recorder = CCRecorder()
        assert recorder.is_idle is True
    
    def test_is_idle_false_when_recording(self) -> None:
        """is_idle is False when recording."""
        recorder = CCRecorder()
        recorder.start_recording()
        assert recorder.is_idle is False
    
    def test_event_count_zero_initially(self) -> None:
        """event_count is 0 initially."""
        recorder = CCRecorder()
        recorder.start_recording()
        assert recorder.event_count == 0
    
    def test_event_count_increments(self) -> None:
        """event_count increments with captures."""
        recorder = CCRecorder()
        recorder.start_recording()
        
        recorder.capture_cc(cc_number=1, value=64)
        assert recorder.event_count == 1
        
        recorder.capture_cc(cc_number=1, value=80)
        assert recorder.event_count == 2


class TestCCRecorderPatternAnalysis:
    """Tests for pattern analysis during stop_recording."""
    
    def test_pattern_has_attack_decay_analysis(self) -> None:
        """Pattern has attack_events and decay_events populated."""
        recorder = CCRecorder()
        recorder.start_recording()
        
        # Simulate filter sweep: 0 -> 127 -> 64
        recorder.capture_cc(cc_number=74, value=0)
        time.sleep(0.01)
        recorder.capture_cc(cc_number=74, value=64)
        time.sleep(0.01)
        recorder.capture_cc(cc_number=74, value=127)  # peak
        time.sleep(0.01)
        recorder.capture_cc(cc_number=74, value=64)
        
        pattern = recorder.stop_recording()
        
        # Attack should include up to peak (values 0, 64, 127)
        assert len(pattern.attack_events) == 3
        assert pattern.attack_events[-1].value == 127
        
        # Decay should include events after peak (value 64)
        assert len(pattern.decay_events) == 1
        assert pattern.decay_events[0].value == 64
    
    def test_pattern_duration_calculated(self) -> None:
        """Pattern duration is calculated from events."""
        recorder = CCRecorder()
        recorder.start_recording()
        
        recorder.capture_cc(cc_number=1, value=64)
        time.sleep(0.05)
        recorder.capture_cc(cc_number=1, value=127)
        
        pattern = recorder.stop_recording()
        
        # Duration should be approximately 50ms (last event timestamp)
        assert pattern.duration >= 0.04
        assert pattern.duration < 0.2


class TestCCRecorderTriggerIntegration:
    """Tests for trigger handler integration."""
    
    def test_trigger_handler_state_callback_wired(self) -> None:
        """Trigger handler state changes start/stop capture."""
        recorder = CCRecorder()
        
        # Simulate pedal press via trigger handler
        recorder.trigger_handler.handle_trigger_on()
        
        # Should have started capture
        assert recorder.stream_capture.is_active is True
        assert recorder.current_pattern_id is not None
    
    def test_trigger_stop_ends_capture(self) -> None:
        """Trigger handler stop ends capture."""
        recorder = CCRecorder()
        recorder.set_recording_mode(RecordingMode.HOLD)
        
        recorder.trigger_handler.handle_trigger_on()
        assert recorder.stream_capture.is_active is True
        
        recorder.trigger_handler.handle_trigger_off()
        assert recorder.stream_capture.is_active is False


class TestCCRecorderFullWorkflow:
    """Integration tests for complete recording workflow."""
    
    def test_complete_recording_workflow(self) -> None:
        """Test full recording workflow."""
        recorder = CCRecorder()
        
        # Start recording
        pattern_id = recorder.start_recording()
        assert recorder.is_recording is True
        
        # Capture some events
        recorder.capture_cc(cc_number=74, value=0)
        recorder.capture_cc(cc_number=74, value=64)
        recorder.capture_cc(cc_number=74, value=127)
        recorder.capture_cc(cc_number=74, value=64)
        recorder.capture_cc(cc_number=74, value=0)
        
        # Stop and get pattern
        pattern = recorder.stop_recording(name="Test Sweep")
        
        # Verify pattern
        assert pattern.pattern_id == pattern_id
        assert pattern.name == "Test Sweep"
        assert len(pattern.cc_events) == 5
        assert pattern.duration >= 0.0
        assert len(pattern.attack_events) > 0
        
        # Verify recorder is ready for next recording
        assert recorder.is_recording is False
        assert recorder.current_pattern_id is None
    
    def test_multiple_recordings(self) -> None:
        """Multiple recordings can be made sequentially."""
        recorder = CCRecorder()
        
        # First recording
        id1 = recorder.start_recording()
        recorder.capture_cc(cc_number=1, value=64)
        pattern1 = recorder.stop_recording()
        recorder.reset()
        
        # Second recording
        id2 = recorder.start_recording()
        recorder.capture_cc(cc_number=1, value=127)
        pattern2 = recorder.stop_recording()
        
        assert id1 != id2
        assert pattern1.cc_events[0].value == 64
        assert pattern2.cc_events[0].value == 127

"""Tests for StreamCapture class."""

import time

import pytest

from midi_maker.core import CCEvent
from midi_maker.recording import StreamCapture


class TestStreamCaptureInit:
    """Tests for StreamCapture initialization."""
    
    def test_init_without_source_port(self) -> None:
        """StreamCapture can be created without a source port."""
        capture = StreamCapture()
        assert capture.source_port is None
        assert capture.recording_buffer == []
        assert capture.recording_active is False
        assert capture.start_time is None
    
    def test_init_with_source_port(self) -> None:
        """StreamCapture can be created with a source port."""
        mock_port = object()
        capture = StreamCapture(source_port=mock_port)
        assert capture.source_port is mock_port


class TestStreamCaptureStartStop:
    """Tests for start/stop capture functionality."""
    
    def test_start_capture(self) -> None:
        """start_capture activates recording."""
        capture = StreamCapture()
        capture.start_capture()
        
        assert capture.recording_active is True
        assert capture.start_time is not None
        assert capture.is_active is True
    
    def test_start_capture_clears_buffer(self) -> None:
        """start_capture clears any existing events."""
        capture = StreamCapture()
        capture.start_capture()
        capture.capture_cc(1, 64)
        capture.stop_capture()
        
        # Start again should clear
        capture.start_capture()
        assert capture.event_count == 0
    
    def test_start_capture_when_active_raises(self) -> None:
        """start_capture raises if already active."""
        capture = StreamCapture()
        capture.start_capture()
        
        with pytest.raises(RuntimeError, match="already active"):
            capture.start_capture()
    
    def test_stop_capture(self) -> None:
        """stop_capture deactivates recording and returns events."""
        capture = StreamCapture()
        capture.start_capture()
        capture.capture_cc(1, 64)
        
        events = capture.stop_capture()
        
        assert capture.recording_active is False
        assert capture.is_active is False
        assert len(events) == 1
    
    def test_stop_capture_when_not_active_raises(self) -> None:
        """stop_capture raises if not active."""
        capture = StreamCapture()
        
        with pytest.raises(RuntimeError, match="not active"):
            capture.stop_capture()


class TestStreamCaptureCaptureCC:
    """Tests for capture_cc method."""
    
    def test_capture_cc_basic(self) -> None:
        """capture_cc records a CC event."""
        capture = StreamCapture()
        capture.start_capture()
        capture.capture_cc(cc_number=1, value=64, channel=0)
        
        events = capture.get_events()
        assert len(events) == 1
        assert events[0].cc_number == 1
        assert events[0].value == 64
        assert events[0].channel == 0
        assert events[0].timestamp >= 0
    
    def test_capture_cc_default_channel(self) -> None:
        """capture_cc defaults to channel 0."""
        capture = StreamCapture()
        capture.start_capture()
        capture.capture_cc(cc_number=7, value=100)
        
        events = capture.get_events()
        assert events[0].channel == 0
    
    def test_capture_cc_with_explicit_timestamp(self) -> None:
        """capture_cc can use explicit timestamp."""
        capture = StreamCapture()
        capture.start_capture()
        
        # Use a timestamp slightly after start_time
        explicit_time = capture.start_time + 1.5  # type: ignore
        capture.capture_cc(cc_number=10, value=127, channel=5, timestamp=explicit_time)
        
        events = capture.get_events()
        assert abs(events[0].timestamp - 1.5) < 0.001
    
    def test_capture_cc_negative_explicit_timestamp_clamps_to_zero(self) -> None:
        """Explicit timestamps before start time are clamped to 0."""
        capture = StreamCapture()
        capture.start_capture()
        
        explicit_time = capture.start_time - 1.0  # type: ignore
        capture.capture_cc(cc_number=10, value=127, timestamp=explicit_time)
        
        events = capture.get_events()
        assert events[0].timestamp == 0.0
    
    def test_capture_cc_multiple_events(self) -> None:
        """capture_cc records multiple events in order."""
        capture = StreamCapture()
        capture.start_capture()
        
        capture.capture_cc(1, 10)
        capture.capture_cc(2, 20)
        capture.capture_cc(3, 30)
        
        events = capture.get_events()
        assert len(events) == 3
        assert [e.cc_number for e in events] == [1, 2, 3]
        assert [e.value for e in events] == [10, 20, 30]
    
    def test_capture_cc_timestamps_increase(self) -> None:
        """Captured events have increasing timestamps."""
        capture = StreamCapture()
        capture.start_capture()
        
        capture.capture_cc(1, 10)
        time.sleep(0.01)
        capture.capture_cc(1, 20)
        time.sleep(0.01)
        capture.capture_cc(1, 30)
        
        events = capture.get_events()
        timestamps = [e.timestamp for e in events]
        assert timestamps == sorted(timestamps)
        assert timestamps[2] > timestamps[0]
    
    def test_capture_cc_when_not_active_raises(self) -> None:
        """capture_cc raises if capture not active."""
        capture = StreamCapture()
        
        with pytest.raises(RuntimeError, match="not active"):
            capture.capture_cc(1, 64)
    
    def test_capture_cc_raises_if_start_time_missing(self) -> None:
        """capture_cc raises if active capture has no start time set."""
        capture = StreamCapture()
        capture.recording_active = True
        capture.start_time = None
        
        with pytest.raises(RuntimeError, match="Start time not set"):
            capture.capture_cc(1, 64)
    
    def test_capture_cc_validates_parameters(self) -> None:
        """capture_cc validates CC parameters via CCEvent."""
        capture = StreamCapture()
        capture.start_capture()
        
        with pytest.raises(ValueError, match="cc_number"):
            capture.capture_cc(cc_number=200, value=64)
        
        with pytest.raises(ValueError, match="value"):
            capture.capture_cc(cc_number=1, value=200)
        
        with pytest.raises(ValueError, match="channel"):
            capture.capture_cc(cc_number=1, value=64, channel=20)


class TestStreamCaptureGetEvents:
    """Tests for get_events method."""
    
    def test_get_events_returns_copy(self) -> None:
        """get_events returns a copy, not the original list."""
        capture = StreamCapture()
        capture.start_capture()
        capture.capture_cc(1, 64)
        
        events1 = capture.get_events()
        events2 = capture.get_events()
        
        assert events1 == events2
        assert events1 is not events2
        assert events1 is not capture.recording_buffer
    
    def test_get_events_empty_buffer(self) -> None:
        """get_events returns empty list if no events."""
        capture = StreamCapture()
        events = capture.get_events()
        assert events == []


class TestStreamCaptureClear:
    """Tests for clear method."""
    
    def test_clear_removes_events(self) -> None:
        """clear removes all events from buffer."""
        capture = StreamCapture()
        capture.start_capture()
        capture.capture_cc(1, 64)
        capture.capture_cc(2, 65)
        
        assert capture.event_count == 2
        
        capture.clear()
        
        assert capture.event_count == 0
        assert capture.get_events() == []
    
    def test_clear_while_active(self) -> None:
        """clear works while capture is active."""
        capture = StreamCapture()
        capture.start_capture()
        capture.capture_cc(1, 64)
        capture.clear()
        
        # Can continue capturing after clear
        capture.capture_cc(2, 65)
        assert capture.event_count == 1
        assert capture.get_events()[0].cc_number == 2


class TestStreamCaptureProperties:
    """Tests for property accessors."""
    
    def test_event_count(self) -> None:
        """event_count returns number of buffered events."""
        capture = StreamCapture()
        assert capture.event_count == 0
        
        capture.start_capture()
        capture.capture_cc(1, 10)
        assert capture.event_count == 1
        
        capture.capture_cc(2, 20)
        assert capture.event_count == 2
    
    def test_is_active(self) -> None:
        """is_active reflects recording state."""
        capture = StreamCapture()
        assert capture.is_active is False
        
        capture.start_capture()
        assert capture.is_active is True
        
        capture.stop_capture()
        assert capture.is_active is False

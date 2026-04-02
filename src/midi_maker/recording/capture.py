"""Stream capture for real-time MIDI CC recording.

This module provides the StreamCapture class for buffering incoming
CC messages with precise timestamps during recording.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from midi_maker.core import CCEvent

if TYPE_CHECKING:
    from collections.abc import Sequence


class StreamCapture:
    """Buffers incoming CC messages with precise timestamps during recording.
    
    StreamCapture manages the capture of MIDI CC messages in real-time,
    maintaining a buffer of CCEvent objects with timestamps relative to
    the recording start time.
    
    Attributes:
        source_port: Optional MIDI input port for future integration.
        recording_buffer: List of captured CCEvent objects.
        recording_active: Whether capture is currently active.
        start_time: Timestamp when recording started.
    
    Example:
        >>> capture = StreamCapture()
        >>> capture.start_capture()
        >>> capture.capture_cc(cc_number=1, value=64, channel=0)
        >>> events = capture.get_events()
        >>> capture.stop_capture()
    """
    
    def __init__(self, source_port: Any | None = None) -> None:
        """Initialize StreamCapture.
        
        Args:
            source_port: Optional MIDI input port. Can be None for testing
                or standalone use without midi-scripter dependency.
        """
        self.source_port = source_port
        self.recording_buffer: list[CCEvent] = []
        self.recording_active: bool = False
        self.start_time: float | None = None
    
    def start_capture(self) -> None:
        """Start capturing CC messages.
        
        Sets recording_active to True and records the start time.
        Clears any existing buffer.
        
        Raises:
            RuntimeError: If capture is already active.
        """
        if self.recording_active:
            raise RuntimeError("Capture already active")
        
        self.recording_buffer.clear()
        self.start_time = time.perf_counter()
        self.recording_active = True
    
    def stop_capture(self) -> list[CCEvent]:
        """Stop capturing CC messages.
        
        Sets recording_active to False and returns the captured events.
        
        Returns:
            List of CCEvent objects captured during recording.
            
        Raises:
            RuntimeError: If capture is not active.
        """
        if not self.recording_active:
            raise RuntimeError("Capture not active")
        
        self.recording_active = False
        return list(self.recording_buffer)
    
    def capture_cc(
        self,
        cc_number: int,
        value: int,
        channel: int = 0,
        timestamp: float | None = None,
    ) -> None:
        """Capture a CC message.
        
        Creates a CCEvent with the given parameters and adds it to the buffer.
        If timestamp is not provided, uses current time relative to start_time.
        
        Args:
            cc_number: MIDI CC number (0-127).
            value: CC value (0-127).
            channel: MIDI channel (0-15). Defaults to 0.
            timestamp: Optional absolute timestamp. If None, current time is used.
            
        Raises:
            RuntimeError: If capture is not active.
        """
        if not self.recording_active:
            raise RuntimeError("Capture not active")
        
        if self.start_time is None:
            raise RuntimeError("Start time not set")
        
        if timestamp is None:
            relative_time = time.perf_counter() - self.start_time
        else:
            relative_time = timestamp - self.start_time
        
        # Clamp negative timestamps to 0
        relative_time = max(0.0, relative_time)
        
        event = CCEvent(
            cc_number=cc_number,
            value=value,
            channel=channel,
            timestamp=relative_time,
        )
        self.recording_buffer.append(event)
    
    def get_events(self) -> list[CCEvent]:
        """Get a copy of captured events.
        
        Returns:
            List of CCEvent objects in capture order.
        """
        return list(self.recording_buffer)
    
    def clear(self) -> None:
        """Clear the recording buffer.
        
        Removes all captured events without stopping the capture.
        """
        self.recording_buffer.clear()
    
    @property
    def event_count(self) -> int:
        """Number of events in the buffer."""
        return len(self.recording_buffer)
    
    @property
    def is_active(self) -> bool:
        """Whether capture is currently active."""
        return self.recording_active

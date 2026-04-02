"""Main recording coordinator for MIDI CC automation.

This module provides the CCRecorder class that coordinates TriggerHandler
and StreamCapture for complete recording lifecycle management.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from midi_maker.automation import AutomationPattern
from midi_maker.core import RecordingMode, RecordingState

from .capture import StreamCapture
from .triggers import TriggerHandler

if TYPE_CHECKING:
    from midi_maker.core import CCEvent


class CCRecorder:
    """Main recording coordinator that manages the recording lifecycle.
    
    CCRecorder orchestrates TriggerHandler and StreamCapture to provide
    a complete recording workflow. It handles pattern creation, ID generation,
    and coordinates state transitions between components.
    
    Attributes:
        trigger_handler: Handles pedal input and recording state transitions.
        stream_capture: Buffers incoming CC messages during recording.
        recording_mode: Current mode (TOGGLE or HOLD).
        current_pattern_id: ID of the pattern currently being recorded.
    
    Example:
        >>> recorder = CCRecorder()
        >>> pattern_id = recorder.start_recording()
        >>> recorder.capture_cc(cc_number=1, value=64)
        >>> pattern = recorder.stop_recording()
        >>> pattern.pattern_id == pattern_id
        True
    """
    
    def __init__(
        self,
        trigger_port: Any | None = None,
        source_port: Any | None = None,
    ) -> None:
        """Initialize CCRecorder.
        
        Args:
            trigger_port: Optional MIDI input port for the pedal/trigger.
                Can be None for testing or standalone use.
            source_port: Optional MIDI input port for CC capture.
                Can be None for testing or standalone use.
        """
        self.trigger_handler = TriggerHandler(trigger_port)
        self.stream_capture = StreamCapture(source_port)
        self.recording_mode: RecordingMode = RecordingMode.TOGGLE
        self.current_pattern_id: str | None = None
        
        # Wire up trigger handler state changes to control stream capture
        self.trigger_handler.set_on_state_change(self._on_trigger_state_change)
    
    def start_recording(self, pattern_id: str | None = None) -> str:
        """Start a new recording session.
        
        Generates a unique pattern ID and begins capturing CC events.
        
        Args:
            pattern_id: Optional explicit pattern ID. If None, a UUID is generated.
        
        Returns:
            The pattern_id for the new recording.
            
        Raises:
            RuntimeError: If already recording.
        """
        if self.is_recording:
            raise RuntimeError("Already recording")
        
        # Generate or use provided pattern ID
        self.current_pattern_id = pattern_id or self._generate_pattern_id()
        
        # Start capture
        self.stream_capture.start_capture()
        
        # Update trigger handler state manually if not driven by trigger
        if not self.trigger_handler.is_recording:
            self.trigger_handler.handle_trigger_on()
        
        return self.current_pattern_id
    
    def stop_recording(self, name: str | None = None) -> AutomationPattern:
        """Stop recording and return the completed pattern.
        
        Stops capture, creates an AutomationPattern from captured events,
        and performs attack/decay analysis.
        
        Args:
            name: Optional human-readable name for the pattern.
                If None, defaults to "Pattern <id>".
        
        Returns:
            Completed AutomationPattern with captured events and analysis.
            
        Raises:
            RuntimeError: If not currently recording.
        """
        if not self.is_recording:
            raise RuntimeError("Not recording")
        
        # Stop capture and get events
        events = self.stream_capture.stop_capture()
        
        # Calculate duration from events
        duration = events[-1].timestamp if events else 0.0
        
        # Create pattern
        pattern_id = self.current_pattern_id or self._generate_pattern_id()
        pattern_name = name or f"Pattern {pattern_id[:8]}"
        
        pattern = AutomationPattern(
            pattern_id=pattern_id,
            name=pattern_name,
            cc_events=events,
            duration=duration,
        )
        
        # Analyze attack/decay phases
        pattern.analyze_attack_decay()
        
        # Update trigger handler state
        if self.trigger_handler.is_recording:
            self.trigger_handler.handle_trigger_on()  # Toggle to STOPPED
        
        # Clear current pattern ID
        self.current_pattern_id = None
        
        return pattern
    
    def set_recording_mode(self, mode: RecordingMode) -> None:
        """Set the recording mode.
        
        Switches between HOLD and TOGGLE modes for pedal behavior.
        
        Args:
            mode: The recording mode to use.
            
        Raises:
            TypeError: If mode is not a RecordingMode enum value.
        """
        if not isinstance(mode, RecordingMode):
            raise TypeError(f"mode must be RecordingMode, got {type(mode).__name__}")
        
        self.recording_mode = mode
        self.trigger_handler.set_mode(mode)
    
    def capture_cc(
        self,
        cc_number: int,
        value: int,
        channel: int = 0,
        timestamp: float | None = None,
    ) -> None:
        """Capture a CC message during recording.
        
        Convenience method that delegates to StreamCapture.
        
        Args:
            cc_number: MIDI CC number (0-127).
            value: CC value (0-127).
            channel: MIDI channel (0-15). Defaults to 0.
            timestamp: Optional absolute timestamp.
            
        Raises:
            RuntimeError: If not recording.
        """
        self.stream_capture.capture_cc(
            cc_number=cc_number,
            value=value,
            channel=channel,
            timestamp=timestamp,
        )
    
    def reset(self) -> None:
        """Reset the recorder to initial state.
        
        Clears any in-progress recording and returns to IDLE state.
        """
        if self.stream_capture.is_active:
            # Discard events by stopping and ignoring result
            self.stream_capture.stop_capture()
        
        self.stream_capture.clear()
        self.trigger_handler.reset()
        self.current_pattern_id = None
    
    def get_state(self) -> RecordingState:
        """Get the current recording state.
        
        Returns:
            Current RecordingState from trigger handler.
        """
        return self.trigger_handler.get_state()
    
    def get_events(self) -> list[CCEvent]:
        """Get captured events (copy) during recording.
        
        Returns:
            List of CCEvent objects captured so far.
        """
        return self.stream_capture.get_events()
    
    @property
    def is_recording(self) -> bool:
        """Whether currently recording."""
        return self.stream_capture.is_active
    
    @property
    def is_idle(self) -> bool:
        """Whether in idle state."""
        return self.trigger_handler.is_idle
    
    @property
    def event_count(self) -> int:
        """Number of events captured so far."""
        return self.stream_capture.event_count
    
    def _generate_pattern_id(self) -> str:
        """Generate a unique pattern ID.
        
        Returns:
            UUID string for pattern identification.
        """
        return str(uuid.uuid4())
    
    def _on_trigger_state_change(
        self,
        old_state: RecordingState,
        new_state: RecordingState,
    ) -> None:
        """Handle trigger state changes to coordinate capture.
        
        Called by TriggerHandler when state changes due to pedal events.
        
        Args:
            old_state: Previous recording state.
            new_state: New recording state.
        """
        if new_state == RecordingState.RECORDING and not self.stream_capture.is_active:
            # Start capture when trigger starts recording
            self.current_pattern_id = self._generate_pattern_id()
            self.stream_capture.start_capture()
        
        elif old_state == RecordingState.RECORDING and new_state == RecordingState.STOPPED:
            # Stop capture when trigger stops recording
            if self.stream_capture.is_active:
                self.stream_capture.stop_capture()

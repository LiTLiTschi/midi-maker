"""Trigger handling for pedal-based recording control.

This module provides the TriggerHandler class for managing recording state
based on pedal input with support for HOLD and TOGGLE modes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

from midi_maker.core import RecordingMode, RecordingState

if TYPE_CHECKING:
    pass


class TriggerHandler:
    """Handles pedal input and manages recording state transitions.
    
    TriggerHandler manages the recording state machine based on pedal
    press/release events. Supports two modes:
    
    - TOGGLE: Press once to start recording, press again to stop
    - HOLD: Record only while pedal is held down
    
    Attributes:
        trigger_port: Optional MIDI input port for pedal.
        recording_state: Current recording state.
        mode: Current recording mode (TOGGLE or HOLD).
    
    Example:
        >>> handler = TriggerHandler()
        >>> handler.get_state()
        <RecordingState.IDLE: 1>
        >>> handler.handle_trigger_on(None)
        >>> handler.get_state()
        <RecordingState.RECORDING: 2>
    """
    
    def __init__(self, trigger_port: Any | None = None) -> None:
        """Initialize TriggerHandler.
        
        Args:
            trigger_port: Optional MIDI input port for the pedal/trigger.
                Can be None for testing or standalone use without
                midi-scripter dependency.
        """
        self.trigger_port = trigger_port
        self.recording_state: RecordingState = RecordingState.IDLE
        self.mode: RecordingMode = RecordingMode.TOGGLE
        
        # Callbacks for state change notifications
        self._on_state_change: Callable[[RecordingState, RecordingState], None] | None = None
    
    def handle_trigger_on(self, msg: Any | None = None) -> None:
        """Handle pedal press event.
        
        State transitions depend on current mode:
        
        TOGGLE mode:
            - IDLE -> RECORDING (start recording)
            - RECORDING -> STOPPED (stop recording)
            - STOPPED -> RECORDING (start new recording)
        
        HOLD mode:
            - IDLE -> RECORDING (start recording)
            - STOPPED -> RECORDING (start new recording)
        
        Args:
            msg: Optional MIDI message from the pedal. Can be None for
                direct API calls or testing.
        """
        old_state = self.recording_state
        
        if self.mode == RecordingMode.TOGGLE:
            if self.recording_state == RecordingState.IDLE:
                self.recording_state = RecordingState.RECORDING
            elif self.recording_state == RecordingState.RECORDING:
                self.recording_state = RecordingState.STOPPED
            elif self.recording_state == RecordingState.STOPPED:
                self.recording_state = RecordingState.RECORDING
        
        elif self.mode == RecordingMode.HOLD:
            if self.recording_state in (RecordingState.IDLE, RecordingState.STOPPED):
                self.recording_state = RecordingState.RECORDING
        
        self._notify_state_change(old_state, self.recording_state)
    
    def handle_trigger_off(self, msg: Any | None = None) -> None:
        """Handle pedal release event.
        
        State transitions depend on current mode:
        
        TOGGLE mode:
            - No state change (toggle handled on press only)
        
        HOLD mode:
            - RECORDING -> STOPPED (stop recording on release)
        
        Args:
            msg: Optional MIDI message from the pedal. Can be None for
                direct API calls or testing.
        """
        old_state = self.recording_state
        
        if self.mode == RecordingMode.HOLD:
            if self.recording_state == RecordingState.RECORDING:
                self.recording_state = RecordingState.STOPPED
        
        # In TOGGLE mode, release does nothing
        
        self._notify_state_change(old_state, self.recording_state)
    
    def set_mode(self, mode: RecordingMode) -> None:
        """Set the recording mode.
        
        Args:
            mode: The recording mode to use (TOGGLE or HOLD).
        
        Raises:
            TypeError: If mode is not a RecordingMode enum value.
        """
        if not isinstance(mode, RecordingMode):
            raise TypeError(f"mode must be RecordingMode, got {type(mode).__name__}")
        self.mode = mode
    
    def get_state(self) -> RecordingState:
        """Get the current recording state.
        
        Returns:
            Current RecordingState value.
        """
        return self.recording_state
    
    def reset(self) -> None:
        """Reset to IDLE state.
        
        Useful for canceling a recording or starting fresh.
        """
        old_state = self.recording_state
        self.recording_state = RecordingState.IDLE
        self._notify_state_change(old_state, self.recording_state)
    
    def set_on_state_change(
        self,
        callback: Callable[[RecordingState, RecordingState], None] | None,
    ) -> None:
        """Set callback for state change notifications.
        
        Args:
            callback: Function called with (old_state, new_state) on changes.
                Pass None to remove the callback.
        """
        self._on_state_change = callback
    
    def _notify_state_change(
        self,
        old_state: RecordingState,
        new_state: RecordingState,
    ) -> None:
        """Notify callback if state changed."""
        if old_state != new_state and self._on_state_change is not None:
            self._on_state_change(old_state, new_state)
    
    @property
    def is_recording(self) -> bool:
        """Whether currently recording."""
        return self.recording_state == RecordingState.RECORDING
    
    @property
    def is_idle(self) -> bool:
        """Whether in idle state."""
        return self.recording_state == RecordingState.IDLE
    
    @property
    def is_stopped(self) -> bool:
        """Whether recording has stopped."""
        return self.recording_state == RecordingState.STOPPED

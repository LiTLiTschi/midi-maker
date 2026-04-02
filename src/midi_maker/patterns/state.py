"""Gate state machine for sequencer integration.

This module provides GateStateMachine for tracking sequencer step states
and managing overlapping gates in attack/decay automation scenarios.
"""

from collections import deque
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, Deque
import time

from midi_maker.core import GateState


class GateTransition(Enum):
    """Gate state transition types.
    
    Attributes:
        OPENED: Gate transitioned from closed to open
        CLOSED: Gate transitioned from open to closed
        NO_CHANGE: Gate state did not change
    """
    
    OPENED = auto()
    CLOSED = auto()
    NO_CHANGE = auto()


@dataclass
class GateEvent:
    """Record of a gate state change.
    
    Attributes:
        channel: MIDI channel (0-15)
        state: The gate state (OPEN or CLOSED)
        timestamp: Time of the event in seconds
    """
    
    channel: int
    state: GateState
    timestamp: float


@dataclass
class ChannelGateInfo:
    """Tracking info for a single channel's gate.
    
    Attributes:
        state: Current gate state
        open_timestamp: When the gate was last opened (None if never opened)
        open_count: Number of overlapping opens (for sustain detection)
    """
    
    state: GateState = field(default=GateState.CLOSED)
    open_timestamp: float = field(default=0.0)
    open_count: int = field(default=0)


class GateStateMachine:
    """Tracks sequencer step states and manages overlapping gates.
    
    This state machine monitors gate-on/gate-off events from a sequencer
    and provides transition detection, overlap detection (sustain scenarios),
    and gate duration calculation for timing adjustments.
    
    Example:
        >>> gsm = GateStateMachine()
        >>> transition = gsm.update_gate_state(channel=0, gate_on=True)
        >>> assert transition == GateTransition.OPENED
        >>> assert gsm.get_current_state(0) == GateState.OPEN
    """
    
    def __init__(self, history_size: int = 100):
        """Initialize the gate state machine.
        
        Args:
            history_size: Maximum number of gate events to keep for overlap detection
        """
        self._channel_states: Dict[int, ChannelGateInfo] = {}
        self._gate_history: Deque[GateEvent] = deque(maxlen=history_size)
        self._time_func = time.time
    
    def _get_channel_info(self, channel: int) -> ChannelGateInfo:
        """Get or create gate info for a channel."""
        if channel not in self._channel_states:
            self._channel_states[channel] = ChannelGateInfo()
        return self._channel_states[channel]
    
    def update_gate_state(self, channel: int, gate_on: bool) -> GateTransition:
        """Update gate state and return transition type.
        
        Args:
            channel: MIDI channel (0-15)
            gate_on: True for gate-on, False for gate-off
            
        Returns:
            GateTransition indicating what type of transition occurred
        """
        info = self._get_channel_info(channel)
        current_time = self._time_func()
        new_state = GateState.OPEN if gate_on else GateState.CLOSED
        
        # Record the event in history
        event = GateEvent(channel=channel, state=new_state, timestamp=current_time)
        self._gate_history.append(event)
        
        # Determine transition
        if gate_on:
            info.open_count += 1
            if info.state == GateState.CLOSED:
                info.state = GateState.OPEN
                info.open_timestamp = current_time
                return GateTransition.OPENED
            else:
                # Already open - overlapping gate
                return GateTransition.NO_CHANGE
        else:
            if info.open_count > 0:
                info.open_count -= 1
            if info.state == GateState.OPEN and info.open_count == 0:
                info.state = GateState.CLOSED
                return GateTransition.CLOSED
            else:
                # Either already closed or still has overlapping gates
                return GateTransition.NO_CHANGE
    
    def has_overlapping_gates(self, channel: int) -> bool:
        """Check if gates are overlapping (sustain scenario).
        
        This detects when a new gate-on occurs before the previous gate-off,
        which is common in legato playing or when notes are sustained.
        
        Args:
            channel: MIDI channel to check
            
        Returns:
            True if there are overlapping gates on this channel
        """
        info = self._get_channel_info(channel)
        return info.open_count > 1
    
    def get_gate_duration(self, channel: int) -> float:
        """Calculate gate duration for timing adjustments.
        
        Returns the duration since the gate was opened. If the gate is closed,
        returns 0.0.
        
        Args:
            channel: MIDI channel to check
            
        Returns:
            Duration in seconds since gate opened, or 0.0 if closed
        """
        info = self._get_channel_info(channel)
        if info.state == GateState.CLOSED:
            return 0.0
        return self._time_func() - info.open_timestamp
    
    def get_current_state(self, channel: int) -> GateState:
        """Get the current gate state for a channel.
        
        Args:
            channel: MIDI channel to check
            
        Returns:
            Current GateState (OPEN or CLOSED)
        """
        return self._get_channel_info(channel).state
    
    def get_open_count(self, channel: int) -> int:
        """Get the number of overlapping opens for a channel.
        
        Args:
            channel: MIDI channel to check
            
        Returns:
            Number of gate-ons without corresponding gate-offs
        """
        return self._get_channel_info(channel).open_count
    
    def get_history(self) -> list[GateEvent]:
        """Get the gate event history.
        
        Returns:
            List of recent gate events (up to history_size)
        """
        return list(self._gate_history)
    
    def clear_channel(self, channel: int) -> None:
        """Reset a channel to its initial state.
        
        Args:
            channel: MIDI channel to reset
        """
        if channel in self._channel_states:
            self._channel_states[channel] = ChannelGateInfo()
    
    def clear_all(self) -> None:
        """Reset all channels and clear history."""
        self._channel_states.clear()
        self._gate_history.clear()

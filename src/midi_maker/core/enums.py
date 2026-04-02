"""Core enumerations for MIDI Maker.

This module defines the fundamental enums used throughout the MIDI Maker system
for recording, playback, and automation control.
"""

from enum import Enum, auto


class RecordingState(Enum):
    """State machine for recording lifecycle.
    
    Attributes:
        IDLE: Not recording, waiting to start
        RECORDING: Actively recording MIDI data
        STOPPED: Recording has finished
    """
    
    IDLE = auto()
    RECORDING = auto()
    STOPPED = auto()


class RecordingMode(Enum):
    """Pedal behavior configuration for recording control.
    
    Attributes:
        HOLD: Record only while pedal is held down
        TOGGLE: Press once to start recording, press again to stop
    """
    
    HOLD = auto()
    TOGGLE = auto()


class PlaybackMode(Enum):
    """Different playback strategies for automation sequences.
    
    Attributes:
        FULL_SEQUENCE: Play complete automation with original timing
        ATTACK_ONLY: Play only the attack portion
        DECAY_ONLY: Play only the decay portion
        ATTACK_DECAY: Play attack on gate-on, decay on gate-off
        SNAPSHOT: Send instantaneous CC values (no timing)
    """
    
    FULL_SEQUENCE = auto()
    ATTACK_ONLY = auto()
    DECAY_ONLY = auto()
    ATTACK_DECAY = auto()
    SNAPSHOT = auto()


class CCAutomationType(Enum):
    """Types of CC automation patterns for classification.
    
    Attributes:
        FILTER_SWEEP: Filter cutoff automation
        VOLUME_FADE: Volume/amplitude automation
        PAN_SWEEP: Panning automation
        RESONANCE: Filter resonance automation
        CUSTOM: User-defined or unclassified automation
    """
    
    FILTER_SWEEP = auto()
    VOLUME_FADE = auto()
    PAN_SWEEP = auto()
    RESONANCE = auto()
    CUSTOM = auto()


class GateState(Enum):
    """Sequencer gate states.
    
    Attributes:
        CLOSED: Gate is off (note-off state)
        OPEN: Gate is on (note-on state)
    """
    
    CLOSED = auto()
    OPEN = auto()

"""Core module for MIDI Maker.

This module exports all core types: enums, events, and exceptions.
"""

from .enums import (
    RecordingState,
    RecordingMode,
    PlaybackMode,
    CCAutomationType,
    GateState,
)
from .events import CCEvent
from .exceptions import (
    MidiMakerError,
    RecordingError,
    PlaybackError,
    PatternError,
)

__all__ = [
    # Enums
    "RecordingState",
    "RecordingMode",
    "PlaybackMode",
    "CCAutomationType",
    "GateState",
    # Events
    "CCEvent",
    # Exceptions
    "MidiMakerError",
    "RecordingError",
    "PlaybackError",
    "PatternError",
]
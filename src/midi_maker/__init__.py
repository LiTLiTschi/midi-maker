"""MIDI Maker - A Python tool for creating and manipulating MIDI files."""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

# Core enums are available immediately
from .core.enums import (
    RecordingState,
    RecordingMode,
    PlaybackMode,
    CCAutomationType,
    GateState,
)

__all__ = [
    "RecordingState",
    "RecordingMode",
    "PlaybackMode",
    "CCAutomationType",
    "GateState",
]
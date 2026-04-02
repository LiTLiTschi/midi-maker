"""Recording module for MIDI Maker.

This module provides capture and recording functionality for MIDI CC automation.
"""

from .capture import StreamCapture
from .recorder import CCRecorder
from .triggers import TriggerHandler

__all__ = [
    "CCRecorder",
    "StreamCapture",
    "TriggerHandler",
]

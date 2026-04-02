"""Playback module for MIDI Maker.

This module provides playback capabilities for CC automation sequences.
"""

from .player import AutomationPlayer
from .scheduler import PlaybackScheduler

__all__ = [
    "AutomationPlayer",
    "PlaybackScheduler",
]

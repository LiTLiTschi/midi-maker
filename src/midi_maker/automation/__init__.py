"""Automation module for MIDI Maker.

This module provides pattern storage and analysis for CC automation sequences.
"""

from .analyzer import PatternAnalyzer
from .library import PatternLibrary, PatternNotFoundError
from .patterns import AutomationPattern

__all__ = [
    "AutomationPattern",
    "PatternAnalyzer",
    "PatternLibrary",
    "PatternNotFoundError",
]

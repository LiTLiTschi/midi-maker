"""Pattern management module for MIDI Maker.

This module provides state machine and pattern organization components
for sequencer integration and automation playback.
"""

from .state import GateStateMachine, GateTransition

__all__ = [
    "GateStateMachine",
    "GateTransition",
]

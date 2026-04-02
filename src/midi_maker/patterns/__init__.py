"""Pattern management module for MIDI Maker.

This module provides state machine and pattern organization components
for sequencer integration and automation playback.
"""

from typing import TYPE_CHECKING

from .state import GateStateMachine, GateTransition

if TYPE_CHECKING:
    from .sequencer import SequencerInterface

__all__ = [
    "GateStateMachine",
    "GateTransition",
    "SequencerInterface",
]


def __getattr__(name: str):
    if name == "SequencerInterface":
        from .sequencer import SequencerInterface

        return SequencerInterface
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

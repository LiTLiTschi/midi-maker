"""Pattern management module for MIDI Maker.

This module provides state machine and pattern organization components
for sequencer integration and automation playback.
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .state import GateStateMachine, GateTransition
    from .sequencer import SequencerInterface

__all__ = [
    "GateStateMachine",
    "GateTransition",
    "SequencerInterface",
]


def __getattr__(name: str) -> Any:
    if name in {"GateStateMachine", "GateTransition"}:
        from .state import GateStateMachine, GateTransition
        return {
            "GateStateMachine": GateStateMachine,
            "GateTransition": GateTransition,
        }[name]

    if name == "SequencerInterface":
        from .sequencer import SequencerInterface
        return SequencerInterface

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

"""Tests for exports from the ``midi_maker.patterns`` package."""

from __future__ import annotations

import importlib
import sys

import pytest


_EXPORTS = ["GateStateMachine", "GateTransition", "SequencerInterface"]


def _reset_patterns_modules() -> None:
    for module_name in (
        "midi_maker.patterns",
        "midi_maker.patterns.state",
        "midi_maker.patterns.sequencer",
    ):
        sys.modules.pop(module_name, None)


def test_patterns_package_exports_public_api() -> None:
    _reset_patterns_modules()

    from midi_maker.patterns import GateStateMachine, GateTransition, SequencerInterface

    assert GateStateMachine.__name__ == "GateStateMachine"
    assert GateTransition.__name__ == "GateTransition"
    assert SequencerInterface.__name__ == "SequencerInterface"


def test_patterns_package_defers_submodule_imports_until_access() -> None:
    _reset_patterns_modules()

    patterns = importlib.import_module("midi_maker.patterns")

    assert patterns.__all__ == _EXPORTS
    assert "midi_maker.patterns.state" not in sys.modules
    assert "midi_maker.patterns.sequencer" not in sys.modules

    _ = patterns.GateStateMachine

    assert "midi_maker.patterns.state" in sys.modules
    assert "midi_maker.patterns.sequencer" not in sys.modules


def test_patterns_package_raises_attribute_error_for_unknown_exports() -> None:
    _reset_patterns_modules()

    patterns = importlib.import_module("midi_maker.patterns")

    with pytest.raises(AttributeError):
        _ = patterns.UnknownExport

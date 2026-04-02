"""Smoke tests for the sequencer integration example."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType


EXAMPLE_PATH = (
    Path(__file__).resolve().parents[2] / "examples" / "sequencer_integration.py"
)


def _load_example_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("sequencer_integration", EXAMPLE_PATH)
    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_run_demo_smoke(capsys) -> None:
    module = _load_example_module()

    result = module.run_demo()

    assert result.mapped_channel == 1
    assert len(result.pattern.cc_events) == 4
    assert len(result.callback_events) == len(result.pattern.cc_events)
    assert result.callback_events[0] == (74, 20, 1)

    output = capsys.readouterr().out
    assert "Gate ON" in output
    assert "Gate OFF" in output
    assert "Playback callback" in output


def test_main_returns_zero() -> None:
    module = _load_example_module()

    assert module.main() == 0

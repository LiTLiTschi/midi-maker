"""Smoke tests for the basic recording/playback example."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType


EXAMPLE_PATH = (
    Path(__file__).resolve().parents[2] / "examples" / "basic_recording_playback.py"
)


def _load_example_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("basic_recording_playback", EXAMPLE_PATH)
    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_run_demo_smoke(capsys) -> None:
    module = _load_example_module()

    result = module.run_demo()

    assert result.pattern.pattern_id in result.stored_patterns
    assert len(result.pattern.cc_events) == 4
    assert len(result.played_events) == 4
    assert result.played_events[0] == (74, 20, 0)

    output = capsys.readouterr().out
    assert "Trigger ON" in output
    assert "Trigger OFF" in output
    assert "Played 4 events" in output


def test_main_returns_zero() -> None:
    module = _load_example_module()

    assert module.main() == 0

#!/usr/bin/env python3
"""Basic recording + playback example without MIDI hardware."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

# Import order workaround for known package init cycle:
# importing midi_maker.patterns first ensures playback package can initialize.
import midi_maker.patterns

from midi_maker.automation.patterns import AutomationPattern
from midi_maker.playback.player import AutomationPlayer
from midi_maker.recording.recorder import CCRecorder


@dataclass
class DemoResult:
    """Collected results from the example flow."""

    pattern: AutomationPattern
    stored_patterns: Dict[str, AutomationPattern]
    played_events: List[Tuple[int, int, int]]


def _simulate_recording(recorder: CCRecorder) -> AutomationPattern:
    print("Trigger ON")
    recorder.start_recording(pattern_id="example-basic")

    start_time = recorder.stream_capture.start_time
    assert start_time is not None

    recorded_values = [20, 64, 110, 40]
    for index, value in enumerate(recorded_values):
        recorder.capture_cc(
            cc_number=74,
            value=value,
            channel=0,
            timestamp=start_time + (index * 0.001),
        )

    print("Trigger OFF")
    return recorder.stop_recording(name="Basic Recording")


def _play_pattern(pattern: AutomationPattern) -> List[Tuple[int, int, int]]:
    player = AutomationPlayer()
    played_events: List[Tuple[int, int, int]] = []

    def on_cc_output(cc_number: int, value: int, channel: int) -> None:
        played_events.append((cc_number, value, channel))
        print(f"CC{cc_number}={value} ch{channel}")

    player.set_cc_output_callback(on_cc_output)
    player.play_full_sequence(pattern)
    return played_events


def run_demo() -> DemoResult:
    """Run the basic record/playback flow and return captured results."""
    recorder = CCRecorder()
    pattern = _simulate_recording(recorder)

    stored_patterns: Dict[str, AutomationPattern] = {pattern.pattern_id: pattern}
    played_events = _play_pattern(pattern)

    print(f"Played {len(played_events)} events")
    return DemoResult(
        pattern=pattern,
        stored_patterns=stored_patterns,
        played_events=played_events,
    )


def main() -> int:
    """CLI entrypoint."""
    run_demo()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

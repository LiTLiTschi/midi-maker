#!/usr/bin/env python3
"""Sequencer integration example without MIDI hardware."""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

# Import order workaround for known package init cycle.
import midi_maker.patterns

from midi_maker.automation import AutomationPattern, PatternLibrary
from midi_maker.core import CCEvent
from midi_maker.patterns import SequencerInterface
from midi_maker.playback import GateProcessor, PlaybackScheduler


class CallbackOutputPort:
    """Collects scheduler output and prints callback messages."""

    def __init__(self) -> None:
        self._events: List[Tuple[int, int, int]] = []
        self._lock = Lock()

    def send_cc(self, cc_number: int, value: int, channel: int) -> None:
        with self._lock:
            self._events.append((cc_number, value, channel))
        print(f"Playback callback: CC{cc_number}={value} ch{channel}")

    def snapshot(self) -> List[Tuple[int, int, int]]:
        with self._lock:
            return list(self._events)


@dataclass
class DemoResult:
    """Collected output from the sequencer integration demo."""

    pattern: AutomationPattern
    mapped_channel: int
    callback_events: List[Tuple[int, int, int]]


def _build_pattern(channel: int) -> AutomationPattern:
    events = [
        CCEvent(cc_number=74, value=20, channel=channel, timestamp=0.0),
        CCEvent(cc_number=74, value=64, channel=channel, timestamp=0.001),
        CCEvent(cc_number=74, value=110, channel=channel, timestamp=0.002),
        CCEvent(cc_number=74, value=40, channel=channel, timestamp=0.003),
    ]
    pattern = AutomationPattern(
        pattern_id="example-sequencer",
        name="Sequencer Integration Example",
        cc_events=events,
        duration=0.003,
    )
    pattern.analyze_attack_decay()
    return pattern


def _wait_for_events(
    output_port: CallbackOutputPort, expected_count: int, timeout_s: float = 1.0
) -> None:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if len(output_port.snapshot()) >= expected_count:
            return
        time.sleep(0.005)


def run_demo() -> DemoResult:
    """Run a sequencer + gate + scheduler integration flow."""
    mapped_channel = 1

    pattern_library = PatternLibrary()
    pattern = _build_pattern(channel=mapped_channel)
    pattern_library.add_pattern(pattern)

    output_port = CallbackOutputPort()
    playback_scheduler = PlaybackScheduler(output_port=output_port)
    gate_processor = GateProcessor(
        scheduler=playback_scheduler,
        pattern_library=pattern_library,
    )
    sequencer = SequencerInterface(gate_processor=gate_processor)

    sequencer.map_pattern_to_channel(channel=mapped_channel, pattern_id=pattern.pattern_id)
    print(f"Mapped pattern '{pattern.pattern_id}' to channel {mapped_channel}")

    print("Gate ON")
    sequencer.handle_note_on(channel=mapped_channel)
    _wait_for_events(output_port=output_port, expected_count=len(pattern.attack_events))

    print("Gate OFF")
    sequencer.handle_note_off(channel=mapped_channel)
    _wait_for_events(output_port=output_port, expected_count=len(pattern.cc_events))

    callback_events = output_port.snapshot()
    print(f"Total callback events: {len(callback_events)}")

    return DemoResult(
        pattern=pattern,
        mapped_channel=mapped_channel,
        callback_events=callback_events,
    )


def main() -> int:
    """CLI entrypoint."""
    run_demo()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

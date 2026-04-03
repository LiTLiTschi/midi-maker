"""Application entrypoint for midi-scripter GUI runtime."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from midi_maker.app import midi_scripter_api
from midi_maker.app.config import ConfigError, load_app_config
from midi_maker.app.runtime import MidiMakerRuntime


def main(argv: Sequence[str] | None = None) -> int:
    """Run the MIDI Maker GUI application."""
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        config = load_app_config(Path(args.config))
        runtime = MidiMakerRuntime.from_config(config)
        _register_subscriptions(runtime)
        midi_scripter_api.start_gui()
        return 0
    except (ConfigError, RuntimeError) as exc:
        print(f"Startup failed: {exc}", file=sys.stderr)
        return 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="midi-maker")
    parser.add_argument("--config", required=True, help="Path to JSON config file")
    return parser


def _register_subscriptions(runtime: MidiMakerRuntime) -> None:
    trigger_port = midi_scripter_api.MidiIn(name=runtime.config.ports.trigger_input)
    source_port = midi_scripter_api.MidiIn(name=runtime.config.ports.cc_source_input)
    sequencer_port = midi_scripter_api.MidiIn(name=runtime.config.ports.sequencer_input)

    def handle_trigger_on(msg: object) -> None:
        if runtime.engine_running:
            runtime.cc_recorder.trigger_handler.handle_trigger_on(msg)

    def handle_trigger_off(msg: object) -> None:
        if runtime.engine_running:
            runtime.cc_recorder.trigger_handler.handle_trigger_off(msg)

    def handle_source_cc(msg: object) -> None:
        if not runtime.engine_running:
            return

        cc_number = getattr(msg, "control", None)
        value = getattr(msg, "value", None)
        channel = getattr(msg, "channel", 0)

        if not isinstance(cc_number, int) or not isinstance(value, int):
            return

        runtime.cc_recorder.capture_cc(
            cc_number=cc_number,
            value=value,
            channel=channel if isinstance(channel, int) else 0,
        )

    def handle_sequencer_note_on(msg: object) -> None:
        if runtime.engine_running:
            runtime.sequencer_interface.handle_note_on(
                channel=getattr(msg, "channel", 0),
            )

    def handle_sequencer_note_off(msg: object) -> None:
        if runtime.engine_running:
            runtime.sequencer_interface.handle_note_off(
                channel=getattr(msg, "channel", 0),
            )

    trigger_port.subscribe(midi_scripter_api.MidiType.NOTE_ON, handle_trigger_on)
    trigger_port.subscribe(midi_scripter_api.MidiType.NOTE_OFF, handle_trigger_off)
    source_port.subscribe(midi_scripter_api.MidiType.CONTROL_CHANGE, handle_source_cc)
    sequencer_port.subscribe(midi_scripter_api.MidiType.NOTE_ON, handle_sequencer_note_on)
    sequencer_port.subscribe(midi_scripter_api.MidiType.NOTE_OFF, handle_sequencer_note_off)


if __name__ == "__main__":
    raise SystemExit(main())

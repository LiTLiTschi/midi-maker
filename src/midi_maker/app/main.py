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
    trigger_port = _resolve_runtime_port(
        runtime=runtime,
        path=("cc_recorder", "trigger_handler", "trigger_port"),
        port_name=runtime.config.ports.trigger_input,
    )
    source_port = _resolve_runtime_port(
        runtime=runtime,
        path=("cc_recorder", "stream_capture", "source_port"),
        port_name=runtime.config.ports.cc_source_input,
    )
    sequencer_port = _resolve_runtime_port(
        runtime=runtime,
        path=("sequencer_interface", "sequencer_port"),
        port_name=runtime.config.ports.sequencer_input,
    )

    def handle_trigger_on(msg: object) -> None:
        if runtime.engine_running:
            runtime.cc_recorder.trigger_handler.handle_trigger_on(msg)

    def handle_trigger_off(msg: object) -> None:
        if runtime.engine_running:
            runtime.cc_recorder.trigger_handler.handle_trigger_off(msg)

    def handle_source_cc(msg: object) -> None:
        if not runtime.engine_running:
            return

        cc_number = _first_int_attr(msg, ("data1", "control"))
        value = _first_int_attr(msg, ("data2", "value"))
        channel = _safe_channel(getattr(msg, "channel", 0))

        if cc_number is None or value is None:
            return

        runtime.cc_recorder.capture_cc(
            cc_number=cc_number,
            value=value,
            channel=channel,
        )

    def handle_sequencer_note_on(msg: object) -> None:
        if runtime.engine_running:
            runtime.sequencer_interface.handle_note_on(
                channel=_safe_channel(getattr(msg, "channel", 0)),
            )

    def handle_sequencer_note_off(msg: object) -> None:
        if runtime.engine_running:
            runtime.sequencer_interface.handle_note_off(
                channel=_safe_channel(getattr(msg, "channel", 0)),
            )

    _bind_subscription(trigger_port, midi_scripter_api.MidiType.NOTE_ON, handle_trigger_on)
    _bind_subscription(trigger_port, midi_scripter_api.MidiType.NOTE_OFF, handle_trigger_off)
    _bind_subscription(
        source_port,
        midi_scripter_api.MidiType.CONTROL_CHANGE,
        handle_source_cc,
    )
    _bind_subscription(
        sequencer_port,
        midi_scripter_api.MidiType.NOTE_ON,
        handle_sequencer_note_on,
    )
    _bind_subscription(
        sequencer_port,
        midi_scripter_api.MidiType.NOTE_OFF,
        handle_sequencer_note_off,
    )


def _resolve_runtime_port(
    *,
    runtime: MidiMakerRuntime,
    path: tuple[str, ...],
    port_name: str,
) -> object:
    value: object = runtime
    for attr in path:
        value = getattr(value, attr, None)
        if value is None:
            break
    if value is not None:
        return value
    return midi_scripter_api.MidiIn(name=port_name)


def _bind_subscription(port: object, midi_type: object, callback: object) -> None:
    subscribe = getattr(port, "subscribe", None)
    if not callable(subscribe):
        raise RuntimeError("Configured MIDI input port does not support subscribe()")

    try:
        subscribe(midi_type, callback)
        return
    except TypeError:
        pass

    decorator = subscribe(midi_type)
    if not callable(decorator):
        raise RuntimeError("Port subscribe() did not return a callable decorator")
    decorator(callback)


def _first_int_attr(msg: object, names: tuple[str, ...]) -> int | None:
    for name in names:
        value = getattr(msg, name, None)
        if isinstance(value, int):
            return value
    return None


def _safe_channel(value: object) -> int:
    if isinstance(value, int) and 0 <= value <= 15:
        return value
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

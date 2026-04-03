# Usage Guide

This guide covers the runnable midi-scripter app path and the supporting CC automation workflow.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"
pip install midi-scripter
```

## Launch the app

Startup requires a config file and fails fast on invalid config or unresolved ports.

```bash
midi-maker --config /path/to/config.json
```

Equivalent module run:

```bash
python -m midi_maker.app.main --config /path/to/config.json
```

## Config schema

Required keys:

- `ports.trigger_input` (string)
- `ports.cc_source_input` (string)
- `ports.sequencer_input` (string)
- `ports.daw_output` (string)
- `library_path` (string)

Optional keys:

- `default_recording_mode`: `"HOLD"` or `"TOGGLE"` (default `"TOGGLE"`)
- `default_channel_mappings`: object of string channel keys `"0"`..`"15"` to pattern IDs

Example:

```json
{
  "ports": {
    "trigger_input": "Drum Pedal",
    "cc_source_input": "MIDI Controller",
    "sequencer_input": "MPD232",
    "daw_output": "To DAW"
  },
  "library_path": "patterns/library.json",
  "default_recording_mode": "TOGGLE",
  "default_channel_mappings": {
    "0": "filter-a",
    "1": "filter-b"
  }
}
```

Semantics:

- Relative `library_path` resolves from the config file directory.
- Missing library file starts as empty library.
- Existing but invalid library file fails startup.
- Mapping entries with missing pattern IDs are warned and skipped.

## Runtime behavior

- `start_engine()` enables event processing.
- While stopped, subscribed MIDI callbacks do nothing.
- `stop_engine()` returns `False` while recording and keeps the engine running.

## Channel numbering

- Runtime/config channels: `0..15`
- UI channels in playback controls: `1..16`
- Conversion rule: `runtime_channel = ui_channel - 1`

## Library and playback workflow

1. Trigger recording and capture CC events.
2. Save to pattern library.
3. Map a sequencer channel to the saved pattern.
4. Note-on triggers attack playback; note-off triggers decay playback.

## Console examples

```bash
python examples/basic_recording_playback.py
python examples/sequencer_integration.py
```

## Test commands

```bash
pytest -q
pytest tests/test_app -q
pytest tests/test_gui -q
pytest tests/integration/test_midi_scripter_workflow.py -q
```

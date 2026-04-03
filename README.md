# MIDI Maker

MIDI Maker is a MIDI CC automation toolkit for **midi-scripter** workflows: capture CC movement, store reusable patterns, and trigger attack/decay playback from sequencer gates.

## Installation

From this repository checkout:

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"
```

To run the app entrypoint, install midi-scripter in the same environment:

```bash
pip install midi-scripter
```

## Start the app

The app requires an explicit JSON config file:

```bash
midi-maker --config /path/to/config.json
# or
python -m midi_maker.app.main --config /path/to/config.json
```

## Config format

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
    "0": "pattern-id-a"
  }
}
```

Notes:
- `library_path` may be relative; relative paths resolve from the config file directory.
- Missing library file is allowed (runtime starts with an empty in-memory library).
- Invalid existing library file is fail-fast at startup.
- Channel mappings use runtime channels `0..15`.

## Engine behavior

- Subscriptions are always registered, but event handling is gated by `engine_running`.
- `stop_engine()` is blocked while recording and reports: `Stop recording before stopping engine`.
- Default mappings that reference unknown pattern IDs are skipped with a warning.

## Channel numbering

- Runtime and config channel keys: `0..15`
- PlaybackControls UI channels: `1..16` (converted to runtime by subtracting 1)

## Examples

```bash
python examples/basic_recording_playback.py
python examples/sequencer_integration.py
```

## Development

```bash
pytest -q
```

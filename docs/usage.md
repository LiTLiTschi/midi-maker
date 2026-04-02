# Usage Guide

This guide covers setup and the CC automation workflow implemented in this repository.

## Installation and setup

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"
```

`-e` installs the package in editable mode, and `[dev]` adds development tools (including `pytest`, `black`, `mypy`, and `isort`).

## Core concepts

### Recording

Use `CCRecorder` to capture CC automation:

- `start_recording(pattern_id=...)` begins capture
- `capture_cc(...)` appends CC events while recording
- `stop_recording(name=...)` returns an `AutomationPattern`

Relevant module: `midi_maker.recording`.

### Automation patterns

`AutomationPattern` stores captured `CCEvent`s plus metadata.

- `analyze_attack_decay()` splits events into `attack_events` and `decay_events`
- `PatternLibrary` stores patterns in memory and can save/load JSON libraries

Relevant module: `midi_maker.automation`.

### Playback

Use `AutomationPlayer` for direct playback and `PlaybackScheduler` for threaded/scheduled playback.

Playback behavior is controlled with `PlaybackMode` (for example: `FULL_SEQUENCE`, `ATTACK_ONLY`, `DECAY_ONLY`, `SNAPSHOT`).

Relevant module: `midi_maker.playback`.

### Sequencer integration

`SequencerInterface` maps channels to pattern IDs and forwards note gate events:

- note-on (`handle_note_on`) triggers attack playback
- note-off (`handle_note_off`) triggers decay playback

`GateProcessor` resolves mapped patterns and triggers the configured player/scheduler.

Relevant modules: `midi_maker.patterns`, `midi_maker.playback.gates`.

## Basic workflow (examples)

### 1) Record + play back a pattern

Run:

```bash
python examples/basic_recording_playback.py
```

This example (`examples/basic_recording_playback.py`) demonstrates:

1. Creating a `CCRecorder`
2. Starting recording (`start_recording`)
3. Capturing CC values with `capture_cc`
4. Stopping recording to produce an `AutomationPattern`
5. Playing the full sequence via `AutomationPlayer.play_full_sequence`

### 2) Sequencer-driven attack/decay playback

Run:

```bash
python examples/sequencer_integration.py
```

This example (`examples/sequencer_integration.py`) demonstrates:

1. Building/storing a pattern in `PatternLibrary`
2. Creating `PlaybackScheduler`, `GateProcessor`, and `SequencerInterface`
3. Mapping a channel to a pattern ID (`map_pattern_to_channel`)
4. Triggering attack on gate open (`handle_note_on`)
5. Triggering decay on gate close (`handle_note_off`)

## Running tests

Run the full suite:

```bash
pytest -q
```

Run example smoke tests only:

```bash
pytest tests/test_examples -q
```

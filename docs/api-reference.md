# API Reference

This document summarizes the primary public APIs used by the midi-scripter integration pass.

## `midi_maker.app`

### `midi_maker.app.config`

- `ConfigError`: configuration load/validation failure.
- `PortConfig(trigger_input, cc_source_input, sequencer_input, daw_output)`
- `AppConfig(ports, library_path, default_recording_mode, default_channel_mappings, config_dir)`
- `load_app_config(path: Path) -> AppConfig`

Behavior:
- strict required-key/type validation
- channel keys constrained to `0..15`
- relative library paths resolved from config directory

### `midi_maker.app.runtime`

- `RuntimeDependencies(list_input_ports, list_output_ports, create_input_port, create_output_port)`
- `MidiMakerRuntime.from_config(config, deps=None) -> MidiMakerRuntime`

Runtime members:
- `cc_recorder`
- `pattern_library`
- `playback_scheduler`
- `gate_processor`
- `sequencer_interface`
- `engine_running`
- `last_status_message`

Lifecycle methods:
- `start_engine() -> None`
- `stop_engine() -> bool`
- `shutdown() -> None`

Semantics:
- unresolved configured ports fail fast with available-port diagnostics
- missing pattern library file is allowed
- invalid existing library file fails fast
- default mappings to missing pattern IDs warn-and-skip
- engine stop is blocked while recording

### `midi_maker.app.main`

- `main(argv: Sequence[str] | None = None) -> int`

Startup flow:
1. parse required `--config`
2. load config
3. compose runtime
4. register MIDI subscriptions
5. call `start_gui()`

Callback behavior:
- all handlers are gated by `engine_running`
- CC message extraction supports both (`data1`, `data2`) and (`control`, `value`)
- channel input is normalized to `0..15`

### `midi_maker.app.midi_scripter_api`

Adapter boundary around optional dependency:
- `MidiIn`, `MidiOut`, `MidiType`, `start_gui`
- `list_input_ports() -> list[str]`
- `list_output_ports() -> list[str]`

When midi-scripter is unavailable, constructor calls fail with install guidance.

## `midi_maker.gui`

Refactored as widget-owner adapters with injected widget protocols:

- `RecordingPanel`
- `PatternBrowser`
- `PlaybackControls`

These classes delegate business logic to runtime/backend services and keep UI-state logic testable via fake widget facades.

`PlaybackControls` channel contract:
- UI channel range: `1..16`
- runtime channel range: `0..15`

## Core backend modules

### `midi_maker.recording`
- `CCRecorder`
- `StreamCapture`
- `TriggerHandler`

### `midi_maker.automation`
- `AutomationPattern`
- `PatternLibrary`
- `PatternAnalyzer`

### `midi_maker.playback`
- `AutomationPlayer`
- `PlaybackScheduler`
- `GateProcessor`

### `midi_maker.patterns`
- `GateStateMachine`
- `SequencerInterface`

For runnable examples, see:
- `examples/basic_recording_playback.py`
- `examples/sequencer_integration.py`

# API Reference

This document describes the current public APIs for the framework modules in `midi_maker`.

> **Current integration status:** Several interfaces intentionally use optional ports/protocols and can run without MIDI hardware or GUI frameworks. These are framework placeholders designed for hardware-free development and testing.

## `midi_maker.core`

Exports: `RecordingState`, `RecordingMode`, `PlaybackMode`, `CCAutomationType`, `GateState`, `CCEvent`, `MidiMakerError`, `RecordingError`, `PlaybackError`, `PatternError`

### Enums
- `RecordingState`: `IDLE`, `RECORDING`, `STOPPED`
- `RecordingMode`: `HOLD`, `TOGGLE`
- `PlaybackMode`: `FULL_SEQUENCE`, `ATTACK_ONLY`, `DECAY_ONLY`, `ATTACK_DECAY`, `SNAPSHOT`
- `CCAutomationType`: `FILTER_SWEEP`, `VOLUME_FADE`, `PAN_SWEEP`, `RESONANCE`, `CUSTOM`
- `GateState`: `CLOSED`, `OPEN`

### `CCEvent`
Dataclass for captured MIDI CC events.

```python
CCEvent(cc_number: int, value: int, channel: int, timestamp: float)
```

- Constructor validates MIDI ranges (`cc_number` 0-127, `value` 0-127, `channel` 0-15) and non-negative `timestamp`.

### Exceptions
- `MidiMakerError`: Base exception.
- `RecordingError`: Recording-related errors.
- `PlaybackError`: Playback-related errors.
- `PatternError`: Pattern/library-related errors.

---

## `midi_maker.recording`

Exports: `CCRecorder`, `StreamCapture`, `TriggerHandler`

> Hardware note: `trigger_port` and `source_port` are optional (`None` is valid), so recording logic is usable without real MIDI devices.

### `StreamCapture`
Buffers CC messages with timestamps.

```python
StreamCapture(source_port: Any | None = None)
```

Primary methods:
- `start_capture() -> None`
- `stop_capture() -> list[CCEvent]`
- `capture_cc(cc_number: int, value: int, channel: int = 0, timestamp: float | None = None) -> None`
- `get_events() -> list[CCEvent]`
- `clear() -> None`

Properties:
- `event_count: int`
- `is_active: bool`

### `TriggerHandler`
State machine for pedal-triggered recording.

```python
TriggerHandler(trigger_port: Any | None = None)
```

Primary methods:
- `handle_trigger_on(msg: Any | None = None) -> None`
- `handle_trigger_off(msg: Any | None = None) -> None`
- `set_mode(mode: RecordingMode) -> None`
- `get_state() -> RecordingState`
- `reset() -> None`
- `set_on_state_change(callback: Callable[[RecordingState, RecordingState], None] | None) -> None`

Properties:
- `is_recording: bool`
- `is_idle: bool`
- `is_stopped: bool`

### `CCRecorder`
Coordinator combining trigger handling and stream capture.

```python
CCRecorder(trigger_port: Any | None = None, source_port: Any | None = None)
```

Primary methods:
- `start_recording(pattern_id: str | None = None) -> str`
- `stop_recording(name: str | None = None) -> AutomationPattern`
- `set_recording_mode(mode: RecordingMode) -> None`
- `capture_cc(cc_number: int, value: int, channel: int = 0, timestamp: float | None = None) -> None`
- `reset() -> None`
- `get_state() -> RecordingState`
- `get_events() -> list[CCEvent]`

Properties:
- `is_recording: bool`
- `is_idle: bool`
- `event_count: int`

---

## `midi_maker.automation`

Exports: `AutomationPattern`, `PatternAnalyzer`, `PatternLibrary`, `PatternNotFoundError`

### `AutomationPattern`
Dataclass storing captured automation and derived attack/decay segments.

```python
AutomationPattern(
    pattern_id: str,
    name: str,
    cc_events: list[CCEvent],
    duration: float,
    attack_events: list[CCEvent] = [],
    decay_events: list[CCEvent] = [],
    metadata: dict[str, Any] = {},
)
```

Primary methods:
- `analyze_attack_decay() -> None`
- `to_dict() -> dict[str, Any]`
- `@classmethod from_dict(data: dict[str, Any]) -> AutomationPattern`

### `PatternLibrary`
In-memory pattern collection with JSON persistence.

```python
PatternLibrary(library_path: str = "patterns.json")
```

Primary methods:
- `add_pattern(pattern: AutomationPattern) -> None`
- `get_pattern(pattern_id: str) -> AutomationPattern`
- `remove_pattern(pattern_id: str) -> None`
- `list_patterns() -> list[str]`
- `save_library(path: str | None = None) -> None`
- `load_library(path: str | None = None) -> None`
- `clear() -> None`

Dunder helpers:
- `__len__() -> int`
- `__contains__(pattern_id: str) -> bool`

### `PatternAnalyzer`
Static utility class for automation analysis.

Primary methods:
- `split_attack_decay(cc_events: list[CCEvent]) -> tuple[list[CCEvent], list[CCEvent]]`
- `detect_cc_type(cc_events: list[CCEvent]) -> CCAutomationType`
- `optimize_events(cc_events: list[CCEvent]) -> list[CCEvent]`
- `calculate_duration(cc_events: list[CCEvent]) -> float`
- `find_peak_event(cc_events: list[CCEvent]) -> CCEvent | None`
- `get_value_range(cc_events: list[CCEvent]) -> tuple[int, int]`

### `PatternNotFoundError`
- Custom `KeyError` subclass raised for missing pattern IDs.

---

## `midi_maker.playback`

Exports: `AutomationPlayer`, `PlaybackScheduler`, `GateProcessor`

> Hardware note: playback APIs are intentionally decoupled from concrete MIDI backends via protocols/optional ports.

### `AutomationPlayer`
Core CC playback implementation.

```python
AutomationPlayer(output_port: MidiOutputPort | None = None)
```

Related protocol:
- `MidiOutputPort.send_cc(cc_number: int, value: int, channel: int) -> None`

Primary methods:
- `set_cc_output_callback(callback: CCOutputCallback | None) -> None`
- `play_full_sequence(pattern: AutomationPattern) -> None`
- `play_attack_phase(attack_events: list[CCEvent]) -> None`
- `play_decay_phase(decay_events: list[CCEvent]) -> None`
- `play_cc_snapshot(cc_values: dict[int, int], channel: int = 0) -> None`

### `PlaybackScheduler`
Threaded scheduler for asynchronous playback.

```python
PlaybackScheduler(output_port: MidiOutputPort | None = None)
```

Primary methods:
- `start_pattern_playback(pattern: AutomationPattern, playback_mode: PlaybackMode) -> str`
- `stop_pattern_playback(playback_id: str) -> None`
- `stop_all_playbacks() -> None`
- `schedule_cc_event(cc_event: CCEvent, delay_ms: float) -> None`

### `GateProcessor`
Triggers attack/decay playback from gate transitions.

```python
GateProcessor(
    sequencer_port: object | None = None,
    *,
    player: AttackDecayPlayer | None = None,
    scheduler: AttackDecayScheduler | None = None,
    pattern_library: PatternProvider | None = None,
)
```

Primary methods:
- `set_pattern_for_channel(channel: int, pattern_id: str) -> None`
- `handle_gate_on(channel: int) -> str | None`
- `handle_gate_off(channel: int) -> str | None`

---

## `midi_maker.patterns`

Exports: `GateStateMachine`, `GateTransition`, `SequencerInterface`

> Integration note: these classes model sequencing behavior and mappings; they do not require a concrete sequencer implementation to operate.

### `GateTransition`
Enum for gate transitions:
- `OPENED`
- `CLOSED`
- `NO_CHANGE`

### `GateStateMachine`
Tracks per-channel gate state and overlap behavior.

```python
GateStateMachine(history_size: int = 100)
```

Primary methods:
- `update_gate_state(channel: int, gate_on: bool) -> GateTransition`
- `has_overlapping_gates(channel: int) -> bool`
- `get_gate_duration(channel: int) -> float`
- `get_current_state(channel: int) -> GateState`
- `get_open_count(channel: int) -> int`
- `get_history() -> list[GateEvent]`
- `clear_channel(channel: int) -> None`
- `clear_all() -> None`

### `SequencerInterface`
Coordinates note gates with channel-to-pattern mappings.

```python
SequencerInterface(
    sequencer_port=None,
    channel_mapping: dict[int, str] | None = None,
    gate_processor=None,
)
```

Primary methods:
- `map_pattern_to_channel(channel: int, pattern_id: str) -> None`
- `unmap_channel(channel: int) -> None`
- `get_active_channels() -> set[int]`
- `handle_note_on(channel: int) -> None`
- `handle_note_off(channel: int) -> None`

---

## `midi_maker.gui`

Exports: `RecordingPanel`, `PatternBrowser`, `PlaybackControls`

> Placeholder note: GUI module currently provides dependency-free state models (not concrete toolkit widgets).

### `RecordingPanel`
State holder for recording UI-facing data.

```python
RecordingPanel(cc_recorder: CCRecorderLike)
```

Primary methods:
- `update_recording_status(status: RecordingState) -> None`
- `update_input_level(cc_value: int) -> None`

### `PatternBrowser`
Pattern list/details model.

```python
PatternBrowser(pattern_library: Any)
```

Primary methods:
- `refresh_pattern_list() -> None`
- `show_pattern_details(pattern_id: str) -> None`

### `PlaybackControls`
Playback scaling control model.

```python
PlaybackControls(playback_scheduler: Any)
```

Primary methods:
- `apply_tempo_scaling(scale_factor: float) -> None`
- `apply_velocity_scaling(scale_factor: float) -> None`

Constants:
- `MIN_TEMPO_SCALE = 0.1`
- `MAX_TEMPO_SCALE = 4.0`
- `MIN_VELOCITY_SCALE = 0.0`
- `MAX_VELOCITY_SCALE = 2.0`

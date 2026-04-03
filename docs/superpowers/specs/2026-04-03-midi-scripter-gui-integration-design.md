# MIDI Maker: midi-scripter GUI Integration Design (Pass One)

**Date**: 2026-04-03  
**Status**: Design Approved (Drafted for Spec Review)  
**Scope**: Runnable midi-scripter app with core live workflow

## Problem Statement

The repository currently provides a complete backend CC automation framework and GUI state-model classes, but does not launch a real midi-scripter GUI window or wire live MIDI ports/events.  
This pass implements the first practical performer-facing app layer on top of the existing framework.

## Target Outcome (Middle Path)

Deliver a **runnable midi-scripter app** with:

1. Recording status indicator
2. HOLD/TOGGLE recording mode control
3. Pattern save/load controls
4. Channel-to-pattern mapping controls
5. Engine Start/Stop control

Plus end-to-end live wiring:

- Pedal trigger controls recording
- CC input is captured while recording
- Sequencer gate events trigger attack/decay playback

## User Constraints and Decisions

1. Implement the **middle path**: runnable app + core live workflow (not full feature-complete system in one pass).
2. Convert `midi_maker.gui/*` into **direct midi-scripter widget classes** (not pure state models).
3. Configuration must be **explicit and required**, with **fail-fast startup**.
4. Config source in pass one: **required CLI argument** (`--config <path>`), no fallback discovery.

## Architecture

### 1. GUI layer (refactor existing package)

Refactor:

- `midi_maker.gui.recording_panel`
- `midi_maker.gui.pattern_browser`
- `midi_maker.gui.playback_controls`

from dependency-free models to concrete midi-scripter GUI widget owners.

Responsibilities:

- Render controls and status text.
- Expose clear callbacks/hooks for runtime actions.
- Avoid direct business logic; delegate to runtime services.

### 2. Runtime composition layer (new)

Add app composition modules:

- `midi_maker.app.config`  
  Parse and validate required config file.
- `midi_maker.app.runtime`  
  Construct and wire services (recorder, library, scheduler, gates, sequencer).
- `midi_maker.app.main`  
  Parse CLI args, initialize runtime/UI, register MIDI subscriptions, call `start_gui()`.

### 3. Existing domain modules (reuse)

Reuse current backend implementation as-is where possible:

- Recording: `CCRecorder`, `TriggerHandler`, `StreamCapture`
- Automation: `AutomationPattern`, `PatternLibrary`, `PatternAnalyzer`
- Playback: `AutomationPlayer`, `PlaybackScheduler`, `GateProcessor`
- Patterns: `GateStateMachine`, `SequencerInterface`

## Runtime Data Flow

### Startup

1. `python -m midi_maker.app.main --config <path>`
2. Parse + validate config (required).
3. Open configured MIDI ports:
   - trigger input (pedal)
   - CC source input
   - sequencer input
   - DAW output
4. Initialize services:
   - `CCRecorder`
   - `PatternLibrary`
   - `PlaybackScheduler`
   - `GateProcessor`
   - `SequencerInterface`
5. Load pattern library from configured path.
6. Build GUI widgets and bind callbacks.
7. Register midi-scripter subscriptions.
8. Start GUI loop via `start_gui()`.

### Recording flow

1. Pedal NOTE_ON / NOTE_OFF events route to trigger handling.
2. While recording is active, incoming CC messages are captured.
3. Stop recording yields `AutomationPattern`.
4. Pattern can be named/saved via pattern browser controls.

### Sequencer playback flow

1. Sequencer NOTE_ON / NOTE_OFF arrives on configured input.
2. `SequencerInterface` resolves channel mapping.
3. `GateProcessor` triggers attack/decay via scheduler/player.
4. CC output sent to configured DAW output port.

## GUI Controls (Pass One)

### Recording panel

- Recording status display: IDLE / RECORDING / STOPPED
- HOLD/TOGGLE selector bound to recorder mode
- Optional recent-event level indicator from captured CC values

### Pattern browser

- Pattern list (loaded + newly recorded)
- Save pattern action
- Load/reload library action
- Pattern selection for mapping

### Playback controls

- Channel -> pattern mapping controls
- Engine Start/Stop
- Clear mapping action (if included, must be explicit in UI and tests)

## Configuration Contract

Required file via `--config`.

Minimum required keys:

- Trigger input port name
- CC source input port name
- Sequencer input port name
- DAW output port name
- Pattern library file path

Optional keys (if included in pass one):

- default recording mode
- default channel mappings

## Error Handling Strategy

### Fail-fast startup (required)

- Missing `--config` argument -> immediate exit with usage and actionable message.
- Config file missing/unreadable/invalid format -> immediate exit with clear reason.
- Missing required config keys -> immediate exit listing all missing keys.
- Configured MIDI ports not found -> immediate exit listing unresolved names and available ports.

### Runtime behavior

- Runtime MIDI send/port errors surface via visible status + logging.
- Engine Stop performs graceful shutdown:
  - stop all active playbacks
  - flush/close runtime resources cleanly

## Testing Strategy

### Unit tests

- Config parser/validator:
  - missing file
  - malformed config
  - missing keys
  - successful parse
- GUI callback wiring:
  - control actions invoke expected runtime methods

### Integration tests

- Runtime wiring with mocked midi-scripter ports/messages.
- End-to-end:
  - trigger start/stop
  - capture CC
  - create/save pattern
  - channel mapping
  - sequencer gate-triggered playback

### Smoke tests

- App entrypoint with fixture config starts successfully through initialization path.
- Startup failure tests confirm fail-fast diagnostics.

## Deliverables

1. Real midi-scripter GUI integration in `midi_maker.gui/*`
2. New app runtime/config/entrypoint modules
3. Required `--config` startup contract
4. Live MIDI subscription wiring for recording + sequencer playback
5. Tests for config/startup/wiring/GUI callback behavior
6. Updated usage docs with startup/config instructions

## Out of Scope (This Pass)

1. Rich desktop GUI polish beyond required controls
2. Advanced multi-pattern layering UX
3. Dynamic auto-discovery/fallback config sources
4. Full DAW-specific integrations
5. Broad refactor of core domain behavior unrelated to midi-scripter app wiring

## Definition of Done

1. App starts only with explicit config file and fails fast on invalid setup.
2. GUI window launches via midi-scripter `start_gui()`.
3. Required controls (recording status, HOLD/TOGGLE, save/load, mapping, engine start/stop) are functional.
4. Pedal-trigger recording and sequencer-trigger playback both operate end-to-end.
5. Test suite includes new config + runtime + GUI integration coverage.
6. Documentation explains configuration and startup for live usage.


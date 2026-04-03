# MIDI Maker midi-scripter GUI Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a runnable midi-scripter app that wires the existing MIDI automation backend to a real GUI and live MIDI ports with explicit config, fail-fast startup, and core recording/sequencer workflow.

**Architecture:** Add an app composition layer (`config`, `runtime`, `main`) and refactor `midi_maker.gui/*` from state models into direct midi-scripter widget owners. Reuse existing recording/automation/playback/pattern modules for business logic, while the new app layer handles config validation, port wiring, subscriptions, lifecycle gating, and GUI callbacks.

**Tech Stack:** Python 3.8+, pytest, midi-scripter (`MidiIn`, `MidiOut`, `MidiType`, `@subscribe`, `start_gui`), existing midi_maker modules

---

## Adapter Contract (must exist before runtime wiring)

`src/midi_maker/app/midi_scripter_api.py` must expose:

- `MidiIn`, `MidiOut`, `MidiType`, `start_gui`
- GUI widget symbols used by refactored GUI classes
- `list_input_ports() -> list[str]`
- `list_output_ports() -> list[str]`

Port-listing fallback behavior:
- If midi-scripter exposes native listing APIs, use them.
- Otherwise return an empty list and include `"available ports unavailable"` text in fail-fast diagnostics.

## File Structure

### New files
- `src/midi_maker/app/__init__.py` — app package exports
- `src/midi_maker/app/config.py` — config dataclasses + JSON loading/validation
- `src/midi_maker/app/runtime.py` — runtime composition and lifecycle coordination
- `src/midi_maker/app/main.py` — CLI/entrypoint (`--config`) and GUI launch
- `src/midi_maker/app/midi_scripter_api.py` — centralized midi-scripter import/adapter boundary
- `tests/test_app/test_config.py` — config parser/validator tests
- `tests/test_app/test_runtime.py` — runtime lifecycle + wiring tests
- `tests/test_app/test_main.py` — startup/fail-fast entrypoint tests
- `tests/integration/test_midi_scripter_workflow.py` — end-to-end app workflow with mocked midi-scripter interfaces

### Modified files
- `src/midi_maker/gui/recording_panel.py` — refactor to real midi-scripter widget owner
- `src/midi_maker/gui/pattern_browser.py` — refactor to real midi-scripter widget owner
- `src/midi_maker/gui/playback_controls.py` — refactor to real midi-scripter widget owner
- `src/midi_maker/gui/__init__.py` — export refactored GUI classes
- `src/midi_maker/recording/triggers.py` — optional: adapter method(s) for msg-driven subscribe callbacks if needed
- `src/midi_maker/recording/capture.py` — optional: adapter method(s) for msg-driven CC capture if needed
- `README.md` — replace stale generic CLI section with app-launch instructions
- `docs/usage.md` — add config schema/start command/live workflow sections
- `docs/api-reference.md` — add app module APIs and clarify GUI now binds midi-scripter widgets
- `pyproject.toml` — correct script entrypoint to existing `midi_maker.app.main:main` (or remove stale entry)

### Runtime config fixture files for tests
- `tests/fixtures/config/valid-config.json`
- `tests/fixtures/config/missing-keys.json`
- `tests/fixtures/config/invalid-mappings.json`

---

### Task 1: Create app config schema and fail-fast validator

**Files:**
- Create: `src/midi_maker/app/config.py`
- Create: `tests/test_app/test_config.py`
- Create: `tests/fixtures/config/valid-config.json`
- Create: `tests/fixtures/config/missing-keys.json`
- Create: `tests/fixtures/config/invalid-mappings.json`
- Modify: `src/midi_maker/app/__init__.py`

- [ ] **Step 1: Write failing config tests first**

```python
def test_load_valid_config_parses_required_and_optional_fields(tmp_path):
    cfg = load_app_config(Path("tests/fixtures/config/valid-config.json"))
    assert cfg.ports.trigger_input == "Drum Pedal"
    assert cfg.default_recording_mode.name == "TOGGLE"
    assert cfg.default_channel_mappings[0] == "pattern-id-a"

def test_missing_required_keys_raise_config_error(tmp_path):
    with pytest.raises(ConfigError, match="missing required keys"):
        load_app_config(Path("tests/fixtures/config/missing-keys.json"))

def test_invalid_channel_mapping_keys_raise_config_error(tmp_path):
    with pytest.raises(ConfigError, match="channel keys must be 0-15"):
        load_app_config(Path("tests/fixtures/config/invalid-mappings.json"))

def test_malformed_json_raises_config_error(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not valid json")
    with pytest.raises(ConfigError, match="invalid JSON"):
        load_app_config(bad)
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/test_app/test_config.py -v`  
Expected: FAIL (`ConfigError` or loader types not defined yet)

- [ ] **Step 3: Implement minimal config module**

```python
@dataclass
class PortConfig:
    trigger_input: str
    cc_source_input: str
    sequencer_input: str
    daw_output: str

@dataclass
class AppConfig:
    ports: PortConfig
    library_path: Path
    default_recording_mode: RecordingMode
    default_channel_mappings: Dict[int, str]
    config_dir: Path
```

Implement:
- `load_app_config(path: Path) -> AppConfig`
- strict required-key checks
- optional defaults (`TOGGLE`, empty mapping)
- channel key coercion from `"0"`..`"15"` to `int`
- resolve relative `library_path` against config-file directory
- malformed/unreadable JSON -> fail-fast `ConfigError` with actionable message

- [ ] **Step 4: Re-run tests**

Run: `pytest tests/test_app/test_config.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/midi_maker/app/config.py src/midi_maker/app/__init__.py tests/test_app/test_config.py tests/fixtures/config/*.json
git commit -m "feat(app): add config schema and fail-fast validation"
```

---

### Task 2: Build runtime composition and engine lifecycle gate

**Files:**
- Create: `src/midi_maker/app/runtime.py`
- Modify: `src/midi_maker/app/__init__.py`
- Create: `tests/test_app/test_runtime.py`

- [ ] **Step 1: Write failing runtime lifecycle tests**

```python
def test_runtime_starts_with_engine_stopped(valid_config):
    rt = MidiMakerRuntime.from_config(valid_config, deps=fakes())
    assert rt.engine_running is False

def test_start_engine_enables_processing(valid_config):
    rt = MidiMakerRuntime.from_config(valid_config, deps=fakes())
    rt.start_engine()
    assert rt.engine_running is True

def test_stop_engine_while_recording_is_blocked(valid_config):
    rt = MidiMakerRuntime.from_config(valid_config, deps=fakes(recording=True))
    stopped = rt.stop_engine()
    assert stopped is False
    assert "Stop recording before stopping engine" in rt.last_status_message

def test_unresolved_ports_fail_fast_with_available_ports(valid_config):
    with pytest.raises(RuntimeError, match="available ports"):
        MidiMakerRuntime.from_config(valid_config, deps=fakes(available_ports=["Known A", "Known B"]))
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/test_app/test_runtime.py -v`  
Expected: FAIL (`MidiMakerRuntime` not implemented)

- [ ] **Step 3: Implement runtime orchestrator**

Implement `MidiMakerRuntime` with:
- service composition (`CCRecorder`, `PatternLibrary`, `PlaybackScheduler`, `GateProcessor`, `SequencerInterface`)
- `engine_running` gate
- `start_engine()`, `stop_engine()`, `shutdown()`
- stop behavior while recording: return `False`, keep engine running, and set actionable status message
- startup behavior for `library_path`:
  - missing file => initialize empty library
  - invalid existing file => raise fail-fast error
- unresolved configured MIDI ports => fail-fast error listing missing names and available names
- default mapping load with warn-and-skip for missing pattern IDs

- [ ] **Step 4: Re-run runtime tests**

Run: `pytest tests/test_app/test_runtime.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/midi_maker/app/runtime.py src/midi_maker/app/__init__.py tests/test_app/test_runtime.py
git commit -m "feat(app): add runtime composition and engine lifecycle"
```

---

### Task 3: Refactor GUI modules to concrete midi-scripter widget adapters

**Files:**
- Modify: `src/midi_maker/gui/recording_panel.py`
- Modify: `src/midi_maker/gui/pattern_browser.py`
- Modify: `src/midi_maker/gui/playback_controls.py`
- Modify: `src/midi_maker/gui/__init__.py`
- Modify: `tests/test_gui/test_recording_panel.py`
- Modify: `tests/test_gui/test_pattern_browser.py`
- Modify: `tests/test_gui/test_playback_controls.py`
- Modify: `tests/test_gui/test_init.py`

- [ ] **Step 1: Write/adjust failing GUI tests against widget contract**

```python
def test_recording_panel_updates_status_widget(fake_widgets):
    panel = RecordingPanel(cc_recorder=fake_recorder(), widgets=fake_widgets)
    panel.update_recording_status(RecordingState.RECORDING)
    assert "RECORDING" in fake_widgets.status.text

def test_recording_panel_updates_recent_level_indicator(fake_widgets):
    panel = RecordingPanel(cc_recorder=fake_recorder(), widgets=fake_widgets)
    panel.update_input_level(96)
    assert fake_widgets.level.value == 96

def test_playback_controls_channel_mapping_conversion(fake_widgets):
    controls = PlaybackControls(playback_scheduler=fake_scheduler(), widgets=fake_widgets)
    controls.set_channel_mapping(ui_channel=2, pattern_id="pat-a")
    assert controls.runtime_mapping[1] == "pat-a"  # UI 2 -> runtime 1
```

Test-double contract for GUI task:
- define protocol-like test doubles in `tests/test_gui/fakes.py`:
  - `FakeGuiText` with `.text` and `set_text(...)`
  - `FakeButtonSelectorH` with selected value and on_change callback
  - `FakeButton` with on_click callback
  - `FakeListSelector` with items/selection
  - `FakeProgressBarH` + `FakeSliderH` with set/get value
- GUI modules accept widget factory/deps injection in constructors for deterministic tests.

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/test_gui -v`  
Expected: FAIL due to changed constructor/behavior

- [ ] **Step 3: Implement GUI refactor minimally**

Implement each class as:
- widget-owner with callbacks into runtime/services
- still testable via injected widget facades/mocks
- no direct business logic duplication

Required controls:
- recording status
- HOLD/TOGGLE
- recent-event level indicator
- pattern save/load/select
- channel mapping + clear mapping
- start/stop engine actions

- [ ] **Step 4: Re-run GUI tests**

Run: `pytest tests/test_gui -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/midi_maker/gui/*.py tests/test_gui/*.py
git commit -m "refactor(gui): bind gui modules to midi-scripter widget adapters"
```

---

### Task 4: Implement app entrypoint and midi-scripter subscriptions

**Files:**
- Create: `src/midi_maker/app/main.py`
- Create: `src/midi_maker/app/midi_scripter_api.py`
- Modify: `pyproject.toml`
- Create: `tests/test_app/test_main.py`

- [ ] **Step 1: Write failing entrypoint tests**

```python
def test_main_requires_config_arg():
    exit_code = main(["midi-maker"])
    assert exit_code != 0

def test_main_invokes_start_gui_with_valid_config(monkeypatch, tmp_path):
    called = {"start_gui": False}
    monkeypatch.setattr("midi_maker.app.main.start_gui", lambda: called.__setitem__("start_gui", True))
    assert main(["midi-maker", "--config", str(tmp_path / "valid-config.json")]) == 0
    assert called["start_gui"] is True
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/test_app/test_main.py -v`  
Expected: FAIL (`main` missing)

- [ ] **Step 3: Implement entrypoint and subscriptions**

Implement in `midi_maker.app.main`:
- argparse for required `--config`
- load/validate config
- create runtime and GUI components
- register subscriptions:
  - trigger input NOTE_ON/NOTE_OFF
  - CC source CONTROL_CHANGE
  - sequencer NOTE_ON/NOTE_OFF
- handler gating with `engine_running`
- call `start_gui()`

Update `pyproject.toml`:
- point script to `midi_maker.app.main:main`
- add/install midi-scripter dependency if available from index; if not available, implement guarded import path through `midi_scripter_api.py` with clear runtime install error.

midi-scripter adapter contract for this task:
- create a thin adapter module `src/midi_maker/app/midi_scripter_api.py` that centralizes imports:
  - `MidiIn`, `MidiOut`, `MidiType`, `start_gui`, widget classes used by GUI
- tests monkeypatch this adapter module (not third-party package directly), so app/main tests can run without midi-scripter installed/hardware.

- [ ] **Step 4: Re-run app-main tests**

Run: `pytest tests/test_app/test_main.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/midi_maker/app/main.py src/midi_maker/app/midi_scripter_api.py pyproject.toml tests/test_app/test_main.py
git commit -m "feat(app): add midi-scripter entrypoint and event subscriptions"
```

---

### Task 5: Wire integration behavior and startup failure semantics

**Files:**
- Create: `tests/integration/test_midi_scripter_workflow.py`
- Modify: `tests/integration/test_full_workflow.py` (only if shared helpers are needed)

- [ ] **Step 1: Write failing integration test for middle-path workflow**

```python
def test_midi_scripter_workflow_record_save_map_play(fake_midi_scripter, valid_config):
    app = boot_app(valid_config, fake_midi_scripter)
    app.runtime.start_engine()
    fake_midi_scripter.emit_trigger_on()
    fake_midi_scripter.emit_cc(74, 90, channel=0)
    fake_midi_scripter.emit_trigger_off()
    app.gui.pattern_browser.save_current_pattern("pat-live")
    app.gui.playback_controls.map_channel(ui_channel=1, pattern_id="pat-live")
    fake_midi_scripter.emit_sequencer_on(channel=0)
    assert fake_midi_scripter.output_events
```

- [ ] **Step 2: Run integration test to verify failure**

Run: `pytest tests/integration/test_midi_scripter_workflow.py -v`  
Expected: FAIL until app wiring is complete

- [ ] **Step 3: Implement minimal integration glue fixes**

Only add fixes needed to satisfy integration:
- mapping conversion correctness
- gate processing path
- save/load semantics per config

- [ ] **Step 4: Re-run integration tests**

Run: `pytest tests/integration/test_midi_scripter_workflow.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/integration/test_midi_scripter_workflow.py src/midi_maker/app/*.py src/midi_maker/gui/*.py
git commit -m "test(integration): cover midi-scripter live workflow"
```

---

### Task 6: Update docs and runnable startup instructions

**Files:**
- Modify: `README.md`
- Modify: `docs/usage.md`
- Modify: `docs/api-reference.md`

- [ ] **Step 1: Write failing doc-consistency checks (lightweight)**

Add assertions in existing doc-related tests (or create a small test) to ensure:
- startup command includes required `--config`
- no stale claim of `midi_maker.cli`

```python
def test_readme_references_app_entrypoint():
    readme = Path("README.md").read_text()
    assert "--config" in readme
    assert "midi_maker.cli" not in readme
```

- [ ] **Step 2: Run doc tests to verify failure**

Run: `pytest tests/test_examples -v` (or targeted doc test file)  
Expected: FAIL until docs updated

- [ ] **Step 3: Update docs minimally**

Document:
- required config file schema
- `python -m midi_maker.app.main --config ...`
- engine start/stop behavior
- channel numbering conversion (UI 1..16, runtime 0..15)
- missing-library-file semantics

- [ ] **Step 4: Re-run doc-related tests**

Run: `pytest tests/test_examples -v` + targeted doc tests  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add README.md docs/usage.md docs/api-reference.md tests/**/*.py
git commit -m "docs: add midi-scripter app startup and config guidance"
```

---

### Task 7: Full verification, polish, and final commit hygiene

**Files:**
- Modify: any touched files from prior tasks (only if verification reveals defects)

- [ ] **Step 1: Run full test suite**

Run: `pytest -q`  
Expected: PASS all tests

- [ ] **Step 2: Run focused app/GUI/integration commands**

Run:
- `pytest tests/test_app -q`
- `pytest tests/test_gui -q`
- `pytest tests/integration/test_midi_scripter_workflow.py -q`

Expected: PASS

- [ ] **Step 3: Startup smoke (CI-safe + optional hardware)**

Run (CI-safe):
- `pytest tests/test_app/test_main.py::test_main_invokes_start_gui_with_valid_config -q`

Expected:
- startup path succeeds with mocked midi-scripter adapter + fake ports

Optional local hardware smoke (manual):
- `python -m midi_maker.app.main --config /path/to/real-rig-config.json`

Expected:
- app reaches real GUI launch with resolved hardware ports

- [ ] **Step 4: Final cleanup commit (only if needed)**

```bash
git add -A
git commit -m "chore: finalize midi-scripter gui integration pass one"
```

- [ ] **Step 5: Prepare PR summary**

Include:
- implemented scope vs spec
- test evidence
- known follow-ups deferred to future pass

---

## Skills and execution notes

- Preferred implementation mode: `superpowers:subagent-driven-development`
- Alternative: `superpowers:executing-plans`
- Maintain TDD discipline per task (failing test -> minimal implementation -> passing test -> commit)
- Keep changes DRY and avoid speculative features outside this spec
- Use one focused commit per task to simplify review and rollback

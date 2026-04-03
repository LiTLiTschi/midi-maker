"""Tests for app runtime composition and lifecycle behavior."""

from __future__ import annotations

from pathlib import Path
from types import MappingProxyType

import pytest

from midi_maker.app.config import AppConfig, PortConfig
from midi_maker.automation import AutomationPattern, PatternLibrary
from midi_maker.core import CCEvent, RecordingMode


class FakeMidiPort:
    """Minimal fake MIDI port object with close tracking."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.closed = False

    def close(self) -> None:
        self.closed = True


class FakeRuntimeDeps:
    """Test double for runtime MIDI adapter dependencies."""

    def __init__(
        self,
        *,
        available_inputs: list[str],
        available_outputs: list[str],
    ) -> None:
        self.available_inputs = available_inputs
        self.available_outputs = available_outputs
        self.created_input_ports: list[FakeMidiPort] = []
        self.created_output_ports: list[FakeMidiPort] = []

    def list_input_ports(self) -> list[str]:
        return list(self.available_inputs)

    def list_output_ports(self) -> list[str]:
        return list(self.available_outputs)

    def create_input_port(self, name: str) -> FakeMidiPort:
        port = FakeMidiPort(name)
        self.created_input_ports.append(port)
        return port

    def create_output_port(self, name: str) -> FakeMidiPort:
        port = FakeMidiPort(name)
        self.created_output_ports.append(port)
        return port


@pytest.fixture
def valid_config(tmp_path: Path) -> AppConfig:
    return AppConfig(
        ports=PortConfig(
            trigger_input="Drum Pedal",
            cc_source_input="MIDI Controller",
            sequencer_input="MPD232",
            daw_output="To DAW",
        ),
        library_path=tmp_path / "patterns.json",
        default_recording_mode=RecordingMode.TOGGLE,
        default_channel_mappings=MappingProxyType({}),
        config_dir=tmp_path,
    )


def make_deps() -> FakeRuntimeDeps:
    return FakeRuntimeDeps(
        available_inputs=["Drum Pedal", "MIDI Controller", "MPD232"],
        available_outputs=["To DAW"],
    )


def make_pattern(pattern_id: str) -> AutomationPattern:
    return AutomationPattern(
        pattern_id=pattern_id,
        name=f"Pattern {pattern_id}",
        cc_events=[CCEvent(cc_number=74, value=64, channel=0, timestamp=0.0)],
        duration=0.0,
    )


def test_runtime_starts_with_engine_stopped(valid_config: AppConfig) -> None:
    from midi_maker.app.runtime import MidiMakerRuntime

    runtime = MidiMakerRuntime.from_config(valid_config, deps=make_deps())

    assert runtime.engine_running is False


def test_runtime_composes_core_services(valid_config: AppConfig) -> None:
    from midi_maker.app.runtime import MidiMakerRuntime
    from midi_maker.automation import PatternLibrary
    from midi_maker.patterns import SequencerInterface
    from midi_maker.playback import GateProcessor, PlaybackScheduler
    from midi_maker.recording import CCRecorder

    runtime = MidiMakerRuntime.from_config(valid_config, deps=make_deps())

    assert isinstance(runtime.cc_recorder, CCRecorder)
    assert isinstance(runtime.pattern_library, PatternLibrary)
    assert isinstance(runtime.playback_scheduler, PlaybackScheduler)
    assert isinstance(runtime.gate_processor, GateProcessor)
    assert isinstance(runtime.sequencer_interface, SequencerInterface)


def test_start_engine_enables_processing(valid_config: AppConfig) -> None:
    from midi_maker.app.runtime import MidiMakerRuntime

    runtime = MidiMakerRuntime.from_config(valid_config, deps=make_deps())

    runtime.start_engine()

    assert runtime.engine_running is True


def test_stop_engine_while_recording_is_blocked(valid_config: AppConfig) -> None:
    from midi_maker.app.runtime import MidiMakerRuntime

    runtime = MidiMakerRuntime.from_config(valid_config, deps=make_deps())
    runtime.start_engine()
    runtime.cc_recorder.start_recording(pattern_id="runtime-test")

    stopped = runtime.stop_engine()

    assert stopped is False
    assert runtime.engine_running is True
    assert runtime.last_status_message == "Stop recording before stopping engine"


def test_shutdown_stops_engine_and_recording(valid_config: AppConfig) -> None:
    from midi_maker.app.runtime import MidiMakerRuntime

    runtime = MidiMakerRuntime.from_config(valid_config, deps=make_deps())
    runtime.start_engine()
    runtime.cc_recorder.start_recording(pattern_id="runtime-test")

    runtime.shutdown()

    assert runtime.engine_running is False
    assert runtime.cc_recorder.is_recording is False


def test_missing_library_file_initializes_empty_library(valid_config: AppConfig) -> None:
    from midi_maker.app.runtime import MidiMakerRuntime

    runtime = MidiMakerRuntime.from_config(valid_config, deps=make_deps())

    assert runtime.pattern_library.list_patterns() == []


def test_invalid_existing_library_file_fails_fast(valid_config: AppConfig) -> None:
    from midi_maker.app.runtime import MidiMakerRuntime

    valid_config.library_path.write_text("{not valid json", encoding="utf-8")

    with pytest.raises(RuntimeError, match="Failed to load pattern library"):
        MidiMakerRuntime.from_config(valid_config, deps=make_deps())


def test_unresolved_ports_fail_fast_with_available_ports(valid_config: AppConfig) -> None:
    from midi_maker.app.runtime import MidiMakerRuntime

    deps = FakeRuntimeDeps(
        available_inputs=["Known A", "Known B"],
        available_outputs=["Known Out"],
    )

    with pytest.raises(RuntimeError, match="available") as exc_info:
        MidiMakerRuntime.from_config(valid_config, deps=deps)

    message = str(exc_info.value)
    assert "Drum Pedal" in message
    assert "MIDI Controller" in message
    assert "MPD232" in message
    assert "To DAW" in message
    assert "Known A" in message
    assert "Known Out" in message


def test_missing_default_mapping_warns_and_skips(valid_config: AppConfig) -> None:
    from midi_maker.app.runtime import MidiMakerRuntime

    library = PatternLibrary(str(valid_config.library_path))
    library.add_pattern(make_pattern("existing-pattern"))
    library.save_library()

    config_with_mappings = AppConfig(
        ports=valid_config.ports,
        library_path=valid_config.library_path,
        default_recording_mode=RecordingMode.TOGGLE,
        default_channel_mappings=MappingProxyType(
            {
                0: "existing-pattern",
                1: "missing-pattern",
            }
        ),
        config_dir=valid_config.config_dir,
    )

    with pytest.warns(UserWarning, match="missing-pattern"):
        runtime = MidiMakerRuntime.from_config(config_with_mappings, deps=make_deps())

    assert runtime.sequencer_interface.channel_mapping == {0: "existing-pattern"}

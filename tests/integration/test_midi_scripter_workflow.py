"""Integration coverage for midi-scripter workflow wiring."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType, SimpleNamespace

import pytest

from midi_maker.app.config import AppConfig, PortConfig
from midi_maker.app.main import _register_subscriptions
from midi_maker.app.runtime import MidiMakerRuntime, RuntimeDependencies
from midi_maker.automation import AutomationPattern
from midi_maker.core import RecordingMode
from midi_maker.gui.pattern_browser import PatternBrowser, PatternBrowserWidgets
from midi_maker.gui.playback_controls import PlaybackControls, PlaybackControlsWidgets


class FakeMidiIn:
    """Fake MIDI input port with subscription and emit support."""

    def __init__(self, name: str) -> None:
        self.name = name
        self._subscriptions: dict[str, object] = {}
        self.closed = False

    def subscribe(self, midi_type: str, callback: object) -> None:
        self._subscriptions[midi_type] = callback

    def emit(self, midi_type: str, msg: object) -> None:
        callback = self._subscriptions.get(midi_type)
        assert callback is not None
        callback(msg)

    def close(self) -> None:
        self.closed = True


class FakeMidiOut:
    """Fake MIDI output port that records outgoing CC events."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.sent_events: list[tuple[int, int, int]] = []
        self.closed = False

    def send_cc(self, cc_number: int, value: int, channel: int) -> None:
        self.sent_events.append((cc_number, value, channel))

    def close(self) -> None:
        self.closed = True


class FakeText:
    """Minimal text widget."""

    def __init__(self) -> None:
        self.text = ""

    def set_text(self, text: str) -> None:
        self.text = text


class FakeValue:
    """Minimal numeric widget."""

    def __init__(self, value: float = 0.0) -> None:
        self.value = value
        self.on_change = None

    def set_value(self, value: float) -> None:
        self.value = value

    def set_on_change(self, callback) -> None:  # noqa: ANN001
        self.on_change = callback


class FakeSelector:
    """Minimal selector widget."""

    def __init__(self, selected: str | None = None) -> None:
        self.items: list[str] = []
        self.selected = selected
        self.on_change = None

    def set_items(self, items: list[str]) -> None:
        self.items = items

    def set_selected(self, value: str | None) -> None:
        self.selected = value

    def set_on_change(self, callback) -> None:  # noqa: ANN001
        self.on_change = callback


class FakeButton:
    """Minimal button widget."""

    def __init__(self) -> None:
        self.on_click = None

    def set_on_click(self, callback) -> None:  # noqa: ANN001
        self.on_click = callback

    def click(self) -> object | None:
        if self.on_click is None:
            return None
        return self.on_click()


@dataclass
class FakeRuntimeDeps:
    """Runtime dependency provider backed by fake MIDI ports."""

    input_ports: dict[str, FakeMidiIn]
    output_port: FakeMidiOut

    def list_input_ports(self) -> list[str]:
        return list(self.input_ports.keys())

    def list_output_ports(self) -> list[str]:
        return [self.output_port.name]

    def create_input_port(self, name: str) -> FakeMidiIn:
        return self.input_ports[name]

    def create_output_port(self, name: str) -> FakeMidiOut:
        assert name == self.output_port.name
        return self.output_port


@pytest.fixture
def valid_config(tmp_path: Path) -> AppConfig:
    return AppConfig(
        ports=PortConfig(
            trigger_input="Trigger",
            cc_source_input="Source",
            sequencer_input="Sequencer",
            daw_output="DAW",
        ),
        library_path=tmp_path / "patterns.json",
        default_recording_mode=RecordingMode.HOLD,
        default_channel_mappings=MappingProxyType({}),
        config_dir=tmp_path,
    )


@pytest.fixture
def runtime_deps() -> FakeRuntimeDeps:
    return FakeRuntimeDeps(
        input_ports={
            "Trigger": FakeMidiIn("Trigger"),
            "Source": FakeMidiIn("Source"),
            "Sequencer": FakeMidiIn("Sequencer"),
        },
        output_port=FakeMidiOut("DAW"),
    )


def test_midi_scripter_workflow_record_save_map_play(
    monkeypatch: pytest.MonkeyPatch,
    valid_config: AppConfig,
    runtime_deps: FakeRuntimeDeps,
) -> None:
    from midi_maker import app

    class ImmediateThread:
        def __init__(self, *, target, args=(), daemon: bool = False, kwargs=None):  # noqa: ANN001
            _ = daemon
            self._target = target
            self._args = args
            self._kwargs = kwargs or {}

        def start(self) -> None:
            self._target(*self._args, **self._kwargs)

    capture_perf_counter_values = iter([100.0, 100.0, 100.0])
    monkeypatch.setattr(
        "midi_maker.recording.capture.time.perf_counter",
        lambda: next(capture_perf_counter_values),
    )
    monkeypatch.setattr(
        "midi_maker.playback.scheduler.threading.Thread",
        ImmediateThread,
    )

    def instant_play_with_interrupt(self, player, events, stop_event) -> None:  # noqa: ANN001
        for event in events:
            if stop_event.is_set():
                break
            player._send_cc(event.cc_number, event.value, event.channel)  # noqa: SLF001

    monkeypatch.setattr(
        "midi_maker.playback.scheduler.PlaybackScheduler._play_with_interrupt",
        instant_play_with_interrupt,
    )

    runtime = MidiMakerRuntime.from_config(
        valid_config,
        deps=RuntimeDependencies(
            list_input_ports=runtime_deps.list_input_ports,
            list_output_ports=runtime_deps.list_output_ports,
            create_input_port=runtime_deps.create_input_port,
            create_output_port=runtime_deps.create_output_port,
        ),
    )

    monkeypatch.setattr(
        app.main.midi_scripter_api,
        "MidiType",
        SimpleNamespace(NOTE_ON="NOTE_ON", NOTE_OFF="NOTE_OFF", CONTROL_CHANGE="CONTROL_CHANGE"),
    )
    _register_subscriptions(runtime)
    runtime.start_engine()

    runtime_deps.input_ports["Trigger"].emit("NOTE_ON", SimpleNamespace(channel=0))
    runtime_deps.input_ports["Source"].emit(
        "CONTROL_CHANGE",
        SimpleNamespace(control=74, value=40, channel=0),
    )
    runtime_deps.input_ports["Source"].emit(
        "CONTROL_CHANGE",
        SimpleNamespace(control=74, value=90, channel=0),
    )
    runtime_deps.input_ports["Trigger"].emit("NOTE_OFF", SimpleNamespace(channel=0))

    assert runtime.cc_recorder.is_recording is False
    assert len(runtime.cc_recorder.get_events()) == 2

    pattern = AutomationPattern(
        pattern_id="pat-live",
        name="Pat Live",
        cc_events=runtime.cc_recorder.get_events(),
        duration=runtime.cc_recorder.get_events()[-1].timestamp,
    )
    pattern.analyze_attack_decay()
    runtime.pattern_library.add_pattern(pattern)

    pattern_browser = PatternBrowser(
        runtime.pattern_library,
        widgets=PatternBrowserWidgets(
            pattern_list=FakeSelector(),
            info_text=FakeText(),
            save_button=FakeButton(),
            load_button=FakeButton(),
        ),
    )
    pattern_browser.save_patterns()
    assert valid_config.library_path.exists()

    playback_controls = PlaybackControls(
        playback_scheduler=runtime.playback_scheduler,
        sequencer_interface=runtime.sequencer_interface,
        widgets=PlaybackControlsWidgets(
            tempo=FakeValue(1.0),
            velocity=FakeValue(1.0),
            channel=FakeSelector(selected="1"),
            pattern=FakeSelector(selected="pat-live"),
            clear_mapping=FakeButton(),
            start_engine=FakeButton(),
            stop_engine=FakeButton(),
        ),
    )
    playback_controls.set_channel_mapping(ui_channel=1, pattern_id="pat-live")

    runtime_deps.input_ports["Sequencer"].emit("NOTE_ON", SimpleNamespace(channel=0))

    assert runtime_deps.output_port.sent_events == [(74, 40, 0), (74, 90, 0)]

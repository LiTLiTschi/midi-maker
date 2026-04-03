"""Tests for app entrypoint wiring and startup behavior."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from midi_maker.app.config import ConfigError


class FakeMidiIn:
    """Test-double MIDI input port that records subscription handlers."""

    instances: list["FakeMidiIn"] = []

    def __init__(self, *, name: str) -> None:
        self.name = name
        self.subscriptions: dict[str, object] = {}
        FakeMidiIn.instances.append(self)

    def subscribe(self, midi_type: str, callback: object) -> None:
        self.subscriptions[midi_type] = callback


class FakeTriggerHandler:
    """Records trigger on/off callback invocations."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    def handle_trigger_on(self, msg: object) -> None:
        self.calls.append("on")

    def handle_trigger_off(self, msg: object) -> None:
        self.calls.append("off")


class FakeCCRecorder:
    """Records captured CC events."""

    def __init__(self) -> None:
        self.trigger_handler = FakeTriggerHandler()
        self.capture_calls: list[tuple[int, int, int]] = []

    def capture_cc(self, *, cc_number: int, value: int, channel: int) -> None:
        self.capture_calls.append((cc_number, value, channel))


class FakeSequencerInterface:
    """Records sequencer note on/off events."""

    def __init__(self) -> None:
        self.note_on_channels: list[int] = []
        self.note_off_channels: list[int] = []

    def handle_note_on(self, channel: int) -> None:
        self.note_on_channels.append(channel)

    def handle_note_off(self, channel: int) -> None:
        self.note_off_channels.append(channel)


class FakeRuntime:
    """Runtime test double for subscription callback assertions."""

    def __init__(self) -> None:
        self.engine_running = False
        self.cc_recorder = FakeCCRecorder()
        self.sequencer_interface = FakeSequencerInterface()
        self.config = SimpleNamespace(
            ports=SimpleNamespace(
                trigger_input="trigger",
                cc_source_input="source",
                sequencer_input="sequencer",
            )
        )


def _port_for(name: str) -> FakeMidiIn:
    return next(port for port in FakeMidiIn.instances if port.name == name)


def test_main_requires_config_arg() -> None:
    from midi_maker.app.main import main

    with pytest.raises(SystemExit) as exc_info:
        main([])

    assert exc_info.value.code == 2


def test_main_invokes_start_gui_and_registers_gated_subscriptions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from midi_maker.app import main as main_module

    FakeMidiIn.instances.clear()
    fake_runtime = FakeRuntime()
    fake_config = object()
    called = {"start_gui": False}

    def fake_start_gui() -> None:
        called["start_gui"] = True

    monkeypatch.setattr(main_module, "load_app_config", lambda _path: fake_config)
    monkeypatch.setattr(
        main_module.MidiMakerRuntime,
        "from_config",
        staticmethod(lambda _config: fake_runtime),
    )
    monkeypatch.setattr(main_module.midi_scripter_api, "MidiIn", FakeMidiIn)
    monkeypatch.setattr(
        main_module.midi_scripter_api,
        "MidiType",
        SimpleNamespace(NOTE_ON="NOTE_ON", NOTE_OFF="NOTE_OFF", CONTROL_CHANGE="CONTROL_CHANGE"),
    )
    monkeypatch.setattr(main_module.midi_scripter_api, "start_gui", fake_start_gui)

    exit_code = main_module.main(["--config", "tests/fixtures/config/valid-config.json"])
    assert exit_code == 0
    assert called["start_gui"] is True

    trigger_port = _port_for("trigger")
    source_port = _port_for("source")
    sequencer_port = _port_for("sequencer")

    trigger_on = trigger_port.subscriptions["NOTE_ON"]
    trigger_off = trigger_port.subscriptions["NOTE_OFF"]
    source_cc = source_port.subscriptions["CONTROL_CHANGE"]
    seq_on = sequencer_port.subscriptions["NOTE_ON"]
    seq_off = sequencer_port.subscriptions["NOTE_OFF"]

    msg = SimpleNamespace(control=74, value=90, channel=5)
    trigger_on(msg)
    trigger_off(msg)
    source_cc(msg)
    seq_on(msg)
    seq_off(msg)

    assert fake_runtime.cc_recorder.trigger_handler.calls == []
    assert fake_runtime.cc_recorder.capture_calls == []
    assert fake_runtime.sequencer_interface.note_on_channels == []
    assert fake_runtime.sequencer_interface.note_off_channels == []

    fake_runtime.engine_running = True
    trigger_on(msg)
    trigger_off(msg)
    source_cc(msg)
    seq_on(msg)
    seq_off(msg)

    assert fake_runtime.cc_recorder.trigger_handler.calls == ["on", "off"]
    assert fake_runtime.cc_recorder.capture_calls == [(74, 90, 5)]
    assert fake_runtime.sequencer_interface.note_on_channels == [5]
    assert fake_runtime.sequencer_interface.note_off_channels == [5]


def test_main_surfaces_fail_fast_errors_clearly(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from midi_maker.app import main as main_module

    monkeypatch.setattr(
        main_module,
        "load_app_config",
        lambda _path: (_ for _ in ()).throw(ConfigError("invalid config payload")),
    )

    exit_code = main_module.main(["--config", "broken.json"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "invalid config payload" in captured.err

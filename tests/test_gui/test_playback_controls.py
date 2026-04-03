"""Tests for PlaybackControls GUI widget adapter behavior."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

from midi_maker.gui.playback_controls import PlaybackControls

sys.path.append(str(Path(__file__).parent))
from fakes import FakeButton, FakeButtonSelectorH, FakeSliderH


@dataclass
class PlaybackWidgets:
    tempo: FakeSliderH
    velocity: FakeSliderH
    channel: FakeButtonSelectorH
    pattern: FakeButtonSelectorH
    clear_mapping: FakeButton
    start_engine: FakeButton
    stop_engine: FakeButton


class FakeScheduler:
    def __init__(self) -> None:
        self.tempo_scale: float = 1.0
        self.velocity_scale: float = 1.0
        self.channel_mapping: dict[int, str] = {}

    def set_tempo_scale(self, value: float) -> None:
        self.tempo_scale = value

    def set_velocity_scale(self, value: float) -> None:
        self.velocity_scale = value


class FakeSequencer:
    def __init__(self) -> None:
        self.mapped: list[tuple[int, str]] = []
        self.unmapped: list[int] = []

    def map_pattern_to_channel(self, channel: int, pattern_id: str) -> None:
        self.mapped.append((channel, pattern_id))

    def unmap_channel(self, channel: int) -> None:
        self.unmapped.append(channel)


def make_widgets() -> PlaybackWidgets:
    return PlaybackWidgets(
        tempo=FakeSliderH(1.0),
        velocity=FakeSliderH(1.0),
        channel=FakeButtonSelectorH(options=tuple(str(i) for i in range(1, 17)), selected="1"),
        pattern=FakeButtonSelectorH(options=("pat-a", "pat-b"), selected="pat-a"),
        clear_mapping=FakeButton(),
        start_engine=FakeButton(),
        stop_engine=FakeButton(),
    )


def test_playback_controls_apply_scaling_from_slider_callbacks() -> None:
    scheduler = FakeScheduler()
    controls = PlaybackControls(playback_scheduler=scheduler, widgets=make_widgets())

    controls.tempo_slider.trigger_change(2.5)
    controls.velocity_slider.trigger_change(0.2)

    assert controls.tempo_scale == 2.5
    assert controls.velocity_scale == 0.2
    assert scheduler.tempo_scale == 2.5
    assert scheduler.velocity_scale == 0.2


def test_playback_controls_channel_mapping_conversion() -> None:
    scheduler = FakeScheduler()
    sequencer = FakeSequencer()
    controls = PlaybackControls(
        playback_scheduler=scheduler,
        sequencer_interface=sequencer,
        widgets=make_widgets(),
    )

    controls.set_channel_mapping(ui_channel=2, pattern_id="pat-a")

    assert controls.runtime_mapping[1] == "pat-a"
    assert sequencer.mapped == [(1, "pat-a")]


def test_playback_controls_clear_mapping_surface() -> None:
    scheduler = FakeScheduler()
    sequencer = FakeSequencer()
    widgets = make_widgets()
    controls = PlaybackControls(
        playback_scheduler=scheduler,
        sequencer_interface=sequencer,
        widgets=widgets,
    )
    controls.set_channel_mapping(ui_channel=3, pattern_id="pat-b")

    widgets.channel.set_selected("3")
    widgets.clear_mapping.click()

    assert 2 not in controls.runtime_mapping
    assert sequencer.unmapped == [2]


def test_playback_controls_engine_start_stop_callbacks() -> None:
    scheduler = FakeScheduler()
    widgets = make_widgets()
    calls = {"start": 0, "stop": 0}
    controls = PlaybackControls(
        playback_scheduler=scheduler,
        widgets=widgets,
        on_start_engine=lambda: calls.__setitem__("start", calls["start"] + 1),
        on_stop_engine=lambda: calls.__setitem__("stop", calls["stop"] + 1),
    )

    widgets.start_engine.click()
    widgets.stop_engine.click()

    assert calls == {"start": 1, "stop": 1}

"""Tests for GUI playback control model."""

from typing import Optional

import pytest

from midi_maker.playback.scheduler import PlaybackScheduler

from midi_maker.gui.playback_controls import PlaybackControls


class _SchedulerWithSetters:
    def __init__(self) -> None:
        self.last_tempo_scale: Optional[float] = None
        self.last_velocity_scale: Optional[float] = None

    def set_tempo_scale(self, value: float) -> None:
        self.last_tempo_scale = value

    def set_velocity_scale(self, value: float) -> None:
        self.last_velocity_scale = value


class _SchedulerWithAttributes:
    def __init__(self) -> None:
        self.tempo_scale: Optional[float] = None
        self.velocity_scale: Optional[float] = None


def test_init_sets_defaults() -> None:
    scheduler = object()
    controls = PlaybackControls(playback_scheduler=scheduler)

    assert controls.playback_scheduler is scheduler
    assert controls.tempo_scale == 1.0
    assert controls.velocity_scale == 1.0
    assert isinstance(controls.channel_mapping, dict)
    assert controls.channel_mapping == {}


def test_init_reuses_scheduler_channel_mapping_if_present() -> None:
    scheduler = type("Scheduler", (), {})()
    scheduler.channel_mapping = {1: "kick"}

    controls = PlaybackControls(playback_scheduler=scheduler)

    assert controls.channel_mapping is scheduler.channel_mapping


@pytest.mark.parametrize(
    ("input_value", "expected_value"),
    [
        (0.05, 0.1),
        (1.0, 1.0),
        (8.0, 4.0),
    ],
)
def test_apply_tempo_scaling_clamps_and_stores(
    input_value: float, expected_value: float
) -> None:
    controls = PlaybackControls(playback_scheduler=object())

    controls.apply_tempo_scaling(input_value)

    assert controls.tempo_scale == expected_value


@pytest.mark.parametrize(
    ("input_value", "expected_value"),
    [
        (-0.5, 0.0),
        (1.25, 1.25),
        (8.0, 2.0),
    ],
)
def test_apply_velocity_scaling_clamps_and_stores(
    input_value: float, expected_value: float
) -> None:
    controls = PlaybackControls(playback_scheduler=object())

    controls.apply_velocity_scaling(input_value)

    assert controls.velocity_scale == expected_value


def test_apply_scaling_calls_scheduler_setters_when_available() -> None:
    scheduler = _SchedulerWithSetters()
    controls = PlaybackControls(playback_scheduler=scheduler)

    controls.apply_tempo_scaling(9.0)
    controls.apply_velocity_scaling(-2.0)

    assert scheduler.last_tempo_scale == 4.0
    assert scheduler.last_velocity_scale == 0.0


def test_apply_scaling_updates_scheduler_attributes_when_available() -> None:
    scheduler = _SchedulerWithAttributes()
    controls = PlaybackControls(playback_scheduler=scheduler)

    controls.apply_tempo_scaling(0.25)
    controls.apply_velocity_scaling(1.75)

    assert scheduler.tempo_scale == 0.25
    assert scheduler.velocity_scale == 1.75


def test_apply_scaling_ignores_noncallable_setters_and_uses_attributes() -> None:
    scheduler = _SchedulerWithAttributes()
    scheduler.set_tempo_scale = "not-callable"
    scheduler.set_velocity_scale = "not-callable"
    controls = PlaybackControls(playback_scheduler=scheduler)

    controls.apply_tempo_scaling(3.5)
    controls.apply_velocity_scaling(1.5)

    assert scheduler.tempo_scale == 3.5
    assert scheduler.velocity_scale == 1.5


def test_controls_work_with_existing_playback_scheduler() -> None:
    scheduler = PlaybackScheduler()
    controls = PlaybackControls(playback_scheduler=scheduler)

    controls.apply_tempo_scaling(1.5)
    controls.apply_velocity_scaling(0.8)

    assert controls.tempo_scale == 1.5
    assert controls.velocity_scale == 0.8

"""Playback controls adapter that owns widgets and delegates runtime actions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, MutableMapping, Protocol


class PlaybackSchedulerLike(Protocol):
    """Subset of playback scheduler behavior used by PlaybackControls."""

    channel_mapping: MutableMapping[int, str]

    def set_tempo_scale(self, value: float) -> None:
        """Set tempo scaling."""

    def set_velocity_scale(self, value: float) -> None:
        """Set velocity scaling."""


class SequencerInterfaceLike(Protocol):
    """Subset of sequencer behavior used by PlaybackControls."""

    def map_pattern_to_channel(self, channel: int, pattern_id: str) -> None:
        """Map channel to pattern."""

    def unmap_channel(self, channel: int) -> None:
        """Clear mapping for channel."""


class ValueWidgetLike(Protocol):
    """Numeric value widget protocol."""

    value: float

    def set_value(self, value: float) -> None:
        """Set numeric value."""

    def set_on_change(self, callback: Callable[[float], None]) -> None:
        """Register change callback."""


class SelectorWidgetLike(Protocol):
    """Simple selector widget protocol."""

    selected: str | None

    def set_selected(self, value: str) -> None:
        """Set selected string."""

    def set_on_change(self, callback: Callable[[str], None]) -> None:
        """Register selection callback."""


class ButtonWidgetLike(Protocol):
    """Button widget protocol."""

    def set_on_click(self, callback: Callable[[], object]) -> None:
        """Register click callback."""


@dataclass(frozen=True)
class PlaybackControlsWidgets:
    """Injected widget facades for playback controls."""

    tempo: ValueWidgetLike
    velocity: ValueWidgetLike
    channel: SelectorWidgetLike
    pattern: SelectorWidgetLike
    clear_mapping: ButtonWidgetLike
    start_engine: ButtonWidgetLike
    stop_engine: ButtonWidgetLike


class PlaybackControls:
    """Widget-owner adapter for playback and mapping controls."""

    MIN_TEMPO_SCALE = 0.1
    MAX_TEMPO_SCALE = 4.0
    MIN_VELOCITY_SCALE = 0.0
    MAX_VELOCITY_SCALE = 2.0

    def __init__(
        self,
        *,
        playback_scheduler: PlaybackSchedulerLike,
        widgets: PlaybackControlsWidgets,
        sequencer_interface: SequencerInterfaceLike | None = None,
        on_start_engine: Callable[[], object] | None = None,
        on_stop_engine: Callable[[], object] | None = None,
    ) -> None:
        self.playback_scheduler = playback_scheduler
        self.sequencer_interface = sequencer_interface
        self._on_start_engine = on_start_engine
        self._on_stop_engine = on_stop_engine

        scheduler_mapping = getattr(playback_scheduler, "channel_mapping", None)
        if isinstance(scheduler_mapping, MutableMapping):
            self.runtime_mapping = scheduler_mapping
        else:
            self.runtime_mapping = {}

        self.tempo_slider = widgets.tempo
        self.velocity_slider = widgets.velocity
        self.channel_selector = widgets.channel
        self.pattern_selector = widgets.pattern
        self.clear_mapping_button = widgets.clear_mapping
        self.start_engine_button = widgets.start_engine
        self.stop_engine_button = widgets.stop_engine

        self.tempo_scale = 1.0
        self.velocity_scale = 1.0

        self.tempo_slider.set_value(self.tempo_scale)
        self.velocity_slider.set_value(self.velocity_scale)

        self.tempo_slider.set_on_change(self.apply_tempo_scaling)
        self.velocity_slider.set_on_change(self.apply_velocity_scaling)
        self.clear_mapping_button.set_on_click(self.clear_selected_channel_mapping)
        self.start_engine_button.set_on_click(self.start_engine)
        self.stop_engine_button.set_on_click(self.stop_engine)

        self.channel_selector.set_on_change(self._on_mapping_selection_changed)
        self.pattern_selector.set_on_change(self._on_mapping_selection_changed)

    def apply_tempo_scaling(self, scale_factor: float) -> None:
        """Clamp and delegate tempo scale changes."""
        clamped = self._clamp(scale_factor, self.MIN_TEMPO_SCALE, self.MAX_TEMPO_SCALE)
        self.tempo_scale = clamped
        self.tempo_slider.set_value(clamped)
        self._set_scheduler_value("set_tempo_scale", "tempo_scale", clamped)

    def apply_velocity_scaling(self, scale_factor: float) -> None:
        """Clamp and delegate velocity scale changes."""
        clamped = self._clamp(scale_factor, self.MIN_VELOCITY_SCALE, self.MAX_VELOCITY_SCALE)
        self.velocity_scale = clamped
        self.velocity_slider.set_value(clamped)
        self._set_scheduler_value("set_velocity_scale", "velocity_scale", clamped)

    def set_channel_mapping(self, *, ui_channel: int, pattern_id: str) -> None:
        """Map UI channel (1..16) onto runtime channel (0..15)."""
        runtime_channel = self._to_runtime_channel(ui_channel)
        self.runtime_mapping[runtime_channel] = pattern_id
        if self.sequencer_interface is not None:
            self.sequencer_interface.map_pattern_to_channel(runtime_channel, pattern_id)

    def clear_channel_mapping(self, *, ui_channel: int) -> None:
        """Clear mapping for UI channel and delegate to sequencer."""
        runtime_channel = self._to_runtime_channel(ui_channel)
        self.runtime_mapping.pop(runtime_channel, None)
        if self.sequencer_interface is not None:
            self.sequencer_interface.unmap_channel(runtime_channel)

    def clear_selected_channel_mapping(self) -> None:
        selected = self.channel_selector.selected
        if selected is None:
            return
        self.clear_channel_mapping(ui_channel=int(selected))

    def start_engine(self) -> object | None:
        if self._on_start_engine is None:
            return None
        return self._on_start_engine()

    def stop_engine(self) -> object | None:
        if self._on_stop_engine is None:
            return None
        return self._on_stop_engine()

    def _on_mapping_selection_changed(self, _value: str) -> None:
        selected_channel = self.channel_selector.selected
        selected_pattern = self.pattern_selector.selected
        if selected_channel is None or selected_pattern is None:
            return
        self.set_channel_mapping(ui_channel=int(selected_channel), pattern_id=selected_pattern)

    def _set_scheduler_value(self, setter_name: str, attribute_name: str, value: float) -> None:
        setter = getattr(self.playback_scheduler, setter_name, None)
        if callable(setter):
            setter(value)
            return
        if hasattr(self.playback_scheduler, attribute_name):
            setattr(self.playback_scheduler, attribute_name, value)

    @staticmethod
    def _to_runtime_channel(ui_channel: int) -> int:
        if not 1 <= ui_channel <= 16:
            raise ValueError("UI channel must be 1-16")
        return ui_channel - 1

    @staticmethod
    def _clamp(value: float, minimum: float, maximum: float) -> float:
        return max(minimum, min(maximum, value))


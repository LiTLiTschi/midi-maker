"""Dependency-free GUI playback control model."""

from typing import Any, MutableMapping


class PlaybackControls:
    """State holder for real-time playback adjustments."""

    MIN_TEMPO_SCALE = 0.1
    MAX_TEMPO_SCALE = 4.0
    MIN_VELOCITY_SCALE = 0.0
    MAX_VELOCITY_SCALE = 2.0

    def __init__(self, playback_scheduler: Any) -> None:
        self.playback_scheduler = playback_scheduler
        self.tempo_scale = 1.0
        self.velocity_scale = 1.0

        scheduler_mapping = getattr(playback_scheduler, "channel_mapping", None)
        if isinstance(scheduler_mapping, MutableMapping):
            self.channel_mapping = scheduler_mapping
        else:
            self.channel_mapping = {}

    def apply_tempo_scaling(self, scale_factor: float) -> None:
        """Clamp and store tempo scaling."""
        clamped = self._clamp(
            scale_factor, self.MIN_TEMPO_SCALE, self.MAX_TEMPO_SCALE
        )
        self.tempo_scale = clamped

        setter = getattr(self.playback_scheduler, "set_tempo_scale", None)
        if callable(setter):
            setter(clamped)
            return
        if hasattr(self.playback_scheduler, "tempo_scale"):
            setattr(self.playback_scheduler, "tempo_scale", clamped)

    def apply_velocity_scaling(self, scale_factor: float) -> None:
        """Clamp and store velocity scaling."""
        clamped = self._clamp(
            scale_factor, self.MIN_VELOCITY_SCALE, self.MAX_VELOCITY_SCALE
        )
        self.velocity_scale = clamped

        setter = getattr(self.playback_scheduler, "set_velocity_scale", None)
        if callable(setter):
            setter(clamped)
            return
        if hasattr(self.playback_scheduler, "velocity_scale"):
            setattr(self.playback_scheduler, "velocity_scale", clamped)

    @staticmethod
    def _clamp(value: float, minimum: float, maximum: float) -> float:
        return max(minimum, min(maximum, value))

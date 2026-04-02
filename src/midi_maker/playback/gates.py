"""Sequencer gate processing for attack/decay playback."""

from typing import Dict, Optional, Protocol

from midi_maker.automation import AutomationPattern
from midi_maker.core import CCEvent, PlaybackMode
from midi_maker.patterns.state import GateStateMachine, GateTransition


class PatternProvider(Protocol):
    """Protocol for looking up automation patterns by ID."""

    def get_pattern(self, pattern_id: str) -> AutomationPattern:
        """Return the pattern associated with pattern_id."""
        ...


class AttackDecayPlayer(Protocol):
    """Protocol for direct attack/decay playback."""

    def play_attack_phase(self, attack_events: list[CCEvent]) -> None:
        """Play pattern attack events."""
        ...

    def play_decay_phase(self, decay_events: list[CCEvent]) -> None:
        """Play pattern decay events."""
        ...


class AttackDecayScheduler(Protocol):
    """Protocol for scheduled attack/decay playback."""

    def start_pattern_playback(
        self, pattern: AutomationPattern, playback_mode: PlaybackMode
    ) -> str:
        """Start playback of a pattern in a specific mode."""
        ...


class GateProcessor:
    """Handle sequencer gate transitions and trigger pattern attack/decay playback."""

    def __init__(
        self,
        sequencer_port: object | None = None,
        *,
        player: AttackDecayPlayer | None = None,
        scheduler: AttackDecayScheduler | None = None,
        pattern_library: PatternProvider | None = None,
    ) -> None:
        """Initialize GateProcessor.

        Args:
            sequencer_port: Optional sequencer input port reference.
            player: Optional direct player dependency.
            scheduler: Optional scheduler dependency.
            pattern_library: Optional provider used to resolve pattern IDs.
        """
        self.sequencer_port = sequencer_port
        self.player = player
        self.scheduler = scheduler
        self.pattern_library = pattern_library
        self.gate_state_machine = GateStateMachine()
        self._channel_pattern_map: Dict[int, str] = {}

    def set_pattern_for_channel(self, channel: int, pattern_id: str) -> None:
        """Map a sequencer channel to an automation pattern ID."""
        self._channel_pattern_map[channel] = pattern_id

    def handle_gate_on(self, channel: int) -> Optional[str]:
        """Process gate-on and trigger attack playback when applicable."""
        transition = self.gate_state_machine.update_gate_state(
            channel=channel, gate_on=True
        )
        if transition != GateTransition.OPENED:
            return None
        return self._trigger_phase(channel=channel, mode=PlaybackMode.ATTACK_ONLY)

    def handle_gate_off(self, channel: int) -> Optional[str]:
        """Process gate-off and trigger decay playback when applicable."""
        transition = self.gate_state_machine.update_gate_state(
            channel=channel, gate_on=False
        )
        if transition != GateTransition.CLOSED:
            return None
        return self._trigger_phase(channel=channel, mode=PlaybackMode.DECAY_ONLY)

    def _trigger_phase(self, channel: int, mode: PlaybackMode) -> Optional[str]:
        """Resolve mapped pattern and trigger the requested playback phase."""
        pattern_id = self._channel_pattern_map.get(channel)
        if pattern_id is None:
            return None

        pattern = self._resolve_pattern(pattern_id)
        if pattern is None:
            return None

        if self.scheduler is not None:
            self.scheduler.start_pattern_playback(pattern, mode)
            return pattern_id

        if self.player is not None:
            if mode == PlaybackMode.ATTACK_ONLY:
                self.player.play_attack_phase(pattern.attack_events)
            elif mode == PlaybackMode.DECAY_ONLY:
                self.player.play_decay_phase(pattern.decay_events)
            return pattern_id

        return pattern_id

    def _resolve_pattern(self, pattern_id: str) -> Optional[AutomationPattern]:
        """Resolve a mapped pattern ID to an AutomationPattern instance."""
        if self.pattern_library is None:
            return None
        try:
            return self.pattern_library.get_pattern(pattern_id)
        except KeyError:
            return None

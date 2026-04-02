"""Sequencer interface for channel-to-pattern gate control."""

from __future__ import annotations

from midi_maker.core import GateState
from midi_maker.patterns.state import GateStateMachine
from midi_maker.playback.gates import GateProcessor


class SequencerInterface:
    """Coordinate sequencer note gates with mapped automation patterns."""

    def __init__(
        self,
        sequencer_port=None,
        channel_mapping: dict[int, str] | None = None,
        gate_processor=None,
    ) -> None:
        self.sequencer_port = sequencer_port
        self.channel_mapping: dict[int, str] = dict(channel_mapping or {})
        self.gate_processor = (
            gate_processor
            if gate_processor is not None
            else GateProcessor(sequencer_port=sequencer_port)
        )
        self._gate_state_machine = GateStateMachine()
        self._tracked_channels: set[int] = set()
        self._sync_mapping_to_gate_processor()

    def map_pattern_to_channel(self, channel: int, pattern_id: str) -> None:
        """Map a sequencer channel to a pattern identifier."""
        self.channel_mapping[channel] = pattern_id
        self._set_processor_mapping(channel=channel, pattern_id=pattern_id)

    def unmap_channel(self, channel: int) -> None:
        """Remove a channel-to-pattern mapping from the sequencer interface."""
        self.channel_mapping.pop(channel, None)
        channel_map = getattr(self.gate_processor, "_channel_pattern_map", None)
        if isinstance(channel_map, dict):
            channel_map.pop(channel, None)

    def get_active_channels(self) -> set[int]:
        """Return channels whose gate state is currently open."""
        return {
            channel
            for channel in self._tracked_channels
            if self._gate_state_machine.get_current_state(channel) == GateState.OPEN
        }

    def handle_note_on(self, channel: int) -> None:
        """Handle note-on by updating state and delegating to gate processor."""
        self._tracked_channels.add(channel)
        self._gate_state_machine.update_gate_state(channel=channel, gate_on=True)
        self.gate_processor.handle_gate_on(channel)

    def handle_note_off(self, channel: int) -> None:
        """Handle note-off by updating state and delegating to gate processor."""
        self._tracked_channels.add(channel)
        self._gate_state_machine.update_gate_state(channel=channel, gate_on=False)
        self.gate_processor.handle_gate_off(channel)

    def _sync_mapping_to_gate_processor(self) -> None:
        for channel, pattern_id in self.channel_mapping.items():
            self._set_processor_mapping(channel=channel, pattern_id=pattern_id)

    def _set_processor_mapping(self, channel: int, pattern_id: str) -> None:
        self.gate_processor.set_pattern_for_channel(channel=channel, pattern_id=pattern_id)

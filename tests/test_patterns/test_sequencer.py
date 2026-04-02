"""Tests for SequencerInterface pattern integration."""

from midi_maker.core import GateState
from midi_maker.patterns import SequencerInterface


class SpyGateProcessor:
    """Minimal GateProcessor test double for delegation checks."""

    def __init__(self) -> None:
        self._channel_pattern_map: dict[int, str] = {}
        self.note_on_calls: list[int] = []
        self.note_off_calls: list[int] = []

    def set_pattern_for_channel(self, channel: int, pattern_id: str) -> None:
        self._channel_pattern_map[channel] = pattern_id

    def handle_gate_on(self, channel: int) -> None:
        self.note_on_calls.append(channel)

    def handle_gate_off(self, channel: int) -> None:
        self.note_off_calls.append(channel)


class TestSequencerInterface:
    """Tests for SequencerInterface behavior."""

    def test_init_syncs_initial_mapping_into_gate_processor(self) -> None:
        mapping = {1: "pattern-a", 2: "pattern-b"}

        sequencer = SequencerInterface(channel_mapping=mapping)

        assert sequencer.channel_mapping == mapping
        assert sequencer.gate_processor._channel_pattern_map == mapping

    def test_init_passes_sequencer_port_to_default_gate_processor(self) -> None:
        sequencer_port = object()

        sequencer = SequencerInterface(sequencer_port=sequencer_port)

        assert sequencer.sequencer_port is sequencer_port
        assert sequencer.gate_processor.sequencer_port is sequencer_port

    def test_map_pattern_to_channel_updates_local_and_gate_processor_maps(self) -> None:
        sequencer = SequencerInterface()

        sequencer.map_pattern_to_channel(channel=3, pattern_id="pattern-c")

        assert sequencer.channel_mapping[3] == "pattern-c"
        assert sequencer.gate_processor._channel_pattern_map[3] == "pattern-c"

    def test_unmap_channel_removes_channel_from_local_and_gate_processor_maps(self) -> None:
        sequencer = SequencerInterface(channel_mapping={4: "pattern-d"})

        sequencer.unmap_channel(channel=4)

        assert 4 not in sequencer.channel_mapping
        assert 4 not in sequencer.gate_processor._channel_pattern_map

    def test_handle_note_on_and_off_delegate_to_gate_processor(self) -> None:
        gate_processor = SpyGateProcessor()
        sequencer = SequencerInterface(gate_processor=gate_processor)

        sequencer.handle_note_on(channel=8)
        sequencer.handle_note_off(channel=8)

        assert gate_processor.note_on_calls == [8]
        assert gate_processor.note_off_calls == [8]

    def test_get_active_channels_returns_open_channels(self) -> None:
        sequencer = SequencerInterface()

        sequencer.handle_note_on(channel=1)
        sequencer.handle_note_on(channel=2)
        sequencer.handle_note_off(channel=2)

        assert sequencer.get_active_channels() == {1}

    def test_get_active_channels_tracks_overlapping_gates(self) -> None:
        sequencer = SequencerInterface()

        sequencer.handle_note_on(channel=5)
        sequencer.handle_note_on(channel=5)
        sequencer.handle_note_off(channel=5)

        assert sequencer.get_active_channels() == {5}

        sequencer.handle_note_off(channel=5)

        assert sequencer.get_active_channels() == set()

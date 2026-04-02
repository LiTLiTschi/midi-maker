"""Tests for GateProcessor sequencer gate handling."""

from typing import Dict, List

from midi_maker.automation import AutomationPattern
from midi_maker.core import CCEvent, GateState, PlaybackMode
from midi_maker.playback.gates import GateProcessor


class SpyPlayer:
    """Test double that records attack and decay playback calls."""

    def __init__(self) -> None:
        self.attack_calls: List[List[CCEvent]] = []
        self.decay_calls: List[List[CCEvent]] = []

    def play_attack_phase(self, attack_events: List[CCEvent]) -> None:
        self.attack_calls.append(attack_events)

    def play_decay_phase(self, decay_events: List[CCEvent]) -> None:
        self.decay_calls.append(decay_events)


class SpyScheduler:
    """Test double that records scheduler playback requests."""

    def __init__(self) -> None:
        self.calls: List[tuple[AutomationPattern, PlaybackMode]] = []

    def start_pattern_playback(
        self, pattern: AutomationPattern, playback_mode: PlaybackMode
    ) -> str:
        self.calls.append((pattern, playback_mode))
        return "playback-id"


class FakePatternLibrary:
    """Simple in-memory pattern provider for tests."""

    def __init__(self, patterns: Dict[str, AutomationPattern]) -> None:
        self._patterns = patterns

    def get_pattern(self, pattern_id: str) -> AutomationPattern:
        return self._patterns[pattern_id]


def make_pattern(pattern_id: str = "pattern-a") -> AutomationPattern:
    """Create a test pattern with explicit attack and decay events."""
    events = [
        CCEvent(cc_number=74, value=10, channel=0, timestamp=0.0),
        CCEvent(cc_number=74, value=100, channel=0, timestamp=0.01),
        CCEvent(cc_number=74, value=20, channel=0, timestamp=0.02),
    ]
    return AutomationPattern(
        pattern_id=pattern_id,
        name="Test Pattern",
        cc_events=events,
        duration=0.02,
        attack_events=events[:2],
        decay_events=events[2:],
    )


class TestGateProcessorMapping:
    """Tests for channel to pattern mapping behavior."""

    def test_set_pattern_for_channel_maps_channel(self) -> None:
        pattern = make_pattern()
        player = SpyPlayer()
        library = FakePatternLibrary({pattern.pattern_id: pattern})
        processor = GateProcessor(player=player, pattern_library=library)

        processor.set_pattern_for_channel(channel=2, pattern_id=pattern.pattern_id)
        result = processor.handle_gate_on(channel=2)

        assert result == pattern.pattern_id
        assert player.attack_calls == [pattern.attack_events]


class TestGateProcessorGateHandling:
    """Tests for gate on/off playback behavior."""

    def test_handle_gate_on_triggers_attack_playback(self) -> None:
        pattern = make_pattern()
        player = SpyPlayer()
        library = FakePatternLibrary({pattern.pattern_id: pattern})
        processor = GateProcessor(player=player, pattern_library=library)
        processor.set_pattern_for_channel(channel=1, pattern_id=pattern.pattern_id)

        result = processor.handle_gate_on(channel=1)

        assert result == pattern.pattern_id
        assert player.attack_calls == [pattern.attack_events]
        assert player.decay_calls == []
        assert processor.gate_state_machine.get_current_state(1) == GateState.OPEN

    def test_handle_gate_off_triggers_decay_playback(self) -> None:
        pattern = make_pattern()
        player = SpyPlayer()
        library = FakePatternLibrary({pattern.pattern_id: pattern})
        processor = GateProcessor(player=player, pattern_library=library)
        processor.set_pattern_for_channel(channel=1, pattern_id=pattern.pattern_id)
        processor.handle_gate_on(channel=1)

        result = processor.handle_gate_off(channel=1)

        assert result == pattern.pattern_id
        assert player.attack_calls == [pattern.attack_events]
        assert player.decay_calls == [pattern.decay_events]
        assert processor.gate_state_machine.get_current_state(1) == GateState.CLOSED

    def test_unmapped_channel_returns_none_but_updates_state(self) -> None:
        processor = GateProcessor()

        gate_on_result = processor.handle_gate_on(channel=9)
        gate_off_result = processor.handle_gate_off(channel=9)

        assert gate_on_result is None
        assert gate_off_result is None
        assert processor.gate_state_machine.get_current_state(9) == GateState.CLOSED

    def test_overlapping_gate_transitions_only_trigger_on_state_changes(self) -> None:
        pattern = make_pattern()
        player = SpyPlayer()
        library = FakePatternLibrary({pattern.pattern_id: pattern})
        processor = GateProcessor(player=player, pattern_library=library)
        processor.set_pattern_for_channel(channel=4, pattern_id=pattern.pattern_id)

        first_on = processor.handle_gate_on(channel=4)
        second_on = processor.handle_gate_on(channel=4)
        first_off = processor.handle_gate_off(channel=4)
        second_off = processor.handle_gate_off(channel=4)

        assert first_on == pattern.pattern_id
        assert second_on is None
        assert first_off is None
        assert second_off == pattern.pattern_id
        assert player.attack_calls == [pattern.attack_events]
        assert player.decay_calls == [pattern.decay_events]

    def test_scheduler_dependency_is_supported(self) -> None:
        pattern = make_pattern()
        scheduler = SpyScheduler()
        library = FakePatternLibrary({pattern.pattern_id: pattern})
        processor = GateProcessor(scheduler=scheduler, pattern_library=library)
        processor.set_pattern_for_channel(channel=3, pattern_id=pattern.pattern_id)

        on_result = processor.handle_gate_on(channel=3)
        off_result = processor.handle_gate_off(channel=3)

        assert on_result == pattern.pattern_id
        assert off_result == pattern.pattern_id
        assert scheduler.calls == [
            (pattern, PlaybackMode.ATTACK_ONLY),
            (pattern, PlaybackMode.DECAY_ONLY),
        ]

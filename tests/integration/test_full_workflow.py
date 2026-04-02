"""Integration test for full recording → playback workflow."""

from __future__ import annotations

import pytest

from midi_maker.automation import AutomationPattern, PatternLibrary
from midi_maker.core import RecordingMode, RecordingState
from midi_maker.playback import AutomationPlayer
from midi_maker.recording import CCRecorder


def test_full_recording_to_playback_workflow(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Record deterministic CC events, persist them, then play them back."""
    perf_counter_values = iter([100.0, 100.0, 100.01, 100.03, 100.05])
    monkeypatch.setattr(
        "midi_maker.recording.capture.time.perf_counter",
        lambda: next(perf_counter_values),
    )

    recorder = CCRecorder()
    recorder.set_recording_mode(RecordingMode.HOLD)

    assert recorder.get_state() == RecordingState.IDLE

    recorder.trigger_handler.handle_trigger_on()
    assert recorder.is_recording is True
    assert recorder.get_state() == RecordingState.RECORDING

    recorded_values = [10, 64, 127, 45]
    for value in recorded_values:
        recorder.capture_cc(cc_number=74, value=value, channel=2)

    recorder.trigger_handler.handle_trigger_off()
    assert recorder.is_recording is False
    assert recorder.get_state() == RecordingState.STOPPED

    captured_events = recorder.get_events()
    assert len(captured_events) == 4
    assert [event.value for event in captured_events] == recorded_values
    assert [event.timestamp for event in captured_events] == pytest.approx(
        [0.0, 0.01, 0.03, 0.05]
    )

    pattern = AutomationPattern(
        pattern_id="integration-pattern",
        name="Integration Pattern",
        cc_events=captured_events,
        duration=captured_events[-1].timestamp,
    )
    pattern.analyze_attack_decay()

    library_path = tmp_path / "patterns.json"
    library = PatternLibrary(str(library_path))
    library.add_pattern(pattern)
    library.save_library()

    reloaded_library = PatternLibrary(str(library_path))
    reloaded_library.load_library()
    loaded_pattern = reloaded_library.get_pattern("integration-pattern")

    assert len(loaded_pattern.cc_events) == 4
    assert loaded_pattern.cc_events[0].value == 10
    assert loaded_pattern.cc_events[-1].value == 45
    assert len(loaded_pattern.attack_events) == 3
    assert len(loaded_pattern.decay_events) == 1
    assert loaded_pattern.duration == pytest.approx(0.05)

    sleep_calls: list[float] = []
    played_events: list[tuple[int, int, int]] = []
    monkeypatch.setattr(
        "midi_maker.playback.player.time.sleep",
        lambda delay: sleep_calls.append(delay),
    )

    player = AutomationPlayer()
    player.set_cc_output_callback(
        lambda cc_number, value, channel: played_events.append((cc_number, value, channel))
    )
    player.play_full_sequence(loaded_pattern)

    assert played_events == [
        (74, 10, 2),
        (74, 64, 2),
        (74, 127, 2),
        (74, 45, 2),
    ]
    assert len(played_events) == len(recorded_values)
    assert sleep_calls == pytest.approx([0.01, 0.02, 0.02])

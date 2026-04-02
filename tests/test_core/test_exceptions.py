"""Tests for custom exceptions."""

import pytest

from midi_maker.core.exceptions import (
    MidiMakerError,
    PatternError,
    PlaybackError,
    RecordingError,
)


class TestExceptionHierarchy:
    """Test exception inheritance hierarchy."""

    def test_recording_error_is_midi_maker_error(self):
        assert issubclass(RecordingError, MidiMakerError)

    def test_playback_error_is_midi_maker_error(self):
        assert issubclass(PlaybackError, MidiMakerError)

    def test_pattern_error_is_midi_maker_error(self):
        assert issubclass(PatternError, MidiMakerError)

    def test_midi_maker_error_is_exception(self):
        assert issubclass(MidiMakerError, Exception)


class TestExceptionRaising:
    """Test that exceptions can be raised and caught."""

    def test_raise_midi_maker_error(self):
        with pytest.raises(MidiMakerError):
            raise MidiMakerError("base error")

    def test_raise_recording_error(self):
        with pytest.raises(RecordingError):
            raise RecordingError("recording failed")

    def test_raise_playback_error(self):
        with pytest.raises(PlaybackError):
            raise PlaybackError("playback failed")

    def test_raise_pattern_error(self):
        with pytest.raises(PatternError):
            raise PatternError("pattern invalid")

    def test_catch_subclass_as_base(self):
        """Catching MidiMakerError should catch subclasses."""
        with pytest.raises(MidiMakerError):
            raise RecordingError("should be caught as base")

    def test_exception_message(self):
        error = RecordingError("test message")
        assert str(error) == "test message"

    def test_exception_without_message(self):
        error = PlaybackError()
        assert str(error) == ""

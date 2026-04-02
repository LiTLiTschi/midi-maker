"""Custom exceptions for MIDI Maker."""


class MidiMakerError(Exception):
    """Base exception for all MIDI Maker errors."""

    pass


class RecordingError(MidiMakerError):
    """Errors during recording operations."""

    pass


class PlaybackError(MidiMakerError):
    """Errors during playback operations."""

    pass


class PatternError(MidiMakerError):
    """Errors with patterns or library operations."""

    pass

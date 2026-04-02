"""MIDI Maker - A Python tool for creating and manipulating MIDI files."""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .core.midi_file import MidiFile
from .core.track import Track
from .core.note import Note

__all__ = ["MidiFile", "Track", "Note"]
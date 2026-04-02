"""Core event dataclasses for MIDI Maker.

This module defines the fundamental event types used for capturing
and representing MIDI CC automation data.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class CCEvent:
    """A single MIDI CC event captured during recording.
    
    Represents a Control Change message with timing information
    relative to the start of recording.
    
    Attributes:
        cc_number: MIDI CC number (0-127)
        value: CC value (0-127)
        channel: MIDI channel (0-15)
        timestamp: Time in seconds relative to recording start
    """
    
    cc_number: int
    value: int
    channel: int
    timestamp: float
    
    def __post_init__(self) -> None:
        """Validate MIDI CC event parameters."""
        if not 0 <= self.cc_number <= 127:
            raise ValueError(f"cc_number must be 0-127, got {self.cc_number}")
        if not 0 <= self.value <= 127:
            raise ValueError(f"value must be 0-127, got {self.value}")
        if not 0 <= self.channel <= 15:
            raise ValueError(f"channel must be 0-15, got {self.channel}")
        if self.timestamp < 0:
            raise ValueError(f"timestamp must be >= 0, got {self.timestamp}")

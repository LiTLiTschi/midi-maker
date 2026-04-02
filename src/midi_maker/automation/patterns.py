"""Automation pattern storage and serialization.

This module defines the AutomationPattern dataclass for storing complete
CC sequences with metadata and attack/decay analysis.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List

from midi_maker.core import CCEvent


@dataclass
class AutomationPattern:
    """A complete CC automation sequence with metadata.

    Stores CC events captured during recording along with analysis
    of attack/decay phases for intelligent playback.

    Attributes:
        pattern_id: Unique identifier for the pattern
        name: Human-readable pattern name
        cc_events: Complete list of captured CC events
        duration: Total duration of the pattern in seconds
        attack_events: Events from start until peak (populated by analyze_attack_decay)
        decay_events: Events from peak to end (populated by analyze_attack_decay)
        metadata: Additional pattern metadata (e.g., source CC, creation time)
    """

    pattern_id: str
    name: str
    cc_events: List[CCEvent]
    duration: float
    attack_events: List[CCEvent] = field(default_factory=list)
    decay_events: List[CCEvent] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate pattern parameters."""
        if not self.pattern_id:
            raise ValueError("pattern_id cannot be empty")
        if not self.name:
            raise ValueError("name cannot be empty")
        if self.duration < 0:
            raise ValueError(f"duration must be >= 0, got {self.duration}")

    def analyze_attack_decay(self) -> None:
        """Split cc_events into attack and decay phases.

        Finds the peak value in the CC events and splits the sequence
        at that point. The attack phase includes events up to and including
        the peak; the decay phase includes events after the peak.

        If no events exist, both phases remain empty.
        If multiple events share the peak value, uses the first occurrence.
        """
        if not self.cc_events:
            self.attack_events = []
            self.decay_events = []
            return

        # Find the index of the peak value (first occurrence)
        peak_index = 0
        peak_value = self.cc_events[0].value
        for i, event in enumerate(self.cc_events):
            if event.value > peak_value:
                peak_value = event.value
                peak_index = i

        # Split at peak: attack includes peak, decay is everything after
        self.attack_events = list(self.cc_events[: peak_index + 1])
        self.decay_events = list(self.cc_events[peak_index + 1 :])

    def to_dict(self) -> Dict[str, Any]:
        """Serialize pattern to dictionary for JSON storage.

        Returns:
            Dictionary representation of the pattern suitable for JSON serialization.
        """
        return {
            "pattern_id": self.pattern_id,
            "name": self.name,
            "cc_events": [
                {
                    "cc_number": e.cc_number,
                    "value": e.value,
                    "channel": e.channel,
                    "timestamp": e.timestamp,
                }
                for e in self.cc_events
            ],
            "duration": self.duration,
            "attack_events": [
                {
                    "cc_number": e.cc_number,
                    "value": e.value,
                    "channel": e.channel,
                    "timestamp": e.timestamp,
                }
                for e in self.attack_events
            ],
            "decay_events": [
                {
                    "cc_number": e.cc_number,
                    "value": e.value,
                    "channel": e.channel,
                    "timestamp": e.timestamp,
                }
                for e in self.decay_events
            ],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AutomationPattern":
        """Deserialize pattern from dictionary.

        Args:
            data: Dictionary representation of the pattern (from to_dict or JSON).

        Returns:
            Reconstructed AutomationPattern instance.

        Raises:
            KeyError: If required fields are missing from the data.
            ValueError: If CCEvent validation fails.
        """
        cc_events = [
            CCEvent(
                cc_number=e["cc_number"],
                value=e["value"],
                channel=e["channel"],
                timestamp=e["timestamp"],
            )
            for e in data["cc_events"]
        ]

        attack_events = [
            CCEvent(
                cc_number=e["cc_number"],
                value=e["value"],
                channel=e["channel"],
                timestamp=e["timestamp"],
            )
            for e in data.get("attack_events", [])
        ]

        decay_events = [
            CCEvent(
                cc_number=e["cc_number"],
                value=e["value"],
                channel=e["channel"],
                timestamp=e["timestamp"],
            )
            for e in data.get("decay_events", [])
        ]

        return cls(
            pattern_id=data["pattern_id"],
            name=data["name"],
            cc_events=cc_events,
            duration=data["duration"],
            attack_events=attack_events,
            decay_events=decay_events,
            metadata=data.get("metadata", {}),
        )

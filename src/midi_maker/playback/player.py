"""Core playback logic for CC automation sequences.

This module provides the AutomationPlayer class for playing back CC sequences
with support for full playback, attack/decay phases, and snapshot output.
"""

import time
from typing import Callable, Dict, List, Optional, Protocol

from midi_maker.automation import AutomationPattern
from midi_maker.core import CCEvent


class MidiOutputPort(Protocol):
    """Protocol for MIDI output ports.

    This protocol defines the minimal interface needed for MIDI output,
    allowing compatibility with various MIDI libraries without hard dependencies.
    """

    def send_cc(self, cc_number: int, value: int, channel: int) -> None:
        """Send a MIDI Control Change message.

        Args:
            cc_number: MIDI CC number (0-127)
            value: CC value (0-127)
            channel: MIDI channel (0-15)
        """
        ...


# Type alias for CC output callback
CCOutputCallback = Callable[[int, int, int], None]


class AutomationPlayer:
    """Core playback logic for CC automation sequences.

    AutomationPlayer handles timed playback of CC events with support for:
    - Full sequence playback with original timing
    - Attack-only playback
    - Decay-only playback
    - Instantaneous CC snapshots

    The player can output to a MIDI port (implementing MidiOutputPort protocol)
    or via a callback function, making it suitable for both live use and testing.

    Attributes:
        output_port: Optional MIDI output port for sending CC messages.
    """

    def __init__(self, output_port: Optional[MidiOutputPort] = None) -> None:
        """Initialize the AutomationPlayer.

        Args:
            output_port: Optional MIDI output port. If None, only callback
                output is available.
        """
        self.output_port = output_port
        self._cc_output_callback: Optional[CCOutputCallback] = None

    def set_cc_output_callback(self, callback: Optional[CCOutputCallback]) -> None:
        """Set a callback for CC output.

        The callback is called with (cc_number, value, channel) for each
        CC message sent. This is useful for testing or for routing CC
        output to alternative destinations.

        Args:
            callback: Function to call with CC values, or None to disable.
        """
        self._cc_output_callback = callback

    def _send_cc(self, cc_number: int, value: int, channel: int) -> None:
        """Internal method to send a CC message.

        Sends to both the output port (if configured) and the callback
        (if configured).

        Args:
            cc_number: MIDI CC number (0-127)
            value: CC value (0-127)
            channel: MIDI channel (0-15)
        """
        if self.output_port is not None:
            self.output_port.send_cc(cc_number, value, channel)

        if self._cc_output_callback is not None:
            self._cc_output_callback(cc_number, value, channel)

    def _play_events(self, events: List[CCEvent]) -> None:
        """Play a list of CC events with their timing.

        Events are played with delays between them based on their timestamps.
        The first event plays immediately, subsequent events are delayed
        relative to the previous event's timestamp.

        Args:
            events: List of CCEvent objects to play in order.
        """
        if not events:
            return

        last_timestamp = 0.0

        for event in events:
            delay = event.timestamp - last_timestamp
            if delay > 0:
                time.sleep(delay)

            self._send_cc(event.cc_number, event.value, event.channel)
            last_timestamp = event.timestamp

    def play_full_sequence(self, pattern: AutomationPattern) -> None:
        """Play a complete automation pattern with original timing.

        Plays all CC events in the pattern, preserving the original
        timing relationships between events.

        Args:
            pattern: The AutomationPattern to play.
        """
        self._play_events(pattern.cc_events)

    def play_attack_phase(self, attack_events: List[CCEvent]) -> None:
        """Play only the attack portion of an automation.

        Plays the provided attack events with their original timing.
        Typically used when a gate/trigger opens.

        Args:
            attack_events: List of CCEvent objects representing the attack phase.
        """
        self._play_events(attack_events)

    def play_decay_phase(self, decay_events: List[CCEvent]) -> None:
        """Play only the decay portion of an automation.

        Plays the provided decay events with their original timing.
        Typically used when a gate/trigger closes.

        Args:
            decay_events: List of CCEvent objects representing the decay phase.
        """
        self._play_events(decay_events)

    def play_cc_snapshot(self, cc_values: Dict[int, int], channel: int = 0) -> None:
        """Send instantaneous CC values.

        Immediately sends all provided CC values without any timing delays.
        Useful for initializing CC state or jumping to a specific point.

        Args:
            cc_values: Mapping of CC numbers to values (both 0-127).
            channel: MIDI channel to send on (0-15). Defaults to 0.
        """
        for cc_number, value in cc_values.items():
            self._send_cc(cc_number, value, channel)

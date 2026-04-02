"""Pattern analysis utilities for CC automation sequences.

This module provides static analysis methods for CC events including
attack/decay splitting, automation type detection, and event optimization.
"""

from typing import List, Tuple

from midi_maker.core import CCAutomationType, CCEvent


class PatternAnalyzer:
    """Static analysis methods for CC automation patterns.

    Provides utilities for splitting patterns into phases, detecting
    automation types, and optimizing event sequences.
    """

    # Common CC numbers for classification
    _FILTER_CC_NUMBERS = {74, 71}  # Filter cutoff, filter resonance (common)
    _VOLUME_CC_NUMBERS = {7, 11}  # Volume, Expression
    _PAN_CC_NUMBERS = {10}  # Pan
    _RESONANCE_CC_NUMBERS = {71}  # Filter resonance

    @staticmethod
    def split_attack_decay(
        cc_events: List[CCEvent],
    ) -> Tuple[List[CCEvent], List[CCEvent]]:
        """Split CC events into attack and decay phases.

        Finds the peak value in the CC events and splits the sequence
        at that point. The attack phase includes events up to and including
        the peak; the decay phase includes events after the peak.

        Args:
            cc_events: List of CC events to split.

        Returns:
            Tuple of (attack_events, decay_events). Attack includes the peak,
            decay is everything after. If empty input, returns ([], []).
            If single event, returns ([event], []).
        """
        if not cc_events:
            return [], []

        # Find the index of the peak value (first occurrence)
        peak_index = 0
        peak_value = cc_events[0].value
        for i, event in enumerate(cc_events):
            if event.value > peak_value:
                peak_value = event.value
                peak_index = i

        # Split at peak: attack includes peak, decay is everything after
        attack_events = list(cc_events[: peak_index + 1])
        decay_events = list(cc_events[peak_index + 1 :])

        return attack_events, decay_events

    @staticmethod
    def detect_cc_type(cc_events: List[CCEvent]) -> CCAutomationType:
        """Classify automation type based on CC number and behavior.

        Uses the most common CC number in the events to determine the
        automation type. If the CC number doesn't match a known type,
        returns CCAutomationType.CUSTOM.

        Args:
            cc_events: List of CC events to classify.

        Returns:
            The detected CCAutomationType. Returns CUSTOM for empty lists
            or unrecognized CC numbers.
        """
        if not cc_events:
            return CCAutomationType.CUSTOM

        # Find the most common CC number
        cc_counts: dict[int, int] = {}
        for event in cc_events:
            cc_counts[event.cc_number] = cc_counts.get(event.cc_number, 0) + 1

        primary_cc = max(cc_counts, key=lambda k: cc_counts[k])

        # Classify based on CC number
        if primary_cc in PatternAnalyzer._VOLUME_CC_NUMBERS:
            return CCAutomationType.VOLUME_FADE
        if primary_cc in PatternAnalyzer._PAN_CC_NUMBERS:
            return CCAutomationType.PAN_SWEEP
        if primary_cc in PatternAnalyzer._FILTER_CC_NUMBERS:
            # Check if it's resonance (CC 71) with small value range
            if primary_cc == 71:
                values = [e.value for e in cc_events if e.cc_number == 71]
                value_range = max(values) - min(values) if values else 0
                # Resonance typically has smaller value ranges
                if value_range < 40:
                    return CCAutomationType.RESONANCE
            return CCAutomationType.FILTER_SWEEP

        return CCAutomationType.CUSTOM

    @staticmethod
    def optimize_events(cc_events: List[CCEvent]) -> List[CCEvent]:
        """Remove redundant CC events to optimize playback.

        Removes consecutive events with the same CC number and value,
        keeping only the first occurrence. This reduces MIDI bandwidth
        without affecting the resulting automation curve.

        Also removes events where the value change is less than a threshold
        (currently 1) compared to the previous event for the same CC number.

        Args:
            cc_events: List of CC events to optimize.

        Returns:
            Optimized list of CC events with redundant events removed.
            Events are returned in their original order.
        """
        if not cc_events:
            return []

        optimized: List[CCEvent] = []
        # Track last value per CC number to detect redundancy
        last_value_by_cc: dict[int, int] = {}

        for event in cc_events:
            cc_key = (event.cc_number, event.channel)
            last_value = last_value_by_cc.get(cc_key)

            # Keep event if it's the first for this CC or value has changed
            if last_value is None or event.value != last_value:
                optimized.append(event)
                last_value_by_cc[cc_key] = event.value

        return optimized

    @staticmethod
    def calculate_duration(cc_events: List[CCEvent]) -> float:
        """Calculate the total duration of a CC event sequence.

        Args:
            cc_events: List of CC events.

        Returns:
            Duration in seconds from first to last event, or 0.0 if
            the list is empty or has only one event.
        """
        if len(cc_events) < 2:
            return 0.0

        return cc_events[-1].timestamp - cc_events[0].timestamp

    @staticmethod
    def find_peak_event(cc_events: List[CCEvent]) -> CCEvent | None:
        """Find the event with the highest value.

        If multiple events have the same peak value, returns the first one.

        Args:
            cc_events: List of CC events.

        Returns:
            The CCEvent with the highest value, or None if the list is empty.
        """
        if not cc_events:
            return None

        return max(cc_events, key=lambda e: (e.value, -cc_events.index(e)))

    @staticmethod
    def get_value_range(cc_events: List[CCEvent]) -> Tuple[int, int]:
        """Get the minimum and maximum values in a CC event sequence.

        Args:
            cc_events: List of CC events.

        Returns:
            Tuple of (min_value, max_value). Returns (0, 0) for empty lists.
        """
        if not cc_events:
            return 0, 0

        values = [e.value for e in cc_events]
        return min(values), max(values)

"""Playback scheduler for timed playback management.

This module provides the PlaybackScheduler class for managing multiple
concurrent automation pattern playbacks with different modes.
"""

import threading
import time
import uuid
from dataclasses import dataclass
from typing import Dict, Optional

from midi_maker.automation import AutomationPattern
from midi_maker.core import CCEvent, PlaybackMode, PlaybackError
from midi_maker.playback.player import AutomationPlayer, MidiOutputPort


@dataclass
class PlaybackState:
    """State tracking for an active playback.

    Attributes:
        playback_id: Unique identifier for this playback instance
        pattern: The automation pattern being played
        mode: Playback mode being used
        thread: Thread executing the playback
        stop_event: Event to signal playback should stop
    """

    playback_id: str
    pattern: AutomationPattern
    mode: PlaybackMode
    thread: threading.Thread
    stop_event: threading.Event


class PlaybackScheduler:
    """Manages timed playback of automation patterns.

    PlaybackScheduler coordinates multiple concurrent playbacks of automation
    patterns with support for various playback modes. Each playback runs in
    its own thread and can be stopped independently.

    The scheduler uses AutomationPlayer for the actual playback logic,
    providing a higher-level interface for managing multiple concurrent
    playbacks.

    Attributes:
        output_port: Optional MIDI output port for sending CC messages.
        active_playbacks: Dictionary tracking currently playing patterns.
    """

    def __init__(self, output_port: Optional[MidiOutputPort] = None) -> None:
        """Initialize the PlaybackScheduler.

        Args:
            output_port: Optional MIDI output port. If None, playback occurs
                without actual MIDI output (useful for testing or when using
                callbacks).
        """
        self.output_port = output_port
        self.active_playbacks: Dict[str, PlaybackState] = {}
        self._lock = threading.Lock()

    def start_pattern_playback(
        self, pattern: AutomationPattern, playback_mode: PlaybackMode
    ) -> str:
        """Start playing an automation pattern.

        Creates a new playback thread for the given pattern using the specified
        playback mode. The playback runs asynchronously in its own thread.

        Args:
            pattern: The AutomationPattern to play.
            playback_mode: How to play the pattern (FULL_SEQUENCE, ATTACK_ONLY, etc.)

        Returns:
            A unique playback_id that can be used to stop this playback.

        Raises:
            ValueError: If the playback_mode is not supported.
        """
        playback_id = str(uuid.uuid4())
        stop_event = threading.Event()

        # Create a new player for this playback
        player = AutomationPlayer(output_port=self.output_port)

        # Create and start the playback thread
        thread = threading.Thread(
            target=self._execute_playback,
            args=(player, pattern, playback_mode, stop_event),
            daemon=True,
        )

        # Store playback state
        state = PlaybackState(
            playback_id=playback_id,
            pattern=pattern,
            mode=playback_mode,
            thread=thread,
            stop_event=stop_event,
        )

        with self._lock:
            self.active_playbacks[playback_id] = state
            thread.start()

        return playback_id

    def stop_pattern_playback(self, playback_id: str) -> None:
        """Stop a specific playback.

        Signals the playback thread to stop and removes it from active playbacks.
        This is a non-blocking call; the thread may take a moment to fully stop.

        Args:
            playback_id: The ID returned from start_pattern_playback.

        Raises:
            PlaybackError: If playback_id does not exist in active playbacks.
        """
        with self._lock:
            if playback_id not in self.active_playbacks:
                raise PlaybackError(f"No active playback with id: {playback_id}")

            state = self.active_playbacks[playback_id]
            state.stop_event.set()

            # Remove from active playbacks immediately
            del self.active_playbacks[playback_id]

    def stop_all_playbacks(self) -> None:
        """Stop all active playbacks.

        Signals all playback threads to stop and clears the active playbacks
        dictionary.
        """
        with self._lock:
            for state in self.active_playbacks.values():
                state.stop_event.set()

            self.active_playbacks.clear()

    def schedule_cc_event(self, cc_event: CCEvent, delay_ms: float) -> None:
        """Schedule an individual CC message.

        Sends a single CC event after a specified delay. This is useful for
        one-off CC messages that are not part of a pattern playback.

        Args:
            cc_event: The CCEvent to send.
            delay_ms: Delay in milliseconds before sending the event.
        """
        player = AutomationPlayer(output_port=self.output_port)

        def send_delayed() -> None:
            if delay_ms > 0:
                time.sleep(delay_ms / 1000.0)
            player._send_cc(cc_event.cc_number, cc_event.value, cc_event.channel)

        thread = threading.Thread(target=send_delayed, daemon=True)
        thread.start()

    def _execute_playback(
        self,
        player: AutomationPlayer,
        pattern: AutomationPattern,
        mode: PlaybackMode,
        stop_event: threading.Event,
    ) -> None:
        """Execute playback in a separate thread.

        This method runs in a background thread and handles the actual
        playback logic based on the specified mode.

        Args:
            player: The AutomationPlayer to use for playback.
            pattern: The pattern to play.
            mode: The playback mode to use.
            stop_event: Event that signals the playback should stop.

        Raises:
            ValueError: If the playback mode is not recognized.
        """
        if mode == PlaybackMode.FULL_SEQUENCE:
            self._play_with_interrupt(player, pattern.cc_events, stop_event)
        elif mode == PlaybackMode.ATTACK_ONLY:
            self._play_with_interrupt(player, pattern.attack_events, stop_event)
        elif mode == PlaybackMode.DECAY_ONLY:
            self._play_with_interrupt(player, pattern.decay_events, stop_event)
        elif mode == PlaybackMode.SNAPSHOT:
            # For snapshot mode, extract CC values from the last event of each CC
            cc_values = {}
            for event in pattern.cc_events:
                cc_values[event.cc_number] = event.value
            channel = pattern.cc_events[0].channel if pattern.cc_events else 0
            player.play_cc_snapshot(cc_values, channel)
        elif mode == PlaybackMode.ATTACK_DECAY:
            # ATTACK_DECAY mode requires external gate control
            # For now, just play the full sequence
            self._play_with_interrupt(player, pattern.cc_events, stop_event)
        else:
            raise PlaybackError(f"Unsupported playback mode: {mode}")

    def _play_with_interrupt(
        self,
        player: AutomationPlayer,
        events: list,
        stop_event: threading.Event,
    ) -> None:
        """Play events with support for early termination.

        Similar to AutomationPlayer._play_events but checks the stop_event
        between each event to allow for early termination.

        Args:
            player: The player to use for sending CC messages.
            events: List of CCEvent objects to play.
            stop_event: Event that signals playback should stop.
        """
        if not events:
            return

        playback_start = time.perf_counter()

        for event in events:
            if stop_event.is_set():
                break

            target_time = playback_start + event.timestamp
            while not stop_event.is_set():
                remaining = target_time - time.perf_counter()
                if remaining <= 0:
                    break
                while remaining > 0 and not stop_event.is_set():
                    sleep_time = min(remaining, 0.01)  # Check every 10ms
                    time.sleep(sleep_time)
                    remaining = target_time - time.perf_counter()

            if stop_event.is_set():
                break

            player._send_cc(event.cc_number, event.value, event.channel)

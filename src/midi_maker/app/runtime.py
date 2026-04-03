"""Runtime composition and lifecycle management for the app layer."""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol

from midi_maker.app.config import AppConfig
from midi_maker.automation import PatternLibrary
from midi_maker.patterns import SequencerInterface
from midi_maker.playback import GateProcessor, PlaybackScheduler
from midi_maker.recording import CCRecorder


class RuntimeDeps(Protocol):
    """Adapter boundary for MIDI port discovery and construction."""

    def list_input_ports(self) -> list[str]:
        """Return available MIDI input port names."""

    def list_output_ports(self) -> list[str]:
        """Return available MIDI output port names."""

    def create_input_port(self, name: str) -> Any:
        """Create/open an input port by name."""

    def create_output_port(self, name: str) -> Any:
        """Create/open an output port by name."""


@dataclass(frozen=True)
class RuntimeDependencies:
    """Concrete dependency container for runtime construction."""

    list_input_ports: Callable[[], list[str]]
    list_output_ports: Callable[[], list[str]]
    create_input_port: Callable[[str], Any]
    create_output_port: Callable[[str], Any]


class MidiMakerRuntime:
    """Composed runtime container with engine lifecycle controls."""

    def __init__(
        self,
        *,
        config: AppConfig,
        cc_recorder: CCRecorder,
        pattern_library: PatternLibrary,
        playback_scheduler: PlaybackScheduler,
        gate_processor: GateProcessor,
        sequencer_interface: SequencerInterface,
        managed_ports: list[Any],
    ) -> None:
        self.config = config
        self.cc_recorder = cc_recorder
        self.pattern_library = pattern_library
        self.playback_scheduler = playback_scheduler
        self.gate_processor = gate_processor
        self.sequencer_interface = sequencer_interface
        self.engine_running = False
        self.last_status_message = "Engine stopped"
        self._managed_ports = managed_ports
        self._shutdown = False

    @classmethod
    def from_config(
        cls,
        config: AppConfig,
        deps: RuntimeDeps | RuntimeDependencies | None = None,
    ) -> "MidiMakerRuntime":
        """Build a runtime by validating ports and composing services."""
        resolved_deps = deps or _default_runtime_dependencies()

        input_names = list(resolved_deps.list_input_ports() or [])
        output_names = list(resolved_deps.list_output_ports() or [])
        _validate_configured_ports(config=config, input_names=input_names, output_names=output_names)

        trigger_port = resolved_deps.create_input_port(config.ports.trigger_input)
        cc_source_port = resolved_deps.create_input_port(config.ports.cc_source_input)
        sequencer_port = resolved_deps.create_input_port(config.ports.sequencer_input)
        daw_output_port = resolved_deps.create_output_port(config.ports.daw_output)

        pattern_library = PatternLibrary(str(config.library_path))
        _load_pattern_library_or_fail(pattern_library=pattern_library, library_path=config.library_path)

        cc_recorder = CCRecorder(trigger_port=trigger_port, source_port=cc_source_port)
        cc_recorder.set_recording_mode(config.default_recording_mode)

        playback_scheduler = PlaybackScheduler(output_port=daw_output_port)
        gate_processor = GateProcessor(
            sequencer_port=sequencer_port,
            scheduler=playback_scheduler,
            pattern_library=pattern_library,
        )

        channel_mapping = _resolve_default_channel_mappings(
            configured_mappings=config.default_channel_mappings,
            pattern_library=pattern_library,
        )
        sequencer_interface = SequencerInterface(
            sequencer_port=sequencer_port,
            channel_mapping=channel_mapping,
            gate_processor=gate_processor,
        )

        return cls(
            config=config,
            cc_recorder=cc_recorder,
            pattern_library=pattern_library,
            playback_scheduler=playback_scheduler,
            gate_processor=gate_processor,
            sequencer_interface=sequencer_interface,
            managed_ports=[trigger_port, cc_source_port, sequencer_port, daw_output_port],
        )

    def start_engine(self) -> None:
        """Enable runtime processing."""
        self.engine_running = True
        self.last_status_message = "Engine running"

    def stop_engine(self) -> bool:
        """Disable runtime processing unless recording is active."""
        if self.cc_recorder.is_recording:
            self.last_status_message = "Stop recording before stopping engine"
            return False

        self.playback_scheduler.stop_all_playbacks()
        self.engine_running = False
        self.last_status_message = "Engine stopped"
        return True

    def shutdown(self) -> None:
        """Force-stop runtime activities and release ports."""
        if self._shutdown:
            return

        self.playback_scheduler.stop_all_playbacks()
        if self.cc_recorder.is_recording:
            self.cc_recorder.reset()

        self.engine_running = False
        self.last_status_message = "Runtime shut down"

        close_errors: list[str] = []
        for port in self._managed_ports:
            close = getattr(port, "close", None)
            if callable(close):
                try:
                    close()
                except Exception as exc:  # noqa: BLE001 - continue closing all ports
                    port_name = getattr(port, "name", repr(port))
                    close_errors.append(f"{port_name}: {exc}")

        self._shutdown = True
        if close_errors:
            raise RuntimeError(
                "Failed to close one or more MIDI ports during shutdown: "
                + "; ".join(close_errors)
            )


def _validate_configured_ports(
    *,
    config: AppConfig,
    input_names: list[str],
    output_names: list[str],
) -> None:
    missing_inputs = [
        name
        for name in (
            config.ports.trigger_input,
            config.ports.cc_source_input,
            config.ports.sequencer_input,
        )
        if name not in input_names
    ]
    missing_outputs = [
        name
        for name in (config.ports.daw_output,)
        if name not in output_names
    ]

    if not missing_inputs and not missing_outputs:
        return

    available_inputs = ", ".join(input_names) if input_names else "available ports unavailable"
    available_outputs = ", ".join(output_names) if output_names else "available ports unavailable"

    parts = ["Configured MIDI ports could not be resolved."]
    if missing_inputs:
        parts.append(f"Missing input ports: {', '.join(missing_inputs)}.")
    if missing_outputs:
        parts.append(f"Missing output ports: {', '.join(missing_outputs)}.")
    parts.append(f"available input ports: {available_inputs}.")
    parts.append(f"available output ports: {available_outputs}.")

    raise RuntimeError(" ".join(parts))


def _load_pattern_library_or_fail(*, pattern_library: PatternLibrary, library_path: Path) -> None:
    if not library_path.exists():
        return

    try:
        pattern_library.load_library(str(library_path))
    except Exception as exc:  # noqa: BLE001 - preserve actionable startup diagnostics
        raise RuntimeError(f"Failed to load pattern library '{library_path}': {exc}") from exc


def _resolve_default_channel_mappings(
    *,
    configured_mappings: Mapping[int, str],
    pattern_library: PatternLibrary,
) -> dict[int, str]:
    resolved: dict[int, str] = {}

    for channel, pattern_id in configured_mappings.items():
        if pattern_id in pattern_library:
            resolved[channel] = pattern_id
            continue

        warnings.warn(
            f"Configured default mapping for channel {channel} references missing pattern id '{pattern_id}'; skipping mapping.",
            UserWarning,
            stacklevel=3,
        )

    return resolved


def _default_runtime_dependencies() -> RuntimeDependencies:
    try:
        from midi_maker.app import midi_scripter_api
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "midi_scripter_api is required for runtime construction when deps are not provided"
        ) from exc

    return RuntimeDependencies(
        list_input_ports=midi_scripter_api.list_input_ports,
        list_output_ports=midi_scripter_api.list_output_ports,
        create_input_port=lambda name: midi_scripter_api.MidiIn(name=name),
        create_output_port=lambda name: midi_scripter_api.MidiOut(name=name),
    )

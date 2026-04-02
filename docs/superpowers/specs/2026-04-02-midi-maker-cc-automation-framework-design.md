# MIDI Maker: Modular CC Automation Framework Design

**Date**: 2026-04-02  
**Status**: Design Phase  
**Target Framework**: midi-scripter  

## Project Overview

MIDI Maker is a modular CC automation framework built on top of midi-scripter that enables intelligent recording and playback of MIDI control change sequences. The primary use case is live performance where a drummer's pedal triggers recording of CC automation (filter sweeps, volume changes, etc.) and an MPD232 sequencer triggers intelligent playback with attack/decay pattern recognition.

## Core Requirements

1. **Configurable Recording**: Hold/toggle modes for pedal-triggered CC recording
2. **Intelligent Playback**: Attack/decay automation that responds to sequencer gates
3. **Pattern Management**: Library system for storing and organizing automation patterns
4. **Sequencer Integration**: MPD232 integration with proper gate state handling
5. **Extensible Architecture**: Modular design for future automation types and effects

## System Architecture

### High-Level Component Diagram

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MIDI Input    │    │   Drum Pedal    │    │   MPD232       │
│   (Controller)  │    │   (Trigger)     │    │   (Sequencer)  │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          ▼                      ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                 MIDI Maker Framework                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ Recording   │  │ Automation  │  │      Playback           │  │
│  │ Engine      │  │ Library     │  │      Engine             │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
│  ┌─────────────┐  ┌─────────────────────────────────────────┐  │
│  │ Pattern     │  │           GUI Framework                │  │
│  │ Manager     │  │                                        │  │
│  └─────────────┘  └─────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────┐
│   MIDI Output   │
│   (To DAW)      │
└─────────────────┘
```

## Detailed Component Design

### 1. Recording Engine (`midi_maker.recording`)

#### 1.1 CCRecorder Class

**Purpose**: Main recording coordinator that manages the recording lifecycle.

```python
class CCRecorder:
    def __init__(self, trigger_port: MidiIn, source_port: MidiIn):
        self.trigger_handler = TriggerHandler(trigger_port)
        self.stream_capture = StreamCapture(source_port)
        self.recording_mode = RecordingMode.TOGGLE  # or HOLD
        self.current_pattern = None
        
    def start_recording(self) -> str:
        """Returns pattern_id for the new recording"""
        
    def stop_recording(self) -> AutomationPattern:
        """Returns completed automation pattern"""
        
    def set_recording_mode(self, mode: RecordingMode) -> None:
        """Switch between HOLD and TOGGLE modes"""
```

#### 1.2 TriggerHandler Class

**Purpose**: Handles pedal input and manages recording state transitions.

```python
class TriggerHandler:
    def __init__(self, trigger_port: MidiIn):
        self.trigger_port = trigger_port
        self.recording_state = RecordingState.IDLE
        self.mode = RecordingMode.TOGGLE
        
    @trigger_port.subscribe(MidiType.NOTE_ON)  # Assuming pedal sends notes
    def handle_trigger_on(self, msg: MidiMsg) -> None:
        """Handle pedal press"""
        
    @trigger_port.subscribe(MidiType.NOTE_OFF)
    def handle_trigger_off(self, msg: MidiMsg) -> None:
        """Handle pedal release"""
```

#### 1.3 StreamCapture Class

**Purpose**: Buffers incoming CC messages with precise timestamps.

```python
class StreamCapture:
    def __init__(self, source_port: MidiIn):
        self.source_port = source_port
        self.recording_buffer = []
        self.recording_active = False
        self.start_time = None
        
    @source_port.subscribe(MidiType.CONTROL_CHANGE)
    def capture_cc(self, msg: MidiMsg) -> None:
        """Capture CC messages during recording"""
        if self.recording_active:
            relative_time = msg.ctime - self.start_time
            self.recording_buffer.append(CCEvent(
                cc_number=msg.data1,
                value=msg.data2,
                channel=msg.channel,
                timestamp=relative_time
            ))
```

### 2. Automation Library (`midi_maker.automation`)

#### 2.1 AutomationPattern Class

**Purpose**: Data structure for storing complete CC sequences with metadata.

```python
@dataclass
class AutomationPattern:
    pattern_id: str
    name: str
    cc_events: List[CCEvent]
    duration: float
    attack_events: List[CCEvent]  # First 50% or until peak
    decay_events: List[CCEvent]   # Remaining events
    metadata: Dict[str, Any]
    
    def analyze_attack_decay(self) -> None:
        """Split cc_events into attack and decay phases"""
        
    def to_dict(self) -> Dict:
        """Serialize for JSON storage"""
        
    @classmethod
    def from_dict(cls, data: Dict) -> 'AutomationPattern':
        """Deserialize from JSON storage"""
```

#### 2.2 PatternLibrary Class

**Purpose**: Manages collections of automation patterns with persistence.

```python
class PatternLibrary:
    def __init__(self, library_path: str = "patterns.json"):
        self.patterns: Dict[str, AutomationPattern] = {}
        self.library_path = library_path
        
    def add_pattern(self, pattern: AutomationPattern) -> None:
        """Add new pattern to library"""
        
    def get_pattern(self, pattern_id: str) -> AutomationPattern:
        """Retrieve pattern by ID"""
        
    def list_patterns(self) -> List[str]:
        """Get all pattern IDs"""
        
    def save_library(self) -> None:
        """Persist library to JSON file"""
        
    def load_library(self) -> None:
        """Load library from JSON file"""
```

#### 2.3 PatternAnalyzer Class

**Purpose**: Analyzes recordings to identify attack/decay characteristics.

```python
class PatternAnalyzer:
    @staticmethod
    def split_attack_decay(cc_events: List[CCEvent]) -> Tuple[List[CCEvent], List[CCEvent]]:
        """Split CC events into attack and decay phases"""
        # Algorithm: Find peak value or midpoint, split there
        
    @staticmethod
    def detect_cc_type(cc_events: List[CCEvent]) -> CCAutomationType:
        """Classify automation type (filter_sweep, volume_fade, etc.)"""
        
    @staticmethod
    def optimize_events(cc_events: List[CCEvent]) -> List[CCEvent]:
        """Remove redundant CC events to optimize playback"""
```

### 3. Playback Engine (`midi_maker.playback`)

#### 3.1 PlaybackScheduler Class

**Purpose**: Manages timed playback of CC sequences with precise timing.

```python
class PlaybackScheduler:
    def __init__(self, output_port: MidiOut):
        self.output_port = output_port
        self.active_playbacks = {}  # pattern_id -> PlaybackState
        self.scheduler_thread = None
        
    def start_pattern_playback(self, pattern: AutomationPattern, 
                             playback_mode: PlaybackMode) -> str:
        """Start playing automation pattern"""
        
    def stop_pattern_playback(self, playback_id: str) -> None:
        """Stop specific playback"""
        
    def schedule_cc_event(self, cc_event: CCEvent, delay_ms: float) -> None:
        """Schedule individual CC message"""
```

#### 3.2 GateProcessor Class

**Purpose**: Handles sequencer gate logic for attack/decay triggering.

```python
class GateProcessor:
    def __init__(self, sequencer_port: MidiIn):
        self.sequencer_port = sequencer_port
        self.gate_states = {}  # channel -> GateState
        self.attack_decay_mappings = {}  # pattern_id -> (attack_pattern, decay_pattern)
        
    @sequencer_port.subscribe(MidiType.NOTE_ON)
    def handle_gate_on(self, msg: MidiMsg) -> None:
        """Trigger attack automation on sequencer step"""
        
    @sequencer_port.subscribe(MidiType.NOTE_OFF)  
    def handle_gate_off(self, msg: MidiMsg) -> None:
        """Trigger decay automation on sequencer step release"""
        
    def set_pattern_for_channel(self, channel: int, pattern_id: str) -> None:
        """Map automation pattern to sequencer channel"""
```

#### 3.3 AutomationPlayer Class

**Purpose**: Core playback logic with multiple playback modes.

```python
class AutomationPlayer:
    def __init__(self, output_port: MidiOut):
        self.output_port = output_port
        
    def play_full_sequence(self, pattern: AutomationPattern) -> None:
        """Play complete automation with original timing"""
        
    def play_attack_phase(self, attack_events: List[CCEvent]) -> None:
        """Play only attack portion"""
        
    def play_decay_phase(self, decay_events: List[CCEvent]) -> None:
        """Play only decay portion"""
        
    def play_cc_snapshot(self, cc_values: Dict[int, int]) -> None:
        """Send instantaneous CC values"""
```

### 4. Pattern Manager (`midi_maker.patterns`)

#### 4.1 SequencerInterface Class

**Purpose**: Manages integration with MPD232 and other sequencers.

```python
class SequencerInterface:
    def __init__(self, sequencer_port: MidiIn, channel_mapping: Dict[int, str]):
        self.sequencer_port = sequencer_port
        self.channel_mapping = channel_mapping  # channel -> pattern_id
        self.gate_processor = GateProcessor(sequencer_port)
        
    def map_pattern_to_channel(self, channel: int, pattern_id: str) -> None:
        """Associate automation pattern with sequencer channel"""
        
    def get_active_channels(self) -> Set[int]:
        """Return currently active sequencer channels"""
```

#### 4.2 GateStateMachine Class

**Purpose**: Tracks sequencer step states and manages overlapping gates.

```python
class GateStateMachine:
    def __init__(self):
        self.channel_states = {}  # channel -> GateState
        self.gate_history = deque(maxlen=100)  # For overlap detection
        
    def update_gate_state(self, channel: int, gate_on: bool) -> GateTransition:
        """Update gate state and return transition type"""
        
    def has_overlapping_gates(self, channel: int) -> bool:
        """Check if gates are overlapping (sustain scenario)"""
        
    def get_gate_duration(self, channel: int) -> float:
        """Calculate gate duration for timing adjustments"""
```

### 5. GUI Framework (`midi_maker.gui`)

#### 5.1 RecordingPanel Class

**Purpose**: Visual interface for recording operations.

```python
class RecordingPanel:
    def __init__(self, cc_recorder: CCRecorder):
        self.cc_recorder = cc_recorder
        self.recording_indicator = GuiText("● IDLE", title="Recording Status")
        self.mode_selector = GuiButtonSelectorH(("HOLD", "TOGGLE"), 
                                              title="Recording Mode")
        self.level_meter = GuiProgressBarH(title="Input Level")
        
    def update_recording_status(self, status: RecordingState) -> None:
        """Update visual recording indicator"""
        
    def update_input_level(self, cc_value: int) -> None:
        """Show incoming CC levels"""
```

#### 5.2 PatternBrowser Class

**Purpose**: Library management and pattern selection interface.

```python
class PatternBrowser:
    def __init__(self, pattern_library: PatternLibrary):
        self.pattern_library = pattern_library
        self.pattern_list = GuiListSelector([], title="Automation Patterns")
        self.pattern_info = GuiText("", title="Pattern Info")
        self.play_button = GuiButton("▶ Play", title="Test Playback")
        
    def refresh_pattern_list(self) -> None:
        """Update GUI with current patterns"""
        
    def show_pattern_details(self, pattern_id: str) -> None:
        """Display pattern metadata and statistics"""
```

#### 5.3 PlaybackControls Class

**Purpose**: Real-time parameter adjustment during performance.

```python
class PlaybackControls:
    def __init__(self, playback_scheduler: PlaybackScheduler):
        self.playback_scheduler = playback_scheduler
        self.tempo_scale = GuiSliderH(1.0, 0.1, 4.0, title="Tempo Scale")
        self.velocity_scale = GuiSliderH(1.0, 0.0, 2.0, title="Velocity Scale")
        self.channel_mapping = GuiWidgetLayout("Sequencer Mapping")
        
    def apply_tempo_scaling(self, scale_factor: float) -> None:
        """Adjust playback timing in real-time"""
        
    def apply_velocity_scaling(self, scale_factor: float) -> None:
        """Adjust CC value ranges in real-time"""
```

## Data Flow Architecture

### Recording Flow
1. **Pedal Press** → TriggerHandler → CCRecorder.start_recording()
2. **CC Input** → StreamCapture → recording_buffer
3. **Pedal Release** → TriggerHandler → CCRecorder.stop_recording()
4. **Pattern Creation** → PatternAnalyzer → AutomationPattern
5. **Library Storage** → PatternLibrary.add_pattern()

### Playback Flow
1. **Sequencer Note-On** → GateProcessor.handle_gate_on()
2. **Pattern Lookup** → SequencerInterface.channel_mapping
3. **Attack Playback** → AutomationPlayer.play_attack_phase()
4. **CC Output** → midi-scripter output port → DAW
5. **Sequencer Note-Off** → GateProcessor.handle_gate_off()
6. **Decay Playback** → AutomationPlayer.play_decay_phase()

## Integration with midi-scripter

### Port Configuration
```python
# Input ports
drum_pedal = MidiIn('Drum Pedal')
midi_controller = MidiIn('MIDI Controller') 
mpd232_sequencer = MidiIn('MPD232')

# Output ports  
daw_output = MidiOut('To DAW', virtual=True)

# MIDI Maker initialization
recorder = CCRecorder(drum_pedal, midi_controller)
playback = PlaybackScheduler(daw_output)
sequencer = SequencerInterface(mpd232_sequencer, {})
```

### GUI Integration
```python
# MIDI Maker GUI components integrate with midi-scripter widgets
recording_panel = RecordingPanel(recorder)
pattern_browser = PatternBrowser(library)
playback_controls = PlaybackControls(playback)

# Standard midi-scripter startup
if __name__ == '__main__':
    start_gui()
```

## Performance Considerations

1. **Low Latency**: Critical for live performance
   - Use midi-scripter's efficient message routing
   - Minimize processing in @subscribe decorated functions
   - Pre-calculate automation curves where possible

2. **Memory Management**: 
   - Limit pattern library size
   - Implement LRU cache for frequently used patterns
   - Stream large automation sequences rather than loading entirely

3. **Timing Precision**:
   - Leverage midi-scripter's sub-millisecond timing
   - Use separate threads for playback scheduling
   - Implement jitter compensation for long automation sequences

## Error Handling Strategy

1. **Recording Failures**: Continue operation, log errors, provide user feedback
2. **Playback Issues**: Graceful degradation, fallback to simpler playback modes
3. **Pattern Corruption**: Validate patterns on load, backup library automatically
4. **MIDI Port Issues**: Auto-reconnection, port monitoring, user notifications

## Extensibility Points

1. **Automation Types**: Plugin architecture for new CC automation patterns
2. **Sequencer Support**: Abstract interface for different sequencer types
3. **Effects Processing**: Real-time CC transformation plugins
4. **Export Formats**: Multiple output formats (DAW-specific, standard MIDI)
5. **Pattern Analysis**: Machine learning integration for pattern classification

## Testing Strategy

1. **Unit Tests**: Individual component functionality
2. **Integration Tests**: Full recording → playback workflow
3. **Performance Tests**: Latency measurements, stress testing
4. **Hardware Tests**: Real MPD232 and pedal integration
5. **User Acceptance Tests**: Live performance scenarios

## Future Enhancements

1. **Advanced Pattern Analysis**: Machine learning for automatic attack/decay detection
2. **Cloud Pattern Library**: Shared patterns across devices
3. **DAW Integration**: Direct plugin versions for major DAWs
4. **Multi-Pattern Layering**: Simultaneous playback of multiple patterns
5. **Live Performance Modes**: Set-list management, cue systems

---

*This design provides the foundation for a powerful, extensible CC automation framework that leverages midi-scripter's strengths while adding sophisticated pattern management and intelligent playback capabilities.*
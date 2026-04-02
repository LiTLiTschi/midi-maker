# MIDI Maker

A Python tool for creating and manipulating MIDI files with ease.

## Features

- Create MIDI files programmatically
- Manipulate existing MIDI files
- Support for multiple tracks and channels
- Easy-to-use API for music composition
- Command-line interface for quick operations

## Installation

### From PyPI (when published)
```bash
pip install midi-maker
```

### For Development
```bash
git clone https://github.com/yourusername/midi-maker.git
cd midi-maker
pip install -e ".[dev]"
```

## Quick Start

For the current CC automation workflow, see [docs/usage.md](docs/usage.md).

```python
from midi_maker import MidiFile, Track, Note

# Create a new MIDI file
midi = MidiFile()

# Add a track
track = Track("Piano")
midi.add_track(track)

# Add some notes
track.add_note(Note("C4", duration=1.0))
track.add_note(Note("E4", duration=1.0))
track.add_note(Note("G4", duration=1.0))

# Save the file
midi.save("my_song.mid")
```

## Command Line Usage

```bash
# Create a simple MIDI file
midi-maker create --output song.mid --notes "C4,E4,G4" --duration 1.0

# Convert between formats
midi-maker convert input.mid --output song.wav

# Analyze a MIDI file
midi-maker analyze song.mid
```

## Project Structure

```
midi-maker/
├── src/
│   └── midi_maker/
│       ├── __init__.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── midi_file.py
│       │   ├── track.py
│       │   └── note.py
│       ├── utils/
│       │   ├── __init__.py
│       │   └── helpers.py
│       └── cli.py
├── tests/
│   ├── __init__.py
│   ├── test_midi_file.py
│   ├── test_track.py
│   └── test_note.py
├── docs/
├── examples/
├── pyproject.toml
├── README.md
└── .gitignore
```

## Development

### Setting up the development environment

```bash
# Clone the repository
git clone https://github.com/yourusername/midi-maker.git
cd midi-maker

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"
```

### Running tests

```bash
pytest
```

### Code formatting

```bash
black src tests
isort src tests
```

### Type checking

```bash
mypy src
```

## Dependencies

- **mido**: For MIDI file I/O operations
- **pretty-midi**: For advanced MIDI manipulation
- **pytest**: Testing framework (development)
- **black**: Code formatting (development)
- **mypy**: Type checking (development)

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for your changes
5. Run the test suite (`pytest`)
6. Format your code (`black src tests`)
7. Commit your changes (`git commit -m 'Add amazing feature'`)
8. Push to the branch (`git push origin feature/amazing-feature`)
9. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Roadmap

- [ ] Basic MIDI file creation and manipulation
- [ ] Command-line interface
- [ ] Support for different time signatures
- [ ] MIDI effects and transformations
- [ ] Real-time MIDI input/output
- [ ] Integration with popular DAWs
- [ ] Web interface for online MIDI creation

## Acknowledgments

- The MIDI specification community
- Contributors to the `mido` and `pretty-midi` libraries
- The Python music programming community

---

**Note**: This project is currently in early development. APIs may change before the first stable release.
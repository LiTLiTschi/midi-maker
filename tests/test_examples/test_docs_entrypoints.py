"""Doc consistency checks for app startup entrypoint guidance."""

from __future__ import annotations

from pathlib import Path


def test_readme_references_config_required_entrypoint() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    assert "--config" in readme
    assert "midi_maker.cli" not in readme


def test_usage_doc_references_config_required_entrypoint() -> None:
    usage = Path("docs/usage.md").read_text(encoding="utf-8")
    assert "--config" in usage
    assert "midi_maker.cli" not in usage


def test_configs_example_exists_with_required_keys() -> None:
    config_example = Path("configs.example").read_text(encoding="utf-8")
    assert '"ports"' in config_example
    assert '"trigger_input"' in config_example
    assert '"cc_source_input"' in config_example
    assert '"sequencer_input"' in config_example
    assert '"daw_output"' in config_example
    assert '"library_path"' in config_example

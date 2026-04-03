"""Widget facades used by GUI adapter tests."""

from __future__ import annotations

from typing import Callable, Sequence


class FakeGuiText:
    """Simple text widget with mutable text content."""

    def __init__(self, text: str = "") -> None:
        self.text = text

    def set_text(self, text: str) -> None:
        self.text = text


class FakeButtonSelectorH:
    """Horizontal selector widget with change callback support."""

    def __init__(
        self,
        *,
        options: Sequence[str] = (),
        selected: str | None = None,
    ) -> None:
        self.options = list(options)
        if selected is not None:
            self.selected = selected
        elif self.options:
            self.selected = self.options[0]
        else:
            self.selected = None
        self.on_change: Callable[[str], None] | None = None

    def set_on_change(self, callback: Callable[[str], None]) -> None:
        self.on_change = callback

    def set_selected(self, value: str) -> None:
        self.selected = value

    def trigger_change(self, value: str) -> None:
        self.selected = value
        if self.on_change is not None:
            self.on_change(value)


class FakeButton:
    """Button widget with click callback support."""

    def __init__(self) -> None:
        self.on_click: Callable[[], object] | None = None

    def set_on_click(self, callback: Callable[[], object]) -> None:
        self.on_click = callback

    def click(self) -> object | None:
        if self.on_click is None:
            return None
        return self.on_click()


class FakeListSelector:
    """List selector with items, selection, and change callback."""

    def __init__(
        self,
        *,
        items: Sequence[str] = (),
        selected: str | None = None,
    ) -> None:
        self.items = list(items)
        self.selected = selected
        self.on_change: Callable[[str], None] | None = None

    def set_items(self, items: Sequence[str]) -> None:
        self.items = list(items)

    def set_selected(self, value: str | None) -> None:
        self.selected = value

    def set_on_change(self, callback: Callable[[str], None]) -> None:
        self.on_change = callback

    def select(self, value: str) -> None:
        self.selected = value
        if self.on_change is not None:
            self.on_change(value)


class _ValueWidget:
    """Base value widget supporting callback wiring and value changes."""

    def __init__(self, value: float = 0.0) -> None:
        self.value = value
        self.on_change: Callable[[float], None] | None = None

    def set_value(self, value: float) -> None:
        self.value = value

    def get_value(self) -> float:
        return self.value

    def set_on_change(self, callback: Callable[[float], None]) -> None:
        self.on_change = callback

    def trigger_change(self, value: float) -> None:
        self.value = value
        if self.on_change is not None:
            self.on_change(value)


class FakeProgressBarH(_ValueWidget):
    """Fake horizontal progress bar."""


class FakeSliderH(_ValueWidget):
    """Fake horizontal slider."""


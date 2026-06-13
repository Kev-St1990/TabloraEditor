"""Platform-aware keyboard shortcut helpers."""

from dataclasses import dataclass
import sys
from typing import Callable, Protocol


class ShortcutHandlers(Protocol):
    """Callback set used to bind standard application shortcuts."""

    def on_open(self, event: object | None = None) -> object | None: ...

    def on_save(self, event: object | None = None) -> object | None: ...

    def on_save_as(self, event: object | None = None) -> object | None: ...

    def on_undo(self, event: object | None = None) -> object | None: ...

    def on_redo(self, event: object | None = None) -> object | None: ...

    def on_copy(self, event: object | None = None) -> object | None: ...

    def on_paste(self, event: object | None = None) -> object | None: ...


@dataclass(frozen=True, slots=True)
class ShortcutBinding:
    """A single keyboard shortcut expression and its target callback."""

    sequence: str
    callback_name: str


class ShortcutManager:
    """Create platform-appropriate shortcut bindings for the editor."""

    def primary_modifier(self) -> str:
        """Return the primary modifier key for the current platform."""
        return "Command" if sys.platform == "darwin" else "Control"

    def secondary_modifier(self) -> str:
        """Return the redo modifier variant for the current platform."""
        return "Shift-Command" if sys.platform == "darwin" else "Control"

    def standard_bindings(self) -> list[ShortcutBinding]:
        """Return the standard shortcut map used by the application."""
        primary = self.primary_modifier()
        return [
            ShortcutBinding(f"<{primary}-o>", "on_open"),
            ShortcutBinding(f"<{primary}-s>", "on_save"),
            ShortcutBinding(f"<{primary}-Shift-S>", "on_save_as"),
            ShortcutBinding(f"<{primary}-z>", "on_undo"),
            ShortcutBinding(f"<{primary}-y>", "on_redo"),
            ShortcutBinding(f"<{primary}-c>", "on_copy"),
            ShortcutBinding(f"<{primary}-v>", "on_paste"),
        ]

    def bind_standard_shortcuts(self, root: object, handlers: ShortcutHandlers) -> list[str]:
        """Bind the standard shortcut set to a tkinter root."""
        bound_sequences: list[str] = []
        for binding in self.standard_bindings():
            callback = getattr(handlers, binding.callback_name)
            root.bind(binding.sequence, callback)
            bound_sequences.append(binding.sequence)
        return bound_sequences

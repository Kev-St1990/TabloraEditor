"""Platform-specific services for shortcuts, dialogs, and clipboard access."""

from tablora.platform.clipboard import ClipboardService, InMemoryClipboardBackend, TkClipboardBackend
from tablora.platform.dialogs import DialogService
from tablora.platform.shortcuts import ShortcutBinding, ShortcutManager

__all__ = [
    "ClipboardService",
    "DialogService",
    "InMemoryClipboardBackend",
    "TkClipboardBackend",
    "ShortcutBinding",
    "ShortcutManager",
]

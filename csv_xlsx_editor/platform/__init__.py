"""Platform-specific services for shortcuts, dialogs, and clipboard access."""

from csv_xlsx_editor.platform.clipboard import ClipboardService, InMemoryClipboardBackend
from csv_xlsx_editor.platform.dialogs import DialogService
from csv_xlsx_editor.platform.shortcuts import ShortcutBinding, ShortcutManager

__all__ = [
    "ClipboardService",
    "DialogService",
    "InMemoryClipboardBackend",
    "ShortcutBinding",
    "ShortcutManager",
]

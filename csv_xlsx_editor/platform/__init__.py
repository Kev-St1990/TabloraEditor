"""Platform-specific services for shortcuts, dialogs, and clipboard access."""

from csv_xlsx_editor.platform.clipboard import ClipboardService, InMemoryClipboardBackend

__all__ = ["ClipboardService", "InMemoryClipboardBackend"]

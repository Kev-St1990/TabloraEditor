"""Application bootstrap for the CSV/XLSX editor."""

import tkinter as tk

from csv_xlsx_editor.config import APP_NAME
from csv_xlsx_editor.actions import UndoRedoManager
from csv_xlsx_editor.domain import WorkbookDocument
from csv_xlsx_editor.io import FileManager
from csv_xlsx_editor.platform import ClipboardService, DialogService, InMemoryClipboardBackend, ShortcutManager
from csv_xlsx_editor.ui.menu_bar import MenuBar
from csv_xlsx_editor.ui.sheet_manager import SheetManager


class CsvXlsxEditorApp(tk.Tk):
    """Main tkinter application window.

    The app currently wires the existing sheet placeholder into the new package
    layout. Later steps will move business logic into domain, IO, and action
    services while keeping this class as the composition root.
    """

    def __init__(self) -> None:
        super().__init__()
        self.title(APP_NAME)
        self.geometry("1400x900")

        self.file_manager = FileManager()
        self.dialogs = DialogService()
        self.shortcut_manager = ShortcutManager()
        self.clipboard = ClipboardService(InMemoryClipboardBackend())
        self.undo_redo_manager = UndoRedoManager()
        self.current_document: WorkbookDocument | None = None

        self.sheet_manager = SheetManager(self)
        self.sheet_manager.pack(fill="both", expand=True)
        self.menu_bar = MenuBar(self).attach_to(self)
        self.shortcut_manager.bind_standard_shortcuts(self, self)

    def on_open_file(self, event: object | None = None) -> object | None:
        """Open a spreadsheet file through the platform dialog service."""
        path = self.dialogs.choose_open_path()
        if not path:
            return event
        try:
            self.current_document = self.file_manager.open(path)
            self.sheet_manager.sheet_view.load_worksheet(self.current_document.get_active_sheet())
            self.undo_redo_manager.clear()
        except Exception as exc:  # pragma: no cover - routed through messagebox in real UI
            self.dialogs.show_error_message("Open file failed", str(exc))
        return event

    def on_save_file(self, event: object | None = None) -> object | None:
        """Save the current spreadsheet to its existing path."""
        if self.current_document is None:
            return self.on_save_as_file(event)
        try:
            self.file_manager.save(self.current_document)
        except Exception as exc:  # pragma: no cover - routed through messagebox in real UI
            self.dialogs.show_error_message("Save file failed", str(exc))
        return event

    def on_save_as_file(self, event: object | None = None) -> object | None:
        """Save the current spreadsheet to a new location."""
        if self.current_document is None:
            return event
        path = self.dialogs.choose_save_path(default_extension=f".{self.current_document.file_type}")
        if not path:
            return event
        try:
            self.file_manager.save(self.current_document, path)
        except Exception as exc:  # pragma: no cover - routed through messagebox in real UI
            self.dialogs.show_error_message("Save file failed", str(exc))
        return event

    def on_undo(self, event: object | None = None) -> object | None:
        """Undo the last command."""
        self.undo_redo_manager.undo()
        return event

    def on_redo(self, event: object | None = None) -> object | None:
        """Redo the last undone command."""
        self.undo_redo_manager.redo()
        return event

    def on_copy(self, event: object | None = None) -> object | None:
        """Copy the current selection to the clipboard."""
        if self.current_document is None:
            return event
        matrix = self._selected_matrix()
        if matrix:
            self.clipboard.copy_cells(matrix)
        return event

    def on_paste(self, event: object | None = None) -> object | None:
        """Paste clipboard contents into the active worksheet."""
        if self.current_document is None:
            return event
        matrix = self.clipboard.paste_cells()
        if matrix:
            self.current_document.get_active_sheet().set_cells(0, 0, matrix)
            self.sheet_manager.sheet_view.refresh()
        return event

    def on_exit(self, event: object | None = None) -> object | None:
        """Close the application."""
        self.destroy()
        return event

    def _selected_matrix(self) -> list[list[object]]:
        if self.current_document is None:
            return []
        worksheet = self.current_document.get_active_sheet()
        matrix: list[list[object]] = []
        for row_index in worksheet.get_display_rows():
            row_values = [worksheet.get_cell(row_index, column).value for column in range(worksheet.max_column)]
            matrix.append(row_values)
        return matrix

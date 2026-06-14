"""Tests for shortcut-driven copy and paste behavior in the app."""

import unittest
from dataclasses import dataclass

from tablora import CsvXlsxEditorApp
from tablora.actions import EditCellCommand, UndoRedoManager
from tablora.domain import WorkbookDocument, WorksheetDocument
from tablora.platform import ClipboardService, InMemoryClipboardBackend


@dataclass
class FakeSheetView:
    """Minimal sheet-view double exposing selection helpers."""

    selected_matrix: list[list[object]]
    selected_start_cell: tuple[int, int]
    refresh_count: int = 0

    def get_selected_source_matrix(self) -> list[list[object]]:
        return self.selected_matrix

    def get_selected_source_start_cell(self) -> tuple[int, int]:
        return self.selected_start_cell

    def refresh(self) -> None:
        self.refresh_count += 1


@dataclass
class FakeSheetManager:
    """Wrap a fake sheet view in the shape expected by the app."""

    sheet_view: FakeSheetView


class AppClipboardShortcutTests(unittest.TestCase):
    """Verify copy and paste use the current selection rather than the full sheet."""

    def test_copy_uses_selected_matrix(self) -> None:
        worksheet = WorksheetDocument(sheet_id="sheet-1", title="Sheet 1")
        worksheet.set_cell(0, 0, "full-sheet-value")
        workbook = WorkbookDocument(worksheets=[worksheet], file_type="csv")
        app = CsvXlsxEditorApp.__new__(CsvXlsxEditorApp)
        app.current_document = workbook
        app.clipboard = ClipboardService(InMemoryClipboardBackend())
        app.sheet_manager = FakeSheetManager(
            FakeSheetView(
                selected_matrix=[[0.117318], [1.0]],
                selected_start_cell=(0, 0),
            )
        )

        result = CsvXlsxEditorApp.on_copy(app)

        self.assertEqual(app.clipboard.backend.text, "0.117318\r\n1")
        self.assertEqual(result, "break")

    def test_paste_uses_selected_start_cell(self) -> None:
        worksheet = WorksheetDocument(sheet_id="sheet-1", title="Sheet 1")
        workbook = WorkbookDocument(worksheets=[worksheet], file_type="csv")
        backend = InMemoryClipboardBackend("A\tB\r\nC\tD")
        app = CsvXlsxEditorApp.__new__(CsvXlsxEditorApp)
        app.current_document = workbook
        app.clipboard = ClipboardService(backend)
        app.sheet_manager = FakeSheetManager(
            FakeSheetView(
                selected_matrix=[["ignored"]],
                selected_start_cell=(2, 3),
            )
        )

        result = CsvXlsxEditorApp.on_paste(app)

        self.assertEqual(worksheet.get_cell(2, 3).value, "A")
        self.assertEqual(worksheet.get_cell(2, 4).value, "B")
        self.assertEqual(worksheet.get_cell(3, 3).value, "C")
        self.assertEqual(worksheet.get_cell(3, 4).value, "D")
        self.assertEqual(result, "break")

    def test_undo_refreshes_sheet_view_after_reverting_command(self) -> None:
        worksheet = WorksheetDocument(sheet_id="sheet-1", title="Sheet 1")
        worksheet.set_cell(0, 0, "before")
        workbook = WorkbookDocument(worksheets=[worksheet], file_type="csv")
        manager = UndoRedoManager()
        manager.execute(EditCellCommand(worksheet=worksheet, row=0, column=0, value="after", workbook=workbook))

        sheet_view = FakeSheetView(selected_matrix=[], selected_start_cell=(0, 0))
        app = CsvXlsxEditorApp.__new__(CsvXlsxEditorApp)
        app.current_document = workbook
        app.undo_redo_manager = manager
        app.sheet_manager = FakeSheetManager(sheet_view)

        CsvXlsxEditorApp.on_undo(app)

        self.assertEqual(worksheet.get_cell(0, 0).value, "before")
        self.assertEqual(sheet_view.refresh_count, 1)

    def test_redo_refreshes_sheet_view_after_reapplying_command(self) -> None:
        worksheet = WorksheetDocument(sheet_id="sheet-1", title="Sheet 1")
        worksheet.set_cell(0, 0, "before")
        workbook = WorkbookDocument(worksheets=[worksheet], file_type="csv")
        manager = UndoRedoManager()
        manager.execute(EditCellCommand(worksheet=worksheet, row=0, column=0, value="after", workbook=workbook))
        manager.undo()

        sheet_view = FakeSheetView(selected_matrix=[], selected_start_cell=(0, 0))
        app = CsvXlsxEditorApp.__new__(CsvXlsxEditorApp)
        app.current_document = workbook
        app.undo_redo_manager = manager
        app.sheet_manager = FakeSheetManager(sheet_view)

        CsvXlsxEditorApp.on_redo(app)

        self.assertEqual(worksheet.get_cell(0, 0).value, "after")
        self.assertEqual(sheet_view.refresh_count, 1)


if __name__ == "__main__":
    unittest.main()

"""Tests for undo and redo command handling."""

import unittest

from csv_xlsx_editor.actions import (
    EditCellCommand,
    FilterCommand,
    PasteRangeCommand,
    SortCommand,
    SortValuesCommand,
    UndoRedoManager,
)
from csv_xlsx_editor.domain import FilterState, SortState, WorkbookDocument, WorksheetDocument


class UndoRedoCommandTests(unittest.TestCase):
    """Verify command execution, undo, redo, and stack behavior."""

    def make_workbook(self) -> tuple[WorkbookDocument, WorksheetDocument]:
        worksheet = WorksheetDocument(sheet_id="sheet-1", title="Sheet 1")
        worksheet.set_cell(0, 0, "Charlie")
        worksheet.set_cell(1, 0, "Alice")
        worksheet.set_cell(2, 0, "Bob")
        workbook = WorkbookDocument(worksheets=[worksheet], file_type="csv")
        workbook.mark_clean()
        return workbook, worksheet

    def test_edit_cell_command_supports_undo_and_redo(self) -> None:
        workbook, worksheet = self.make_workbook()
        manager = UndoRedoManager()

        command = EditCellCommand(worksheet=worksheet, row=0, column=0, value="Delta", workbook=workbook)
        manager.execute(command)

        self.assertEqual(worksheet.get_cell(0, 0).value, "Delta")
        self.assertTrue(workbook.dirty)
        self.assertEqual(command.description(), "Edit cell R1C1")
        self.assertTrue(manager.can_undo())
        self.assertFalse(manager.can_redo())

        manager.undo()
        self.assertEqual(worksheet.get_cell(0, 0).value, "Charlie")
        self.assertTrue(manager.can_redo())

        manager.redo()
        self.assertEqual(worksheet.get_cell(0, 0).value, "Delta")

    def test_paste_range_command_restores_previous_cells(self) -> None:
        workbook, worksheet = self.make_workbook()
        manager = UndoRedoManager()

        command = PasteRangeCommand(
            worksheet=worksheet,
            start_row=1,
            start_column=0,
            matrix=[["Berlin", "1"], ["Paris", "2"]],
            workbook=workbook,
        )
        manager.execute(command)

        self.assertEqual(worksheet.get_cell(1, 0).value, "Berlin")
        self.assertEqual(worksheet.get_cell(2, 1).value, "2")
        self.assertEqual(command.description(), "Paste range 2x2 at R2C1")

        manager.undo()
        self.assertEqual(worksheet.get_cell(1, 0).value, "Alice")
        self.assertEqual(worksheet.get_cell(2, 0).value, "Bob")

    def test_sort_and_filter_commands_restore_view_state(self) -> None:
        workbook, worksheet = self.make_workbook()
        manager = UndoRedoManager()

        sort_command = SortCommand(
            worksheet=worksheet,
            sort_state=SortState(column=0, direction="asc"),
            workbook=workbook,
        )
        manager.execute(sort_command)
        self.assertEqual(worksheet.get_display_rows(), [1, 2, 0])
        self.assertEqual(sort_command.description(), "Sort column 1 asc")

        filter_state = FilterState()
        filter_state.set_filter(0, {"Alice"}, include_blanks=False)
        filter_command = FilterCommand(worksheet=worksheet, filter_state=filter_state, workbook=workbook)
        manager.execute(filter_command)
        self.assertEqual(worksheet.get_display_rows(), [1])
        self.assertEqual(filter_command.description(), "Filter 1 column(s)")

        manager.undo()
        self.assertEqual(worksheet.get_display_rows(), [1, 2, 0])
        manager.redo()
        self.assertEqual(worksheet.get_display_rows(), [1])

    def test_sort_values_command_sorts_one_column_and_supports_undo(self) -> None:
        workbook, worksheet = self.make_workbook()
        manager = UndoRedoManager()

        command = SortValuesCommand(worksheet=worksheet, column=0, reverse=False, workbook=workbook)
        manager.execute(command)

        self.assertEqual(
            [worksheet.get_cell(row, 0).value for row in range(3)],
            ["Alice", "Bob", "Charlie"],
        )
        self.assertEqual(command.description(), "Sort values column 1 asc")

        manager.undo()
        self.assertEqual(
            [worksheet.get_cell(row, 0).value for row in range(3)],
            ["Charlie", "Alice", "Bob"],
        )

    def test_new_execute_clears_redo_stack(self) -> None:
        workbook, worksheet = self.make_workbook()
        manager = UndoRedoManager()

        manager.execute(EditCellCommand(worksheet=worksheet, row=0, column=0, value="Delta", workbook=workbook))
        manager.execute(EditCellCommand(worksheet=worksheet, row=1, column=0, value="Echo", workbook=workbook))
        manager.undo()

        self.assertTrue(manager.can_redo())
        manager.execute(EditCellCommand(worksheet=worksheet, row=2, column=0, value="Foxtrot", workbook=workbook))
        self.assertFalse(manager.can_redo())
        self.assertEqual(worksheet.get_cell(2, 0).value, "Foxtrot")


if __name__ == "__main__":
    unittest.main()

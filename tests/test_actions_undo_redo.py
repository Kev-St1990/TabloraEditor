"""Tests for undo and redo command handling."""

import unittest

from tablora.actions import (
    EditCellCommand,
    FilterCommand,
    FormatCellsCommand,
    PasteRangeCommand,
    SortCommand,
    SortValuesCommand,
    UndoRedoManager,
    UpdateHiddenColumnsCommand,
    UpdateHiddenRowsCommand,
)
from tablora.domain import FilterState, FormatRequest, SortState, WorkbookDocument, WorksheetDocument


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

    def test_format_cells_command_restores_values_and_number_formats(self) -> None:
        worksheet = WorksheetDocument(sheet_id="sheet-1", title="Sheet 1")
        worksheet.set_cell(0, 0, "23 Jan 2024")
        worksheet.cells[(1, 0)] = worksheet.get_cell(1, 0)
        worksheet.cells[(1, 0)].value = 1234.5
        worksheet.cells[(1, 0)].number_format = "General"
        worksheet.max_row = 2
        worksheet.max_column = 1
        worksheet.rebuild_view()
        workbook = WorkbookDocument(worksheets=[worksheet], file_type="xlsx")
        manager = UndoRedoManager()

        command = FormatCellsCommand(
            worksheet=worksheet,
            addresses=[(0, 0), (1, 0)],
            request=FormatRequest(kind="date", source_hint="auto", target="de_date"),
            workbook=workbook,
        )
        manager.execute(command)

        self.assertEqual(worksheet.get_cell(0, 0).value, "23.01.2024")
        self.assertEqual(worksheet.get_cell(1, 0).number_format, "General")

        number_command = FormatCellsCommand(
            worksheet=worksheet,
            addresses=[(1, 0)],
            request=FormatRequest(kind="decimal", source_hint="auto", target="de_decimal"),
            workbook=workbook,
        )
        manager.execute(number_command)
        self.assertEqual(worksheet.get_cell(1, 0).number_format, "[$-de-DE]#,##0.0")

        manager.undo()
        self.assertEqual(worksheet.get_cell(1, 0).number_format, "General")

        manager.undo()
        self.assertEqual(worksheet.get_cell(0, 0).value, "23 Jan 2024")

    def test_hide_row_and_column_commands_support_undo(self) -> None:
        workbook, worksheet = self.make_workbook()
        worksheet.set_cell(0, 1, "Paris")
        worksheet.set_cell(1, 1, "Berlin")
        worksheet.set_cell(2, 1, "London")
        manager = UndoRedoManager()

        row_command = UpdateHiddenRowsCommand(worksheet=worksheet, rows=[1], hide=True, workbook=workbook)
        manager.execute(row_command)
        self.assertEqual(worksheet.get_display_rows(), [0, 2])

        column_command = UpdateHiddenColumnsCommand(worksheet=worksheet, columns=[1], hide=True, workbook=workbook)
        manager.execute(column_command)
        self.assertEqual(worksheet.table_view.visible_source_columns, [0])

        manager.undo()
        self.assertEqual(worksheet.table_view.visible_source_columns, [0, 1])
        manager.undo()
        self.assertEqual(worksheet.get_display_rows(), [0, 1, 2])


if __name__ == "__main__":
    unittest.main()

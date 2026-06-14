"""Tests for workbook and worksheet document behavior."""

from datetime import date, datetime
import unittest

from tablora.domain import CellData, WorkbookDocument, WorksheetDocument
from tablora.domain.sort_state import SortState


class WorkbookDocumentTests(unittest.TestCase):
    """Verify workbook sheet selection and dirty-state behavior."""

    def test_workbook_uses_first_sheet_as_default_active_sheet(self) -> None:
        sheet = WorksheetDocument(sheet_id="sheet-1", title="Sheet 1")
        workbook = WorkbookDocument(worksheets=[sheet], file_type="csv")

        self.assertIs(workbook.get_active_sheet(), sheet)

    def test_workbook_can_switch_active_sheet(self) -> None:
        first = WorksheetDocument(sheet_id="sheet-1", title="Sheet 1")
        second = WorksheetDocument(sheet_id="sheet-2", title="Sheet 2")
        workbook = WorkbookDocument(worksheets=[first, second], file_type="xlsx")

        workbook.set_active_sheet("sheet-2")

        self.assertIs(workbook.get_active_sheet(), second)

    def test_dirty_state_can_be_marked(self) -> None:
        workbook = WorkbookDocument(file_type="csv")

        workbook.mark_dirty()
        self.assertTrue(workbook.dirty)

        workbook.mark_clean()
        self.assertFalse(workbook.dirty)


class CellDataTests(unittest.TestCase):
    """Verify cell value and formula handling."""

    def test_formula_is_detected_from_value(self) -> None:
        cell = CellData.from_value("=SUM(A1:A2)")

        self.assertEqual(cell.value, "=SUM(A1:A2)")
        self.assertEqual(cell.formula, "=SUM(A1:A2)")

    def test_setting_plain_value_clears_formula(self) -> None:
        cell = CellData.from_value("=A1")

        cell.set_value("plain")

        self.assertEqual(cell.value, "plain")
        self.assertIsNone(cell.formula)


class WorksheetDocumentSortTests(unittest.TestCase):
    """Verify worksheet sorting behavior for typed values."""

    def test_date_sort_uses_real_date_values_and_number_formats(self) -> None:
        worksheet = WorksheetDocument(sheet_id="sheet-1", title="Sheet 1")
        worksheet.column_headers = ["date"]
        worksheet.cells[(0, 0)] = CellData(value="31.12.2024", number_format="DD.MM.YYYY")
        worksheet.cells[(1, 0)] = CellData(value=datetime(2024, 1, 2, 9, 30), number_format="YYYY-MM-DD HH:MM")
        worksheet.cells[(2, 0)] = CellData(value=date(2024, 1, 15), number_format="YYYY-MM-DD")
        worksheet.cells[(3, 0)] = CellData(value="23 Jan 2024", number_format="DD MMM YYYY")
        worksheet.cells[(4, 0)] = CellData(value="02 Feb 2024 14:30", number_format="DD MMM YYYY HH:MM")
        worksheet.cells[(5, 0)] = CellData(value="23 Mär 2024", number_format="DD MMM YYYY")
        worksheet.cells[(6, 0)] = CellData(value="01 Mai 2024", number_format="DD MMM YYYY")
        worksheet.cells[(7, 0)] = CellData(value="31 Dez 2024", number_format="DD MMM YYYY")
        worksheet.max_row = 8
        worksheet.max_column = 1
        worksheet.rebuild_view()

        worksheet.apply_sort(SortState(column=0, direction="asc"))

        self.assertEqual(worksheet.get_display_rows(), [1, 2, 3, 4, 5, 6, 0, 7])

    def test_column_value_sort_keeps_row_order_and_sorts_one_column(self) -> None:
        worksheet = WorksheetDocument(sheet_id="sheet-1", title="Sheet 1")
        worksheet.set_cell(0, 0, "27 Mär 2024")
        worksheet.set_cell(1, 0, "23 Jan 2024")
        worksheet.set_cell(2, 0, "02 Okt 2025")
        worksheet.set_cell(0, 1, "A")
        worksheet.set_cell(1, 1, "B")
        worksheet.set_cell(2, 1, "C")

        worksheet.sort_column_values(0, reverse=False)

        self.assertEqual(
            [worksheet.get_cell(row, 0).value for row in range(3)],
            ["23 Jan 2024", "27 Mär 2024", "02 Okt 2025"],
        )
        self.assertEqual(
            [worksheet.get_cell(row, 1).value for row in range(3)],
            ["A", "B", "C"],
        )

    def test_column_value_sort_clears_previous_row_sort_state(self) -> None:
        worksheet = WorksheetDocument(sheet_id="sheet-1", title="Sheet 1")
        worksheet.set_cell(0, 0, "Charlie")
        worksheet.set_cell(1, 0, "Alice")
        worksheet.set_cell(2, 0, "Bob")

        worksheet.apply_sort(SortState(column=0, direction="asc"))
        worksheet.sort_column_values(0, reverse=False)

        self.assertEqual(worksheet.get_display_rows(), [0, 1, 2])
        self.assertIsNone(worksheet.sort_state)
        self.assertEqual(
            [worksheet.get_cell(row, 0).value for row in range(3)],
            ["Alice", "Bob", "Charlie"],
        )


if __name__ == "__main__":
    unittest.main()

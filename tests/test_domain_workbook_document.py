"""Tests for workbook and worksheet document behavior."""

import unittest

from csv_xlsx_editor.domain import CellData, WorkbookDocument, WorksheetDocument


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


if __name__ == "__main__":
    unittest.main()

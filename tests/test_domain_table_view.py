"""Tests for worksheet table view coordinate mapping."""

import unittest

from csv_xlsx_editor.domain import TableView, WorksheetDocument


class TableViewTests(unittest.TestCase):
    """Verify source/UI coordinate invariants."""

    def test_default_view_uses_zero_based_sources_and_one_based_row_ids(self) -> None:
        view = TableView.from_dimensions(row_count=3, column_count=2)

        self.assertEqual(view.visible_source_rows, [0, 1, 2])
        self.assertEqual(view.visible_source_columns, [0, 1])
        self.assertEqual(view.row_id_for_ui(0), 1)
        self.assertEqual(view.row_id_for_ui(2), 3)

    def test_ui_column_zero_is_index_column(self) -> None:
        view = TableView.from_dimensions(row_count=1, column_count=2)

        with self.assertRaises(ValueError):
            view.source_column_for_ui(0)

        self.assertEqual(view.source_column_for_ui(1), 0)
        self.assertEqual(view.source_column_for_ui(2), 1)

    def test_worksheet_rebuild_creates_expected_view(self) -> None:
        worksheet = WorksheetDocument(sheet_id="sheet-1", title="Sheet 1")
        worksheet.set_cell(0, 0, "A")
        worksheet.set_cell(1, 0, "B")

        self.assertEqual(worksheet.get_display_rows(), [0, 1])
        self.assertEqual(worksheet.table_view.source_row_for_ui(1), 1)
        self.assertEqual(worksheet.table_view.source_column_for_ui(1), 0)


if __name__ == "__main__":
    unittest.main()

"""Tests for sheet UI coordinate mapping and matrix generation."""

import unittest

from csv_xlsx_editor.domain import FilterState, SortState, WorksheetDocument
from csv_xlsx_editor.ui.sheet_mapping import (
    INDEX_COLUMN_HEADER,
    SheetCoordinateMapper,
    SheetMatrixBuilder,
)


class SheetCoordinateMappingTests(unittest.TestCase):
    """Verify index-column and source-coordinate invariants for sheet UI."""

    def make_worksheet(self) -> WorksheetDocument:
        """Build a small worksheet with predictable row and column values."""
        worksheet = WorksheetDocument(sheet_id="sheet-1", title="Sheet 1")
        worksheet.set_cell(0, 0, "Charlie")
        worksheet.set_cell(0, 1, "Paris")
        worksheet.set_cell(1, 0, "Alice")
        worksheet.set_cell(1, 1, "Berlin")
        worksheet.set_cell(2, 0, "Bob")
        worksheet.set_cell(2, 1, "London")
        return worksheet

    def test_matrix_includes_read_only_index_column(self) -> None:
        worksheet = self.make_worksheet()
        builder = SheetMatrixBuilder(worksheet)

        self.assertEqual(builder.headers(), [INDEX_COLUMN_HEADER, "A", "B"])
        self.assertEqual(
            builder.matrix(),
            [
                [1, "Charlie", "Paris"],
                [2, "Alice", "Berlin"],
                [3, "Bob", "London"],
            ],
        )

    def test_matrix_uses_loaded_column_headers(self) -> None:
        worksheet = self.make_worksheet()
        worksheet.set_headers(["name", "city"])
        builder = SheetMatrixBuilder(worksheet)

        self.assertEqual(builder.headers(), [INDEX_COLUMN_HEADER, "name", "city"])

    def test_mapper_rejects_index_column_as_source_cell(self) -> None:
        mapper = SheetCoordinateMapper(self.make_worksheet())

        self.assertTrue(mapper.is_index_column(0))
        with self.assertRaises(ValueError):
            mapper.to_source_cell(0, 0)

    def test_mapper_converts_ui_data_column_to_source_cell(self) -> None:
        mapper = SheetCoordinateMapper(self.make_worksheet())

        self.assertEqual(mapper.to_source_cell(1, 1), (1, 0))
        self.assertEqual(mapper.to_source_cell(1, 2), (1, 1))

    def test_mapper_handles_sorted_visible_rows(self) -> None:
        worksheet = self.make_worksheet()
        worksheet.apply_sort(SortState(column=0, direction="asc"))
        mapper = SheetCoordinateMapper(worksheet)
        builder = SheetMatrixBuilder(worksheet)

        self.assertEqual(worksheet.get_display_rows(), [1, 2, 0])
        self.assertEqual(builder.matrix()[0], [2, "Alice", "Berlin"])
        self.assertEqual(mapper.to_source_cell(0, 1), (1, 0))
        self.assertEqual(mapper.from_source_cell(2, 1), (1, 2))

    def test_matrix_uses_filtered_visible_rows_but_keeps_original_row_ids(self) -> None:
        worksheet = self.make_worksheet()
        filters = FilterState()
        filters.set_filter(1, {"Berlin"}, include_blanks=False)
        worksheet.apply_filter(filters)

        self.assertEqual(SheetMatrixBuilder(worksheet).matrix(), [[2, "Alice", "Berlin"]])

    def test_column_labels_continue_after_z(self) -> None:
        worksheet = WorksheetDocument(sheet_id="sheet-1", title="Sheet 1", max_row=1, max_column=28)
        worksheet.rebuild_view()

        headers = SheetMatrixBuilder(worksheet).headers()

        self.assertEqual(headers[1], "A")
        self.assertEqual(headers[26], "Z")
        self.assertEqual(headers[27], "AA")
        self.assertEqual(headers[28], "AB")


if __name__ == "__main__":
    unittest.main()

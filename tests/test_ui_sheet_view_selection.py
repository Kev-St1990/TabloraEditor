"""Tests for selection-aware copy helpers in the sheet view."""

from dataclasses import dataclass
import unittest

from tablora.domain import WorksheetDocument
from tablora.ui.sheet_mapping import SheetCoordinateMapper
from tablora.ui.sheet_view import SheetView


@dataclass
class FakeSheet:
    """Minimal tksheet double that returns selected cells."""

    cells: list[tuple[int, int]]

    def get_selected_cells(self) -> list[tuple[int, int]]:
        return self.cells


class SheetViewSelectionTests(unittest.TestCase):
    """Verify that selected cells are copied instead of the whole sheet."""

    def test_selected_source_matrix_uses_only_selected_cells(self) -> None:
        worksheet = WorksheetDocument(sheet_id="sheet-1", title="Sheet 1")
        worksheet.set_cell(0, 0, "A")
        worksheet.set_cell(0, 1, "B")
        worksheet.set_cell(1, 0, "C")
        worksheet.set_cell(1, 1, "D")

        sheet_view = SheetView.__new__(SheetView)
        sheet_view.worksheet = worksheet
        sheet_view.mapper = SheetCoordinateMapper(worksheet)
        sheet_view.sheet = FakeSheet(cells=[(0, 1), (1, 1)])

        self.assertEqual(sheet_view.get_selected_source_matrix(), [["A"], ["C"]])
        self.assertEqual(sheet_view.get_selected_source_start_cell(), (0, 0))


if __name__ == "__main__":
    unittest.main()

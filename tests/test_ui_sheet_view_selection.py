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
    rows: list[int] | None = None
    columns: list[int] | None = None
    current: tuple[int, int] | None = None
    selected_row_calls: list[int] | None = None

    def get_selected_cells(self) -> list[tuple[int, int]]:
        return self.cells

    def get_selected_rows(self) -> list[int]:
        return self.rows or []

    def get_selected_columns(self) -> list[int]:
        return self.columns or []

    def get_currently_selected(self):
        if self.current is None:
            return None

        @dataclass
        class Selection:
            row: int
            column: int

        return Selection(*self.current)

    def select_row(self, row: int) -> None:
        if self.selected_row_calls is None:
            self.selected_row_calls = []
        self.selected_row_calls.append(row)


@dataclass
class FakeEvent:
    x: int
    y: int


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

    def test_selected_source_rows_and_columns_respect_hidden_state(self) -> None:
        worksheet = WorksheetDocument(sheet_id="sheet-1", title="Sheet 1")
        worksheet.set_cell(0, 0, "A")
        worksheet.set_cell(0, 1, "B")
        worksheet.set_cell(1, 0, "C")
        worksheet.set_cell(1, 1, "D")
        worksheet.hide_columns([0])

        sheet_view = SheetView.__new__(SheetView)
        sheet_view.worksheet = worksheet
        sheet_view.mapper = SheetCoordinateMapper(worksheet)
        sheet_view.sheet = FakeSheet(cells=[], rows=[0], columns=[1])

        self.assertEqual(sheet_view.get_selected_source_rows(), [0])
        self.assertEqual(sheet_view.get_selected_source_columns(), [1])

    def test_selected_source_rows_fall_back_to_selected_cells(self) -> None:
        worksheet = WorksheetDocument(sheet_id="sheet-1", title="Sheet 1")
        worksheet.set_cell(0, 0, "A")
        worksheet.set_cell(1, 0, "B")
        worksheet.set_cell(2, 0, "C")

        sheet_view = SheetView.__new__(SheetView)
        sheet_view.worksheet = worksheet
        sheet_view.mapper = SheetCoordinateMapper(worksheet)
        sheet_view.sheet = FakeSheet(cells=[(0, 1), (1, 1), (2, 1)], rows=[], columns=[])

        self.assertEqual(sheet_view.get_selected_source_rows(), [0, 1, 2])

    def test_clicking_id_column_promotes_selection_to_full_row(self) -> None:
        worksheet = WorksheetDocument(sheet_id="sheet-1", title="Sheet 1")
        worksheet.set_cell(0, 0, "A")
        worksheet.set_cell(1, 0, "B")

        sheet_view = SheetView.__new__(SheetView)
        sheet_view.worksheet = worksheet
        sheet_view.mapper = SheetCoordinateMapper(worksheet)
        sheet_view.sheet = FakeSheet(cells=[], current=(1, 0), selected_row_calls=[])

        sheet_view._promote_index_selection_to_row()

        self.assertEqual(sheet_view.sheet.selected_row_calls, [1])

    def test_press_in_id_column_selects_row(self) -> None:
        worksheet = WorksheetDocument(sheet_id="sheet-1", title="Sheet 1")
        worksheet.set_cell(0, 0, "A")
        worksheet.set_cell(1, 0, "B")

        class EventAwareSheet(FakeSheet):
            def identify_row(self, y: int) -> int:
                return 1

            def identify_col(self, x: int) -> int:
                return 0

        sheet_view = SheetView.__new__(SheetView)
        sheet_view.worksheet = worksheet
        sheet_view.mapper = SheetCoordinateMapper(worksheet)
        sheet_view.sheet = EventAwareSheet(cells=[], current=None, selected_row_calls=[])

        result = sheet_view._on_primary_press(FakeEvent(x=5, y=20))

        self.assertIsNone(result)
        self.assertEqual(sheet_view.sheet.selected_row_calls, [1])

    def test_ui_cell_from_event_accepts_tksheet_style_identify_methods(self) -> None:
        worksheet = WorksheetDocument(sheet_id="sheet-1", title="Sheet 1")
        worksheet.set_cell(0, 0, "A")

        class EventObjectSheet(FakeSheet):
            def identify_row(self, event: object) -> int:
                return 0 if hasattr(event, "y") else -1

            def identify_col(self, event: object) -> int:
                return 0 if hasattr(event, "x") else -1

        sheet_view = SheetView.__new__(SheetView)
        sheet_view.worksheet = worksheet
        sheet_view.mapper = SheetCoordinateMapper(worksheet)
        sheet_view.sheet = EventObjectSheet(cells=[])

        self.assertEqual(sheet_view._ui_cell_from_event(FakeEvent(x=5, y=20)), (0, 0))


if __name__ == "__main__":
    unittest.main()

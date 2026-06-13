"""Tests for header sort, filter, and autosize interactions."""

import unittest
from dataclasses import dataclass, field

from csv_xlsx_editor.actions import UndoRedoManager
from csv_xlsx_editor.domain import FilterState, SortState, WorksheetDocument
from csv_xlsx_editor.ui.filter_popup import FilterPopupState
from csv_xlsx_editor.ui.header_controller import HeaderController


@dataclass
class RecordingSheetView:
    """Minimal sheet-view double used to verify controller side effects."""

    refreshed: int = 0
    widths: list[tuple[int, int]] = field(default_factory=list)

    def refresh(self) -> None:
        self.refreshed += 1

    def set_column_width(self, column: int, width: int) -> None:
        self.widths.append((column, width))


class HeaderControllerTests(unittest.TestCase):
    """Verify sort, filter, and autosize behavior."""

    def make_worksheet(self) -> WorksheetDocument:
        worksheet = WorksheetDocument(sheet_id="sheet-1", title="Sheet 1")
        worksheet.set_cell(0, 0, "Charlie")
        worksheet.set_cell(0, 1, "Paris")
        worksheet.set_cell(1, 0, "Alice")
        worksheet.set_cell(1, 1, "Berlin")
        worksheet.set_cell(2, 0, "Bob")
        worksheet.set_cell(2, 1, "London")
        return worksheet

    def test_left_click_cycles_sort_state(self) -> None:
        worksheet = self.make_worksheet()
        sheet_view = RecordingSheetView()
        controller = HeaderController(
            worksheet=worksheet,
            undo_redo_manager=UndoRedoManager(),
            sheet_view=sheet_view,
        )

        self.assertEqual(controller.on_left_click_header(1), SortState(column=0, direction="asc"))
        self.assertEqual(worksheet.sort_state, SortState(column=0, direction="asc"))
        self.assertEqual(controller.on_left_click_header(1), SortState(column=0, direction="desc"))
        self.assertIsNone(controller.on_left_click_header(1))
        self.assertEqual(sheet_view.refreshed, 3)

    def test_left_click_ignores_index_column(self) -> None:
        controller = HeaderController(worksheet=self.make_worksheet())
        self.assertIsNone(controller.on_left_click_header(0))

    def test_right_click_builds_filter_popup_state(self) -> None:
        worksheet = self.make_worksheet()
        filters = FilterState()
        filters.set_filter(0, {"Alice"}, include_blanks=False, search_text="Al")
        worksheet.apply_filter(filters)
        controller = HeaderController(worksheet=worksheet)

        popup_state = controller.on_right_click_header(1)

        self.assertIsInstance(popup_state, FilterPopupState)
        self.assertEqual(popup_state.column, 0)
        self.assertEqual(popup_state.values, ["Charlie", "Alice", "Bob"])
        self.assertEqual(popup_state.selected_values, {"Alice"})
        self.assertEqual(popup_state.search_text, "Al")
        self.assertFalse(popup_state.include_blanks)
        self.assertTrue(popup_state.visible_values())

    def test_apply_filter_popup_state_filters_rows_and_supports_undo(self) -> None:
        workbook_worksheet = self.make_worksheet()
        controller = HeaderController(
            worksheet=workbook_worksheet,
            undo_redo_manager=UndoRedoManager(),
        )

        popup_state = FilterPopupState(
            column=0,
            values=["Charlie", "Alice", "Bob"],
            selected_values={"Alice"},
            include_blanks=False,
            search_text="Al",
        )
        filter_state = controller.apply_filter_popup_state(popup_state)

        self.assertEqual(workbook_worksheet.get_display_rows(), [1])
        self.assertEqual(filter_state.column_filters[0].allowed_values, {"Alice"})
        self.assertEqual(filter_state.column_filters[0].search_text, "Al")
        self.assertFalse(controller.undo_redo_manager.can_redo())
        self.assertTrue(controller.undo_redo_manager.can_undo())

        controller.undo_redo_manager.undo()
        self.assertEqual(workbook_worksheet.get_display_rows(), [0, 1, 2])

    def test_apply_column_value_sort_sorts_values_without_reordering_rows(self) -> None:
        worksheet = self.make_worksheet()
        controller = HeaderController(
            worksheet=worksheet,
            undo_redo_manager=UndoRedoManager(),
        )

        controller.apply_column_value_sort(0, reverse=False)

        self.assertEqual(
            [worksheet.get_cell(row, 0).value for row in range(3)],
            ["Alice", "Bob", "Charlie"],
        )
        self.assertEqual(worksheet.get_display_rows(), [0, 1, 2])

    def test_autosize_uses_visible_values_and_header_text(self) -> None:
        worksheet = self.make_worksheet()
        sheet_view = RecordingSheetView()
        controller = HeaderController(worksheet=worksheet, sheet_view=sheet_view)

        width = controller.on_double_click_column_boundary(1)

        self.assertEqual(width, len("Charlie") + 2)
        self.assertEqual(sheet_view.widths, [(1, width)])

    def test_popup_state_search_filters_values(self) -> None:
        popup_state = FilterPopupState(
            column=0,
            values=["Charlie", "Alice", "Bob"],
            selected_values={"Alice"},
            include_blanks=False,
            search_text="li",
        )

        self.assertEqual(popup_state.visible_values(), ["Charlie", "Alice"])
        popup_state.select_none()
        self.assertEqual(popup_state.selected_values, set())
        popup_state.select_all()
        self.assertEqual(popup_state.selected_values, {"Charlie", "Alice", "Bob"})


if __name__ == "__main__":
    unittest.main()

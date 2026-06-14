"""Tests for worksheet sorting."""

import unittest

from tablora.domain import SortState, WorksheetDocument, first_sort_for_column


class SortStateTests(unittest.TestCase):
    """Verify sort state transitions and sorted table views."""

    def test_header_click_cycle(self) -> None:
        ascending = first_sort_for_column(1)
        descending = ascending.next_for_column(1)

        self.assertEqual(ascending, SortState(column=1, direction="asc"))
        self.assertEqual(descending, SortState(column=1, direction="desc"))
        self.assertIsNone(descending.next_for_column(1))
        self.assertEqual(descending.next_for_column(2), SortState(column=2, direction="asc"))

    def test_worksheet_sort_changes_view_not_cell_storage(self) -> None:
        worksheet = WorksheetDocument(sheet_id="sheet-1", title="Sheet 1")
        worksheet.set_cell(0, 0, "Charlie")
        worksheet.set_cell(1, 0, "Alice")
        worksheet.set_cell(2, 0, "Bob")

        worksheet.apply_sort(SortState(column=0, direction="asc"))

        self.assertEqual(worksheet.get_display_rows(), [1, 2, 0])
        self.assertEqual(worksheet.get_cell(0, 0).value, "Charlie")

        worksheet.apply_sort(SortState(column=0, direction="desc"))
        self.assertEqual(worksheet.get_display_rows(), [0, 2, 1])


if __name__ == "__main__":
    unittest.main()

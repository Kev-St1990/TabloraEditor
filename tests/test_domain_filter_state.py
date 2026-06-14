"""Tests for worksheet filtering."""

import unittest

from tablora.domain import FilterState, WorksheetDocument


class FilterStateTests(unittest.TestCase):
    """Verify filter state and worksheet view integration."""

    def test_filter_state_matches_allowed_values(self) -> None:
        filters = FilterState()
        filters.set_filter(0, {"Berlin", "Paris"}, include_blanks=False)

        self.assertTrue(filters.matches(["Berlin"]))
        self.assertFalse(filters.matches(["London"]))
        self.assertFalse(filters.matches([""]))

    def test_filter_state_can_include_blanks(self) -> None:
        filters = FilterState()
        filters.set_filter(0, {"Berlin"}, include_blanks=True)

        self.assertTrue(filters.matches([""]))
        self.assertTrue(filters.matches([None]))

    def test_worksheet_filter_rebuilds_visible_rows_without_deleting_data(self) -> None:
        worksheet = WorksheetDocument(sheet_id="sheet-1", title="Sheet 1")
        worksheet.set_cell(0, 0, "Berlin")
        worksheet.set_cell(1, 0, "London")
        worksheet.set_cell(2, 0, "Berlin")

        filters = FilterState()
        filters.set_filter(0, {"Berlin"}, include_blanks=False)
        worksheet.apply_filter(filters)

        self.assertEqual(worksheet.get_display_rows(), [0, 2])
        self.assertEqual(worksheet.get_cell(1, 0).value, "London")

        filters.clear_all()
        worksheet.apply_filter(filters)
        self.assertEqual(worksheet.get_display_rows(), [0, 1, 2])


if __name__ == "__main__":
    unittest.main()

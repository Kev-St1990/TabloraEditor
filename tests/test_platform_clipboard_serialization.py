"""Tests for Excel-compatible clipboard serialization and paste."""

import unittest
from unittest.mock import patch

from tablora.domain import WorksheetDocument
from tablora.platform import ClipboardService, InMemoryClipboardBackend, TkClipboardBackend


class ClipboardServiceTests(unittest.TestCase):
    """Verify TSV clipboard behavior."""

    def test_serialize_uses_tabs_and_crlf(self) -> None:
        service = ClipboardService(InMemoryClipboardBackend())

        text = service.serialize_tsv([["A", "B"], ["C", None]])

        self.assertEqual(text, "A\tB\r\nC\t")

    def test_serialize_formats_numbers_with_locale_decimal_separator(self) -> None:
        service = ClipboardService(InMemoryClipboardBackend())

        with patch("locale.localeconv", return_value={"decimal_point": ","}):
            text = service.serialize_tsv([[0.117318, 606.060606, 1.0, "ID-1"]])

        self.assertEqual(text, "0,117318\t606,060606\t1\tID-1")

    def test_parse_normalizes_newlines(self) -> None:
        service = ClipboardService(InMemoryClipboardBackend())

        matrix = service.parse_tsv("A\tB\r\nC\tD\rE\tF")

        self.assertEqual(matrix, [["A", "B"], ["C", "D"], ["E", "F"]])

    def test_copy_and_paste_roundtrip_via_backend(self) -> None:
        backend = InMemoryClipboardBackend()
        service = ClipboardService(backend)

        copied = service.copy_cells([["A", "B"], ["C", "D"]])
        pasted = service.paste_cells()

        self.assertEqual(copied, "A\tB\r\nC\tD")
        self.assertEqual(backend.text, "A\tB\r\nC\tD")
        self.assertEqual(pasted, [["A", "B"], ["C", "D"]])

    def test_tk_clipboard_backend_uses_tk_apis(self) -> None:
        class FakeRoot:
            def __init__(self) -> None:
                self.text = ""
                self.cleared = False
                self.updated = False

            def clipboard_clear(self) -> None:
                self.cleared = True
                self.text = ""

            def clipboard_append(self, text: str) -> None:
                self.text = text

            def clipboard_get(self) -> str:
                return self.text

            def update_idletasks(self) -> None:
                self.updated = True

        root = FakeRoot()
        backend = TkClipboardBackend(root)

        backend.set_text("A\tB")

        self.assertTrue(root.cleared)
        self.assertTrue(root.updated)
        self.assertEqual(backend.get_text(), "A\tB")

    def test_paste_into_matrix_expands_target_and_preserves_existing_content(self) -> None:
        service = ClipboardService(InMemoryClipboardBackend())

        result = service.paste_into_matrix(
            [["keep", "x"], ["y", "z"]],
            start_row=1,
            start_column=1,
            source=[["A", "B"], ["C", "D"]],
        )

        self.assertEqual(
            result,
            [
                ["keep", "x"],
                ["y", "A", "B"],
                ["", "C", "D"],
            ],
        )

    def test_paste_into_worksheet_writes_rectangular_range(self) -> None:
        worksheet = WorksheetDocument(sheet_id="sheet-1", title="Sheet 1")
        worksheet.set_cell(0, 0, "old")
        worksheet.set_cell(0, 1, "stay")

        ClipboardService(InMemoryClipboardBackend()).paste_into_worksheet(
            worksheet,
            start_row=0,
            start_column=0,
            source=[["A", "B"], ["C", "D"]],
        )

        self.assertEqual(worksheet.get_cell(0, 0).value, "A")
        self.assertEqual(worksheet.get_cell(0, 1).value, "B")
        self.assertEqual(worksheet.get_cell(1, 0).value, "C")
        self.assertEqual(worksheet.get_cell(1, 1).value, "D")
        self.assertEqual(worksheet.get_display_rows(), [0, 1])


if __name__ == "__main__":
    unittest.main()

"""Tests for Excel-compatible clipboard serialization and paste."""

import unittest

from tablora.domain import WorksheetDocument
from tablora.platform import ClipboardService, InMemoryClipboardBackend


class ClipboardServiceTests(unittest.TestCase):
    """Verify TSV clipboard behavior."""

    def test_serialize_uses_tabs_and_crlf(self) -> None:
        service = ClipboardService(InMemoryClipboardBackend())

        text = service.serialize_tsv([["A", "B"], ["C", None]])

        self.assertEqual(text, "A\tB\r\nC\t")

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

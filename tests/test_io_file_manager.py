"""Tests for the file manager facade."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from csv_xlsx_editor.io import FileManager, UnsupportedFileTypeError


class FileManagerTests(unittest.TestCase):
    """Verify file type detection and adapter routing."""

    def test_detects_supported_file_types(self) -> None:
        manager = FileManager()

        self.assertEqual(manager.detect_file_type("data.csv"), "csv")
        self.assertEqual(manager.detect_file_type("data.xlsx"), "xlsx")
        self.assertEqual(manager.detect_file_type("data.xlsm"), "xlsm")

    def test_rejects_unsupported_file_type(self) -> None:
        with self.assertRaises(UnsupportedFileTypeError):
            FileManager().detect_file_type("data.txt")

    def test_open_routes_csv(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "data.csv"
            path.write_text("A,B\n", encoding="utf-8-sig")

            document = FileManager().open(path)

            self.assertEqual(document.file_type, "csv")
            self.assertEqual(document.get_active_sheet().get_cell(0, 0).value, "A")


if __name__ == "__main__":
    unittest.main()

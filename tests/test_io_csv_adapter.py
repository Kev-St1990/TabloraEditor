"""Tests for CSV loading and saving."""

import csv
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tablora.domain import FilterState, SortState
from tablora.io import CsvAdapter


class CsvAdapterTests(unittest.TestCase):
    """Verify CSV dialect detection and document roundtrips."""

    def test_sniffs_semicolon_delimiter(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "sample.csv"
            path.write_text("name;city\nAda;Berlin\n", encoding="utf-8-sig")

            dialect = CsvAdapter().sniff_dialect(path)

            self.assertEqual(dialect.delimiter, ";")

    def test_load_uses_manual_delimiter_override(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "sample.csv"
            path.write_text("name|city\nAda|Berlin\n", encoding="utf-8-sig")

            document = CsvAdapter().load(path, delimiter="|")

            sheet = document.get_active_sheet()
            self.assertEqual(document.csv_delimiter, "|")
            self.assertEqual(sheet.column_headers, ["name", "city"])
            self.assertEqual(sheet.get_cell(0, 1).value, "Berlin")

    def test_save_materializes_sort_but_not_filter(self) -> None:
        with TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "source.csv"
            target = Path(temp_dir) / "target.csv"
            source.write_text("name,city\nCharlie,Paris\nAlice,Berlin\nBob,London\n", encoding="utf-8-sig")

            adapter = CsvAdapter()
            document = adapter.load(source)
            sheet = document.get_active_sheet()
            sheet.apply_sort(SortState(column=0, direction="asc"))
            filters = FilterState()
            filters.set_filter(1, {"Berlin"}, include_blanks=False)
            sheet.apply_filter(filters)

            adapter.save(document, target)

            with target.open(encoding="utf-8-sig", newline="") as file:
                rows = list(csv.reader(file))

            self.assertEqual(
                rows,
                [
                    ["name", "city"],
                    ["Alice", "Berlin"],
                    ["Bob", "London"],
                    ["Charlie", "Paris"],
                ],
            )

    def test_save_materializes_date_sort_order(self) -> None:
        with TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "dates.csv"
            target = Path(temp_dir) / "dates_sorted.csv"
            source.write_text(
                "date\n31.12.2024\n2024-01-02\n15/01/2024 08:30\n",
                encoding="utf-8-sig",
            )

            adapter = CsvAdapter()
            document = adapter.load(source)
            sheet = document.get_active_sheet()
            sheet.apply_sort(SortState(column=0, direction="asc"))

            adapter.save(document, target)

            with target.open(encoding="utf-8-sig", newline="") as file:
                rows = list(csv.reader(file))

            self.assertEqual(
                rows,
                [
                    ["date"],
                    ["2024-01-02"],
                    ["15/01/2024 08:30"],
                    ["31.12.2024"],
                ],
            )


if __name__ == "__main__":
    unittest.main()

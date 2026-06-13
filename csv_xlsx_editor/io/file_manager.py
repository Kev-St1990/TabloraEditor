"""Current file loading placeholder for CSV and XLSX files."""

import csv
from pathlib import Path
from typing import Any

from openpyxl import load_workbook


class FileManager:
    """Loads spreadsheet data through the existing minimal IO surface.

    This placeholder keeps the original behavior available while later steps
    introduce dedicated CSV, XLSX, and XLSM adapters.
    """

    def load_csv(self, path: str | Path, delimiter: str = ";") -> list[list[str]]:
        """Load a CSV file with the given delimiter."""
        with open(path, encoding="utf-8-sig", newline="") as file:
            return list(csv.reader(file, delimiter=delimiter))

    def load_xlsx(self, path: str | Path) -> Any:
        """Load an XLSX workbook with openpyxl."""
        return load_workbook(path)

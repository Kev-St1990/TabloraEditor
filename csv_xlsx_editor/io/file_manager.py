"""File manager facade for CSV, XLSX, and XLSM documents."""

from pathlib import Path

from csv_xlsx_editor.domain import FileType, WorkbookDocument
from csv_xlsx_editor.io.csv_adapter import CsvAdapter
from csv_xlsx_editor.io.exceptions import UnsupportedFileTypeError
from csv_xlsx_editor.io.xlsx_adapter import XlsxAdapter


class FileManager:
    """Routes file operations to the appropriate format adapter."""

    def __init__(
        self,
        csv_adapter: CsvAdapter | None = None,
        xlsx_adapter: XlsxAdapter | None = None,
    ) -> None:
        self.csv_adapter = csv_adapter or CsvAdapter()
        self.xlsx_adapter = xlsx_adapter or XlsxAdapter()

    def open(self, path: str | Path, *, csv_delimiter: str | None = None) -> WorkbookDocument:
        """Open a supported file as a workbook document."""
        file_type = self.detect_file_type(path)
        if file_type == "csv":
            return self.csv_adapter.load(path, delimiter=csv_delimiter)
        return self.xlsx_adapter.load(path)

    def save(
        self,
        document: WorkbookDocument,
        path: str | Path | None = None,
        *,
        csv_delimiter: str | None = None,
    ) -> None:
        """Save a workbook document to its current or provided path."""
        target_path = Path(path or document.path or "")
        if not str(target_path):
            raise UnsupportedFileTypeError("A target path is required for saving.")

        file_type = self.detect_file_type(target_path)
        if file_type == "csv":
            self.csv_adapter.save(document, target_path, delimiter=csv_delimiter)
            return
        self.xlsx_adapter.save(document, target_path)

    def detect_file_type(self, path: str | Path) -> FileType:
        """Detect a supported file type from a path suffix."""
        suffix = Path(path).suffix.lower()
        if suffix == ".csv":
            return "csv"
        if suffix == ".xlsx":
            return "xlsx"
        if suffix == ".xlsm":
            return "xlsm"
        raise UnsupportedFileTypeError(f"Unsupported file type: {suffix or '<none>'}")

"""Clipboard helpers for Excel-compatible tab-separated copy and paste."""

from dataclasses import dataclass
from typing import Protocol

from csv_xlsx_editor.domain import WorksheetDocument


class ClipboardBackend(Protocol):
    """Minimal clipboard backend abstraction used by the service."""

    def get_text(self) -> str: ...

    def set_text(self, text: str) -> None: ...


@dataclass(slots=True)
class InMemoryClipboardBackend:
    """Simple clipboard backend for tests and non-GUI usage."""

    text: str = ""

    def get_text(self) -> str:
        return self.text

    def set_text(self, text: str) -> None:
        self.text = text


class ClipboardService:
    """Serializes and parses Excel-style TSV clipboard content."""

    def __init__(self, backend: ClipboardBackend | None = None) -> None:
        self.backend = backend or InMemoryClipboardBackend()

    def copy_cells(self, matrix: list[list[object]]) -> str:
        """Serialize a matrix as Excel-compatible TSV and store it in the clipboard."""
        text = self.serialize_tsv(matrix)
        self.backend.set_text(text)
        return text

    def paste_cells(self) -> list[list[str]]:
        """Read clipboard text and parse it into a rectangular matrix."""
        return self.parse_tsv(self.backend.get_text())

    def serialize_tsv(self, matrix: list[list[object]]) -> str:
        """Serialize a matrix to TSV using CRLF line endings.

        Empty cells are preserved as empty fields, matching spreadsheet
        clipboard expectations.
        """
        rows = []
        for row in matrix:
            rows.append("\t".join("" if value is None else str(value) for value in row))
        return "\r\n".join(rows)

    def parse_tsv(self, text: str) -> list[list[str]]:
        """Parse TSV text from the clipboard into a row-major matrix."""
        if not text:
            return []
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        return [line.split("\t") for line in normalized.split("\n")]

    def paste_into_matrix(
        self,
        target: list[list[object]],
        start_row: int,
        start_column: int,
        source: list[list[object]],
    ) -> list[list[object]]:
        """Return a new matrix with `source` pasted into `target`.

        The target matrix is expanded as needed and existing content outside the
        pasted area is preserved.
        """
        if not source:
            return [row[:] for row in target]

        result = [row[:] for row in target]
        required_rows = start_row + len(source)
        while len(result) < required_rows:
            result.append([])

        for row_offset, source_row in enumerate(source):
            target_row_index = start_row + row_offset
            target_row = result[target_row_index]
            required_columns = start_column + len(source_row)
            while len(target_row) < required_columns:
                target_row.append("")
            for column_offset, value in enumerate(source_row):
                target_row[start_column + column_offset] = value
        return result

    def paste_into_worksheet(
        self,
        worksheet: WorksheetDocument,
        start_row: int,
        start_column: int,
        source: list[list[object]],
    ) -> None:
        """Paste a source matrix directly into a worksheet document."""
        worksheet.set_cells(start_row, start_column, source)

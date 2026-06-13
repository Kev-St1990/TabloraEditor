"""CSV adapter for workbook documents."""

import csv
from dataclasses import dataclass
from pathlib import Path

from csv_xlsx_editor.domain import WorkbookDocument, WorksheetDocument


@dataclass(frozen=True, slots=True)
class CsvDialect:
    """Small serializable subset of a detected CSV dialect."""

    delimiter: str = ","
    quotechar: str = '"'


class CsvAdapter:
    """Loads and saves CSV files as single-sheet workbook documents."""

    def load(
        self,
        path: str | Path,
        *,
        encoding: str = "utf-8-sig",
        delimiter: str | None = None,
    ) -> WorkbookDocument:
        """Load a CSV file into a single `WorksheetDocument`.

        If `delimiter` is omitted, the adapter uses `csv.Sniffer` and falls
        back to comma when detection fails.
        """
        file_path = Path(path)
        dialect = self.sniff_dialect(file_path, encoding=encoding)
        selected_delimiter = delimiter or dialect.delimiter

        worksheet = WorksheetDocument(
            sheet_id="csv-1",
            title=file_path.stem or "CSV",
            source_sheet_name=file_path.stem or "CSV",
        )
        with file_path.open(encoding=encoding, newline="") as file:
            reader = csv.reader(file, delimiter=selected_delimiter, quotechar=dialect.quotechar)
            rows = list(reader)

        if rows:
            header_row = rows[0]
            worksheet.set_headers(header_row)
            data_rows = rows[1:]
        else:
            data_rows = []

        for row_index, row in enumerate(data_rows):
            for column_index, value in enumerate(row):
                worksheet.set_cell(row_index, column_index, value)
            worksheet.max_column = max(worksheet.max_column, len(row))
        worksheet.max_row = len(data_rows)
        worksheet.rebuild_view()

        return WorkbookDocument(
            path=file_path,
            file_type="csv",
            worksheets=[worksheet],
            csv_delimiter=selected_delimiter,
        )

    def save(
        self,
        document: WorkbookDocument,
        path: str | Path,
        *,
        delimiter: str | None = None,
        encoding: str = "utf-8-sig",
    ) -> None:
        """Save a workbook document as CSV.

        CSV output never includes the UI-only index column. Active sort state is
        materialized; active filters do not remove rows from the saved file.
        """
        file_path = Path(path)
        worksheet = document.get_active_sheet()
        selected_delimiter = delimiter or document.csv_delimiter or ","

        with file_path.open("w", encoding=encoding, newline="") as file:
            writer = csv.writer(file, delimiter=selected_delimiter)
            if worksheet.column_headers:
                writer.writerow([worksheet.column_headers[column] if column < len(worksheet.column_headers) else "" for column in range(worksheet.max_column)])
            for source_row in self._save_row_order(worksheet):
                writer.writerow(
                    [
                        worksheet.get_cell(source_row, source_column).value
                        for source_column in range(worksheet.max_column)
                    ]
                )

        document.path = file_path
        document.csv_delimiter = selected_delimiter
        document.mark_clean()

    def sniff_dialect(self, path: str | Path, *, encoding: str = "utf-8-sig") -> CsvDialect:
        """Detect a CSV delimiter, falling back to comma."""
        sample = Path(path).read_text(encoding=encoding)[:4096]
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        except csv.Error:
            return CsvDialect()
        return CsvDialect(delimiter=dialect.delimiter, quotechar=dialect.quotechar)

    @staticmethod
    def _save_row_order(worksheet: WorksheetDocument) -> list[int]:
        if worksheet.sort_state is None:
            return list(range(worksheet.max_row))

        rows = list(range(worksheet.max_row))
        reverse = worksheet.sort_state.direction == "desc"
        column = worksheet.sort_state.column
        rows.sort(key=lambda row: WorksheetDocument._sort_key_for_cell(worksheet.get_cell(row, column)), reverse=reverse)
        return rows

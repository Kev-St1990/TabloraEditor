"""Testable mapping helpers for worksheet data shown in tksheet."""

from dataclasses import dataclass
from typing import Any

from tablora.domain import WorksheetDocument

INDEX_COLUMN_HEADER = "ID"


@dataclass(slots=True)
class SheetCoordinateMapper:
    """Maps between tksheet UI coordinates and source worksheet coordinates.

    UI column `0` is always the read-only row ID column. Data columns begin at
    UI column `1` and map to zero-based source columns through `TableView`.
    """

    worksheet: WorksheetDocument

    def is_index_column(self, ui_column: int) -> bool:
        """Return whether a UI column is the synthetic row ID column."""
        return ui_column == 0

    def to_source_cell(self, ui_row: int, ui_column: int) -> tuple[int, int]:
        """Convert a UI cell coordinate to a source worksheet coordinate."""
        if self.is_index_column(ui_column):
            raise ValueError("The row ID index column is read-only.")
        return (
            self.worksheet.table_view.source_row_for_ui(ui_row),
            self.worksheet.table_view.source_column_for_ui(ui_column),
        )

    def from_source_cell(self, source_row: int, source_column: int) -> tuple[int, int]:
        """Convert a source worksheet coordinate to a visible UI coordinate."""
        ui_row = self.worksheet.table_view.visible_source_rows.index(source_row)
        ui_column = self.worksheet.table_view.ui_column_for_source(source_column)
        return ui_row, ui_column


class SheetMatrixBuilder:
    """Builds headers and data matrices for tksheet from a worksheet document."""

    def __init__(self, worksheet: WorksheetDocument) -> None:
        self.worksheet = worksheet

    def headers(self) -> list[str]:
        """Return UI headers including the synthetic index column."""
        if self.worksheet.column_headers:
            headers = [str(self.worksheet.column_headers[source_column]) if source_column < len(self.worksheet.column_headers) else "" for source_column in self.worksheet.table_view.visible_source_columns]
        else:
            headers = [
                self._column_label(source_column)
                for source_column in self.worksheet.table_view.visible_source_columns
            ]
        return [INDEX_COLUMN_HEADER] + headers

    def matrix(self) -> list[list[Any]]:
        """Return visible worksheet data with the row ID as the first column."""
        rows: list[list[Any]] = []
        for ui_row, source_row in enumerate(self.worksheet.table_view.visible_source_rows):
            row = [self.worksheet.table_view.row_id_for_ui(ui_row)]
            row.extend(
                self.worksheet.get_cell(source_row, source_column).value
                for source_column in self.worksheet.table_view.visible_source_columns
            )
            rows.append(row)
        return rows

    @staticmethod
    def _column_label(source_column: int) -> str:
        """Return Excel-like column labels for zero-based source columns."""
        label = ""
        column = source_column + 1
        while column:
            column, remainder = divmod(column - 1, 26)
            label = chr(65 + remainder) + label
        return label

"""tksheet-backed worksheet view."""

from tkinter import Frame
from typing import Any

from csv_xlsx_editor.domain import WorksheetDocument
from csv_xlsx_editor.ui.sheet_mapping import SheetCoordinateMapper, SheetMatrixBuilder


class SheetView(Frame):
    """Displays one `WorksheetDocument` in a tksheet widget.

    The widget renders a synthetic read-only index column at UI column `0`.
    All source-coordinate conversions are delegated to `SheetCoordinateMapper`
    so the behavior remains unit-testable without a GUI.
    """

    def __init__(self, master: Any) -> None:
        super().__init__(master)
        from tksheet import Sheet

        self.worksheet: WorksheetDocument | None = None
        self.mapper: SheetCoordinateMapper | None = None
        self.sheet = Sheet(self, show_row_index=False)
        self.sheet.enable_bindings()
        self.sheet.pack(fill="both", expand=True)

    def load_worksheet(self, worksheet: WorksheetDocument) -> None:
        """Load a worksheet document and render its current table view."""
        self.worksheet = worksheet
        self.mapper = SheetCoordinateMapper(worksheet)
        self.refresh()

    def refresh(self) -> None:
        """Render the loaded worksheet into the tksheet widget."""
        if self.worksheet is None:
            self._set_sheet_data([], [])
            return

        builder = SheetMatrixBuilder(self.worksheet)
        self._set_sheet_data(builder.matrix(), builder.headers())

    def to_source_cell(self, ui_row: int, ui_column: int) -> tuple[int, int]:
        """Convert a UI cell coordinate to a source worksheet coordinate."""
        if self.mapper is None:
            raise RuntimeError("No worksheet is loaded.")
        return self.mapper.to_source_cell(ui_row, ui_column)

    def from_source_cell(self, source_row: int, source_column: int) -> tuple[int, int]:
        """Convert a source worksheet coordinate to a visible UI coordinate."""
        if self.mapper is None:
            raise RuntimeError("No worksheet is loaded.")
        return self.mapper.from_source_cell(source_row, source_column)

    def set_cell_from_ui(self, ui_row: int, ui_column: int, value: Any) -> None:
        """Set a source cell from a UI edit event and refresh the view."""
        if self.worksheet is None:
            raise RuntimeError("No worksheet is loaded.")
        source_row, source_column = self.to_source_cell(ui_row, ui_column)
        self.worksheet.set_cell(source_row, source_column, value)
        self.mapper = SheetCoordinateMapper(self.worksheet)
        self.refresh()

    def set_column_width(self, ui_column: int, width: int) -> None:
        """Set a visible UI column width when the underlying widget supports it."""
        for method_name in ("set_column_width", "column_width", "set_column_widths"):
            method = getattr(self.sheet, method_name, None)
            if callable(method):
                try:
                    method(ui_column, width)
                except TypeError:
                    try:
                        method(ui_column, width=width)
                    except TypeError:
                        continue
                break

    def _set_sheet_data(self, matrix: list[list[Any]], headers: list[str]) -> None:
        if hasattr(self.sheet, "set_sheet_data"):
            self.sheet.set_sheet_data(matrix, reset_col_positions=True, reset_row_positions=True)
        if hasattr(self.sheet, "headers"):
            self.sheet.headers(headers)

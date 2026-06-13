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

    def add_header_context_action(
        self,
        label: str,
        callback: Any,
        *,
        image: Any = "",
        compound: str | None = None,
        accelerator: str | None = None,
    ) -> None:
        """Register a header-only action in the sheet's context menu."""
        delete_command = getattr(self.sheet, "popup_menu_del_command", None)
        add_command = getattr(self.sheet, "popup_menu_add_command", None)
        if callable(delete_command):
            delete_command(label)
        if callable(add_command):
            add_command(
                label,
                callback,
                table_menu=False,
                index_menu=False,
                header_menu=True,
                empty_space_menu=False,
                image=image,
                compound=compound,
                accelerator=accelerator,
            )

    def set_builtin_header_sort_actions_enabled(self, enabled: bool) -> None:
        """Enable or disable tksheet's built-in header sort menu items."""
        mt = getattr(self.sheet, "MT", None)
        if mt is None:
            return
        if hasattr(mt, "rc_sort_column_enabled"):
            mt.rc_sort_column_enabled = enabled
        if hasattr(mt, "rc_sort_rows_enabled"):
            mt.rc_sort_rows_enabled = enabled

    def get_header_context_ui_column(self) -> int | None:
        """Return the header column targeted by the last context-menu invocation."""
        header = getattr(self.sheet, "CH", None)
        popup_menu_loc = getattr(header, "popup_menu_loc", None)
        if isinstance(popup_menu_loc, int):
            return popup_menu_loc
        return self.get_selected_ui_column()

    def get_selected_ui_column(self, *, default: int = 1) -> int | None:
        """Return the primary selected UI column, skipping the synthetic index column."""
        selected = getattr(self.sheet, "get_currently_selected", None)
        if callable(selected):
            current = selected()
            if current is not None:
                column = getattr(current, "column", None)
                if isinstance(column, int) and column > 0:
                    return column

        selected_columns = getattr(self.sheet, "get_selected_columns", None)
        if callable(selected_columns):
            columns = selected_columns()
            for column in columns or ():
                if isinstance(column, int) and column > 0:
                    return column

        if self.worksheet is None:
            return None
        if self.worksheet.max_column <= 0:
            return None
        return min(max(default, 1), self.worksheet.max_column)

    def _set_sheet_data(self, matrix: list[list[Any]], headers: list[str]) -> None:
        if hasattr(self.sheet, "set_sheet_data"):
            self.sheet.set_sheet_data(matrix, reset_col_positions=True, reset_row_positions=True)
        if hasattr(self.sheet, "headers"):
            self.sheet.headers(headers)

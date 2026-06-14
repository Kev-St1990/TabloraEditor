"""tksheet-backed worksheet view."""

from tkinter import Frame
from typing import Any

from tablora.domain import WorksheetDocument
from tablora.ui.sheet_mapping import SheetCoordinateMapper, SheetMatrixBuilder


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

    def get_selected_source_matrix(self) -> list[list[Any]]:
        """Return the currently selected source cells as a rectangular matrix.

        The synthetic index column is ignored. If the widget exposes only a
        single active cell instead of a full selection range, that cell is
        copied as a 1x1 matrix.
        """
        if self.worksheet is None or self.mapper is None:
            return []

        selected_cells = self._selected_ui_cells()
        if not selected_cells:
            current_cell = self._current_ui_cell()
            if current_cell is None:
                return []
            selected_cells = [current_cell]

        source_cells: list[tuple[int, int]] = []
        for ui_row, ui_column in selected_cells:
            if ui_column <= 0:
                continue
            try:
                source_cells.append(self.to_source_cell(ui_row, ui_column))
            except ValueError:
                continue

        if not source_cells:
            return []

        min_row = min(row for row, _ in source_cells)
        max_row = max(row for row, _ in source_cells)
        min_column = min(column for _, column in source_cells)
        max_column = max(column for _, column in source_cells)

        return [
            [self.worksheet.get_cell(source_row, source_column).value for source_column in range(min_column, max_column + 1)]
            for source_row in range(min_row, max_row + 1)
        ]

    def get_selected_source_start_cell(self) -> tuple[int, int] | None:
        """Return the top-left source cell of the current selection.

        This is used as the paste anchor. The synthetic index column is ignored.
        """
        if self.worksheet is None or self.mapper is None:
            return None

        selected_cells = self._selected_ui_cells()
        if not selected_cells:
            current_cell = self._current_ui_cell()
            if current_cell is None:
                return None
            selected_cells = [current_cell]

        source_cells: list[tuple[int, int]] = []
        for ui_row, ui_column in selected_cells:
            if ui_column <= 0:
                continue
            try:
                source_cells.append(self.to_source_cell(ui_row, ui_column))
            except ValueError:
                continue

        if not source_cells:
            return None

        return min(source_cells)

    def get_selected_source_cells(self) -> list[tuple[int, int]]:
        """Return all currently selected source cells.

        The synthetic index column is ignored. If only one active cell exists,
        that cell is returned as a single-element list.
        """
        if self.worksheet is None or self.mapper is None:
            return []

        selected_cells = self._selected_ui_cells()
        if not selected_cells:
            current_cell = self._current_ui_cell()
            if current_cell is None:
                return []
            selected_cells = [current_cell]

        source_cells: list[tuple[int, int]] = []
        for ui_row, ui_column in selected_cells:
            if ui_column <= 0:
                continue
            try:
                source_cell = self.to_source_cell(ui_row, ui_column)
            except ValueError:
                continue
            if source_cell not in source_cells:
                source_cells.append(source_cell)
        return source_cells

    def _selected_ui_cells(self) -> list[tuple[int, int]]:
        """Collect selected UI cells from the underlying tksheet widget."""
        candidates = (
            "get_selected_cells",
            "selected_cells",
            "get_all_selection_boxes",
            "get_selected_boxes",
            "selection_boxes",
        )
        for name in candidates:
            value = getattr(self.sheet, name, None)
            if callable(value):
                normalized = self._normalize_selection_result(value())
                if normalized:
                    return normalized
            elif value:
                normalized = self._normalize_selection_result(value)
                if normalized:
                    return normalized
        current = self._current_ui_cell()
        return [current] if current is not None else []

    def _current_ui_cell(self) -> tuple[int, int] | None:
        """Return the currently focused UI cell, if any."""
        selected = getattr(self.sheet, "get_currently_selected", None)
        if callable(selected):
            current = selected()
            if current is not None:
                row = getattr(current, "row", None)
                column = getattr(current, "column", None)
                if isinstance(row, int) and isinstance(column, int):
                    return row, column
        return None

    @staticmethod
    def _normalize_selection_result(selection: Any) -> list[tuple[int, int]]:
        """Normalize several tksheet selection shapes into UI cell coordinates."""
        if selection is None:
            return []

        if isinstance(selection, tuple):
            selection = [selection]

        cells: list[tuple[int, int]] = []
        for item in selection if isinstance(selection, list) else list(selection):
            if not isinstance(item, (list, tuple)):
                continue
            if len(item) == 2 and all(isinstance(value, int) for value in item):
                cells.append((int(item[0]), int(item[1])))
                continue
            if len(item) == 4 and all(isinstance(value, int) for value in item):
                row_start, row_end, column_start, column_end = item
                for row in range(row_start, row_end + 1):
                    for column in range(column_start, column_end + 1):
                        cells.append((row, column))
        return cells

    def _set_sheet_data(self, matrix: list[list[Any]], headers: list[str]) -> None:
        if hasattr(self.sheet, "set_sheet_data"):
            self.sheet.set_sheet_data(matrix, reset_col_positions=True, reset_row_positions=True)
        if hasattr(self.sheet, "headers"):
            self.sheet.headers(headers)

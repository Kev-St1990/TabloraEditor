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
        self._bind_index_column_row_selection()
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

    def add_index_context_action(
        self,
        label: str,
        callback: Any,
        *,
        image: Any = "",
        compound: str | None = None,
        accelerator: str | None = None,
    ) -> None:
        """Register an index-only action in the sheet's context menu."""
        delete_command = getattr(self.sheet, "popup_menu_del_command", None)
        add_command = getattr(self.sheet, "popup_menu_add_command", None)
        if callable(delete_command):
            delete_command(label)
        if callable(add_command):
            add_command(
                label,
                callback,
                table_menu=False,
                index_menu=True,
                header_menu=False,
                empty_space_menu=False,
                image=image,
                compound=compound,
                accelerator=accelerator,
            )

    def add_table_context_action(
        self,
        label: str,
        callback: Any,
        *,
        image: Any = "",
        compound: str | None = None,
        accelerator: str | None = None,
    ) -> None:
        """Register a table-cell action in the sheet's context menu."""
        delete_command = getattr(self.sheet, "popup_menu_del_command", None)
        add_command = getattr(self.sheet, "popup_menu_add_command", None)
        if callable(delete_command):
            delete_command(label)
        if callable(add_command):
            add_command(
                label,
                callback,
                table_menu=True,
                index_menu=False,
                header_menu=False,
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

    def get_index_context_ui_row(self) -> int | None:
        """Return the row targeted by the last index context-menu invocation."""
        index = getattr(self.sheet, "RI", None)
        popup_menu_loc = getattr(index, "popup_menu_loc", None)
        if isinstance(popup_menu_loc, int):
            return popup_menu_loc
        return self.get_selected_ui_row()

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
        if not self.worksheet.table_view.visible_source_columns:
            return None
        return min(max(default, 1), len(self.worksheet.table_view.visible_source_columns))

    def get_selected_ui_columns(self) -> list[int]:
        """Return all selected visible UI data columns."""
        selected_columns = getattr(self.sheet, "get_selected_columns", None)
        columns: list[int] = []
        if callable(selected_columns):
            for column in selected_columns() or ():
                if isinstance(column, int) and column > 0 and column not in columns:
                    columns.append(column)
        if columns:
            return columns
        current = self.get_selected_ui_column()
        return [current] if isinstance(current, int) else []

    def get_selected_ui_row(self, *, default: int = 0) -> int | None:
        """Return the primary selected UI row."""
        selected = getattr(self.sheet, "get_currently_selected", None)
        if callable(selected):
            current = selected()
            if current is not None:
                row = getattr(current, "row", None)
                if isinstance(row, int) and row >= 0:
                    return row

        selected_rows = getattr(self.sheet, "get_selected_rows", None)
        if callable(selected_rows):
            rows = selected_rows() or ()
            for row in rows:
                if isinstance(row, int) and row >= 0:
                    return row

        if self.worksheet is None or not self.worksheet.table_view.visible_source_rows:
            return None
        return min(max(default, 0), len(self.worksheet.table_view.visible_source_rows) - 1)

    def get_selected_ui_rows(self) -> list[int]:
        """Return all selected visible UI rows."""
        selected_rows = getattr(self.sheet, "get_selected_rows", None)
        rows: list[int] = []
        if callable(selected_rows):
            for row in selected_rows() or ():
                if isinstance(row, int) and row >= 0 and row not in rows:
                    rows.append(row)
        if rows:
            return rows
        for ui_row, _ui_column in self._selected_ui_cells():
            if ui_row >= 0 and ui_row not in rows:
                rows.append(ui_row)
        if rows:
            return rows
        current = self.get_selected_ui_row()
        return [current] if isinstance(current, int) else []

    def get_selected_source_columns(self) -> list[int]:
        """Return selected source columns for visible UI data columns."""
        if self.worksheet is None:
            return []
        columns: list[int] = []
        for ui_column in self.get_selected_ui_columns():
            try:
                source_column = self.worksheet.table_view.source_column_for_ui(ui_column)
            except ValueError:
                continue
            if source_column not in columns:
                columns.append(source_column)
        return columns

    def get_selected_source_rows(self) -> list[int]:
        """Return selected source rows for visible UI rows."""
        if self.worksheet is None:
            return []
        rows: list[int] = []
        for ui_row in self.get_selected_ui_rows():
            if 0 <= ui_row < len(self.worksheet.table_view.visible_source_rows):
                source_row = self.worksheet.table_view.source_row_for_ui(ui_row)
                if source_row not in rows:
                    rows.append(source_row)
        return rows

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

    def _bind_index_column_row_selection(self) -> None:
        """Promote clicks in the synthetic ID column to row selection.

        This uses tksheet's extension hook instead of replacing its native
        mouse bindings, so normal cell, row-range, and column selection
        behavior stays intact.
        """
        main_table = getattr(self.sheet, "MT", None)
        if main_table is None:
            return
        previous = getattr(main_table, "extra_b1_press_func", None)

        def handle_press(event: Any) -> None:
            if callable(previous):
                previous(event)
            self._promote_index_selection_from_event(event)

        main_table.extra_b1_press_func = handle_press

    def _promote_index_selection_from_event(self, event: Any) -> None:
        """Select the full row when the user clicks inside the ID column."""
        current = self._ui_cell_from_event(event) or self._current_ui_cell()
        if current is None:
            return
        ui_row, ui_column = current
        if ui_column != 0:
            return
        self._select_ui_row(ui_row)

    def _on_primary_press(self, event: Any) -> str | None:
        """Backward-compatible no-op helper kept for tests and old hooks."""
        self._promote_index_selection_from_event(event)
        return None

    def _promote_index_selection_to_row(self) -> None:
        """Backward-compatible helper used by tests."""
        self._promote_index_selection_from_event(None)

    def _select_ui_row(self, ui_row: int) -> None:
        """Ask the underlying widget to select one visible UI row."""
        for method_name in ("select_row", "row_select", "select_rows"):
            method = getattr(self.sheet, method_name, None)
            if not callable(method):
                continue
            try:
                if method_name == "select_rows":
                    method([ui_row])
                else:
                    method(ui_row)
                return
            except TypeError:
                try:
                    if method_name == "select_rows":
                        method(rows=[ui_row])
                    else:
                        method(row=ui_row)
                    return
                except TypeError:
                    continue

    def _ui_cell_from_event(self, event: Any) -> tuple[int, int] | None:
        """Infer a UI cell coordinate from a pointer event when supported."""
        if event is None:
            return None

        for target in (self.sheet, getattr(self.sheet, "MT", None)):
            row_method = getattr(target, "identify_row", None)
            column_method = getattr(target, "identify_col", None)
            if not callable(row_method) or not callable(column_method):
                continue
            for row_arg, column_arg in (
                (event, event),
                (getattr(event, "y", None), getattr(event, "x", None)),
            ):
                if row_arg is None or column_arg is None:
                    continue
                try:
                    row = row_method(row_arg)
                    column = column_method(column_arg)
                except TypeError:
                    continue
                if isinstance(row, int) and isinstance(column, int):
                    return row, column
        return None

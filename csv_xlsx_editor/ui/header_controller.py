"""Header interaction controller for sorting, filtering, and autosize."""

from dataclasses import dataclass
from typing import Any

from csv_xlsx_editor.actions import FilterCommand, SortCommand, UndoRedoManager
from csv_xlsx_editor.domain import (
    FilterState,
    SortState,
    WorkbookDocument,
    WorksheetDocument,
    first_sort_for_column,
)
from csv_xlsx_editor.ui.filter_popup import FilterPopupState, build_popup_state_from_values
from csv_xlsx_editor.ui.sheet_mapping import SheetMatrixBuilder


@dataclass(slots=True)
class HeaderController:
    """Coordinates header clicks with worksheet sort/filter/autosize actions."""

    worksheet: WorksheetDocument
    workbook: WorkbookDocument | None = None
    undo_redo_manager: UndoRedoManager | None = None
    sheet_view: Any | None = None

    def on_left_click_header(self, ui_column: int) -> SortState | None:
        """Toggle sort state for a header column."""
        if self._is_index_column(ui_column):
            return None
        source_column = ui_column - 1
        next_state = self.next_sort_state(source_column)
        self._execute_sort(next_state)
        return next_state

    def on_right_click_header(self, ui_column: int) -> FilterPopupState | None:
        """Build filter popup state for a header column."""
        if self._is_index_column(ui_column):
            return None
        return self.build_filter_popup_state(ui_column - 1)

    def on_double_click_column_boundary(self, ui_column: int) -> int:
        """Autosize a column and return the computed width."""
        width = self.calculate_autosize_width(ui_column)
        self._apply_column_width(ui_column, width)
        return width

    def next_sort_state(self, source_column: int) -> SortState | None:
        """Return the next Excel-style sort state for a source column."""
        current = self.worksheet.sort_state
        if current is None:
            return first_sort_for_column(source_column)
        return current.next_for_column(source_column)

    def build_filter_popup_state(self, source_column: int) -> FilterPopupState:
        """Collect distinct values and current selection for one source column."""
        values: list[Any] = []
        seen: set[Any] = set()
        has_blanks = False
        for row_index in range(self.worksheet.max_row):
            value = self.worksheet.get_cell(row_index, source_column).value
            if value is None or value == "":
                has_blanks = True
                continue
            if value not in seen:
                seen.add(value)
                values.append(value)
        current_filter = self.worksheet.filter_state.column_filters.get(source_column)
        return build_popup_state_from_values(
            source_column,
            values,
            current_filter=current_filter,
            has_blanks=has_blanks,
        )

    def apply_filter_popup_state(self, popup_state: FilterPopupState) -> FilterState:
        """Convert a popup state into a filter command and execute it."""
        filter_state = popup_state.build_filter_state()
        command = FilterCommand(
            worksheet=self.worksheet,
            filter_state=filter_state,
            workbook=self.workbook,
        )
        self._execute(command)
        return filter_state

    def calculate_autosize_width(self, ui_column: int, *, padding: int = 2, minimum: int = 4) -> int:
        """Estimate a column width from visible data and headers."""
        builder = SheetMatrixBuilder(self.worksheet)
        headers = builder.headers()
        matrix = builder.matrix()
        if ui_column < 0 or ui_column >= len(headers):
            return minimum

        header_width = len(str(headers[ui_column]))
        cell_widths = [len(str(row[ui_column])) if ui_column < len(row) else 0 for row in matrix]
        width = max([header_width, *cell_widths], default=minimum) + padding
        return max(width, minimum)

    def apply_sort(self, sort_state: SortState | None) -> None:
        """Apply a sort state directly through a command."""
        self._execute_sort(sort_state)

    def apply_filter_state(self, filter_state: FilterState) -> None:
        """Apply a filter state directly through a command."""
        command = FilterCommand(
            worksheet=self.worksheet,
            filter_state=filter_state,
            workbook=self.workbook,
        )
        self._execute(command)

    def _execute_sort(self, sort_state: SortState | None) -> None:
        command = SortCommand(
            worksheet=self.worksheet,
            sort_state=sort_state,
            workbook=self.workbook,
        )
        self._execute(command)

    def _execute(self, command: Any) -> None:
        if self.undo_redo_manager is not None:
            self.undo_redo_manager.execute(command)
        else:
            command.execute()
        self._refresh_view()

    def _apply_column_width(self, ui_column: int, width: int) -> None:
        if self.sheet_view is None:
            return
        if hasattr(self.sheet_view, "set_column_width"):
            self.sheet_view.set_column_width(ui_column, width)

    def _refresh_view(self) -> None:
        if self.sheet_view is not None and hasattr(self.sheet_view, "refresh"):
            self.sheet_view.refresh()

    @staticmethod
    def _is_index_column(ui_column: int) -> bool:
        return ui_column == 0

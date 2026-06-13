"""Worksheet document model independent from UI and file IO."""

from dataclasses import dataclass, field
from copy import deepcopy
from typing import Any, TypeAlias

from csv_xlsx_editor.domain.cell_data import CellData
from csv_xlsx_editor.domain.filter_state import FilterState
from csv_xlsx_editor.domain.sort_state import SortState
from csv_xlsx_editor.domain.table_view import TableView

CellAddress: TypeAlias = tuple[int, int]


@dataclass(slots=True)
class WorksheetSnapshot:
    """Immutable-style copy of worksheet state used for undo and redo."""

    cells: dict[CellAddress, CellData]
    column_headers: list[Any]
    header_cells: dict[int, CellData]
    max_row: int
    max_column: int
    sort_state: SortState | None
    filter_state: FilterState


@dataclass(slots=True)
class WorksheetDocument:
    """Represents one worksheet and its non-destructive table view state."""

    sheet_id: str
    title: str
    source_sheet_name: str | None = None
    column_headers: list[Any] = field(default_factory=list)
    header_cells: dict[int, CellData] = field(default_factory=dict)
    cells: dict[CellAddress, CellData] = field(default_factory=dict)
    max_row: int = 0
    max_column: int = 0
    table_view: TableView = field(default_factory=TableView)
    sort_state: SortState | None = None
    filter_state: FilterState = field(default_factory=FilterState)

    def __post_init__(self) -> None:
        self._expand_dimensions_for_existing_cells()
        if not self.table_view.visible_source_rows and self.max_row > 0:
            self.rebuild_view()

    def get_cell(self, row: int, column: int) -> CellData:
        """Return cell data for zero-based source coordinates.

        Missing cells are represented as empty `CellData` objects without
        mutating the worksheet.
        """
        return self.cells.get((row, column), CellData())

    def set_cell(self, row: int, column: int, value: Any) -> None:
        """Set a cell value at zero-based source coordinates."""
        self._validate_coordinates(row, column)
        cell = self.cells.get((row, column))
        if cell is None:
            cell = CellData.from_value(value)
            self.cells[(row, column)] = cell
        else:
            cell.set_value(value)
        self.max_row = max(self.max_row, row + 1)
        self.max_column = max(self.max_column, column + 1)
        self.rebuild_view()

    def set_headers(self, headers: list[Any], header_cells: dict[int, CellData] | None = None) -> None:
        """Set the worksheet column headers and optional style metadata."""
        self.column_headers = list(headers)
        self.header_cells = {column: deepcopy(cell) for column, cell in (header_cells or {}).items()}
        self.max_column = max(self.max_column, len(self.column_headers))
        self.rebuild_view()

    def set_cells(self, start_row: int, start_column: int, matrix: list[list[Any]]) -> None:
        """Paste a rectangular matrix of values at zero-based source coordinates."""
        if not matrix:
            return

        for row_offset, row_values in enumerate(matrix):
            for column_offset, value in enumerate(row_values):
                self._validate_coordinates(start_row + row_offset, start_column + column_offset)
                cell = self.cells.get((start_row + row_offset, start_column + column_offset))
                if cell is None:
                    self.cells[(start_row + row_offset, start_column + column_offset)] = CellData.from_value(value)
                else:
                    cell.set_value(value)

        self.max_row = max(self.max_row, start_row + len(matrix))
        self.max_column = max(
            self.max_column,
            start_column + max((len(row_values) for row_values in matrix), default=0),
        )
        self.rebuild_view()

    def capture_state(self) -> WorksheetSnapshot:
        """Create a snapshot of the complete worksheet state."""
        return WorksheetSnapshot(
            cells={address: deepcopy(cell) for address, cell in self.cells.items()},
            column_headers=deepcopy(self.column_headers),
            header_cells={column: deepcopy(cell) for column, cell in self.header_cells.items()},
            max_row=self.max_row,
            max_column=self.max_column,
            sort_state=deepcopy(self.sort_state),
            filter_state=deepcopy(self.filter_state),
        )

    def restore_state(self, snapshot: WorksheetSnapshot) -> None:
        """Replace the worksheet state with a previously captured snapshot."""
        self.cells = {address: deepcopy(cell) for address, cell in snapshot.cells.items()}
        self.column_headers = deepcopy(snapshot.column_headers)
        self.header_cells = {column: deepcopy(cell) for column, cell in snapshot.header_cells.items()}
        self.max_row = snapshot.max_row
        self.max_column = snapshot.max_column
        self.sort_state = deepcopy(snapshot.sort_state)
        self.filter_state = deepcopy(snapshot.filter_state)
        self.rebuild_view()

    def get_display_rows(self) -> list[int]:
        """Return source row indexes currently visible in the table view."""
        return list(self.table_view.visible_source_rows)

    def get_row_values(self, row: int) -> list[Any]:
        """Return source values for one row across all known columns."""
        return [self.get_cell(row, column).value for column in range(self.max_column)]

    def rebuild_view(self) -> None:
        """Recompute visible rows from current filter and sort state."""
        rows = list(range(self.max_row))
        rows = [row for row in rows if self.filter_state.matches(self.get_row_values(row))]

        if self.sort_state is not None:
            reverse = self.sort_state.direction == "desc"
            column = self.sort_state.column
            rows.sort(key=lambda row: self._sort_key(self.get_cell(row, column).value), reverse=reverse)

        self.table_view = TableView(
            visible_source_rows=rows,
            visible_source_columns=list(range(self.max_column)),
            row_ids={row: row + 1 for row in range(self.max_row)},
        )

    def apply_sort(self, sort_state: SortState | None) -> None:
        """Update sort state and rebuild the visible table view."""
        self.sort_state = sort_state
        self.rebuild_view()

    def apply_filter(self, filter_state: FilterState) -> None:
        """Update filter state and rebuild the visible table view."""
        self.filter_state = filter_state
        self.rebuild_view()

    def _expand_dimensions_for_existing_cells(self) -> None:
        if not self.cells:
            return
        max_row = max(row for row, _column in self.cells) + 1
        max_column = max(column for _row, column in self.cells) + 1
        self.max_row = max(self.max_row, max_row)
        self.max_column = max(self.max_column, max_column)

    @staticmethod
    def _validate_coordinates(row: int, column: int) -> None:
        if row < 0 or column < 0:
            raise ValueError("Cell coordinates must be zero-based positive integers.")

    @staticmethod
    def _sort_key(value: Any) -> tuple[int, str]:
        if value is None or value == "":
            return (1, "")
        return (0, str(value).casefold())

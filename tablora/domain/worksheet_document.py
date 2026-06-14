"""Worksheet document model independent from UI and file IO."""

from dataclasses import dataclass, field
from copy import deepcopy
from datetime import date, datetime, time
import re
from typing import Any, TypeAlias

from tablora.domain.cell_data import CellData
from tablora.domain.cell_formatting import FormatCellsResult, FormatPreviewItem, FormatRequest, format_cell_value
from tablora.domain.filter_state import FilterState
from tablora.domain.sort_state import SortState
from tablora.domain.table_view import TableView

CellAddress: TypeAlias = tuple[int, int]

_DATE_PATTERNS = (
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%Y.%m.%d",
    "%d.%m.%Y",
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%m/%d/%Y",
    "%m-%d-%Y",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d %H:%M:%S",
    "%d.%m.%Y %H:%M",
    "%d.%m.%Y %H:%M:%S",
    "%d/%m/%Y %H:%M",
    "%d/%m/%Y %H:%M:%S",
    "%m/%d/%Y %H:%M",
    "%m/%d/%Y %H:%M:%S",
    "%Y-%m-%dT%H:%M",
    "%Y-%m-%dT%H:%M:%S",
)

_ENGLISH_MONTHS = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}

_GERMAN_MONTHS = {
    "jan": 1,
    "januar": 1,
    "feb": 2,
    "februar": 2,
    "mär": 3,
    "maerz": 3,
    "märz": 3,
    "mrz": 3,
    "apr": 4,
    "april": 4,
    "mai": 5,
    "jun": 6,
    "juni": 6,
    "jul": 7,
    "juli": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "okt": 10,
    "oktober": 10,
    "nov": 11,
    "november": 11,
    "dez": 12,
    "dezember": 12,
}


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
            rows.sort(key=lambda row: self._sort_key_for_cell(self.get_cell(row, column)), reverse=reverse)

        self.table_view = TableView(
            visible_source_rows=rows,
            visible_source_columns=list(range(self.max_column)),
            row_ids={row: row + 1 for row in range(self.max_row)},
        )

    def apply_sort(self, sort_state: SortState | None) -> None:
        """Update sort state and rebuild the visible table view."""
        self.sort_state = sort_state
        self.rebuild_view()

    def sort_column_values(self, column: int, *, reverse: bool = False) -> None:
        """Sort the values of one source column without changing row order."""
        if column < 0:
            raise ValueError("Column must be zero-based positive integer.")

        column_cells = [deepcopy(self.get_cell(row, column)) for row in range(self.max_row)]
        sorted_cells = sorted(column_cells, key=self._sort_key_for_cell, reverse=reverse)
        self.sort_state = None

        for row in range(self.max_row):
            self.cells.pop((row, column), None)

        for row, cell in enumerate(sorted_cells):
            if cell.value is None and cell.formula is None and cell.number_format is None and cell.style_id is None:
                continue
            self.cells[(row, column)] = cell

        self.rebuild_view()

    def apply_filter(self, filter_state: FilterState) -> None:
        """Update filter state and rebuild the visible table view."""
        self.filter_state = filter_state
        self.rebuild_view()

    def preview_format_cells(
        self,
        addresses: list[CellAddress],
        request: FormatRequest,
        *,
        preview_limit: int = 5,
    ) -> FormatCellsResult:
        """Build a preview summary for formatting a set of cells."""
        return self._format_cells_internal(addresses, request, apply=False, preview_limit=preview_limit)

    def format_cells(
        self,
        addresses: list[CellAddress],
        request: FormatRequest,
        *,
        preview_limit: int = 5,
    ) -> FormatCellsResult:
        """Apply formatting to a set of cells and return a structured summary."""
        return self._format_cells_internal(addresses, request, apply=True, preview_limit=preview_limit)

    def _expand_dimensions_for_existing_cells(self) -> None:
        if not self.cells:
            return
        max_row = max(row for row, _column in self.cells) + 1
        max_column = max(column for _row, column in self.cells) + 1
        self.max_row = max(self.max_row, max_row)
        self.max_column = max(self.max_column, max_column)

    def _format_cells_internal(
        self,
        addresses: list[CellAddress],
        request: FormatRequest,
        *,
        apply: bool,
        preview_limit: int,
    ) -> FormatCellsResult:
        result = FormatCellsResult()
        normalized_addresses = sorted(set(addresses))
        any_value_changed = False

        for row, column in normalized_addresses:
            self._validate_coordinates(row, column)
            cell = self.get_cell(row, column)
            decision = format_cell_value(
                cell.value,
                number_format=cell.number_format,
                request=request,
            )
            result.add_preview(
                FormatPreviewItem(
                    address=self._cell_label(row, column),
                    original=decision.original_display,
                    formatted=decision.formatted_display,
                    status=decision.status,
                    note=decision.note,
                ),
                limit=preview_limit,
            )

            if decision.status == "changed":
                result.changed_count += 1
                if decision.metadata_only:
                    result.metadata_only_count += 1
                if decision.text_changed:
                    result.text_changed_count += 1
            elif decision.status == "unchanged":
                result.unchanged_count += 1
            elif decision.status == "ambiguous":
                result.ambiguous_count += 1
            elif decision.status == "invalid":
                result.invalid_count += 1
            elif decision.status == "empty":
                result.empty_count += 1

            if not apply or not decision.changed:
                continue

            target_cell = self.cells.get((row, column))
            if target_cell is None:
                target_cell = CellData()
                self.cells[(row, column)] = target_cell

            if decision.new_value is not None and decision.text_changed:
                target_cell.set_value(decision.new_value)
                any_value_changed = True
            if decision.new_number_format is not None:
                target_cell.number_format = decision.new_number_format

        if apply and (any_value_changed or result.metadata_only_count):
            self.rebuild_view()
        return result

    @staticmethod
    def _cell_label(row: int, column: int) -> str:
        """Return an Excel-style 1-based cell label such as `B12`."""
        letters = ""
        number = column + 1
        while number > 0:
            number, remainder = divmod(number - 1, 26)
            letters = chr(ord("A") + remainder) + letters
        return f"{letters}{row + 2}"

    @staticmethod
    def _validate_coordinates(row: int, column: int) -> None:
        if row < 0 or column < 0:
            raise ValueError("Cell coordinates must be zero-based positive integers.")

    @staticmethod
    def _sort_key_for_cell(cell: CellData) -> tuple[int, Any]:
        value = cell.value
        if value is None or value == "":
            return (3, "")

        parsed_date = WorksheetDocument._coerce_datetime(value, cell.number_format)
        if parsed_date is not None:
            return (0, parsed_date)

        parsed_number = WorksheetDocument._coerce_number(value)
        if parsed_number is not None:
            return (1, parsed_number)

        return (2, str(value).casefold())

    @staticmethod
    def _sort_key(value: Any) -> tuple[int, Any]:
        return WorksheetDocument._sort_key_for_cell(CellData(value=value))

    @staticmethod
    def _coerce_datetime(value: Any, number_format: str | None = None) -> datetime | None:
        if isinstance(value, datetime):
            return value.replace(tzinfo=None)
        if isinstance(value, date):
            return datetime.combine(value, time.min)
        if not isinstance(value, str):
            return None

        text = value.strip()
        if not text:
            return None

        candidates = WorksheetDocument._date_patterns_for_number_format(number_format)
        for pattern in candidates:
            try:
                return datetime.strptime(text, pattern)
            except ValueError:
                continue

        parsed_month_name = WorksheetDocument._parse_english_month_date(text)
        if parsed_month_name is not None:
            return parsed_month_name

        try:
            return datetime.fromisoformat(text)
        except ValueError:
            return None

    @staticmethod
    def _parse_english_month_date(text: str) -> datetime | None:
        match = re.fullmatch(
            r"(?P<day>\d{1,2})\s+(?P<month>[A-Za-zÄÖÜäöüß]{3,12})\.?\s+(?P<year>\d{4})(?:\s+(?P<hour>\d{1,2}):(?P<minute>\d{2})(?::(?P<second>\d{2}))?)?",
            text,
        )
        if match is None:
            return None

        month_key = match.group("month").casefold()
        month = _ENGLISH_MONTHS.get(month_key) or _GERMAN_MONTHS.get(month_key)
        if month is None:
            return None

        day = int(match.group("day"))
        year = int(match.group("year"))
        hour = int(match.group("hour") or 0)
        minute = int(match.group("minute") or 0)
        second = int(match.group("second") or 0)
        try:
            return datetime(year, month, day, hour, minute, second)
        except ValueError:
            return None

    @staticmethod
    def _coerce_number(value: Any) -> float | int | None:
        if isinstance(value, bool):
            return None
        if isinstance(value, (int, float)):
            return value
        if not isinstance(value, str):
            return None

        text = value.strip()
        if not text:
            return None
        if re.fullmatch(r"[-+]?\d+", text):
            return int(text)
        if re.fullmatch(r"[-+]?\d+[.,]\d+", text):
            return float(text.replace(",", "."))
        return None

    @staticmethod
    def _date_patterns_for_number_format(number_format: str | None) -> tuple[str, ...]:
        if not number_format:
            return _DATE_PATTERNS

        fmt = number_format.casefold()
        preferred: list[str] = []

        def add_patterns(patterns: tuple[str, ...]) -> None:
            for pattern in patterns:
                if pattern not in preferred:
                    preferred.append(pattern)

        ymd_patterns = tuple(pattern for pattern in _DATE_PATTERNS if pattern.startswith("%Y"))
        dmy_patterns = tuple(pattern for pattern in _DATE_PATTERNS if pattern.startswith("%d"))
        mdy_patterns = tuple(pattern for pattern in _DATE_PATTERNS if pattern.startswith("%m"))

        if "yyyy" in fmt:
            add_patterns(ymd_patterns)

        if "dd" in fmt and "mm" in fmt:
            if fmt.index("dd") < fmt.index("mm"):
                add_patterns(dmy_patterns)
                add_patterns(mdy_patterns)
            else:
                add_patterns(mdy_patterns)
                add_patterns(dmy_patterns)

        if "yyyy" not in fmt and "dd" not in fmt and "mm" not in fmt:
            add_patterns(_DATE_PATTERNS)

        add_patterns(_DATE_PATTERNS)
        return tuple(preferred)

"""Filter state for worksheet table views."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ColumnFilter:
    """Allowed-value filter for a single source column."""

    allowed_values: set[Any] = field(default_factory=set)
    search_text: str = ""
    include_blanks: bool = True

    def allows(self, value: Any) -> bool:
        """Return whether a cell value passes this column filter."""
        is_blank = value is None or value == ""
        if is_blank:
            return self.include_blanks
        return value in self.allowed_values


@dataclass(slots=True)
class FilterState:
    """Stores active per-column filters for a worksheet view."""

    column_filters: dict[int, ColumnFilter] = field(default_factory=dict)

    def set_filter(
        self,
        column: int,
        allowed_values: set[Any],
        *,
        search_text: str = "",
        include_blanks: bool = True,
    ) -> None:
        """Set or replace the filter for a source column."""
        self.column_filters[column] = ColumnFilter(
            allowed_values=set(allowed_values),
            search_text=search_text,
            include_blanks=include_blanks,
        )

    def clear_filter(self, column: int) -> None:
        """Remove the filter for a source column if one exists."""
        self.column_filters.pop(column, None)

    def clear_all(self) -> None:
        """Remove all active column filters."""
        self.column_filters.clear()

    def matches(self, row_values: list[Any]) -> bool:
        """Return whether a row passes all active filters.

        `row_values` is indexed by source column. Missing columns are treated as
        blank values so sparse rows can still be filtered predictably.
        """
        for column, column_filter in self.column_filters.items():
            value = row_values[column] if column < len(row_values) else None
            if not column_filter.allows(value):
                return False
        return True

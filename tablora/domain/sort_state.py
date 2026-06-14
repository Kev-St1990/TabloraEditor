"""Sort state for a worksheet view."""

from dataclasses import dataclass
from typing import Literal

SortDirection = Literal["asc", "desc"]


@dataclass(frozen=True, slots=True)
class SortState:
    """Describes the active sort column and direction for a table view."""

    column: int
    direction: SortDirection

    def next_for_column(self, column: int) -> "SortState | None":
        """Return the next sort state for Excel-like header click cycling.

        The cycle is ascending, descending, then no sort. Clicking a different
        column starts again with ascending order.
        """
        if column != self.column:
            return SortState(column=column, direction="asc")
        if self.direction == "asc":
            return SortState(column=column, direction="desc")
        return None


def first_sort_for_column(column: int) -> SortState:
    """Return the initial ascending sort state for a clicked column."""
    return SortState(column=column, direction="asc")

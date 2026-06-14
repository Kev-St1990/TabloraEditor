"""Filter popup state and helpers for Excel-style column filtering."""

from dataclasses import dataclass, field
from typing import Any

from tablora.domain import ColumnFilter, FilterState


@dataclass(slots=True)
class FilterPopupState:
    """Represents the state of a filter popup for one source column."""

    column: int
    values: list[Any] = field(default_factory=list)
    selected_values: set[Any] = field(default_factory=set)
    include_blanks: bool = True
    search_text: str = ""
    has_blanks: bool = False

    def visible_values(self) -> list[Any]:
        """Return values that match the current search text."""
        query = self.search_text.casefold().strip()
        if not query:
            return list(self.values)
        return [value for value in self.values if query in str(value).casefold()]

    def select_all(self) -> None:
        """Select every currently known value."""
        self.selected_values = set(self.values)
        self.include_blanks = True

    def select_none(self) -> None:
        """Clear the selection."""
        self.selected_values.clear()
        self.include_blanks = False

    def toggle_value(self, value: Any) -> None:
        """Toggle a single distinct value in the selection."""
        if value in self.selected_values:
            self.selected_values.remove(value)
        else:
            self.selected_values.add(value)

    def set_search_text(self, search_text: str) -> None:
        """Update the search filter text."""
        self.search_text = search_text

    def build_filter_state(self) -> FilterState:
        """Convert the popup state into a `FilterState`."""
        filter_state = FilterState()
        filter_state.column_filters[self.column] = ColumnFilter(
            allowed_values=set(self.selected_values),
            search_text=self.search_text,
            include_blanks=self.include_blanks,
        )
        return filter_state


def build_popup_state_from_values(
    column: int,
    values: list[Any],
    *,
    current_filter: ColumnFilter | None = None,
    has_blanks: bool = False,
) -> FilterPopupState:
    """Create a popup state from the known distinct values of one column."""
    selected_values = set(values)
    include_blanks = has_blanks
    search_text = ""
    if current_filter is not None:
        selected_values = set(current_filter.allowed_values)
        include_blanks = current_filter.include_blanks
        search_text = current_filter.search_text
    return FilterPopupState(
        column=column,
        values=list(values),
        selected_values=selected_values,
        include_blanks=include_blanks,
        search_text=search_text,
        has_blanks=has_blanks,
    )

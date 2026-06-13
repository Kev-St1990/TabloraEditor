"""Temporary filter state placeholder.

This module preserves the existing minimal FilterManager while the dedicated
domain filter model is introduced in a later implementation step.
"""


class FilterManager:
    """Stores active column filters for the current sheet placeholder."""

    def __init__(self) -> None:
        self.active_filters: dict[int, object] = {}

    def clear(self) -> None:
        """Remove all active filters."""
        self.active_filters.clear()

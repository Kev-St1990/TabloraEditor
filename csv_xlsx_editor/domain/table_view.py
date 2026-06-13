"""Visible projection of a worksheet after sorting and filtering."""

from dataclasses import dataclass, field


@dataclass(slots=True)
class TableView:
    """Maps UI rows and columns to source worksheet coordinates.

    Source coordinates are zero-based. UI column `0` is reserved for the
    read-only index column, so data column `0` appears at UI column `1`.
    """

    visible_source_rows: list[int] = field(default_factory=list)
    visible_source_columns: list[int] = field(default_factory=list)
    row_ids: dict[int, int] = field(default_factory=dict)

    @classmethod
    def from_dimensions(cls, row_count: int, column_count: int) -> "TableView":
        """Create a default view showing every source row and column."""
        rows = list(range(max(row_count, 0)))
        columns = list(range(max(column_count, 0)))
        return cls(
            visible_source_rows=rows,
            visible_source_columns=columns,
            row_ids={row: row + 1 for row in rows},
        )

    def source_row_for_ui(self, ui_row: int) -> int:
        """Return the source row for a visible UI row."""
        return self.visible_source_rows[ui_row]

    def source_column_for_ui(self, ui_column: int) -> int:
        """Return the source column for a UI data column.

        UI column `0` is the index column and has no source data column.
        """
        if ui_column == 0:
            raise ValueError("UI column 0 is the read-only index column.")
        return self.visible_source_columns[ui_column - 1]

    def row_id_for_ui(self, ui_row: int) -> int:
        """Return the displayed row ID for a visible UI row."""
        source_row = self.source_row_for_ui(ui_row)
        return self.row_ids[source_row]

    def ui_column_for_source(self, source_column: int) -> int:
        """Return the UI column for a source data column."""
        return self.visible_source_columns.index(source_column) + 1

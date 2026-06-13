"""Undoable command for sorting values within one worksheet column."""

from dataclasses import dataclass

from csv_xlsx_editor.actions.command import SnapshotCommand
from csv_xlsx_editor.domain import WorkbookDocument, WorksheetDocument


@dataclass(slots=True)
class SortValuesCommand(SnapshotCommand):
    """Sort the values in a single column while keeping row order stable."""

    worksheet: WorksheetDocument
    column: int
    reverse: bool = False
    workbook: WorkbookDocument | None = None

    def __post_init__(self) -> None:
        SnapshotCommand.__init__(self)

    def description(self) -> str:
        direction = "desc" if self.reverse else "asc"
        return f"Sort values column {self.column + 1} {direction}"

    def _capture_snapshot(self):
        return self.worksheet.capture_state()

    def _restore_snapshot(self, snapshot) -> None:
        self.worksheet.restore_state(snapshot)

    def _apply(self) -> None:
        self.worksheet.sort_column_values(self.column, reverse=self.reverse)

    def _mark_dirty(self) -> None:
        if self.workbook is not None:
            self.workbook.mark_dirty()

"""Undoable command for worksheet filtering."""

from dataclasses import dataclass

from tablora.actions.command import SnapshotCommand
from tablora.domain import FilterState, WorkbookDocument, WorksheetDocument


@dataclass(slots=True)
class FilterCommand(SnapshotCommand):
    """Apply a filter state to a worksheet and support undo/redo."""

    worksheet: WorksheetDocument
    filter_state: FilterState
    workbook: WorkbookDocument | None = None

    def __post_init__(self) -> None:
        SnapshotCommand.__init__(self)

    def description(self) -> str:
        return f"Filter {len(self.filter_state.column_filters)} column(s)"

    def _capture_snapshot(self):
        return self.worksheet.capture_state()

    def _restore_snapshot(self, snapshot) -> None:
        self.worksheet.restore_state(snapshot)

    def _apply(self) -> None:
        self.worksheet.apply_filter(self.filter_state)

    def _mark_dirty(self) -> None:
        if self.workbook is not None:
            self.workbook.mark_dirty()

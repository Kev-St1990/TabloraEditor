"""Undoable command for worksheet sorting."""

from dataclasses import dataclass

from tablora.actions.command import SnapshotCommand
from tablora.domain import SortState, WorkbookDocument, WorksheetDocument


@dataclass(slots=True)
class SortCommand(SnapshotCommand):
    """Apply a sort state to a worksheet and support undo/redo."""

    worksheet: WorksheetDocument
    sort_state: SortState | None
    workbook: WorkbookDocument | None = None

    def __post_init__(self) -> None:
        SnapshotCommand.__init__(self)

    def description(self) -> str:
        if self.sort_state is None:
            return "Clear sort"
        return f"Sort column {self.sort_state.column + 1} {self.sort_state.direction}"

    def _capture_snapshot(self):
        return self.worksheet.capture_state()

    def _restore_snapshot(self, snapshot) -> None:
        self.worksheet.restore_state(snapshot)

    def _apply(self) -> None:
        self.worksheet.apply_sort(self.sort_state)

    def _mark_dirty(self) -> None:
        if self.workbook is not None:
            self.workbook.mark_dirty()

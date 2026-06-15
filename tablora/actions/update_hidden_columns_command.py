"""Undoable command for updating hidden column state."""

from dataclasses import dataclass

from tablora.actions.command import SnapshotCommand
from tablora.domain import WorkbookDocument, WorksheetDocument


@dataclass(slots=True)
class UpdateHiddenColumnsCommand(SnapshotCommand):
    """Hide or unhide source columns and support undo/redo."""

    worksheet: WorksheetDocument
    columns: list[int]
    hide: bool
    workbook: WorkbookDocument | None = None

    def __post_init__(self) -> None:
        SnapshotCommand.__init__(self)
        self.columns = sorted(set(self.columns))

    def description(self) -> str:
        action = "Hide" if self.hide else "Unhide"
        return f"{action} {len(self.columns)} column(s)"

    def _capture_snapshot(self):
        return self.worksheet.capture_state()

    def _restore_snapshot(self, snapshot) -> None:
        self.worksheet.restore_state(snapshot)

    def _apply(self) -> None:
        if self.hide:
            self.worksheet.hide_columns(self.columns)
        else:
            self.worksheet.unhide_columns(self.columns or None)

    def _mark_dirty(self) -> None:
        return None

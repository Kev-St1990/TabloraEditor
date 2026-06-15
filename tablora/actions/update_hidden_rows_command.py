"""Undoable command for updating hidden row state."""

from dataclasses import dataclass

from tablora.actions.command import SnapshotCommand
from tablora.domain import WorkbookDocument, WorksheetDocument


@dataclass(slots=True)
class UpdateHiddenRowsCommand(SnapshotCommand):
    """Hide or unhide source rows and support undo/redo."""

    worksheet: WorksheetDocument
    rows: list[int]
    hide: bool
    workbook: WorkbookDocument | None = None

    def __post_init__(self) -> None:
        SnapshotCommand.__init__(self)
        self.rows = sorted(set(self.rows))

    def description(self) -> str:
        action = "Hide" if self.hide else "Unhide"
        return f"{action} {len(self.rows)} row(s)"

    def _capture_snapshot(self):
        return self.worksheet.capture_state()

    def _restore_snapshot(self, snapshot) -> None:
        self.worksheet.restore_state(snapshot)

    def _apply(self) -> None:
        if self.hide:
            self.worksheet.hide_rows(self.rows)
        else:
            self.worksheet.unhide_rows(self.rows or None)

    def _mark_dirty(self) -> None:
        return None

"""Undoable command for editing a single worksheet cell."""

from dataclasses import dataclass

from csv_xlsx_editor.actions.command import SnapshotCommand
from csv_xlsx_editor.domain import WorkbookDocument, WorksheetDocument


@dataclass(slots=True)
class EditCellCommand(SnapshotCommand):
    """Change one cell in a worksheet and support undo/redo."""

    worksheet: WorksheetDocument
    row: int
    column: int
    value: object
    workbook: WorkbookDocument | None = None

    def __post_init__(self) -> None:
        SnapshotCommand.__init__(self)

    def description(self) -> str:
        return f"Edit cell R{self.row + 1}C{self.column + 1}"

    def _capture_snapshot(self):
        return self.worksheet.capture_state()

    def _restore_snapshot(self, snapshot) -> None:
        self.worksheet.restore_state(snapshot)

    def _apply(self) -> None:
        self.worksheet.set_cell(self.row, self.column, self.value)

    def _mark_dirty(self) -> None:
        if self.workbook is not None:
            self.workbook.mark_dirty()

"""Undoable command for pasting a rectangular matrix into a worksheet."""

from dataclasses import dataclass, field

from tablora.actions.command import SnapshotCommand
from tablora.domain import WorkbookDocument, WorksheetDocument


@dataclass(slots=True)
class PasteRangeCommand(SnapshotCommand):
    """Paste a matrix at a source coordinate and support undo/redo."""

    worksheet: WorksheetDocument
    start_row: int
    start_column: int
    matrix: list[list[object]] = field(default_factory=list)
    workbook: WorkbookDocument | None = None

    def __post_init__(self) -> None:
        SnapshotCommand.__init__(self)
        self.matrix = [row[:] for row in self.matrix]

    def description(self) -> str:
        height = len(self.matrix)
        width = max((len(row) for row in self.matrix), default=0)
        return f"Paste range {height}x{width} at R{self.start_row + 1}C{self.start_column + 1}"

    def _capture_snapshot(self):
        return self.worksheet.capture_state()

    def _restore_snapshot(self, snapshot) -> None:
        self.worksheet.restore_state(snapshot)

    def _apply(self) -> None:
        self.worksheet.set_cells(self.start_row, self.start_column, self.matrix)

    def _mark_dirty(self) -> None:
        if self.workbook is not None:
            self.workbook.mark_dirty()

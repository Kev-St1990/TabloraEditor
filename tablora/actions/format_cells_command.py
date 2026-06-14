"""Undoable command for applying cell formatting to a worksheet region."""

from dataclasses import dataclass

from tablora.actions.command import SnapshotCommand
from tablora.domain import FormatCellsResult, FormatRequest, WorkbookDocument, WorksheetDocument


@dataclass(slots=True)
class FormatCellsCommand(SnapshotCommand):
    """Apply formatting to selected cells and support undo/redo."""

    worksheet: WorksheetDocument
    addresses: list[tuple[int, int]]
    request: FormatRequest
    workbook: WorkbookDocument | None = None
    last_result: FormatCellsResult | None = None

    def __post_init__(self) -> None:
        SnapshotCommand.__init__(self)
        self.addresses = list(self.addresses)

    def description(self) -> str:
        return f"Format {len(self.addresses)} cell(s) as {self.request.target}"

    def _capture_snapshot(self):
        return self.worksheet.capture_state()

    def _restore_snapshot(self, snapshot) -> None:
        self.worksheet.restore_state(snapshot)

    def _apply(self) -> None:
        self.last_result = self.worksheet.format_cells(self.addresses, self.request)

    def _mark_dirty(self) -> None:
        if self.workbook is not None:
            self.workbook.mark_dirty()

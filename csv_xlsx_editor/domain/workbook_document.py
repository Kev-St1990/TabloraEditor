"""Workbook document model for CSV, XLSX, and XLSM files."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from csv_xlsx_editor.domain.worksheet_document import WorksheetDocument

FileType = Literal["csv", "xlsx", "xlsm"]


@dataclass(slots=True)
class WorkbookDocument:
    """Represents an opened workbook and its active worksheet state."""

    path: str | Path | None = None
    file_type: FileType = "csv"
    worksheets: list[WorksheetDocument] = field(default_factory=list)
    active_sheet_id: str = ""
    openpyxl_workbook: Any = None
    dirty: bool = False
    csv_delimiter: str | None = None

    def __post_init__(self) -> None:
        if self.worksheets and not self.active_sheet_id:
            self.active_sheet_id = self.worksheets[0].sheet_id

    def get_active_sheet(self) -> WorksheetDocument:
        """Return the active worksheet."""
        return self.get_sheet(self.active_sheet_id)

    def get_sheet(self, sheet_id: str) -> WorksheetDocument:
        """Return a worksheet by stable sheet ID."""
        for worksheet in self.worksheets:
            if worksheet.sheet_id == sheet_id:
                return worksheet
        raise KeyError(f"Unknown worksheet id: {sheet_id}")

    def set_active_sheet(self, sheet_id: str) -> None:
        """Select the active worksheet by ID."""
        self.get_sheet(sheet_id)
        self.active_sheet_id = sheet_id

    def mark_dirty(self) -> None:
        """Mark the document as having unsaved changes."""
        self.dirty = True

    def mark_clean(self) -> None:
        """Mark the document as saved."""
        self.dirty = False

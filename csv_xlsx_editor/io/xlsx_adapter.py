"""XLSX/XLSM adapter for workbook documents."""

from copy import copy
from pathlib import Path
from typing import Any

from openpyxl import Workbook, load_workbook
from openpyxl.worksheet.worksheet import Worksheet

from csv_xlsx_editor.domain import CellData, WorkbookDocument, WorksheetDocument


class XlsxAdapter:
    """Loads and saves XLSX/XLSM files while preserving workbook structure."""

    def load(self, path: str | Path) -> WorkbookDocument:
        """Load an XLSX or XLSM file with formulas preserved."""
        file_path = Path(path)
        file_type = "xlsm" if file_path.suffix.lower() == ".xlsm" else "xlsx"
        workbook = load_workbook(
            file_path,
            data_only=False,
            keep_vba=file_type == "xlsm",
        )
        worksheets = [self._worksheet_from_openpyxl(sheet, index) for index, sheet in enumerate(workbook.worksheets)]

        return WorkbookDocument(
            path=file_path,
            file_type=file_type,
            worksheets=worksheets,
            openpyxl_workbook=workbook,
        )

    def save(self, document: WorkbookDocument, path: str | Path) -> None:
        """Save an XLSX/XLSM document back to disk."""
        file_path = Path(path)
        workbook = self.sync_document_to_workbook(document)
        workbook.save(file_path)
        document.path = file_path
        document.mark_clean()

    def sync_document_to_workbook(self, document: WorkbookDocument) -> Workbook:
        """Write document cells into the backing openpyxl workbook."""
        workbook = document.openpyxl_workbook or Workbook()

        for worksheet_document in document.worksheets:
            sheet = self._get_or_create_sheet(workbook, worksheet_document)
            self._sync_worksheet(worksheet_document, sheet)

        return workbook

    def _worksheet_from_openpyxl(self, sheet: Worksheet, index: int) -> WorksheetDocument:
        worksheet = WorksheetDocument(
            sheet_id=f"sheet-{index + 1}",
            title=sheet.title,
            source_sheet_name=sheet.title,
        )

        for row in sheet.iter_rows():
            for cell in row:
                if cell.value is None:
                    continue
                row_index = cell.row - 1
                column_index = cell.column - 1
                worksheet.cells[(row_index, column_index)] = CellData(
                    value=cell.value,
                    formula=cell.value if isinstance(cell.value, str) and cell.value.startswith("=") else None,
                    number_format=cell.number_format,
                    style_id=cell.style_id,
                    readonly_style_ref=copy(cell._style),
                )
                worksheet.max_row = max(worksheet.max_row, row_index + 1)
                worksheet.max_column = max(worksheet.max_column, column_index + 1)

        worksheet.max_row = max(worksheet.max_row, sheet.max_row or 0)
        worksheet.max_column = max(worksheet.max_column, sheet.max_column or 0)
        worksheet.rebuild_view()
        return worksheet

    def _get_or_create_sheet(self, workbook: Workbook, worksheet_document: WorksheetDocument) -> Worksheet:
        sheet_name = worksheet_document.source_sheet_name or worksheet_document.title
        if sheet_name in workbook.sheetnames:
            return workbook[sheet_name]

        if len(workbook.worksheets) == 1 and workbook.worksheets[0].title == "Sheet":
            sheet = workbook.worksheets[0]
            sheet.title = sheet_name
            return sheet
        return workbook.create_sheet(sheet_name)

    def _sync_worksheet(self, worksheet_document: WorksheetDocument, sheet: Worksheet) -> None:
        row_order = self._save_row_order(worksheet_document)
        snapshot = self._snapshot_rows(sheet, worksheet_document.max_row, worksheet_document.max_column)

        for target_row_index, source_row_index in enumerate(row_order, start=1):
            source_row = snapshot.get(source_row_index, {})
            for source_column_index in range(worksheet_document.max_column):
                target_cell = sheet.cell(row=target_row_index, column=source_column_index + 1)
                cell_data = worksheet_document.get_cell(source_row_index, source_column_index)
                self._write_cell(target_cell, cell_data, source_row.get(source_column_index))

    def _snapshot_rows(
        self,
        sheet: Worksheet,
        max_row: int,
        max_column: int,
    ) -> dict[int, dict[int, dict[str, Any]]]:
        snapshot: dict[int, dict[int, dict[str, Any]]] = {}
        for row_index in range(max_row):
            snapshot[row_index] = {}
            for column_index in range(max_column):
                cell = sheet.cell(row=row_index + 1, column=column_index + 1)
                snapshot[row_index][column_index] = {
                    "style": copy(cell._style),
                    "number_format": cell.number_format,
                    "font": copy(cell.font),
                    "fill": copy(cell.fill),
                    "border": copy(cell.border),
                    "alignment": copy(cell.alignment),
                    "protection": copy(cell.protection),
                }
        return snapshot

    def _write_cell(
        self,
        target_cell: Any,
        cell_data: CellData,
        source_cell_snapshot: dict[str, Any] | None,
    ) -> None:
        target_cell.value = cell_data.formula or cell_data.value
        if source_cell_snapshot is None:
            return
        target_cell._style = copy(source_cell_snapshot["style"])
        target_cell.number_format = source_cell_snapshot["number_format"]
        target_cell.font = copy(source_cell_snapshot["font"])
        target_cell.fill = copy(source_cell_snapshot["fill"])
        target_cell.border = copy(source_cell_snapshot["border"])
        target_cell.alignment = copy(source_cell_snapshot["alignment"])
        target_cell.protection = copy(source_cell_snapshot["protection"])

    @staticmethod
    def _save_row_order(worksheet: WorksheetDocument) -> list[int]:
        if worksheet.sort_state is None:
            return list(range(worksheet.max_row))

        rows = list(range(worksheet.max_row))
        reverse = worksheet.sort_state.direction == "desc"
        column = worksheet.sort_state.column
        rows.sort(key=lambda row: WorksheetDocument._sort_key(worksheet.get_cell(row, column).value), reverse=reverse)
        return rows

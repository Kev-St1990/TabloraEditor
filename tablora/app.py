"""Application bootstrap for the CSV/XLSX editor."""

import tkinter as tk

from tablora.config import APP_NAME
from tablora.actions import FormatCellsCommand, UndoRedoManager
from tablora.domain import FilterState, FormatCellsResult, FormatRequest, SortState, WorkbookDocument
from tablora.io import FileManager
from tablora.platform import ClipboardService, DialogService, ShortcutManager, TkClipboardBackend
from tablora.ui.filter_dialog import FilterDialog
from tablora.ui.format_dialog import FormatDialog
from tablora.ui.header_controller import HeaderController
from tablora.ui.menu_bar import MenuBar
from tablora.ui.sheet_manager import SheetManager


class CsvXlsxEditorApp(tk.Tk):
    """Main tkinter application window.

    The app currently wires the existing sheet placeholder into the new package
    layout. Later steps will move business logic into domain, IO, and action
    services while keeping this class as the composition root.
    """

    def __init__(self) -> None:
        super().__init__()
        self.tk.call("tk", "appname", APP_NAME)
        self.title(APP_NAME)
        self.geometry("1400x900")

        self.file_manager = FileManager()
        self.dialogs = DialogService()
        self.shortcut_manager = ShortcutManager()
        self.clipboard = ClipboardService(TkClipboardBackend(self))
        self.undo_redo_manager = UndoRedoManager()
        self.current_document: WorkbookDocument | None = None
        self.header_controller: HeaderController | None = None

        self.sheet_manager = SheetManager(self)
        self.sheet_manager.pack(fill="both", expand=True)
        self.menu_bar = MenuBar(self).attach_to(self)
        self.shortcut_manager.bind_standard_shortcuts(self, self)

    def on_open_file(self, event: object | None = None) -> object | None:
        """Open a spreadsheet file through the platform dialog service."""
        path = self.dialogs.choose_open_path()
        if not path:
            return event
        try:
            self.current_document = self.file_manager.open(path)
            self.sheet_manager.sheet_view.load_worksheet(self.current_document.get_active_sheet())
            self._install_header_controller()
            self.undo_redo_manager.clear()
        except Exception as exc:  # pragma: no cover - routed through messagebox in real UI
            self.dialogs.show_error_message("Open file failed", str(exc))
        return event

    def on_open(self, event: object | None = None) -> object | None:
        """Shortcut-compatible alias for file opening."""
        return self.on_open_file(event)

    def on_save_file(self, event: object | None = None) -> object | None:
        """Save the current spreadsheet to its existing path."""
        if self.current_document is None:
            return self.on_save_as_file(event)
        try:
            self.file_manager.save(self.current_document)
        except Exception as exc:  # pragma: no cover - routed through messagebox in real UI
            self.dialogs.show_error_message("Save file failed", str(exc))
        return event

    def on_save(self, event: object | None = None) -> object | None:
        """Shortcut-compatible alias for save."""
        return self.on_save_file(event)

    def on_save_as_file(self, event: object | None = None) -> object | None:
        """Save the current spreadsheet to a new location."""
        if self.current_document is None:
            return event
        path = self.dialogs.choose_save_path(default_extension=f".{self.current_document.file_type}")
        if not path:
            return event
        try:
            self.file_manager.save(self.current_document, path)
        except Exception as exc:  # pragma: no cover - routed through messagebox in real UI
            self.dialogs.show_error_message("Save file failed", str(exc))
        return event

    def on_save_as(self, event: object | None = None) -> object | None:
        """Shortcut-compatible alias for save as."""
        return self.on_save_as_file(event)

    def on_undo(self, event: object | None = None) -> object | None:
        """Undo the last command."""
        if self.undo_redo_manager.undo():
            self.sheet_manager.sheet_view.refresh()
        return event

    def on_redo(self, event: object | None = None) -> object | None:
        """Redo the last undone command."""
        if self.undo_redo_manager.redo():
            self.sheet_manager.sheet_view.refresh()
        return event

    def on_copy(self, event: object | None = None) -> object | None:
        """Copy the current selection to the clipboard."""
        if self.current_document is None:
            return event
        matrix = self.sheet_manager.sheet_view.get_selected_source_matrix()
        if matrix:
            self.clipboard.copy_cells(matrix)
            return "break"
        return event

    def on_paste(self, event: object | None = None) -> object | None:
        """Paste clipboard contents into the active worksheet."""
        if self.current_document is None:
            return event
        matrix = self.clipboard.paste_cells()
        if matrix:
            start_cell = self.sheet_manager.sheet_view.get_selected_source_start_cell() or (0, 0)
            self.current_document.get_active_sheet().set_cells(start_cell[0], start_cell[1], matrix)
            self.sheet_manager.sheet_view.refresh()
            return "break"
        return event

    def on_filter_selected_column(self, event: object | None = None) -> object | None:
        """Open the filter dialog for the selected data column."""
        controller = self._ensure_header_controller()
        if controller is None:
            return event

        ui_column = self.sheet_manager.sheet_view.get_header_context_ui_column()
        if ui_column is None or ui_column <= 0:
            return event

        popup_state = controller.build_filter_popup_state(ui_column - 1)
        dialog = FilterDialog(self, popup_state, on_apply=controller.apply_filter_popup_state)
        dialog.wait_window()
        return event

    def on_clear_filters(self, event: object | None = None) -> object | None:
        """Clear all active column filters from the current worksheet."""
        controller = self._ensure_header_controller()
        if controller is None:
            return event
        controller.apply_filter_state(FilterState())
        return event

    def on_format_selected_cells(self, event: object | None = None) -> object | None:
        """Open the format dialog for the current selection."""
        if self.current_document is None:
            return event

        addresses = self.sheet_manager.sheet_view.get_selected_source_cells()
        if not addresses:
            return event

        self._open_format_dialog(
            scope_label=f"{len(addresses)} selected cell(s)",
            addresses=addresses,
        )
        return event

    def on_format_selected_column(self, event: object | None = None) -> object | None:
        """Open the format dialog for the targeted data column."""
        if self.current_document is None:
            return event

        ui_column = self.sheet_manager.sheet_view.get_header_context_ui_column()
        if ui_column is None or ui_column <= 0:
            return event

        worksheet = self.current_document.get_active_sheet()
        source_column = ui_column - 1
        addresses = [(row, source_column) for row in range(worksheet.max_row)]
        self._open_format_dialog(
            scope_label=f"column {self._column_label(source_column)}",
            addresses=addresses,
        )
        return event

    def on_sort_selected_column_ascending(self, event: object | None = None) -> object | None:
        """Sort the selected data column in ascending order."""
        return self._sort_selected_rows("asc", event)

    def on_sort_selected_column_descending(self, event: object | None = None) -> object | None:
        """Sort the selected data column in descending order."""
        return self._sort_selected_rows("desc", event)

    def on_sort_selected_values_ascending(self, event: object | None = None) -> object | None:
        """Sort the selected column values in ascending order."""
        return self._sort_selected_values("asc", event)

    def on_sort_selected_values_descending(self, event: object | None = None) -> object | None:
        """Sort the selected column values in descending order."""
        return self._sort_selected_values("desc", event)

    def on_exit(self, event: object | None = None) -> object | None:
        """Close the application."""
        self.destroy()
        return event

    def _selected_matrix(self) -> list[list[object]]:
        if self.current_document is None:
            return []
        worksheet = self.current_document.get_active_sheet()
        matrix: list[list[object]] = []
        for row_index in worksheet.get_display_rows():
            row_values = [worksheet.get_cell(row_index, column).value for column in range(worksheet.max_column)]
            matrix.append(row_values)
        return matrix

    def _install_header_controller(self) -> None:
        if self.current_document is None:
            self.header_controller = None
            return
        self.header_controller = HeaderController(
            worksheet=self.current_document.get_active_sheet(),
            workbook=self.current_document,
            undo_redo_manager=self.undo_redo_manager,
            sheet_view=self.sheet_manager.sheet_view,
        )
        self.sheet_manager.sheet_view.set_builtin_header_sort_actions_enabled(True)
        self._bind_tksheet_header_sort_proxies()
        self.sheet_manager.sheet_view.sheet.popup_menu_del_command("Sort rows Asc.")
        self.sheet_manager.sheet_view.sheet.popup_menu_del_command("Sort rows Desc.")
        self.sheet_manager.sheet_view.sheet.popup_menu_del_command("Sort values Asc.")
        self.sheet_manager.sheet_view.sheet.popup_menu_del_command("Sort values Desc.")
        self.sheet_manager.sheet_view.add_header_context_action(
            "Filter Selected Column...",
            self.on_filter_selected_column,
        )
        self.sheet_manager.sheet_view.add_header_context_action(
            "Format Column...",
            self.on_format_selected_column,
        )
        self.sheet_manager.sheet_view.add_header_context_action("Clear Filters", self.on_clear_filters)

    def _ensure_header_controller(self) -> HeaderController | None:
        if self.current_document is None:
            return None
        if self.header_controller is None or self.header_controller.worksheet is not self.current_document.get_active_sheet():
            self._install_header_controller()
        return self.header_controller

    def _sort_selected_column(self, direction: str, event: object | None = None) -> object | None:
        controller = self._ensure_header_controller()
        if controller is None:
            return event
        ui_column = self.sheet_manager.sheet_view.get_header_context_ui_column()
        if ui_column is None or ui_column <= 0:
            return event
        controller.apply_sort(SortState(column=ui_column - 1, direction=direction))
        return event

    def _sort_selected_rows(self, direction: str, event: object | None = None) -> object | None:
        return self._sort_selected_column(direction, event)

    def _sort_selected_values(self, direction: str, event: object | None = None) -> object | None:
        controller = self._ensure_header_controller()
        if controller is None:
            return event
        ui_column = self.sheet_manager.sheet_view.get_header_context_ui_column()
        if ui_column is None or ui_column <= 0:
            return event
        controller.apply_column_value_sort(ui_column - 1, reverse=direction == "desc")
        return event

    def _bind_tksheet_header_sort_proxies(self) -> None:
        header_canvas = getattr(self.sheet_manager.sheet_view.sheet, "CH", None)
        if header_canvas is None:
            return
        header_canvas._sort_columns = self._tksheet_sort_values_proxy
        header_canvas._sort_rows_by_column = self._tksheet_sort_rows_proxy

    def _tksheet_sort_values_proxy(
        self,
        event: object | None = None,
        columns: object | None = None,
        reverse: bool = False,
        validation: bool = True,
        key: object | None = None,
        undo: bool = True,
    ) -> object | None:
        return self._sort_selected_values("desc" if reverse else "asc", event)

    def _tksheet_sort_rows_proxy(
        self,
        event: object | None = None,
        column: int | None = None,
        reverse: bool = False,
        key: object | None = None,
        undo: bool = True,
    ) -> object | None:
        return self._sort_selected_column("desc" if reverse else "asc", event)

    def _sheet_ops(self) -> object:
        sheet_widget = self.sheet_manager.sheet_view.sheet
        sheet_par = getattr(sheet_widget, "PAR", None)
        return getattr(sheet_par, "ops", None)

    def _open_format_dialog(self, *, scope_label: str, addresses: list[tuple[int, int]]) -> None:
        worksheet = self.current_document.get_active_sheet() if self.current_document is not None else None
        if worksheet is None:
            return

        dialog = FormatDialog(
            self,
            scope_label=scope_label,
            preview_callback=lambda request: worksheet.preview_format_cells(addresses, request),
            apply_callback=lambda request: self._apply_format_request(addresses, request),
        )
        dialog.wait_window()

    def _apply_format_request(
        self,
        addresses: list[tuple[int, int]],
        request: FormatRequest,
    ) -> FormatCellsResult:
        worksheet = self.current_document.get_active_sheet() if self.current_document is not None else None
        if worksheet is None:
            return FormatCellsResult()

        command = FormatCellsCommand(
            worksheet=worksheet,
            addresses=addresses,
            request=request,
            workbook=self.current_document,
        )
        self.undo_redo_manager.execute(command)
        self.sheet_manager.sheet_view.refresh()
        result = command.last_result or FormatCellsResult()
        self.dialogs.show_info_message("Formatting applied", result.summary_message())
        return result

    @staticmethod
    def _column_label(source_column: int) -> str:
        label = ""
        column = source_column + 1
        while column > 0:
            column, remainder = divmod(column - 1, 26)
            label = chr(ord("A") + remainder) + label
        return label or "A"

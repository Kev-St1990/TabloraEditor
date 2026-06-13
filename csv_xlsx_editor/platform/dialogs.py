"""Platform dialog helpers for file and message interactions."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from csv_xlsx_editor.domain import FileType


@dataclass(frozen=True, slots=True)
class FileTypeFilter:
    """File type label and glob patterns for dialog boxes."""

    label: str
    patterns: tuple[str, ...]


@dataclass(slots=True)
class DialogService:
    """Wrap tkinter file dialogs and message boxes for testability."""

    ask_open_filename: Callable[..., str] | None = None
    ask_save_as_filename: Callable[..., str] | None = None
    ask_yes_no: Callable[..., bool] | None = None
    show_error: Callable[..., Any] | None = None
    show_info: Callable[..., Any] | None = None
    _filetypes: dict[FileType, FileTypeFilter] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self._filetypes:
            self._filetypes = {
                "csv": FileTypeFilter("CSV files", ("*.csv",)),
                "xlsx": FileTypeFilter("Excel workbooks", ("*.xlsx",)),
                "xlsm": FileTypeFilter("Macro-enabled workbooks", ("*.xlsm",)),
            }
        if self.ask_open_filename is None or self.ask_save_as_filename is None:
            from tkinter import filedialog, messagebox

            self.ask_open_filename = self.ask_open_filename or filedialog.askopenfilename
            self.ask_save_as_filename = self.ask_save_as_filename or filedialog.asksaveasfilename
            self.ask_yes_no = self.ask_yes_no or messagebox.askyesno
            self.show_error = self.show_error or messagebox.showerror
            self.show_info = self.show_info or messagebox.showinfo

    def filetypes(self) -> list[tuple[str, str]]:
        """Return tkinter-compatible file type filters."""
        return [
            (self._filetypes["csv"].label, " ".join(self._filetypes["csv"].patterns)),
            (
                "Excel workbooks",
                " ".join(
                    [
                        self._filetypes["xlsx"].patterns[0],
                        self._filetypes["xlsm"].patterns[0],
                    ]
                ),
            ),
            (self._filetypes["xlsx"].label, " ".join(self._filetypes["xlsx"].patterns)),
            (self._filetypes["xlsm"].label, " ".join(self._filetypes["xlsm"].patterns)),
            ("All files", "*.*"),
        ]

    def choose_open_path(self, *, initialdir: str | None = None, title: str = "Open file") -> str:
        """Open a file picker dialog and return the selected path."""
        return self.ask_open_filename(  # type: ignore[misc]
            title=title,
            initialdir=initialdir,
            filetypes=self.filetypes(),
        )

    def choose_save_path(
        self,
        *,
        initialdir: str | None = None,
        title: str = "Save file as",
        default_extension: str | None = None,
    ) -> str:
        """Open a save dialog and return the selected path."""
        return self.ask_save_as_filename(  # type: ignore[misc]
            title=title,
            initialdir=initialdir,
            defaultextension=default_extension or "",
            filetypes=self.filetypes(),
        )

    def choose_csv_delimiter(self, current_delimiter: str | None = None) -> str | None:
        """Resolve the delimiter to use for CSV operations.

        A real GUI dialog can be attached later; for now the service preserves
        the caller-provided delimiter or leaves the current choice unchanged.
        """
        return current_delimiter

    def confirm_discard_changes(self) -> bool:
        """Ask whether unsaved changes should be discarded."""
        return bool(self.ask_yes_no and self.ask_yes_no(title="Discard changes?", message="Unsaved changes will be lost."))  # type: ignore[misc]

    def show_error_message(self, title: str, message: str) -> None:
        """Display an error dialog."""
        if self.show_error is not None:
            self.show_error(title=title, message=message)

    def show_info_message(self, title: str, message: str) -> None:
        """Display an informational dialog."""
        if self.show_info is not None:
            self.show_info(title=title, message=message)

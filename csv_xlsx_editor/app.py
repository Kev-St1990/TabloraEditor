"""Application bootstrap for the CSV/XLSX editor."""

import tkinter as tk

from csv_xlsx_editor.config import APP_NAME
from csv_xlsx_editor.ui.sheet_manager import SheetManager


class CsvXlsxEditorApp(tk.Tk):
    """Main tkinter application window.

    The app currently wires the existing sheet placeholder into the new package
    layout. Later steps will move business logic into domain, IO, and action
    services while keeping this class as the composition root.
    """

    def __init__(self) -> None:
        super().__init__()
        self.title(APP_NAME)
        self.geometry("1400x900")

        self.sheet_manager = SheetManager(self)
        self.sheet_manager.pack(fill="both", expand=True)

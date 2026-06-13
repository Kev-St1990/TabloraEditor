"""Container for the active worksheet view."""

from tkinter import Frame
from typing import Any

from csv_xlsx_editor.ui.sheet_view import SheetView


class SheetManager(Frame):
    """Hosts the sheet view used by the main application window."""

    def __init__(self, master: Any) -> None:
        super().__init__(master)
        self.sheet_view = SheetView(self)
        self.sheet_view.pack(fill="both", expand=True)

"""Current tksheet placeholder embedded in a tkinter frame."""

from tkinter import Frame
from typing import Any


class SheetManager(Frame):
    """Hosts the tksheet widget for the current scaffold UI."""

    def __init__(self, master: Any) -> None:
        super().__init__(master)

        from tksheet import Sheet

        self.sheet = Sheet(self)
        self.sheet.enable_bindings()
        self.sheet.pack(fill="both", expand=True)

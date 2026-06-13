from tkinter import Frame
from tksheet import Sheet

class SheetManager(Frame):
    def __init__(self, master):
        super().__init__(master)

        self.sheet = Sheet(self)
        self.sheet.enable_bindings()
        self.sheet.pack(fill="both", expand=True)

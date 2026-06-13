import tkinter as tk
from tkinter import ttk
from sheet_manager import SheetManager

class CsvXlsxEditorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CSV/XLSX Editor")
        self.geometry("1400x900")

        self.sheet_manager = SheetManager(self)
        self.sheet_manager.pack(fill="both", expand=True)

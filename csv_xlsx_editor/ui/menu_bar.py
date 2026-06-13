"""Application menu bar."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class MenuBar:
    """Builds the File/Edit menu structure for the application."""

    app: Any

    def attach_to(self, root: Any) -> Any:
        """Create and attach a tkinter menu bar to the root window."""
        from tkinter import Menu

        menu_bar = Menu(root)

        file_menu = Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Open...", command=self.app.on_open_file)
        file_menu.add_command(label="Save", command=self.app.on_save_file)
        file_menu.add_command(label="Save As...", command=self.app.on_save_as_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.app.on_exit)
        menu_bar.add_cascade(label="File", menu=file_menu)

        edit_menu = Menu(menu_bar, tearoff=0)
        edit_menu.add_command(label="Undo", command=self.app.on_undo)
        edit_menu.add_command(label="Redo", command=self.app.on_redo)
        edit_menu.add_separator()
        edit_menu.add_command(label="Copy", command=self.app.on_copy)
        edit_menu.add_command(label="Paste", command=self.app.on_paste)
        menu_bar.add_cascade(label="Edit", menu=edit_menu)

        data_menu = Menu(menu_bar, tearoff=0)
        data_menu.add_command(label="Filter Selected Column...", command=self.app.on_filter_selected_column)
        data_menu.add_command(label="Clear Filters", command=self.app.on_clear_filters)
        menu_bar.add_cascade(label="Data", menu=data_menu)

        root.config(menu=menu_bar)
        return menu_bar

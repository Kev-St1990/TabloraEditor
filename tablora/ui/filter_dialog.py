"""Modal filter dialog for selecting allowed values in one column."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import tkinter as tk

from tablora.ui.filter_popup import FilterPopupState


@dataclass(slots=True)
class FilterDialogResult:
    """Capture the filter state returned by the dialog."""

    popup_state: FilterPopupState | None = None


class FilterDialog(tk.Toplevel):
    """A small modal dialog for building an Excel-style column filter."""

    def __init__(
        self,
        master: Any,
        popup_state: FilterPopupState,
        *,
        on_apply: Callable[[FilterPopupState], None],
    ) -> None:
        super().__init__(master)
        self.popup_state = popup_state
        self.on_apply = on_apply
        self.result = FilterDialogResult()
        self.title(f"Filter column {popup_state.column + 1}")
        self.resizable(True, True)
        self.transient(master)

        self.search_var = tk.StringVar(value=popup_state.search_text)
        self.include_blanks_var = tk.BooleanVar(value=popup_state.include_blanks)

        self._build_ui()
        self._sync_from_search()
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self.grab_set()
        self.search_entry.focus_set()

    def _build_ui(self) -> None:
        container = tk.Frame(self, padx=12, pady=12)
        container.pack(fill="both", expand=True)

        search_row = tk.Frame(container)
        search_row.pack(fill="x")
        tk.Label(search_row, text="Search").pack(anchor="w")
        self.search_entry = tk.Entry(search_row, textvariable=self.search_var)
        self.search_entry.pack(fill="x", pady=(2, 8))
        self.search_var.trace_add("write", lambda *_: self._sync_from_search())

        list_row = tk.Frame(container)
        list_row.pack(fill="both", expand=True)
        tk.Label(list_row, text="Values").pack(anchor="w")

        list_frame = tk.Frame(list_row)
        list_frame.pack(fill="both", expand=True, pady=(2, 8))
        self.listbox = tk.Listbox(list_frame, selectmode="multiple", exportselection=False)
        scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scrollbar.set)
        self.listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.listbox.bind("<<ListboxSelect>>", lambda *_: self._sync_selection_from_listbox())

        self.include_blanks_check = tk.Checkbutton(
            container,
            text="Include blanks",
            variable=self.include_blanks_var,
        )
        self.include_blanks_check.pack(anchor="w")

        button_row = tk.Frame(container)
        button_row.pack(fill="x", pady=(12, 0))
        tk.Button(button_row, text="All", command=self._select_all).pack(side="left")
        tk.Button(button_row, text="None", command=self._select_none).pack(side="left", padx=(8, 0))
        tk.Button(button_row, text="Cancel", command=self._cancel).pack(side="right")
        tk.Button(button_row, text="Apply", command=self._apply).pack(side="right", padx=(0, 8))

    def _visible_values(self) -> list[Any]:
        return self.popup_state.visible_values()

    def _sync_from_search(self) -> None:
        self.popup_state.set_search_text(self.search_var.get())
        visible_values = self._visible_values()

        self.listbox.delete(0, "end")
        for value in visible_values:
            self.listbox.insert("end", str(value))

        for index, value in enumerate(visible_values):
            if value in self.popup_state.selected_values:
                self.listbox.selection_set(index)

    def _sync_selection_from_listbox(self) -> None:
        visible_values = self._visible_values()
        selected_indices = set(self.listbox.curselection())
        hidden_selected_values = {
            value for value in self.popup_state.selected_values if value not in visible_values
        }
        selected_values = {visible_values[index] for index in selected_indices if index < len(visible_values)}
        self.popup_state.selected_values = hidden_selected_values | selected_values

    def _select_all(self) -> None:
        self.popup_state.select_all()
        self.search_var.set("")
        self.include_blanks_var.set(True)

    def _select_none(self) -> None:
        self.popup_state.select_none()
        self._sync_from_search()

    def _apply(self) -> None:
        self._sync_selection_from_listbox()
        self.popup_state.include_blanks = self.include_blanks_var.get()
        self.popup_state.set_search_text(self.search_var.get())
        self.result.popup_state = self.popup_state
        self.on_apply(self.popup_state)
        self.destroy()

    def _cancel(self) -> None:
        self.result.popup_state = None
        self.destroy()


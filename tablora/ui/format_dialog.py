"""Modal dialog for formatting decimal and date cell values."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import tkinter as tk
from tkinter import ttk

from tablora.domain import (
    KIND_LABELS,
    SOURCE_LABELS,
    TARGET_LABELS,
    FormatCellsResult,
    FormatRequest,
    ValueFormatKind,
    source_options_for_kind,
    target_options_for_kind,
)


@dataclass(slots=True)
class FormatDialogResult:
    """Capture the apply state returned by the dialog."""

    applied: bool = False
    result: FormatCellsResult | None = None


class FormatDialog(tk.Toplevel):
    """Collect formatting options and preview the outcome before applying."""

    def __init__(
        self,
        master: Any,
        *,
        scope_label: str,
        preview_callback: Callable[[FormatRequest], FormatCellsResult],
        apply_callback: Callable[[FormatRequest], FormatCellsResult],
    ) -> None:
        super().__init__(master)
        self.scope_label = scope_label
        self.preview_callback = preview_callback
        self.apply_callback = apply_callback
        self.result = FormatDialogResult()

        self.title("Format Cells")
        self.resizable(True, True)
        self.transient(master)

        self.kind_var = tk.StringVar(value=KIND_LABELS["date"])
        self.source_var = tk.StringVar()
        self.target_var = tk.StringVar()
        self.warning_var = tk.StringVar(value="")
        self.summary_var = tk.StringVar(value="")

        self._build_ui()
        self._sync_options()
        self._refresh_preview()
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self.grab_set()
        self.kind_combo.focus_set()

    def _build_ui(self) -> None:
        container = tk.Frame(self, padx=12, pady=12)
        container.pack(fill="both", expand=True)

        form = tk.Frame(container)
        form.pack(fill="x")

        tk.Label(form, text="Type").grid(row=0, column=0, sticky="w")
        self.kind_combo = ttk.Combobox(
            form,
            state="readonly",
            textvariable=self.kind_var,
            values=list(KIND_LABELS.values()),
        )
        self.kind_combo.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        self.kind_combo.bind("<<ComboboxSelected>>", lambda *_: self._on_kind_changed())

        tk.Label(form, text="Detect source as").grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.source_combo = ttk.Combobox(form, state="readonly", textvariable=self.source_var)
        self.source_combo.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))
        self.source_combo.bind("<<ComboboxSelected>>", lambda *_: self._refresh_preview())

        tk.Label(form, text="Target format").grid(row=2, column=0, sticky="w", pady=(8, 0))
        self.target_combo = ttk.Combobox(form, state="readonly", textvariable=self.target_var)
        self.target_combo.grid(row=2, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))
        self.target_combo.bind("<<ComboboxSelected>>", lambda *_: self._refresh_preview())

        tk.Label(form, text="Scope").grid(row=3, column=0, sticky="w", pady=(8, 0))
        tk.Label(form, text=self.scope_label).grid(row=3, column=1, sticky="w", padx=(8, 0), pady=(8, 0))
        form.columnconfigure(1, weight=1)

        tk.Label(container, text="Preview").pack(anchor="w", pady=(12, 2))
        preview_frame = tk.Frame(container)
        preview_frame.pack(fill="both", expand=True)

        self.preview_list = tk.Listbox(preview_frame, height=7, exportselection=False)
        preview_scroll = tk.Scrollbar(preview_frame, orient="vertical", command=self.preview_list.yview)
        self.preview_list.configure(yscrollcommand=preview_scroll.set)
        self.preview_list.pack(side="left", fill="both", expand=True)
        preview_scroll.pack(side="right", fill="y")

        tk.Label(container, textvariable=self.summary_var, justify="left").pack(anchor="w", pady=(8, 0))
        tk.Label(container, textvariable=self.warning_var, justify="left", fg="#8a4b00").pack(anchor="w", pady=(4, 0))

        button_row = tk.Frame(container)
        button_row.pack(fill="x", pady=(12, 0))
        tk.Button(button_row, text="Cancel", command=self._cancel).pack(side="right")
        tk.Button(button_row, text="Apply", command=self._apply).pack(side="right", padx=(0, 8))

    def _on_kind_changed(self) -> None:
        self._sync_options()
        self._refresh_preview()

    def _sync_options(self) -> None:
        kind = self._selected_kind()
        source_labels = [SOURCE_LABELS[option] for option in source_options_for_kind(kind)]
        target_labels = [TARGET_LABELS[option] for option in target_options_for_kind(kind)]
        self.source_combo.configure(values=source_labels)
        self.target_combo.configure(values=target_labels)
        self.source_var.set(source_labels[0])
        self.target_var.set(target_labels[0])

    def _selected_kind(self) -> ValueFormatKind:
        reverse = {label: key for key, label in KIND_LABELS.items()}
        return reverse[self.kind_var.get()]

    def _current_request(self) -> FormatRequest:
        kind = self._selected_kind()
        reverse_sources = {label: key for key, label in SOURCE_LABELS.items()}
        reverse_targets = {label: key for key, label in TARGET_LABELS.items()}
        return FormatRequest(
            kind=kind,
            source_hint=reverse_sources[self.source_var.get()],
            target=reverse_targets[self.target_var.get()],
        )

    def _refresh_preview(self) -> None:
        request = self._current_request()
        preview = self.preview_callback(request)
        self.preview_list.delete(0, "end")
        for item in preview.preview_items:
            suffix = f" [{item.note}]" if item.note else ""
            self.preview_list.insert("end", f"{item.address}: {item.original} -> {item.formatted}{suffix}")
        if not preview.preview_items:
            self.preview_list.insert("end", "No matching cells in the selected scope.")
        self.summary_var.set(
            f"Would change {preview.changed_count} cells. "
            f"Metadata only: {preview.metadata_only_count}, text changes: {preview.text_changed_count}."
        )
        warnings: list[str] = []
        if preview.ambiguous_count:
            warnings.append(f"{preview.ambiguous_count} ambiguous")
        if preview.invalid_count:
            warnings.append(f"{preview.invalid_count} not recognized")
        if preview.empty_count:
            warnings.append(f"{preview.empty_count} empty")
        self.warning_var.set("Warnings: " + ", ".join(warnings) if warnings else "")

    def _apply(self) -> None:
        request = self._current_request()
        self.result.result = self.apply_callback(request)
        self.result.applied = True
        self.destroy()

    def _cancel(self) -> None:
        self.result.applied = False
        self.result.result = None
        self.destroy()

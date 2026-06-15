"""Tests for platform shortcuts and file dialogs."""

import unittest
from dataclasses import dataclass, field
from unittest.mock import patch

from tablora.platform.dialogs import DialogService
from tablora.platform.shortcuts import ShortcutManager
from tablora.ui.menu_bar import MenuBar
from tablora.ui.sheet_view import SheetView


@dataclass
class RecordingRoot:
    """Minimal tkinter root double used to capture bindings and menu config."""

    bindings: list[tuple[str, object]] = field(default_factory=list)
    menu: object | None = None

    def bind(self, sequence: str, callback: object) -> None:
        self.bindings.append((sequence, callback))

    def config(self, **kwargs: object) -> None:
        self.menu = kwargs.get("menu")


class RecordingMenu:
    """Minimal menu double that records added entries."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        self.entries: list[tuple[str, str | None]] = []
        self.cascades: list[tuple[str, object]] = []

    def add_command(self, *, label: str, command: object) -> None:
        self.entries.append((label, getattr(command, "__name__", None)))

    def add_separator(self) -> None:
        self.entries.append(("---", None))

    def add_cascade(self, *, label: str, menu: object) -> None:
        self.cascades.append((label, menu))


@dataclass
class RecordingSheetWidget:
    """Capture context-menu registrations."""

    commands: list[tuple[str, object, dict[str, object]]] = field(default_factory=list)
    MT: object | None = None
    CH: object | None = None
    RI: object | None = None

    def popup_menu_add_command(self, label: str, command: object, **kwargs: object) -> None:
        self.commands.append((label, command, kwargs))


@dataclass
class RecordingHandlers:
    """Shortcut handler double with the required callback names."""

    calls: list[str] = field(default_factory=list)

    def on_open(self, event: object | None = None) -> object | None:
        self.calls.append("open")
        return event

    def on_save(self, event: object | None = None) -> object | None:
        self.calls.append("save")
        return event

    def on_save_as(self, event: object | None = None) -> object | None:
        self.calls.append("save_as")
        return event

    def on_undo(self, event: object | None = None) -> object | None:
        self.calls.append("undo")
        return event

    def on_redo(self, event: object | None = None) -> object | None:
        self.calls.append("redo")
        return event

    def on_copy(self, event: object | None = None) -> object | None:
        self.calls.append("copy")
        return event

    def on_paste(self, event: object | None = None) -> object | None:
        self.calls.append("paste")
        return event


class ShortcutAndDialogTests(unittest.TestCase):
    """Verify shortcut selection, dialog filters, and menu wiring."""

    def test_primary_modifier_depends_on_platform(self) -> None:
        with patch("sys.platform", "darwin"):
            self.assertEqual(ShortcutManager().primary_modifier(), "Command")
        with patch("sys.platform", "win32"):
            self.assertEqual(ShortcutManager().primary_modifier(), "Control")

    def test_standard_bindings_are_platform_specific(self) -> None:
        with patch("sys.platform", "darwin"):
            bindings = ShortcutManager().standard_bindings()
            self.assertEqual([binding.sequence for binding in bindings], [
                "<Command-o>",
                "<Command-s>",
                "<Command-Shift-S>",
                "<Command-z>",
                "<Command-y>",
                "<Command-c>",
                "<Command-v>",
            ])

    def test_binding_shortcuts_calls_root_bind(self) -> None:
        root = RecordingRoot()
        handlers = RecordingHandlers()

        with patch("sys.platform", "darwin"):
            sequences = ShortcutManager().bind_standard_shortcuts(root, handlers=handlers)

        self.assertEqual(len(root.bindings), 7)
        self.assertEqual(sequences[0], "<Command-o>")

    def test_dialog_service_exports_expected_filetypes(self) -> None:
        dialogs = DialogService(
            ask_open_filename=lambda **kwargs: "open.csv",
            ask_save_as_filename=lambda **kwargs: "save.csv",
            ask_yes_no=lambda **kwargs: True,
            show_error=lambda **kwargs: None,
            show_info=lambda **kwargs: None,
        )

        self.assertEqual(dialogs.filetypes()[0], ("CSV files", "*.csv"))
        self.assertIn(("Excel workbooks", "*.xlsx *.xlsm"), dialogs.filetypes())
        self.assertEqual(dialogs.choose_open_path(initialdir="/tmp"), "open.csv")
        self.assertEqual(dialogs.choose_save_path(initialdir="/tmp", default_extension=".csv"), "save.csv")
        self.assertTrue(dialogs.confirm_discard_changes())

    def test_menu_bar_attaches_commands(self) -> None:
        class FakeApp:
            def on_open_file(self, event=None): ...
            def on_save_file(self, event=None): ...
            def on_save_as_file(self, event=None): ...
            def on_exit(self, event=None): ...
            def on_undo(self, event=None): ...
            def on_redo(self, event=None): ...
            def on_copy(self, event=None): ...
            def on_paste(self, event=None): ...
            def on_format_selected_cells(self, event=None): ...
            def on_hide_selected_rows(self, event=None): ...
            def on_hide_selected_columns(self, event=None): ...
            def on_unhide_rows(self, event=None): ...
            def on_unhide_columns(self, event=None): ...
            def on_filter_selected_column(self, event=None): ...
            def on_clear_filters(self, event=None): ...

        with patch("tkinter.Menu", RecordingMenu):
            root = RecordingRoot()
            menu = MenuBar(FakeApp()).attach_to(root)

        self.assertIs(root.menu, menu)
        self.assertEqual(len(menu.cascades), 2)

    def test_sheet_view_registers_header_context_actions(self) -> None:
        sheet_view = SheetView.__new__(SheetView)
        sheet_view.sheet = RecordingSheetWidget()

        callback = lambda: None
        sheet_view.add_header_context_action("Filter Selected Column...", callback)

        self.assertEqual(len(sheet_view.sheet.commands), 1)
        label, stored_callback, kwargs = sheet_view.sheet.commands[0]
        self.assertEqual(label, "Filter Selected Column...")
        self.assertIs(stored_callback, callback)
        self.assertEqual(kwargs["header_menu"], True)
        self.assertEqual(kwargs["table_menu"], False)

    def test_sheet_view_registers_index_context_actions(self) -> None:
        sheet_view = SheetView.__new__(SheetView)
        sheet_view.sheet = RecordingSheetWidget()

        callback = lambda: None
        sheet_view.add_index_context_action("Hide Row", callback)

        self.assertEqual(len(sheet_view.sheet.commands), 1)
        label, stored_callback, kwargs = sheet_view.sheet.commands[0]
        self.assertEqual(label, "Hide Row")
        self.assertIs(stored_callback, callback)
        self.assertEqual(kwargs["index_menu"], True)
        self.assertEqual(kwargs["header_menu"], False)

    def test_sheet_view_registers_table_context_actions(self) -> None:
        sheet_view = SheetView.__new__(SheetView)
        sheet_view.sheet = RecordingSheetWidget()

        callback = lambda: None
        sheet_view.add_table_context_action("Hide Selected Rows", callback)

        self.assertEqual(len(sheet_view.sheet.commands), 1)
        label, stored_callback, kwargs = sheet_view.sheet.commands[0]
        self.assertEqual(label, "Hide Selected Rows")
        self.assertIs(stored_callback, callback)
        self.assertEqual(kwargs["table_menu"], True)
        self.assertEqual(kwargs["index_menu"], False)

    def test_sheet_view_registers_menu_icons(self) -> None:
        sheet_view = SheetView.__new__(SheetView)
        sheet_view.sheet = RecordingSheetWidget()

        callback = lambda: None
        sheet_view.add_header_context_action(
            "Sort values Asc.",
            callback,
            image="icon-asc",
            compound="left",
            accelerator="Ctrl+Shift+S",
        )

        self.assertEqual(sheet_view.sheet.commands[0][2]["image"], "icon-asc")
        self.assertEqual(sheet_view.sheet.commands[0][2]["compound"], "left")
        self.assertEqual(sheet_view.sheet.commands[0][2]["accelerator"], "Ctrl+Shift+S")

    def test_sheet_view_can_disable_builtin_sort_actions(self) -> None:
        @dataclass
        class HeaderTable:
            rc_sort_column_enabled: bool = True
            rc_sort_rows_enabled: bool = True

        sheet_view = SheetView.__new__(SheetView)
        sheet_view.sheet = RecordingSheetWidget(MT=HeaderTable())

        sheet_view.set_builtin_header_sort_actions_enabled(False)

        self.assertFalse(sheet_view.sheet.MT.rc_sort_column_enabled)
        self.assertFalse(sheet_view.sheet.MT.rc_sort_rows_enabled)

    def test_sheet_view_uses_header_context_column_when_present(self) -> None:
        @dataclass
        class HeaderCanvas:
            popup_menu_loc: int = 3

        sheet_view = SheetView.__new__(SheetView)
        sheet_view.sheet = RecordingSheetWidget(CH=HeaderCanvas())

        self.assertEqual(sheet_view.get_header_context_ui_column(), 3)

    def test_sheet_view_uses_index_context_row_when_present(self) -> None:
        @dataclass
        class IndexCanvas:
            popup_menu_loc: int = 2

        sheet_view = SheetView.__new__(SheetView)
        sheet_view.sheet = RecordingSheetWidget(RI=IndexCanvas())

        self.assertEqual(sheet_view.get_index_context_ui_row(), 2)


if __name__ == "__main__":
    unittest.main()

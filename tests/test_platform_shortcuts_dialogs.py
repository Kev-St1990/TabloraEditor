"""Tests for platform shortcuts and file dialogs."""

import unittest
from dataclasses import dataclass, field
from unittest.mock import patch

from csv_xlsx_editor.platform.dialogs import DialogService
from csv_xlsx_editor.platform.shortcuts import ShortcutManager
from csv_xlsx_editor.ui.menu_bar import MenuBar


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

        with patch("tkinter.Menu", RecordingMenu):
            root = RecordingRoot()
            menu = MenuBar(FakeApp()).attach_to(root)

        self.assertIs(root.menu, menu)
        self.assertEqual(len(menu.cascades), 2)


if __name__ == "__main__":
    unittest.main()

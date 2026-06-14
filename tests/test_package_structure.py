"""Smoke tests for the initial package structure."""

import importlib
import unittest


class PackageStructureTests(unittest.TestCase):
    """Verify that the first implementation step exposes stable modules."""

    def test_core_packages_are_importable(self) -> None:
        modules = [
            "tablora",
            "tablora.actions",
            "tablora.actions.command",
            "tablora.actions.edit_cell_command",
            "tablora.actions.filter_command",
            "tablora.actions.paste_range_command",
            "tablora.actions.sort_command",
            "tablora.actions.undo_redo_manager",
            "tablora.domain",
            "tablora.domain.cell_data",
            "tablora.domain.filter_state",
            "tablora.domain.sort_state",
            "tablora.domain.table_view",
            "tablora.domain.workbook_document",
            "tablora.domain.worksheet_document",
            "tablora.io",
            "tablora.io.csv_adapter",
            "tablora.io.exceptions",
            "tablora.platform",
            "tablora.platform.clipboard",
            "tablora.platform.dialogs",
            "tablora.platform.shortcuts",
            "tablora.ui",
            "tablora.ui.filter_popup",
            "tablora.ui.header_controller",
            "tablora.ui.menu_bar",
            "tablora.ui.sheet_mapping",
            "tablora.ui.sheet_view",
            "tablora.ui.sheet_manager",
        ]

        for module_name in modules:
            with self.subTest(module=module_name):
                self.assertIsNotNone(importlib.import_module(module_name))

    def test_main_app_class_is_exported(self) -> None:
        from tablora import CsvXlsxEditorApp

        self.assertEqual(CsvXlsxEditorApp.__name__, "CsvXlsxEditorApp")

    def test_app_exposes_shortcut_handlers(self) -> None:
        from tablora import CsvXlsxEditorApp

        for method_name in ["on_open", "on_save", "on_save_as", "on_undo", "on_redo", "on_copy", "on_paste"]:
            with self.subTest(method=method_name):
                self.assertTrue(hasattr(CsvXlsxEditorApp, method_name))

    def test_implementation_modules_are_importable(self) -> None:
        from tablora.domain.filter_manager import FilterManager
        from tablora.io.file_manager import FileManager
        from tablora.ui.sheet_manager import SheetManager

        self.assertEqual(FileManager.__name__, "FileManager")
        self.assertEqual(FilterManager.__name__, "FilterManager")
        self.assertEqual(SheetManager.__name__, "SheetManager")

"""Smoke tests for the initial package structure."""

import importlib
import unittest


class PackageStructureTests(unittest.TestCase):
    """Verify that the first implementation step exposes stable modules."""

    def test_core_packages_are_importable(self) -> None:
        modules = [
            "csv_xlsx_editor",
            "csv_xlsx_editor.actions",
            "csv_xlsx_editor.actions.command",
            "csv_xlsx_editor.actions.edit_cell_command",
            "csv_xlsx_editor.actions.filter_command",
            "csv_xlsx_editor.actions.paste_range_command",
            "csv_xlsx_editor.actions.sort_command",
            "csv_xlsx_editor.actions.undo_redo_manager",
            "csv_xlsx_editor.domain",
            "csv_xlsx_editor.domain.cell_data",
            "csv_xlsx_editor.domain.filter_state",
            "csv_xlsx_editor.domain.sort_state",
            "csv_xlsx_editor.domain.table_view",
            "csv_xlsx_editor.domain.workbook_document",
            "csv_xlsx_editor.domain.worksheet_document",
            "csv_xlsx_editor.io",
            "csv_xlsx_editor.io.csv_adapter",
            "csv_xlsx_editor.io.exceptions",
            "csv_xlsx_editor.platform",
            "csv_xlsx_editor.platform.clipboard",
            "csv_xlsx_editor.ui",
            "csv_xlsx_editor.ui.sheet_mapping",
            "csv_xlsx_editor.ui.sheet_view",
        ]

        for module_name in modules:
            with self.subTest(module=module_name):
                self.assertIsNotNone(importlib.import_module(module_name))

    def test_main_app_class_is_exported(self) -> None:
        from csv_xlsx_editor import CsvXlsxEditorApp

        self.assertEqual(CsvXlsxEditorApp.__name__, "CsvXlsxEditorApp")

    def test_implementation_modules_are_importable(self) -> None:
        from csv_xlsx_editor.domain.filter_manager import FilterManager
        from csv_xlsx_editor.io.file_manager import FileManager
        from csv_xlsx_editor.ui.sheet_manager import SheetManager

        self.assertEqual(FileManager.__name__, "FileManager")
        self.assertEqual(FilterManager.__name__, "FilterManager")
        self.assertEqual(SheetManager.__name__, "SheetManager")

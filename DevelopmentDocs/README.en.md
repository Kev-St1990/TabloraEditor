# Tablora

Tablora is a lightweight desktop editor for CSV and Excel files, built with `tkinter`, `tksheet`, and `openpyxl`.

The app is designed for everyday spreadsheet work: opening data, reviewing it, sorting, filtering, editing, and saving it again without constantly thinking about file-format details.

## Maintainer

- Kevin Staples
- GitHub: [Kev-St1990](https://github.com/Kev-St1990)

## Features

- Open and save CSV, XLSX, and XLSM files
- Preserve formulas when loading and saving
- Preserve formatting when saving without visual rendering in version 1
- Work with multiple worksheets
- Separate index column for row IDs
- Excel-compatible copy/paste
- Undo and redo
- Sort by left-clicking the header
- Autosize by double-clicking a column boundary
- Excel-style filters from the header context menu
- Sort values inside a column
- Sort rows by a selected column
- macOS and Windows support

## Behavior

- CSV delimiters are detected with `csv.Sniffer`, but can be overridden in the open dialog.
- XLSM files are loaded and saved with macro support.
- Sorting understands numeric values and date values, including German and English month abbreviations.
- The visible index column is UI-only and is not exported.

## Technology

- `tkinter` for the desktop UI
- `tksheet` as the spreadsheet widget
- `openpyxl` for XLSX and XLSM files

## Start

Run the app with:

```bash
python main.py
```

You can also install it as a package:

```bash
pip install .
```

That provides a launcher through the `gui_scripts` entry point:

```bash
tablora
```

## Standalone Builds

Recommended standalone build path:

- Windows: `pyinstaller tablora.spec`
- macOS: `pyinstaller tablora.spec`

The resulting artifacts are placed in `dist/`. Before building, install dependencies with `pip install -r requirements.txt`.

The earlier `py2app` path is not recommended for the current Tk/macOS setup.

See [BUILD.md](../BUILD.md) for a short step-by-step guide.

## Project Status

The codebase is organized into:

- `tablora.domain`
- `tablora.io`
- `tablora.ui`
- `tablora.actions`
- `tablora.platform`

The architecture is designed so that the core logic stays testable without a GUI.

## License

This project is open source and freely available.

The full license text is in [LICENSE.md](../LICENSE.md).

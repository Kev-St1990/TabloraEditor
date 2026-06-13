# Architektur: CSV/XLSX Editor

## Zielbild

Der Editor wird als klassische Desktop-Anwendung mit `tkinter` aufgebaut. Die Tabellenoberfläche basiert auf `tksheet`, während XLSX- und XLSM-Dateien über `openpyxl` geladen und gespeichert werden. CSV-Dateien werden über die Python-Standardbibliothek verarbeitet.

Der zentrale Entwurf trennt strikt zwischen:

- UI: Fenster, Menüs, Tabs, Dialoge und `tksheet`-Events
- Dokumentmodell: Workbook, Worksheets, Zellenwerte, Formeln, Formate, Filter- und Sortierzustand
- Datei-IO: CSV/XLSX/XLSM Import und Export
- Aktionen: Undo/Redo-fähige Änderungen
- Plattformintegration: Clipboard, Tastaturkürzel, Dateidialoge, Mac/Windows-Verhalten

Wichtig: Für XLSX- und XLSM-Dateien bleibt die `openpyxl.Workbook`-Instanz die Quelle für Formeln und Formatierungen. Die UI arbeitet auf einer editierbaren View-Schicht, damit Sortierung, Filterung und Indexspalte während der Bearbeitung nicht destruktiv auf die originale Worksheet-Struktur wirken. Beim Speichern wird eine aktive View-Sortierung bewusst in die gespeicherte Datei übernommen.

## Bestehende Projektstruktur

Aktuell vorhandene Dateien und Pakete:

- `main.py`: Einstiegspunkt, erzeugt `CsvXlsxEditorApp`
- `csv_xlsx_editor/app.py`: minimales `tk.Tk`-Fenster mit `SheetManager`
- `csv_xlsx_editor/ui/sheet_manager.py`: einfacher `Frame` mit einer `tksheet.Sheet`
- `csv_xlsx_editor/io/file_manager.py`: rudimentäres CSV-/XLSX-Laden
- `csv_xlsx_editor/domain/filter_manager.py`: Platzhalter für aktive Filter
- `csv_xlsx_editor/config.py`: App-Name und Version
- `requirements.txt`: enthält bereits `tksheet`, `openpyxl`, `pandas`, `tkinterdnd2`, `darkdetect`

Die alte Root-Modulstruktur wurde entfernt. Neue Implementierung erfolgt ausschließlich unter `csv_xlsx_editor/`.

## Vorgeschlagene Paketstruktur

```text
CSVEditor/
  main.py
  csv_xlsx_editor/
    __init__.py
    app.py
    config.py
    platform/
      __init__.py
      shortcuts.py
      clipboard.py
      dialogs.py
    domain/
      __init__.py
      workbook_document.py
      worksheet_document.py
      cell_data.py
      table_view.py
      sort_state.py
      filter_state.py
    io/
      __init__.py
      file_manager.py
      csv_adapter.py
      xlsx_adapter.py
    ui/
      __init__.py
      main_window.py
      menu_bar.py
      workbook_tabs.py
      sheet_view.py
      header_controller.py
      filter_popup.py
      status_bar.py
    actions/
      __init__.py
      command.py
      undo_redo_manager.py
      edit_cell_command.py
      paste_range_command.py
      sort_command.py
      filter_command.py
```

## Hauptkomponenten

### App-Schicht

#### `CsvXlsxEditorApp`

Ort: `csv_xlsx_editor/app.py`

Verantwortung:

- Startet die Anwendung
- Initialisiert Services und UI
- Hält den aktuellen `WorkbookDocument`-Zustand
- Verbindet Menüaktionen mit Use-Cases

Wichtige Attribute:

- `file_manager: FileManager`
- `clipboard_service: ClipboardService`
- `undo_redo_manager: UndoRedoManager`
- `main_window: MainWindow`
- `current_document: WorkbookDocument | None`

Wichtige Methoden:

- `open_file(path: str) -> None`
- `save_file(path: str | None = None) -> None`
- `close_document() -> None`
- `set_active_sheet(sheet_id: str) -> None`

#### `MainWindow`

Ort: `csv_xlsx_editor/ui/main_window.py`

Verantwortung:

- Baut das Hauptfenster aus Menü, Worksheet-Tabs, Sheet-View und Statusbar
- Verwaltet globale Tastaturkürzel
- Delegiert Nutzeraktionen an `CsvXlsxEditorApp`

Wichtige Bestandteile:

- `MenuBar`
- `WorkbookTabs`
- `SheetView`
- `StatusBar`

## Dokumentmodell

### `WorkbookDocument`

Ort: `csv_xlsx_editor/domain/workbook_document.py`

Repräsentiert eine geöffnete CSV-, XLSX- oder XLSM-Datei.

Wichtige Attribute:

- `path: str | None`
- `file_type: Literal["csv", "xlsx", "xlsm"]`
- `worksheets: list[WorksheetDocument]`
- `active_sheet_id: str`
- `openpyxl_workbook: openpyxl.Workbook | None`
- `dirty: bool`

Wichtige Methoden:

- `get_active_sheet() -> WorksheetDocument`
- `get_sheet(sheet_id: str) -> WorksheetDocument`
- `mark_dirty() -> None`
- `mark_clean() -> None`

Hinweis:

- Bei XLSX und XLSM wird `openpyxl_workbook` behalten, damit Formeln, Styles, Spaltenbreiten, Zahlenformate, Makrobestandteile bei XLSM und sonstige Workbook-Metadaten nicht verloren gehen.
- Bei CSV gibt es genau ein `WorksheetDocument`.

### `WorksheetDocument`

Ort: `csv_xlsx_editor/domain/worksheet_document.py`

Repräsentiert ein einzelnes Worksheet inklusive View-Zustand.

Wichtige Attribute:

- `sheet_id: str`
- `title: str`
- `source_sheet_name: str | None`
- `cells: dict[CellAddress, CellData]`
- `max_row: int`
- `max_column: int`
- `table_view: TableView`
- `sort_state: SortState | None`
- `filter_state: FilterState`

Wichtige Methoden:

- `get_cell(row: int, column: int) -> CellData`
- `set_cell(row: int, column: int, value: object) -> None`
- `get_display_rows() -> list[int]`
- `rebuild_view() -> None`

### `CellData`

Ort: `csv_xlsx_editor/domain/cell_data.py`

Transportiert Zelleninformationen zwischen IO, Domain und UI.

Wichtige Attribute:

- `value: object`
- `formula: str | None`
- `number_format: str | None`
- `style_id: object | None`
- `readonly_style_ref: object | None`

Hinweis:

- Formeln werden bei XLSX als Formelstring erhalten, z. B. `=SUM(A1:A3)`.
- Formatierungen sollten nicht in eigene UI-Styles übersetzt werden. Stattdessen speichert das Modell Referenzen auf die `openpyxl`-Styleinformationen und schreibt Werte in die bestehende Workbook-Struktur zurück.

### `TableView`

Ort: `csv_xlsx_editor/domain/table_view.py`

Beschreibt die sichtbare Projektion eines Worksheets.

Wichtige Attribute:

- `visible_source_rows: list[int]`
- `visible_source_columns: list[int]`
- `row_ids: dict[int, int]`

Verantwortung:

- Trennt sichtbare Zeilen von tatsächlichen Excel-/CSV-Zeilennummern
- Ermöglicht Filter und Sortierung ohne irreversible Umordnung der Quelldaten
- Liefert die Datenmatrix für `tksheet`

## Datei-IO

### `FileManager`

Ort: `csv_xlsx_editor/io/file_manager.py`

Fassade für alle Dateioperationen.

Wichtige Methoden:

- `open(path: str) -> WorkbookDocument`
- `save(document: WorkbookDocument, path: str | None = None) -> None`
- `detect_file_type(path: str) -> FileType`

Delegiert an:

- `CsvAdapter`
- `XlsxAdapter`

### `CsvAdapter`

Ort: `csv_xlsx_editor/io/csv_adapter.py`

Wichtige Methoden:

- `load(path: str, encoding: str = "utf-8-sig", delimiter: str | None = None) -> WorkbookDocument`
- `save(document: WorkbookDocument, path: str, delimiter: str = ",") -> None`
- `sniff_dialect(path: str, encoding: str = "utf-8-sig") -> CsvDialect`

Hinweis:

- CSV hat keine Formeln oder Formatierungen als native Metadaten.
- CSV-Dateien werden als ein Worksheet geladen.
- Beim Öffnen wird der Dialekt per `csv.Sniffer` erkannt.
- Der Öffnungsdialog zeigt den erkannten Delimiter an und erlaubt eine manuelle Auswahl, insbesondere Komma oder Semikolon.
- Der erkannte oder manuell gewählte Delimiter wird im `WorkbookDocument` gespeichert und beim Speichern als Standard verwendet.
- Beim Speichern unter kann der Delimiter erneut über den Speicherdialog festgelegt werden.

### `XlsxAdapter`

Ort: `csv_xlsx_editor/io/xlsx_adapter.py`

Wichtige Methoden:

- `load(path: str) -> WorkbookDocument`
- `save(document: WorkbookDocument, path: str) -> None`
- `sync_document_to_workbook(document: WorkbookDocument) -> openpyxl.Workbook`

Wichtige Regeln:

- XLSX mit `load_workbook(path, data_only=False)` laden, damit Formeln erhalten bleiben.
- XLSM mit `load_workbook(path, data_only=False, keep_vba=True)` laden, damit Makros und VBA-Bestandteile erhalten bleiben.
- Bestehende `openpyxl`-Zellen werden aktualisiert, nicht neu erzeugt, wenn Formatierungen erhalten bleiben sollen.
- Zellwerte und Formeln werden in die originale Workbook-Struktur zurückgeschrieben.
- Styles, Zahlenformate, Zeilenhöhen, Spaltenbreiten und Worksheet-Metadaten bleiben in `openpyxl` erhalten, solange nicht explizit geändert.
- Eine aktive View-Sortierung wird beim Speichern materialisiert: Die sichtbare Reihenfolge aus `TableView.visible_source_rows` wird in die gespeicherte Worksheet-Reihenfolge übernommen.
- Filter bleiben ein View-Zustand und entfernen beim Speichern keine ausgefilterten Daten.

## UI-Schicht

### `SheetView`

Ort: `csv_xlsx_editor/ui/sheet_view.py`

Kapselt `tksheet.Sheet`.

Verantwortung:

- Rendert aktive Worksheet-Daten
- Fügt eine separate Indexspalte für Zeilen-IDs hinzu
- Bindet Bearbeiten, Copy/Paste, Header-Klicks, Rechtsklicks und Autosize-Events
- Übersetzt UI-Koordinaten in Source-Koordinaten

Wichtige Attribute:

- `sheet: tksheet.Sheet`
- `worksheet: WorksheetDocument | None`
- `header_controller: HeaderController`
- `clipboard_service: ClipboardService`
- `undo_redo_manager: UndoRedoManager`

Wichtige Methoden:

- `load_worksheet(worksheet: WorksheetDocument) -> None`
- `refresh() -> None`
- `to_source_cell(ui_row: int, ui_column: int) -> tuple[int, int]`
- `from_source_cell(source_row: int, source_column: int) -> tuple[int, int]`
- `set_cell_from_ui(ui_row: int, ui_column: int, value: object) -> None`
- `copy_selection() -> None`
- `paste_selection() -> None`

### `WorkbookTabs`

Ort: `csv_xlsx_editor/ui/workbook_tabs.py`

Verantwortung:

- Zeigt mehrere Worksheets als Tabs
- Synchronisiert aktives Worksheet mit `WorkbookDocument`

Wichtige Methoden:

- `load_document(document: WorkbookDocument) -> None`
- `select_sheet(sheet_id: str) -> None`
- `on_tab_changed(...) -> None`

### `HeaderController`

Ort: `csv_xlsx_editor/ui/header_controller.py`

Verantwortung:

- Linksklick auf Header: Sortierung auslösen
- Rechtsklick auf Header: Filter-Popup öffnen
- Doppelklick auf Spaltengrenze: Autosize auslösen

Wichtige Methoden:

- `on_left_click_header(column: int) -> None`
- `on_right_click_header(column: int, x: int, y: int) -> None`
- `on_double_click_column_boundary(column: int) -> None`
- `autosize_column(column: int) -> None`

Sortierverhalten:

- Erster Linksklick: aufsteigend
- Zweiter Linksklick: absteigend
- Dritter Linksklick: Sortierung entfernen
- Die Sortierung wirkt zunächst nur auf die sichtbare View.
- Beim Speichern wird die aktuelle View-Sortierung in die Datei übernommen.

### `FilterPopup`

Ort: `csv_xlsx_editor/ui/filter_popup.py`

Excel-ähnliches Kontextmenü für Spaltenfilter.

Verantwortung:

- Werte der Spalte sammeln
- Suchfeld anzeigen
- Checkboxen für einzelne Werte anzeigen
- Alles auswählen/abwählen
- Filter anwenden oder zurücksetzen

Wichtige Methoden:

- `show(column: int, screen_x: int, screen_y: int) -> None`
- `load_distinct_values(values: list[object]) -> None`
- `apply_filter() -> None`
- `clear_filter() -> None`

## Sortierung und Filter

### `SortState`

Ort: `csv_xlsx_editor/domain/sort_state.py`

Wichtige Attribute:

- `column: int`
- `direction: Literal["asc", "desc"]`

### `FilterState`

Ort: `csv_xlsx_editor/domain/filter_state.py`

Wichtige Attribute:

- `column_filters: dict[int, ColumnFilter]`

Wichtige Methoden:

- `set_filter(column: int, allowed_values: set[object]) -> None`
- `clear_filter(column: int) -> None`
- `clear_all() -> None`
- `matches(row_values: list[object]) -> bool`

### `ColumnFilter`

Ort: `csv_xlsx_editor/domain/filter_state.py`

Wichtige Attribute:

- `allowed_values: set[object]`
- `search_text: str`
- `include_blanks: bool`

## Clipboard und Excel-kompatibles Copy/Paste

### `ClipboardService`

Ort: `csv_xlsx_editor/platform/clipboard.py`

Verantwortung:

- Plattformneutrales Lesen und Schreiben des Clipboards
- Tab-getrennte Textdaten für Excel-kompatibles Copy/Paste
- Zeilenumbrüche über `\r\n` schreiben, weil Excel unter Windows damit am zuverlässigsten arbeitet

Wichtige Methoden:

- `copy_cells(matrix: list[list[object]]) -> None`
- `paste_cells() -> list[list[str]]`
- `serialize_tsv(matrix: list[list[object]]) -> str`
- `parse_tsv(text: str) -> list[list[str]]`

Integration:

- `Cmd+C`, `Cmd+V`, `Cmd+Z`, `Cmd+Shift+Z` auf macOS
- `Ctrl+C`, `Ctrl+V`, `Ctrl+Z`, `Ctrl+Y` auf Windows

## Undo/Redo

### `UndoRedoManager`

Ort: `csv_xlsx_editor/actions/undo_redo_manager.py`

Wichtige Attribute:

- `undo_stack: list[Command]`
- `redo_stack: list[Command]`

Wichtige Methoden:

- `execute(command: Command) -> None`
- `undo() -> None`
- `redo() -> None`
- `clear() -> None`
- `can_undo() -> bool`
- `can_redo() -> bool`

### `Command`

Ort: `csv_xlsx_editor/actions/command.py`

Basisklasse für reversible Änderungen.

Wichtige Methoden:

- `execute() -> None`
- `undo() -> None`
- `redo() -> None`
- `description() -> str`

Konkrete Commands:

- `EditCellCommand`: einzelne Zelländerung
- `PasteRangeCommand`: mehrzellige Änderung
- `SortCommand`: Änderung von `SortState`
- `FilterCommand`: Änderung von `FilterState`

Hinweis:

- Sortieren und Filtern ändern primär den View-Zustand, nicht die Daten.
- Zellbearbeitung und Paste ändern das Dokumentmodell und markieren das Dokument als dirty.

## Indexspalte

Die Zeilen-ID wird als separate UI-Spalte dargestellt und gehört nicht zur Datei.

Regeln:

- Spalte `0` in `tksheet` ist die Indexspalte.
- Daten-Spalte `0` im Dokument entspricht UI-Spalte `1`.
- Die Indexspalte ist read-only.
- Die angezeigte ID entspricht standardmäßig der ursprünglichen Source-Zeilennummer.
- Sortierung und Filterung verändern die Reihenfolge der sichtbaren IDs, aber nicht die IDs selbst.

## Event-Flows

### Datei öffnen

```text
MainWindow -> CsvXlsxEditorApp.open_file(path)
CsvXlsxEditorApp -> FileManager.open(path)
FileManager -> CsvAdapter oder XlsxAdapter
Adapter -> WorkbookDocument
CsvXlsxEditorApp -> MainWindow.load_document(document)
MainWindow -> WorkbookTabs.load_document(document)
MainWindow -> SheetView.load_worksheet(active_sheet)
```

### Zelle bearbeiten

```text
tksheet edit event
SheetView.to_source_cell(...)
EditCellCommand erstellen
UndoRedoManager.execute(command)
WorksheetDocument.set_cell(...)
SheetView.refresh()
```

### Copy/Paste

```text
Copy:
SheetView liest Auswahl
SheetView übersetzt UI-Koordinaten in Source-Koordinaten
ClipboardService.copy_cells(matrix)

Paste:
ClipboardService.paste_cells()
PasteRangeCommand erstellen
UndoRedoManager.execute(command)
WorksheetDocument aktualisieren
SheetView.refresh()
```

### Header-Linksklick zum Sortieren

```text
tksheet header click
HeaderController.on_left_click_header(column)
SortCommand erstellen
WorksheetDocument.sort_state aktualisieren
WorksheetDocument.rebuild_view()
SheetView.refresh()
```

### Header-Rechtsklick zum Filtern

```text
tksheet header right click
HeaderController.on_right_click_header(column, x, y)
FilterPopup.show(...)
FilterPopup.apply_filter()
FilterCommand erstellen
WorksheetDocument.filter_state aktualisieren
WorksheetDocument.rebuild_view()
SheetView.refresh()
```

### Autosize per Doppelklick

```text
tksheet double click column boundary
HeaderController.on_double_click_column_boundary(column)
HeaderController.autosize_column(column)
tksheet column width aktualisieren
```

## Mac- und Windows-Unterstützung

### `ShortcutManager`

Ort: `csv_xlsx_editor/platform/shortcuts.py`

Verantwortung:

- Erkennt Plattform über `sys.platform`
- Registriert passende Modifiers
- Kapselt Unterschiede zwischen `Command` und `Control`

Wichtige Methoden:

- `primary_modifier() -> str`
- `bind_standard_shortcuts(root: tk.Tk, handlers: ShortcutHandlers) -> None`

### `DialogService`

Ort: `csv_xlsx_editor/platform/dialogs.py`

Verantwortung:

- Datei öffnen/speichern
- Plattformneutrale Dateitypfilter
- Fehlerdialoge und Bestätigungsdialoge
- CSV-Öffnungsoptionen für erkannten oder manuell gewählten Delimiter
- CSV-Speicheroptionen für Komma, Semikolon oder weiteren Delimiter

## Erhalt von Formeln, Makros und Formatierungen

XLSX-Dateien müssen mit `data_only=False` geladen werden. XLSM-Dateien müssen zusätzlich mit `keep_vba=True` geladen werden. Dadurch bleiben Formeln als Zellwerte sowie Makrobestandteile erhalten. Beim Speichern wird die bestehende `openpyxl.Workbook`-Struktur aktualisiert und gespeichert.

Regeln:

- Zellformel bleibt Formelstring, wenn der Wert mit `=` beginnt oder aus einer Formelzelle stammt.
- Zellformatierungen werden nicht durch UI-Daten überschrieben.
- Bestehende `openpyxl`-Zellen behalten Style, Fill, Font, Border, Alignment, Protection und Number Format.
- Neue Zellen können optional Style von Nachbarzellen übernehmen, aber das ist eine spätere Implementierungsentscheidung.
- `openpyxl` berechnet Formeln nicht neu. Excel berechnet sie beim Öffnen, wenn Workbook-Calculation-Properties entsprechend gesetzt werden.
- Formatierungen müssen in Version 1 nicht in `tksheet` sichtbar dargestellt werden.
- Ziel für Version 1 ist ein verlustfreier Formatierungserhalt beim Speichern, nicht visuelle Excel-Parität im UI.

## tksheet-Integration

`tksheet` sollte nicht direkt als Datenmodell verwendet werden. Es ist die View-Komponente.

Die UI-Matrix wird aus `WorksheetDocument.table_view` erzeugt:

```text
[Indexspalte, Spalte A, Spalte B, Spalte C, ...]
```

Koordinatenregel:

```text
source_column = ui_column - 1
source_row = table_view.visible_source_rows[ui_row]
```

Die Indexspalte hat keine Source-Spalte.

## Architekturentscheidungen

- CSV nutzt beim Öffnen `csv.Sniffer`; der Öffnungsdialog erlaubt eine manuelle Delimiter-Auswahl, insbesondere Komma und Semikolon.
- XLSM wird unterstützt. Der XLSX/XLSM-Adapter lädt XLSM-Dateien mit `keep_vba=True`.
- Sortierung ist während der Bearbeitung eine View-Sortierung. Beim Speichern wird die aktuell sortierte View-Reihenfolge in die Datei übernommen.
- Formatierungen müssen in Version 1 nicht im UI sichtbar sein. Verbindlich ist zunächst der verlustfreie Erhalt beim Speichern.

## Empfohlene Umsetzungsschritte

Der konkrete Implementierungsplan mit Tracker, Coding Guidelines, Teststrategie und Definition of Done liegt in `IMPLEMENTATION_PLAN.md`.

1. Paketstruktur anlegen und vorhandene Platzhalter in die neue Struktur überführen.
2. `WorkbookDocument`, `WorksheetDocument`, `CellData`, `TableView`, `SortState` und `FilterState` implementieren.
3. `CsvAdapter` und `XlsxAdapter` mit verlustarmem Roundtrip inklusive CSV-Delimiter-Auswahl und XLSM-Erhalt implementieren.
4. `SheetView` mit Indexspalte und Koordinatenmapping implementieren.
5. Copy/Paste über `ClipboardService` ergänzen.
6. Undo/Redo-Command-System hinzufügen.
7. Header-Controller für Sortierung, Autosize und Filter-Popup anbinden.
8. Mac-/Windows-Kürzel und Datei-Dialoge finalisieren.

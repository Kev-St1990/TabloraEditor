# CSV/XLSX Editor

Ein schlanker Desktop-Editor für Tabellen im CSV- und Excel-Format, gebaut mit `tkinter`, `tksheet` und `openpyxl`.

Die Anwendung ist für die tägliche Arbeit mit Tabellen gedacht: Daten öffnen, prüfen, sortieren, filtern, bearbeiten und wieder speichern, ohne die Datei- und Strukturdetails ständig im Kopf behalten zu müssen.

## Funktionen

- CSV, XLSX und XLSM öffnen und speichern
- Formeln beim Laden und Speichern erhalten
- Formatierungen beim Speichern verlustarm erhalten
- Mehrere Worksheets laden und wechseln
- Separate Indexspalte für Zeilen-IDs
- Excel-kompatibles Copy/Paste
- Undo und Redo
- Sortierung per Linksklick auf den Header
- Autosize per Doppelklick auf die Spaltengrenze
- Excel-ähnliche Filter per Rechtsklick auf den Header
- Sortierung von Werten innerhalb einer Spalte
- Sortierung von Zeilen nach ausgewählter Spalte
- Unterstützung für macOS und Windows

## Verhalten

- CSV-Delimiter werden per `csv.Sniffer` erkannt, können aber im Öffnungsdialog überschrieben werden.
- XLSM-Dateien werden mit Makro-Erhalt geladen und gespeichert.
- Die Sortierung berücksichtigt numerische Werte und Datumswerte, einschließlich deutscher und englischer Monatskürzel.
- Die sichtbare Indexspalte ist nur für die UI gedacht und wird nicht exportiert.

## Technologie

- `tkinter` für die Desktop-Oberfläche
- `tksheet` als Tabellen-Widget
- `openpyxl` für XLSX- und XLSM-Dateien

## Start

Die Anwendung wird über den normalen Python-Einstieg gestartet:

```bash
python main.py
```

Für eine Installation per Paket kannst du auch `pip install .` verwenden. Danach steht unter Windows und macOS ein Launcher über das `gui_scripts`-Entry-Point zur Verfügung:

```bash
csv-xlsx-editor
```

## Standalone Builds

Für ein direkt ausführbares Artefakt gibt es zwei Build-Pfade:

- Windows und allgemein: `pyinstaller csv_xlsx_editor.spec`
- macOS: `python setup_macos.py py2app`

Die erzeugten Dateien liegen anschließend in `dist/`. Dort findest du unter Windows das Standalone-Verzeichnis von PyInstaller und unter macOS das `.app`-Bundle von py2app.
Vor dem macOS-Build sollten die Projektabhängigkeiten bereits installiert sein, zum Beispiel mit `pip install -r requirements.txt`.
Der macOS-Bundle-Name ist dateisystemfreundlich und weicht deshalb vom Fenstertitel `CSV/XLSX Editor` ab.

## Projektstatus

Das Projekt ist modular aufgebaut in die Bereiche:

- `csv_xlsx_editor.domain`
- `csv_xlsx_editor.io`
- `csv_xlsx_editor.ui`
- `csv_xlsx_editor.actions`
- `csv_xlsx_editor.platform`

Die Architektur ist so ausgelegt, dass die Kernlogik ohne GUI testbar bleibt.

## Lizenz

Dieses Projekt ist Open Source und zur freien Verfügung.

Verwendung, Anpassung und Weitergabe sind ausdrücklich erwünscht. Die vollständigen Lizenzbedingungen stehen in [LICENSE.md](LICENSE.md).

# Implementierungsplan

Dieser Plan setzt die in `ARCHITECTURE.md` definierte Architektur um. Der Tracker ist die verbindliche Arbeitsliste und wird nach jedem abgeschlossenen Implementierungsschritt aktualisiert.

## Tracker

Statuswerte:

- `Offen`: Noch nicht begonnen
- `In Arbeit`: Aktuell in Umsetzung
- `Review`: Implementiert, Tests und Codequalität werden geprüft
- `Erledigt`: Implementiert, getestet und dokumentiert
- `Blockiert`: Benötigt Klärung oder externe Voraussetzung

| Schritt | Status | Ergebnis | Tests | Notizen |
| --- | --- | --- | --- | --- |
| 1. Paketstruktur anlegen und vorhandene Platzhalter überführen | Erledigt | Zielpaket `csv_xlsx_editor/` mit Subpackages angelegt; alte Root-Wrapper entfernt | Import-/Smoke-Tests bestanden | `main.py` nutzt ausschließlich das neue Paket |
| 2. Domainmodell implementieren | Erledigt | `WorkbookDocument`, `WorksheetDocument`, `CellData`, `TableView`, `SortState`, `FilterState` implementiert | Unit-Tests für Koordinaten, Filter, Sortierzustand, Workbook und CellData bestanden | Ohne tkinter/tksheet-Abhängigkeit testbar |
| 3. Datei-IO implementieren | Erledigt | CSV/XLSX/XLSM laden und speichern, Delimiter-Erkennung, Formeln/Formate/Makros erhalten | Roundtrip-Tests mit temporären Dateien bestanden | XLSM-Ladepfad nutzt `keep_vba=True`; Formeln mit `data_only=False`; Sortierung wird beim Speichern materialisiert |
| 4. SheetView mit Indexspalte und Koordinatenmapping implementieren | Offen | `tksheet`-View rendert aktive Worksheet-View | Unit-Tests für Mapping; UI-Smoke-Test optional | UI bleibt Adapter über Domainmodell |
| 5. Excel-kompatibles Copy/Paste ergänzen | Offen | Clipboard-Service mit TSV-Serialisierung | Unit-Tests für TSV Parse/Serialize und Range-Paste | Mac/Windows-Zeilenumbrüche beachten |
| 6. Undo/Redo-Command-System hinzufügen | Offen | Reversible Commands für Edit, Paste, Sort, Filter | Unit-Tests für Execute/Undo/Redo | Keine UI-Logik in Commands |
| 7. Header-Controller und Filter-Popup anbinden | Offen | Linksklick-Sortierung, Doppelklick-Autosize, Rechtsklick-Filter | Unit-Tests für Controller-Logik; UI-Smoke-Test optional | Filter entfernt beim Speichern keine Daten |
| 8. Plattformintegration finalisieren | Offen | Menüs, Dateidialoge, Shortcuts für macOS/Windows | Unit-Tests für Shortcut-Auswahl; manueller Smoke-Test | `Command` auf macOS, `Control` auf Windows |

## Umsetzungsgates

Jeder Schritt gilt erst als abgeschlossen, wenn alle Gates erfüllt sind:

1. Der Code folgt der in `ARCHITECTURE.md` beschriebenen Modulgrenze.
2. Neue Logik hat passende Unit-Tests.
3. Relevante öffentliche Klassen und Methoden haben Docstrings.
4. Der Testlauf ist erfolgreich.
5. Der Tracker in diesem Dokument ist aktualisiert.
6. Offene Folgepunkte sind im Tracker oder in einem kurzen Abschnitt `Folgearbeiten` dokumentiert.

## Coding Guidelines

### Modularität

- Domain-Code darf keine direkte Abhängigkeit zu `tkinter`, `tksheet` oder Dateidialogen haben.
- UI-Code darf Domainobjekte verwenden, aber keine Datei-IO-Details kennen.
- Datei-IO darf `openpyxl` und `csv` kapseln, aber keine UI-Komponenten importieren.
- Plattformcode kapselt macOS-/Windows-Unterschiede für Shortcuts, Clipboard und Dialoge.
- Commands verändern Domainobjekte über klar definierte Methoden und bleiben unabhängig von `tksheet`.

### Testbarkeit

- Geschäftslogik wird in reinen Python-Klassen gehalten.
- Koordinatenmapping, Sortierung, Filterung, TSV-Parsing und Undo/Redo müssen ohne GUI testbar sein.
- Datei-Roundtrips nutzen temporäre Dateien.
- UI-Klassen werden schlank gehalten und delegieren testbare Logik an Controller oder Services.
- Für `tkinter`/`tksheet` genügt zunächst ein Smoke-Test oder manuelle Prüfung, solange die Kernlogik über Unit-Tests abgedeckt ist.

### Docstrings

- Öffentliche Klassen erhalten Docstrings mit Zweck und Verantwortungsgrenze.
- Öffentliche Methoden erhalten Docstrings, wenn ihr Verhalten nicht trivial ist oder Koordinaten-/Dateiformatregeln enthält.
- Docstrings sollen konkrete Invarianten nennen, z. B. dass UI-Spalte `0` die Indexspalte ist.
- Interne Hilfsmethoden brauchen nur dann Docstrings, wenn sie nicht selbsterklärend sind.

### Typisierung

- Neue Module verwenden Type Hints.
- Domainobjekte sollten bevorzugt `dataclasses` nutzen, wenn sie hauptsächlich Zustand tragen.
- Literal-Typen werden für feste Zustände verwendet, z. B. `FileType`, Sortierrichtung und Trackerstatus.
- Rückgabewerte werden explizit typisiert.

### Fehlerbehandlung

- Datei-IO wirft fachliche Exceptions, z. B. `UnsupportedFileTypeError` oder `FileLoadError`.
- UI-Schicht übersetzt Exceptions in Dialoge.
- CSV-Dialekt-Erkennung muss einen Fallback auf manuelle Auswahl oder Standarddelimiter haben.
- XLSM-Speicherung darf Makros nicht stillschweigend entfernen.

### Persistenzregeln

- CSV speichert nur sichtbare Zellwerte, keine Formatierung.
- XLSX/XLSM speichert Werte und Formeln zurück in die bestehende Workbook-Struktur.
- Formatierungen werden in Version 1 nicht im UI gerendert, aber beim Speichern erhalten.
- Aktive View-Sortierung wird beim Speichern materialisiert.
- Filter sind nur View-Zustand und löschen beim Speichern keine ausgefilterten Zeilen.
- Die Indexspalte ist UI-only und wird niemals in CSV/XLSX/XLSM geschrieben.

### UI-Regeln

- `tksheet` ist View, nicht Datenmodell.
- Jede UI-Koordinate wird vor Änderungen über `SheetView` oder einen Mapping-Service in Source-Koordinaten übersetzt.
- Header-Interaktionen werden im `HeaderController` gebündelt.
- Filterdialoge ändern nur `FilterState` über Commands.
- UI-Refreshes erfolgen nach Domainänderungen kontrolliert und nicht aus Domainobjekten heraus.

## Teststrategie

Tests sollen unter `tests/` liegen und mit `unittest` ausführbar sein:

```bash
python -m unittest discover -s tests
```

Empfohlene Teststruktur:

```text
tests/
  test_domain_table_view.py
  test_domain_filter_state.py
  test_domain_sort_state.py
  test_io_csv_adapter.py
  test_io_xlsx_adapter.py
  test_platform_clipboard_serialization.py
  test_actions_undo_redo.py
  test_ui_coordinate_mapping.py
```

Mindestabdeckung pro Schritt:

- Schritt 1: Importtests für Hauptmodule und Einstiegspunkt
- Schritt 2: Domain-Unit-Tests für Datenzugriff, View-Reihenfolge, Filter und SortState
- Schritt 3: CSV-Dialekt, CSV-Roundtrip, XLSX-Formel-Roundtrip, Format-Erhalt, XLSM-Ladepfad
- Schritt 4: Indexspalte, Source/UI-Koordinaten, read-only Indexspalte
- Schritt 5: TSV-Serialisierung, TSV-Parsing, mehrzeiliges Paste-Verhalten
- Schritt 6: Undo/Redo-Stack, Redo-Invalidierung nach neuer Aktion, Command-Beschreibungen
- Schritt 7: Sortierzyklus, FilterState-Änderungen, Autosize-Berechnung
- Schritt 8: Shortcut-Mapping für macOS und Windows, Dialog-Dateitypfilter

## Schrittplan

### 1. Paketstruktur

Ziel:

- `csv_xlsx_editor/` mit Subpackages `domain`, `io`, `ui`, `actions`, `platform`
- Bestehende Platzhalter in die neue Struktur verschieben oder als Kompatibilitätsschicht erhalten
- `main.py` bleibt Einstiegspunkt

Akzeptanzkriterien:

- `python -m unittest discover -s tests` läuft erfolgreich
- `main.py` importiert die App aus dem neuen Paket
- Keine Domainlogik in UI-Modulen

### 2. Domainmodell

Ziel:

- Reines, GUI-freies Datenmodell
- Tabellenprojektion über `TableView`
- Filter- und Sortierzustände ohne Datei-IO-Abhängigkeit

Akzeptanzkriterien:

- Filter und Sortierung verändern die sichtbare Zeilenliste, nicht direkt die Rohdaten
- Indexspalte ist nicht Teil des Domain-Zellenrasters
- Unit-Tests decken leere Tabellen, gemischte Werte und ausgeblendete Zeilen ab

### 3. Datei-IO

Ziel:

- CSV, XLSX und XLSM über Adapter laden/speichern
- CSV-Delimiter über Sniffer plus manuelle Auswahl vorbereiten
- XLSX/XLSM erhalten Formeln und Formatierungen

Akzeptanzkriterien:

- CSV-Roundtrip erhält Zellwerte und Delimiter
- XLSX-Roundtrip erhält Formeln und Styles
- XLSM wird mit `keep_vba=True` geladen und ohne Makroverlust gespeichert
- Aktive View-Sortierung wird beim Speichern materialisiert

### 4. SheetView

Ziel:

- `tksheet` rendert `WorksheetDocument`
- UI-Indexspalte ist read-only
- Mapping zwischen UI- und Source-Koordinaten ist zentralisiert

Akzeptanzkriterien:

- UI-Spalte `0` ist Indexspalte
- Daten-Spalte `0` entspricht UI-Spalte `1`
- Sortierte/gefilterte Views liefern korrekte Source-Zeilen

### 5. Copy/Paste

Ziel:

- Excel-kompatibles TSV Copy/Paste
- Mehrzellige Paste-Aktionen über `PasteRangeCommand`

Akzeptanzkriterien:

- TSV wird mit Tabs und Excel-kompatiblen Zeilenumbrüchen serialisiert
- Paste respektiert Zielkoordinate und überschreibt nur den Zielbereich
- Undo stellt den vorherigen Zellbereich wieder her

### 6. Undo/Redo

Ziel:

- Einheitliches Command-System
- Undo/Redo für Zelländerung, Paste, Sortierung und Filter

Akzeptanzkriterien:

- `execute()` legt Command auf Undo-Stack
- `undo()` verschiebt Command auf Redo-Stack
- Neue Aktion nach Undo leert Redo-Stack
- Dokument wird bei Datenänderungen als dirty markiert

### 7. Header-Controller und Filter

Ziel:

- Linksklick auf Header toggelt Sortierung
- Doppelklick auf Spaltengrenze autosized
- Rechtsklick öffnet Excel-ähnlichen Filter

Akzeptanzkriterien:

- Sortierzyklus ist `asc -> desc -> none`
- Filter-Popup kann Werte auswählen, suchen und zurücksetzen
- Filter bleiben View-Zustand und löschen keine Daten

### 8. Plattformintegration

Ziel:

- macOS- und Windows-kompatible Tastaturkürzel
- Datei- und CSV-Optionendialoge
- Fehlerdialoge

Akzeptanzkriterien:

- macOS nutzt `Command`, Windows nutzt `Control`
- Öffnen/Speichern bietet CSV, XLSX und XLSM an
- CSV-Dialog kann Sniffer-Ergebnis überschreiben

## Automatische Tracker-Aktualisierung

Bei jedem Umsetzungsschritt wird dieser Ablauf verwendet:

1. Status des Schritts auf `In Arbeit` setzen.
2. Implementierung durchführen.
3. Tests für den Schritt ergänzen.
4. Testlauf ausführen.
5. Status auf `Review` setzen, wenn Implementierung fertig ist.
6. Status auf `Erledigt` setzen, wenn Tests bestanden sind und keine offenen Blocker bestehen.
7. `Notizen` mit relevanten Entscheidungen oder Folgearbeiten aktualisieren.

## Definition of Done

Ein Feature ist fertig, wenn:

- Es fachlich umgesetzt ist.
- Es über Unit-Tests abgedeckt ist.
- Relevante Klassen und Methoden Docstrings enthalten.
- Die Modulgrenzen aus `ARCHITECTURE.md` eingehalten werden.
- Der Tracker aktualisiert wurde.
- `python -m unittest discover -s tests` erfolgreich läuft.

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
| 1. Paketstruktur anlegen und vorhandene Platzhalter überführen | Erledigt | Zielpaket `tablora/` mit Subpackages angelegt; alte Root-Wrapper entfernt | Import-/Smoke-Tests bestanden | `main.py` nutzt ausschließlich das neue Paket |
| 2. Domainmodell implementieren | Erledigt | `WorkbookDocument`, `WorksheetDocument`, `CellData`, `TableView`, `SortState`, `FilterState` implementiert | Unit-Tests für Koordinaten, Filter, Sortierzustand, Workbook und CellData bestanden | Ohne tkinter/tksheet-Abhängigkeit testbar |
| 3. Datei-IO implementieren | Erledigt | CSV/XLSX/XLSM laden und speichern, Delimiter-Erkennung, Formeln/Formate/Makros erhalten | Roundtrip-Tests mit temporären Dateien bestanden | XLSM-Ladepfad nutzt `keep_vba=True`; Formeln mit `data_only=False`; Sortierung wird beim Speichern materialisiert |
| 4. SheetView mit Indexspalte und Koordinatenmapping implementieren | Erledigt | `SheetView` rendert Worksheet-Views über testbaren Matrix-Builder und Mapper | Unit-Tests für Mapping, Indexspalte, Sortierung, Filterung und Spaltenlabels bestanden | UI bleibt Adapter über Domainmodell |
| 5. Excel-kompatibles Copy/Paste ergänzen | Erledigt | Clipboard-Service mit TSV-Serialisierung und Range-Paste-Helfern | Unit-Tests für TSV Parse/Serialize und Range-Paste bestanden | Mac/Windows-Zeilenumbrüche beachten |
| 6. Undo/Redo-Command-System hinzufügen | Erledigt | Reversible Commands für Edit, Paste, Sort, Filter und Stack-Management implementiert | Unit-Tests für Execute/Undo/Redo, Redo-Invalidierung und Dirty-State bestanden | Keine UI-Logik in Commands |
| 7. Header-Controller und Filter-Popup anbinden | Erledigt | Linksklick-Sortierung, Doppelklick-Autosize, Rechtsklick-Filter und Popup-State-Handling implementiert | Unit-Tests für Controller-Logik und Popup-State bestanden | Filter entfernt beim Speichern keine Daten |
| 8. Plattformintegration finalisieren | Erledigt | Menüs, Dateidialoge, Shortcuts für macOS/Windows und App-Komposition finalisiert | Unit-Tests für Shortcut-Auswahl, Dialog-Filters und Menü-Anbindung bestanden | `Command` auf macOS, `Control` auf Windows |
| 9. Zellformatierung für Dezimalzahlen und Datumswerte ergänzen | Erledigt | Selektion oder ganze Spalte kann zwischen DEU-/US-Zahlenformaten und gängigen Datumsformaten umgestellt werden; Vorschau, Warnungen und Undo/Redo sind angebunden | Domain-, Action-, UI-Import- und Roundtrip-Tests für Erkennung, Ambiguität, Persistenz und Rückgängig/Wiederholen bestanden | XLSX ändert nach Möglichkeit `number_format`, CSV schreibt Textwerte kontrolliert um; `Auto` überspringt mehrdeutige Datumswerte |

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

## Bug Summary und Learnings

### Beobachtete Bugklasse

In den letzten sechs Commits sind mehrere Folge-Bugfixes entstanden, obwohl die betroffenen Änderungen fachlich eng beieinander lagen. Die einzige erwartete Spezialbehandlung war die Datumssortierung. Alles andere hätte durch die bestehende Architektur und Tests stabil bleiben sollen.

### Ursache der Iterationen

- Die Sortierlogik war zu lange gleichzeitig an `tksheet`-Standardverhalten und an eigene Callback-Pfade gekoppelt.
- Die Unterscheidung zwischen `Sort rows` und `Sort values` war in UI und Domain zwar vorgesehen, aber an einigen Stellen indirekt verdrahtet.
- Ein aktiver Row-Sort konnte nach einem Value-Sort weiterwirken, wenn der View-State nicht explizit zurückgesetzt wurde.
- Kontextmenüs in `tksheet` reagieren empfindlich darauf, woher die Callback- und Bildreferenzen stammen. Icons verschwanden, wenn sie nicht stabil und direkt genug registriert wurden.
- Der Header-Kontext musste aus dem tatsächlich geklickten Header kommen, nicht nur aus der aktuellen Auswahl. Sonst verschiebt sich die Zielspalte bei Interaktionen leicht.

### Konkrete Learnings

- Jede Sortieraktion braucht eine eindeutige semantische Zuordnung:
  - `Sort rows` verändert die Zeilenreihenfolge.
  - `Sort values` verändert nur Zellen innerhalb einer Spalte.
- Value-Sort darf keine alte Row-Sortierung im View-State stehen lassen.
- Header-Aktionen sollten aus dem Kontextmenü-Target abgeleitet werden, nicht aus einer impliziten Selektion.
- Icons sollten über stabile Referenzen und über den tatsächlichen Menüeintrag registriert werden, nicht nur indirekt über temporäre Objektpfade.
- Für Sortierung lohnt sich eine Testfolge mit mehreren Schritten hintereinander, nicht nur der Einzelaufruf:
  - Row-Sort
  - Value-Sort
  - Date-Sort mit mehreren Formaten
  - Rücksprung per Undo/Redo

### Schutzregeln für zukünftige Änderungen

- Neue Sortierlogik immer zuerst im Domainmodell verankern, dann in Commands, erst danach in der UI verdrahten.
- Bei Value-Sort zusätzliche Tests schreiben, die einen zuvor aktiven Row-Sort mit einbeziehen.
- Datumssortierung immer mit unterschiedlichen Darstellungen prüfen, insbesondere englische und deutsche Monatskürzel.
- Wenn `tksheet`-Standardverhalten ersetzt wird, sollte das in einer klaren Integrationsschicht passieren, nicht verteilt über mehrere UI-Methoden.

### Kurzfassung für die weitere Arbeit

Die Architektur ist tragfähig, aber Sortier- und Header-Interaktionen sind ein Bereich mit hoher Kopplung an UI-Details. Künftige Änderungen sollten dort grundsätzlich mit kombinierten End-to-End- und Domain-Tests abgesichert werden, damit wir weniger Schleifen zwischen UI, Domain und Menüverdrahtung brauchen.

### Weitere Bugfix-Folge aus den Commits

Die nachfolgenden Commits haben zusätzliche Korrekturen sichtbar gemacht, die weniger die Kernarchitektur als die Verdrahtung und die Datenrepräsentation betrafen:

- `eb06b4cb4325e3d8927546603ca74bb3b7bc7f97`
  - Shortcut-Aliase fehlten für `on_open`, `on_save` und `on_save_as`, obwohl der Shortcut-Manager genau diese Handler erwartet.
  - Lehre: Öffentliche Handler-Namen sind Teil des UI-Vertrags und sollten mit einem Import- oder Strukturtest abgesichert werden.
- `fc321f7d6fab46c2f69c6d901a093c6f24b34aea`
  - Der native Row-Index von `tksheet` kollidierte mit unserer eigenen Indexspalte.
  - Lehre: Sobald eine UI-Komponente eine synthetische Spalte oder Zeile darstellt, sollte das native Gegenstück explizit deaktiviert oder klar getrennt werden.
- `209dd2f41e048b440611a3c53619c641041e6ee5`
  - CSV- und XLSX-Header mussten als eigene Metadaten mitgeführt werden, statt sie implizit in den ersten Datenzeilen mitzulesen.
  - Lehre: Datei-Header sind kein bloßes Anzeigeproblem, sondern Teil des Import-/Exportmodells und brauchen eine eigene Repräsentation.
- `31c58135af914aa9ba356734be0ca7b513e0d017`
  - Filteraktionen wurden erst spät an die Header-/View-Controller angehängt.
  - Lehre: Spaltenbezogene Aktionen gehören in denselben Interaktionskanal wie Sortierung und Autosize, sonst zerfällt die Bedienlogik unnötig.
- `fb0214786251cff27fb9157100888e6fb3df6eca`
  - Die Filteraktion war als Menüpunkts-Lösung zu lose eingebettet und wurde deshalb in das Header-Kontextmenü verschoben.
  - Lehre: Wenn eine Aktion klar an eine Spalte gebunden ist, sollte sie dort angeboten werden, wo auch die Zielspalte eindeutig ist.

### Datums-Sortierung als Sonderfall

Der Commit `e93fbd607bbd49b06f8f7abfbdbd6cf86db2e4c2` brachte die eigentliche fachliche Ausnahme: Sortierung nach Datum.

- Die Sortierung musste mehrere Datumsdarstellungen erkennen, darunter ISO-nahe Formate, `DD.MM.YYYY`, Texte mit englischen Monatsnamen und deutsche Kürzel wie `Mär`, `Mai` und `Dez`.
- In der Praxis brauchte diese Logik mehrere lokale Iterationen, bevor die Reihenfolge stabil und erwartbar war.
- Ein zentraler Stolperstein war, dass `Sort values` und `Sort rows` zwar ähnlich aussehen, aber unterschiedliche Zustände verändern. Gerade bei Datum war es wichtig, die Value-Sortierung sauber vom Row-Sort-View-State zu entkoppeln.
- Die Lösung lebt deshalb nicht nur von einem Parser, sondern auch von klaren Tests mit echten Beispielwerten und gemischten Monatsformaten.

### Lehre aus der Datums-Iteration

- Fachliche Sonderfälle wie Datum sollten früh als explizite Testdaten im Plan oder in der Testmatrix auftauchen.
- Wenn ein Sortierfall mehrere Formate akzeptieren muss, lohnt sich zuerst eine kleine Matrix aus repräsentativen Beispielwerten, bevor man UI-Verkabelung und Undo/Redo darauf setzt.
- Value-Sort und Row-Sort sollten auch dann gemeinsam getestet werden, wenn nur einer der beiden Pfade die Sonderlogik direkt nutzt.

### Gesamtbild

Die Folgefehler zeigen vor allem drei wiederkehrende Risiken:

1. UI-Verträge sind nicht nur Methodensignaturen, sondern auch Erwartung an Benennung, Platzierung und Menüstruktur.
2. Synthetische UI-Elemente wie Indexspalten brauchen eine eindeutige Trennung von nativen Widget-Funktionen.
3. Import-/Export-Metadaten wie Header gehören früh in das Domainmodell, sonst entstehen Off-by-one-Effekte und spätere Korrekturschleifen.

## Schrittplan

### 1. Paketstruktur

Ziel:

- `tablora/` mit Subpackages `domain`, `io`, `ui`, `actions`, `platform`
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

## Erweiterungsplan: Zellformatierung für Zahlen und Datum

### Zielbild

Der Editor soll für markierte Zellen oder eine ausgewählte Spalte Formatwechsel für Dezimalzahlen und Datumswerte anbieten, ohne das bestehende Modell aus Domain, Commands, UI und IO aufzubrechen.

Aus Nutzersicht soll die Funktion drei Dinge leisten:

- Bestehende Werte in gängige Zielschreibweisen überführen, zum Beispiel `1.234,56` nach `1,234.56` oder `23 Jan 2024` nach `23.01.2024`
- Vor dem Anwenden eine kleine Vorschau und erkennbare Warnungen für unklare Werte anzeigen
- Rückgängig machbar sein, genau wie Sortierung, Filter und normale Zellbearbeitung

### Scope der ersten Version

Unterstützte Zahlenformate:

- `DEU decimal`: `1.234,56`, `12,5`, `-0,75`
- `US decimal`: `1,234.56`, `12.5`, `-0.75`

Unterstützte Datumsfamilien:

- `DEU numerisch`: `14.06.2026`, optional mit Uhrzeit
- `US numerisch`: `06/14/2026`, optional mit Uhrzeit
- `ISO`: `2026-06-14`, optional mit Uhrzeit
- `DD MMM YYYY (EN)`: `23 Jan 2024`, `02 Feb 2024`, `03 Apr 2024`, `04 Jun 2024`
- `DD MMM YYYY (DE)`: `01 Mär 2024`, `25 Mär 2024`, `02 Mai 2024`, `31 Dez 2024`
- Optional gleiche Familien mit Zeitanteil, sofern der Ursprungswert bereits eine Uhrzeit trägt

Nicht Teil von v1:

- Frei definierbare Custom-Patterns
- Komplexe Locale-Systeme jenseits von DEU und US
- Vollständige UI-Formatvorschau pro einzelner Zelle im Raster
- Automatische Hintergrund-Konvertierung beim Öffnen einer Datei

### UX-Konzept für die Umsetzung

Eintrittspunkte:

- Header-Kontextmenü: `Format Column...`
- Hauptmenü: `Edit -> Format Selected Cells...`

Dialogfelder:

- `Typ`: `Decimal numbers` oder `Dates`
- `Quelle erkennen als`:
  - Bei Zahlen: `Auto`, `DEU decimal`, `US decimal`
  - Bei Datum: `Auto`, `DEU numeric`, `US numeric`, `ISO`, `Month name EN`, `Month name DE`
- `Zielformat`:
  - Bei Zahlen: `DEU decimal`, `US decimal`
  - Bei Datum: `DEU`, `US`, `ISO`, `DD MMM YYYY (EN)`, `DD MMM YYYY (DE)`
- `Bereich`: reine Info, etwa `column C` oder `18 selected cells`
- `Vorschau`: einige Beispielumwandlungen aus der aktuellen Auswahl
- `Warnungen`: Anzahl mehrdeutiger, unpassender oder leerer Zellen

UX-Regeln:

- Ohne explizites Anwenden findet keine Umformatierung statt.
- Bei `Auto` werden nur eindeutig erkennbare Werte verarbeitet.
- Mehrdeutige Werte wie `01/02/2024` werden standardmäßig übersprungen und im Dialog benannt.
- Nach erfolgreicher Aktion erscheint eine kurze Rückmeldung, z. B. `18 Zellen formatiert, 2 übersprungen`.
- Die gesamte Aktion ist ein einzelner Undo/Redo-Schritt.

### Fachregel: Darstellung ändern, Daten nicht still beschädigen

Es wird fachlich zwischen Dateitypen und Zellinhalten unterschieden:

- `XLSX/XLSM` mit echten numerischen oder Datumswerten:
  - Wenn der Zellwert als `int`, `float`, `date` oder `datetime` vorliegt, bleibt der Wert selbst unverändert.
  - Es wird vorzugsweise nur `number_format` angepasst.
- `CSV` oder textuelle Werte in beliebigen Formaten:
  - Der Zelltext wird kontrolliert umgeschrieben, weil keine nativen Formatmetadaten existieren.
- Textuelle Zellen in `XLSX/XLSM`:
  - Wenn der Inhalt nur als String vorliegt, darf für v1 ebenfalls eine Textumwandlung stattfinden.
  - Diese Umwandlung muss für den Nutzer im Dialog klar als echte Inhaltsänderung erkennbar bleiben.

Grundsatz:

- Die Funktion soll nie still zwischen inhaltlicher Wertumwandlung und bloßer Anzeigeformatierung springen.
- Der Rückgabestatus der Aktion muss zählen, wie viele Zellen als Metadaten-Änderung und wie viele als Textänderung behandelt wurden.

### Ambiguitätsregeln

Die Erkennung braucht bewusst konservative Regeln:

- `01/02/2024` ist unter `Auto` mehrdeutig und wird nicht konvertiert.
- `13/02/2024` ist eindeutig als DMY interpretierbar und darf auch unter `Auto` erkannt werden.
- Monatsnamen wie `Jan`, `Feb`, `Apr`, `Jun`, `Mär`, `Mai`, `Dez` sind eindeutig und dürfen unter `Auto` erkannt werden.
- Ungültige Werte wie `31/02/2024`, `foo`, leere Strings oder Mischtexte werden übersprungen.
- Wenn eine Spalte gemischte Schreibweisen enthält, soll die Vorschau die erkannten Familien sichtbar machen, statt nur eine stille Erfolgsquote anzuzeigen.

### Architekturelle Einordnung

#### Domain

Neue fachliche Logik gehört in die Domain oder in einen kleinen domainnahen Formatierungsservice:

- Erkennung von Zahlenformatfamilien
- Erkennung von Datumsformatfamilien
- Vorschau-Einträge und Ergebniszählung
- Reine Formatierungsoperationen auf Zell- oder Bereichsebene

Empfohlene neue Typen:

- `ValueFormatKind` oder ähnlicher Literal-/Enum-Typ für `decimal` und `date`
- `FormatSourceHint` für erklärte Quellfamilien
- `FormatTarget` für Zielschreibweisen
- `FormatPreviewItem` für Alt-/Neu-Vorschau plus Status
- `FormatCellsResult` für geändert, übersprungen, mehrdeutig, Fehler

Ergänzung im `WorksheetDocument`:

- Bereichsbezogene Methode für Formatierung einer Zellmenge oder einer ganzen Spalte
- Rückgabe eines strukturierten Ergebnisses für Dialog und Undo/Redo

#### Actions

Neue Command-Schicht:

- `FormatCellsCommand` für Selektion
- Optional derselbe Command auch für Spaltenformatierung, wenn der Zielbereich als Zellliste übergeben wird

Anforderungen:

- Snapshot-basiert rückgängig
- Markiert das Workbook als dirty
- Triggert wie andere Commands einen kontrollierten Refresh

#### UI

Neue UI-Bausteine:

- Kleiner modaler `FormatDialog`
- Menüeinträge in `MenuBar`
- Neuer Header-Kontextmenü-Eintrag über `SheetView` bzw. `HeaderController`-Verdrahtung

Aufgaben der UI:

- Zielbereich bestimmen: Selektion oder ganze Spalte
- Domainnahe Vorschau aufrufen
- Warnungen und Ergebnistext anzeigen
- Nach Anwenden Command ausführen

#### IO

Die bestehende IO-Architektur bleibt weitgehend unverändert, muss aber die Fachregel respektieren:

- `XlsxAdapter` muss geänderte `number_format`-Metadaten sauber zurückschreiben
- Textumgeschriebene Zellen werden wie normale Wertänderungen behandelt
- CSV speichert weiterhin nur die finalen sichtbaren Zellwerte

### Schrittablauf für die Implementierung

#### 9.1 Fachliche Testmatrix definieren

Ziel:

- Vor dem Coden eine feste Matrix repräsentativer Zahlen- und Datumswerte verankern
- Darin sowohl eindeutige als auch mehrdeutige und ungültige Fälle abdecken

Abdeckung für Datum:

- `23 Jan 2024`
- `24 Jan 2024`
- `02 Feb 2024`
- `09 Feb 2024`
- `13 Feb 2024`
- `20 Feb 2024`
- `29 Feb 2024`
- `01 Mär 2024`
- `04 Mär 2024`
- `09 Mär 2024`
- `25 Mär 2024`
- `27 Mär 2024`
- `03 Apr 2024`
- `30 Apr 2024`
- `02 Mai 2024`
- `04 Jun 2024`
- `07 Jun 2024`
- `14.06.2026`
- `06/14/2026`
- `2026-06-14`
- `01/02/2024` als Ambiguitätsfall

Abdeckung für Zahlen:

- `1.234,56`
- `1,234.56`
- `12,5`
- `12.5`
- `-0,75`
- `-0.75`
- Leere und ungültige Werte

Akzeptanzkriterien:

- Die Matrix liegt als Testdaten oder klarer Testblock in `tests/` vor.
- Ambiguitäts- und Skip-Regeln sind darin explizit sichtbar.

#### 9.2 Domain-Service für Erkennung und Vorschau

Ziel:

- Reinen Python-Service für Parsing, Ziel-Rendering und Vorschau aufbauen

Akzeptanzkriterien:

- Zahlen und Datum können ohne GUI in Quellfamilien erkannt werden.
- Zielstrings können für alle unterstützten Familien stabil erzeugt werden.
- Mehrdeutige Werte werden als eigener Status zurückgegeben, nicht per Exception.

#### 9.3 Worksheet-Integration für Bereichsformatierung

Ziel:

- Der aktive Bereich oder eine Spalte kann auf Domain-Ebene formatiert werden

Akzeptanzkriterien:

- Ganze Spalten und freie Zellmengen werden unterstützt.
- Ergebnis liefert Zähler für `geändert`, `übersprungen`, `mehrdeutig`.
- `rebuild_view()` wird kontrolliert ausgeführt, wenn Zellinhalte tatsächlich verändert wurden.

#### 9.4 Command für Undo/Redo

Ziel:

- Formatierungsaktion in das bestehende Undo/Redo-System integrieren

Akzeptanzkriterien:

- Ein Anwenden des Dialogs erzeugt genau einen Undo-Schritt.
- Undo und Redo stellen sowohl Zellwerte als auch `number_format` wieder her.

#### 9.5 Dialog und Menüverdrahtung

Ziel:

- Dialog mit Vorschau, Warnungen und Bereichsinformation in die App einhängen

Akzeptanzkriterien:

- `Edit -> Format Selected Cells...` funktioniert für aktuelle Selektion.
- `Format Column...` funktioniert aus dem Header-Kontextmenü für die gezielte Spalte.
- Ohne aktive Datei oder ohne gültigen Bereich passiert keine fehlerhafte Aktion.

#### 9.6 Persistenz- und Roundtrip-Absicherung

Ziel:

- Sicherstellen, dass die Fachunterscheidung zwischen Metadaten-Änderung und Textänderung beim Speichern konsistent bleibt

Akzeptanzkriterien:

- XLSX-Roundtrip behält echte Zahlen-/Datumswerte und schreibt geänderte `number_format`-Muster zurück.
- CSV-Roundtrip speichert umgeschriebene Texte erwartungsgemäß.
- Bereits vorhandene Styles werden durch reine Formataktionen nicht unnötig zerstört.

### Teststrategie für Schritt 9

Neue oder angepasste Tests:

- `tests/test_domain_cell_formatting.py`
  - Zahlen-Erkennung DEU/US
  - Datums-Erkennung für numerische, ISO- und Monatsnamen-Formate
  - Mehrdeutige Fälle
  - Zielrendering
- `tests/test_domain_workbook_document.py`
  - Bereichs- oder Spaltenformatierung auf Worksheet-Ebene
  - Gemischte Spalten mit geändert/übersprungen/mehrdeutig
- `tests/test_actions_undo_redo.py`
  - Formatierungs-Command ist reversibel
- `tests/test_ui_header_controller.py` oder neuer UI-Test
  - Spaltenaktion ist korrekt verdrahtet
- `tests/test_io_xlsx_adapter.py`
  - `number_format`-Änderung bleibt beim Speichern erhalten
- `tests/test_io_csv_adapter.py`
  - Textumgeschriebene Zielwerte landen korrekt in CSV

Manuelle Prüfpunkte:

- Selektion mit gemischten Datumsformaten zeigt sinnvolle Vorschau
- Spalte mit `23 Jan 2024`, `01 Mär 2024`, `02 Mai 2024`, `04 Jun 2024` lässt sich in `DEU` und `US` umwandeln
- Ambige Spalte mit `01/02/2024` zeigt Warnung und überspringt den Wert unter `Auto`
- XLSX-Datei mit echten Excel-Datums-/Zahlenzellen behält nach `Save` den numerischen Kernwert

### Besondere Risiken und Schutzregeln

Risiken:

- Verwechslung zwischen echter Wertumwandlung und bloßer Formatmetadaten-Änderung
- Zu aggressive Auto-Erkennung bei mehrdeutigen Datumswerten
- Verlust von `number_format` oder Styles bei XLSX-Zellen
- Undo/Redo stellt nur Werte, aber nicht Formatmetadaten wieder her

Schutzregeln:

- Auto-Erkennung immer konservativ halten
- Formatlogik zuerst komplett per Domain-Tests absichern, dann UI anbinden
- `number_format` nie ohne Test für XLSX-Roundtrip anfassen
- Vorschau und Ergebniszählung als Pflichtbestandteil des Flows behandeln, nicht als spätere Kosmetik

### Akzeptanz für Schritt 9 insgesamt

Der Schritt gilt als abgeschlossen, wenn:

- Selektion und Spaltenformatierung für Zahlen und Datum verfügbar sind
- Die unterstützten Datumsformate die gängigen numerischen, ISO- sowie EN-/DE-Monatskürzel abdecken
- Mehrdeutige Datumswerte unter `Auto` nicht stillschweigend falsch konvertiert werden
- Undo/Redo die gesamte Aktion sauber rückgängig macht
- XLSX und CSV die jeweiligen Persistenzregeln einhalten
- Tests für Erkennung, Vorschau, Command und Roundtrip grün sind

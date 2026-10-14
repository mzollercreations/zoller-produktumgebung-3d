# Zoller Produktumgebung 3D

Ein begehbarer 3D-Showroom mit **allen 59 Produkten von [zoller.info](https://www.zoller.info/produkte) plus »idChip«** (60, eigene Seite der Webseite), sortiert nach den sieben Themenwelten der Produktübersicht.

**Live:** https://mzollercreations.github.io/zoller-produktumgebung-3d/

## Die Halle

Eine Rundhalle mit zentralem Platz und schwebendem ZOLLER-Symbol. Rund um den Platz liegen sieben zweistufige Bühnen – eine pro Themenwelt – mit Rückwand, Bodenbeschriftung, Wegweiser-Stele und Unterkategorien auf der Stufenkante:

| Nr. | Themenwelt | Produkte |
|---|---|---|
| 01 | Einstellen & Messen | 12 – Vertikale/Horizontale Geräte, CNC-Steinbearbeitung, Speziallösungen |
| 02 | Toolmanagement | 20 – Software & Add-ons, TMS-Softwarepakete, Werkzeuglager, -montage, -transport, Datentransfer |
| 03 | Prüfen & Messen | 15 – Universal-Messmaschinen, prozessorientiertes Messen, CNC-Steinbearbeitung, Speziallösungen |
| 04 | Automation | 8 – Werkzeuglogistik, -vorbereitung, -bereitstellung, -inspektion, Laserbeschriftung |
| 05 | Schrumpftechnik | 2 |
| 06 | Werkzeugaufnahmen | 1 |
| 07 | Wuchttechnik | 1 |

Produkte, die zoller.info in mehreren Kategorien zeigt (z. B. »roboBox«, »conDress«), stehen einmal in ihrer Hauptkategorie und tragen im Detail-Panel den Hinweis „Auch zu finden unter …“.

Darstellung je nach Produktart: freigestellte Geräte auf Bodenplatten, Tischgeräte auf Säulen, Software als schwebende Symbole, Produkte ohne freigestelltes Bild auf Präsentationsdisplays, Werkzeugaufnahmen in einer Vitrine.

## Funktionen

- **Orbit-Ansicht**: ziehen, verschieben, zoomen zum Mauszeiger (Mausrad, Trackpad-Pinch, Zwei-Finger-Geste, `+`/`−`, Zoom-Knöpfe, Doppelklick); Klick auf ein Produkt fliegt hin und öffnet die Details
- **Ausstellungszone**: Kamera und Begehen bleiben innerhalb der gelben Grenzlinie; am Rand erscheint ein Hinweis
- **Steuerungslegende** unten rechts, passend zu Modus (Orbit/Begehen) und Gerät (Maus/Touch), einklappbar
- **Begehen**: Ego-Perspektive mit WASD/Pfeiltasten, Klick auf den Boden zum Hingehen, Treppenstufen und Kollision
- **Rundgang**: automatische Tour durch alle Themenwelten und Produkte
- **Detail-Panel** pro Produkt: Claim, Beschreibung, Highlights, Ausstattung, Modelle, technische Daten, Bilder, Links auf die Produktseite und alle Unterseiten der [ZOLLER Webseite](https://mzollercreations.github.io/zoller-webseite/), Shop- und Anfrage-Link
- **Suche** über Namen, Kategorien, Modelle und Werkzeugtypen
- **Werkzeugtyp-Filter** (wie auf zoller.info): passende Geräte leuchten in der Halle
- **Lageplan** mit Kameraposition, klickbar
- **AR-/3D-Ansicht** für alle Produkte mit offiziellen CAD-Daten (»venturion« 450/600/800, »smile«, »keeper«, »toolOrganizer«, »toolStation«, »zidCode«, »powerShrink 400«, »redomatic 600«, »toolBalancer 550«): Karte »In AR ansehen« im Detail-Panel, Marke »3D · AR« im Produktbild, »AR« in Liste, Suche und Tooltip. iPhone/iPad starten AR Quick Look direkt (Banner »Jetzt anfragen« → Kontakt), Android Scene Viewer bzw. WebXR; am Rechner öffnet ein Dialog mit drehbarem CAD-Modell, Maßlinien, Modellauswahl und QR-Code fürs Handy. Der QR-Code-Link `#ar/<produkt>/<modell>` zeigt sofort die AR-Ansicht, die Halle baut sich erst danach auf.
- **Deep-Links**: `#produkt/venturion`, `#themenwelt/automation`, `#ar/venturion/venturion800`
- Handy-Layout mit Bottom-Sheet, Fallback-Liste ohne WebGL, Tastatursteuerung (`?` zeigt alle Kürzel)

## Aufbau

| Pfad | Inhalt |
|---|---|
| `docs/` | Fertige Webseite (GitHub Pages) |
| `docs/data/products.json` | Kategorien, Produkte, Werkzeugtypen – erzeugt von `tools/build.py` |
| `docs/img/p/`, `docs/img/hd/` | Freigestellte Produktbilder für die 3D-Szene (512 px) und den Fokus (1024 px) |
| `docs/img/g/`, `docs/img/wall/` | Bilder für Detail-Panel und Rückwände |
| `docs/assets/js/world.js` | Three.js-Szene: Layout, Architektur, Exponate, Kamera, Begehen |
| `docs/assets/js/main.js` | Oberfläche: Themenwelten, Suche, Filter, Panel, Lageplan, Rundgang |
| `tools/build.py` | Extrahiert Texte und Bilder aus dem Projekt `zoller-webseite` |
| `docs/assets/js/ar.js` | AR-/3D-Dialog (model-viewer lädt erst beim Öffnen), Quick Look / Scene Viewer |
| `docs/ar/` | CAD-Modelle `<id>.glb` (3D, Android) + `<id>.usdz` (iPhone/iPad) + Vorschaubild – Kopie aus `zoller-webseite/assets/ar` |
| `tools/ar.py` | Kopiert Modelle und Bibliotheken aus der Webseite, ergänzt `products.json` um `ar` (Maße, Texte je Sprache) |

## AR-Modelle aktualisieren

Modelle, Maße (`content/ar_models.json`), Gerätenamen und alle Texte (`content/ar.json`, 19 Sprachvarianten) kommen aus der Webseite – dort erzeugt `tools/ar_models.py` die Dateien. Danach hier:

```bash
python3 tools/ar.py            # Modelle + model-viewer/Draco/QR kopieren, deutsche products.json ergänzen
python3 tools/build_locale.py  # Sprachfassungen (ruft ar.patch je Fassung auf)
```

Welches Produkt welche Modelle zeigt, steht in `content/ar.json` → `pages` (deutscher Produktpfad). `ar.js` wird über die Import-Map in `index.html` versioniert (`build_locale.py` → `with_version`).

## Lokal starten

```bash
python3 -m http.server 8790 --directory docs
```

Dann http://localhost:8790 öffnen.

## Daten neu erzeugen

Die Inhalte stammen aus der strukturierten Kopie von zoller.info im Nachbarprojekt `zoller-webseite`.

```bash
python3 -m venv .venv && .venv/bin/pip install pillow numpy
.venv/bin/python tools/build.py ../zoller-webseite
```

## Hinweise

- Texte, Produktbilder, Logo und Schrift T-Star gehören der E. Zoller GmbH & Co. KG. Jedes Produkt verlinkt auf seine Seite der ZOLLER Webseite.
- `world.js` läuft auch auf der Startseite der Webseite (Kino-Modus `cinematic: true`, Kamera per `setProgress()`); `tools/sync_showroom.py` dort übernimmt die Datei.
- Flüssigkeit: Die Halle baut sich in Portionen auf (Shader per `compileAsync`, Texturen über mehrere Frames), die Renderauflösung passt sich der Bildrate an (`adapt()`), im Kino-Modus läuft sie auf Retina-Displays ohne MSAA und rendert bei stehender Kamera nur jedes zweite Bild.
- Keine Tracker, keine Cookies, keine externen Abhängigkeiten zur Laufzeit (Three.js liegt lokal unter `docs/assets/vendor/`).

## Sprachfassungen für die Länderseiten

Für die Länderseiten der ZOLLER Webseite gibt es den Showroom auch auf Englisch (Kanada, USA), Französisch (Kanada) und Spanisch (Mexiko):
`/en-ca/`, `/fr-ca/`, `/es-mx/`, `/en-us/`. Oben rechts (auf dem Handy in der rechten Spalte) wechselt ein Knopf mit Weltkugel und Flagge Land und Sprache; die geöffnete Ansicht (`#produkt/…`, `#themenwelt/…`) bleibt dabei erhalten. Länderliste und Flaggen kommen aus `zoller-webseite/content/sites.json` bzw. `tools/flags.py` und werden von `build_locale.py` auch in die deutsche `docs/index.html` eingesetzt. Aufbau der Halle und Produktbilder sind dieselben wie in der deutschen Fassung; alle Texte stammen aus den Produktseiten des jeweiligen Landes (`zoller-webseite/content/sites/…`), die Oberfläche aus `tools/i18n.json`.

```bash
python3 tools/build.py          # deutsche Fassung (Pillow + numpy)
python3 tools/build_locale.py   # Sprachfassungen (nur Standardbibliothek)
```

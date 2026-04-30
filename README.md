# Stator-Statusanzeige

Eine kleine, moderne Python-Webanwendung zur Erfassung und Übersicht von Stator-Statusmeldungen.

## Enthaltene Funktionen
- Auswahl des Statortyps: **Ran** oder **Ros**
- Eingabe der **Sachnummer**
- Auswahl des Status: **iO** oder **niO**
- Auswahl von **Datum** und **Uhrzeit**
- Eingabe des **Lagerorts**
- Feld für **weitere Anmerkungen**
- Anzeige und Speicherung des **Bedieners**
- Übersicht der letzten Meldungen
- Kleine Statistik für Gesamt / iO / niO
- **CSV-Export**
- Lokale Speicherung in **SQLite**

## Starten
1. Python 3.10+ installieren
2. Im Projektordner ausführen:

```bash
pip install -r requirements.txt
python app.py
```

3. Im Browser öffnen:

```text
http://127.0.0.1:5000
```

## Für mehrere Nutzer im lokalen Netzwerk
Wenn der Rechner im Netzwerk erreichbar ist, kann die App über die IP des Rechners geöffnet werden, z. B.:

```text
http://192.168.0.25:5000
```

## Hinweise
- Die Datenbankdatei `stator_status.db` wird automatisch erzeugt.
- Der Bediener wird über die Browser-Sitzung gesetzt und bei jedem Eintrag mitgespeichert.
- Für eine einfache, überall abrufbare Lösung ist die App bewusst als **Einzeldatei mit Flask** umgesetzt.

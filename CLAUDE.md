# Projektregeln für Claude

Projekt: Nachbau des Pimoroni OnOff SHIM für den Raspberry Pi (siehe [README.md](README.md)).

## Sprache

- Antworten, README und Kommentare sind auf Deutsch (Schweizer Schreibweise, "ss" statt "ß").

## README.md

- Alle Bemerkungen, Annahmen und offene Punkte zum Projekt kommen zusätzlich ins README.
- Bestehende Inhalte nicht überschreiben, sondern ergänzen.
- Neutral formulieren, keine Ich- oder Du-Form aus dem Chat.
- Nur ein H1 (der Titel), alle weiteren Überschriften ab H2.
- Codeblöcke mit Sprachangabe (`text`, `ini`, ...).

## Rechtschreibung (cspell)

- Konfiguration in [cspell.json](cspell.json) (`en,de-CH`).
- Neue Fachwörter in `words` ergänzen, statt sie im Text umzuschreiben.

## KiCad

- Verwendet wird KiCad 10.
- Zwei Varianten: [kicad/](kicad/) (3 A, einfache CC-Beschaltung) und [kicad5A/](kicad5A/) (5 A, USB-PD mit STUSB4500). Der STUSB4500 muss vor dem ersten Einsatz per I2C programmiert werden (siehe README).
- Änderungen am Schaltplan per *Update PCB from Schematic* in die Platine übernehmen.
- Prüfung mit `kicad-cli` (installiert unter `C:\Program Files\KiCad\10.0\bin`): ERC für den Schaltplan, DRC für die Platine.
- GPIO-Belegung (GPIO4 Hold, GPIO17 Taster, GPIO27 LED) vor einer Platinenbestellung gegen <https://pinout.xyz/pinout/onoff_shim> prüfen.

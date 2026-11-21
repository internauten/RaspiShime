<!-- cspell:locale en,de-CH -->

# OnOff SHIM für Raspberry PI

Dies ist ein Versuch das OnOff SHIME von Pimoroni nach zu bauen.

## Funktionsweise

- Taster um den On or Off Vorgang zu initialisieren
- LED die leuchtet im On Zustand und nicht leuchtet im Off Zustand. Während des ShutDown soll sie blinken.
- USB C eingang
- Signale und Strom zum Raspberry PI über GPIO
- Eine Variante soll auch für Raspberry PI 5 taugen bis 5A

## Links

- Link zum Produkt: <https://shop.pimoroni.com/en-ch/products/onoff-shim?variant=41102600138>
- Pinout: <https://pinout.xyz/pinout/onoff_shim>
- Weitere Informationen: <https://retropie.org.uk/forum/topic/15727/tutorial-onoff-shim-exposed-neat-powerswitch-from-pimoroni>
- Die Software ist hier erreichbar: <https://get.pimoroni.com/onoffshim>

## Umsetzung

Der Schaltungsvorschlag deckt die Funktionen aus der Liste ab: Taster Ein/Aus, LED mit Blinken beim Shutdown, USB-C-Eingang, Versorgung über GPIO und bis 9.2 W für den Pi 5.

Die GPIO-Belegung stammt aus der Erinnerung an das Pimoroni-Original. Sie ist vor einer Platinenbestellung gegen das [Pinout](https://pinout.xyz/pinout/onoff_shim) zu prüfen.

### Prinzip

Ein P-MOSFET (Q1) schaltet die 5 V als High-Side-Schalter. Ein Taster zieht dessen Gate kurz auf Masse und schaltet den Pi damit ein. Sobald der Pi läuft, hält er den Schalter über GPIO4 und Q2 selbst fest (Selbsthaltung). Am Ende des Shutdowns lässt GPIO4 los und der Strom ist weg. Derselbe Taster löst per GPIO17 den Shutdown aus.

### Schaltplan

```text
USB-C                                                  Pi GPIO
 VBUS ──[F1 PTC 2.5A]──┬──[TVS SMBJ5.0A]── GND
                       │
                       ├── C_in 100µF/10V ── GND
                       │
                       ├────────────┬───────────────┐
                       │            │               │
                       │          R1 100k        C1 47µF
                       │            │               │
                       │            ├───────────────┘
                       │            │  (= Gate Q1)
                       │         D1 BAT54 (Anode am Gate)
                       │            │         │
                       │            │       Kathode ── Knoten A
                       │            │                   │
                       S            G                   ├── SW1 Taster ── GND
                      Q1 AO3401A (P-MOSFET)             │
                       D                                └── D2 BAT54 (Kathode an A,
                       │                                    Anode an GPIO17 = Pin 11)
                       │
                       ├── 5V_SW ──────────────────────────► Pin 2 + Pin 4 (5V)
                       ├── C_out 100µF ── GND
                       │
                       └── R_LED 1k ──┬── LED (grün) ── GND
                                      │
                                    Q3 D (2N7002, schliesst LED kurz)
                                      │ G ── R4 100k ── GND
                                      │ G ◄──────────── R5 1k ◄── GPIO27 (Pin 13)
                                    Q3 S ── GND

Selbsthaltung:
   Gate Q1 ── Drain Q2 (2N7002), Source Q2 ── GND
   Gate Q2 ◄── R2 1k ◄── GPIO4 (Pin 7)
   Gate Q2 ── R3 100k ── GND

GND USB-C ───────────────────────────────────────────────► Pin 6/9/14 (GND)
CC1, CC2 ── je 5.1k ── GND   (damit liefert das Netzteil 5 V)
```

### Funktionsablauf

| Zustand | Was passiert |
| --- | --- |
| Aus | R1 hält das Gate auf VBUS, Q1 sperrt. Der Pi ist stromlos. |
| Taster drücken | D1 zieht das Gate über den Taster nach GND, Q1 schaltet durch und der Pi bootet. |
| Taster loslassen | C1 und R1 halten das Gate etwa 7 s unten. In dieser Zeit setzt der Pi GPIO4 auf High, Q2 übernimmt die Selbsthaltung. |
| Betrieb, Taster drücken | D2 gibt GPIO17 nach Low, `gpio-shutdown` fährt den Pi herunter. |
| Shutdown fertig | `gpio-poweroff` setzt GPIO4 auf Low, Q2 sperrt, Q1 sperrt und der Strom ist weg. |
| LED | Sie leuchtet, sobald 5V_SW anliegt. Q3 schliesst sie kurz, sodass GPIO27 sie ausschalten oder blinken lassen kann. |

D2 ist nötig. Ohne D2 würde der 3.3-V-Pullup von GPIO17 über D1 das Gate auf etwa 3.6 V ziehen und Q1 teilweise einschalten.

### Software

Einträge in `/boot/firmware/config.txt`:

```ini
dtoverlay=gpio-shutdown,gpio_pin=17,active_low=1,gpio_pull=up
dtoverlay=gpio-poweroff,gpiopin=4,active_low=1
dtoverlay=gpio-led,gpio=27,label=shutdown-led,trigger=default-off
```

Zum Blinken während des Shutdowns ist ein kleiner systemd-Service nötig. Er setzt beim Shutdown `echo timer > /sys/class/leds/shutdown-led/trigger`.

### Hinweise

- **Pi 5:** Bei 9.2 W fliessen etwa 1.85 A bei 5 V. Q1 (AO3401A, ca. 50 mΩ) und der 2.5-A-PTC reichen dafür. Es sind breite Leiterbahnen oder Kupferflächen und mindestens 1 oz Kupfer zu verwenden. Der Pi 5 meldet beim Booten eventuell "Netzteil liefert keine 5 A". Das lässt sich mit `PSU_MAX_CURRENT=5000` in der EEPROM-Konfiguration übergehen.
- **Boot-Zeit:** Braucht der Pi länger als 7 s bis GPIO4, sind C1 oder R1 zu erhöhen.
- **Verbesserungen:** Möglich ist ein USB-C-Stecker mit Power-only-Pins (16-pol.). Ein Load-Switch-IC wie TPS2553 anstelle von PTC und Q1 wäre robuster, ist aber komplizierter.

## KiCad-Umsetzung

Das KiCad-Projekt liegt in [kicad/](kicad/) und wird mit `RaspiShime.kicad_pro` geöffnet.

### Stand

Geprüft wurde bisher nur mit `kicad-cli`: Der Schaltplan hat im ERC 0 Verstösse, und die exportierte Netzliste stimmt mit dem Entwurf überein. Die Schaltplanseite wurde als PDF gerendert und optisch kontrolliert, die Platine als 3D-Bild.

- **Schaltplan** ([RaspiShime.kicad_sch](kicad/RaspiShime.kicad_sch)): A3-Blatt mit allen Bauteilen aus dem Entwurf (USB-C, PTC, TVS, Q1 bis Q3, Taster, LED, 40-Pin-Header). Die Verbindungen laufen über Netz-Labels statt über gezogene Leitungen, deshalb wirkt der Plan etwas ungewohnt. Die `config.txt`-Zeilen stehen als Text im Plan.
- **Platine** ([RaspiShime.kicad_pcb](kicad/RaspiShime.kicad_pcb)): 65 × 42 mm mit Umriss, platzierten Footprints und zugewiesenen Netzen. Auf `F.Cu` und `B.Cu` liegt je eine GND-Fläche über den ganzen Umriss. Der DRC meldet noch 29 offene, nicht geroutete Verbindungen und 4 Wärmefallen mit zu wenig Anbindung, bis Bahnen und Stitching-Vias gesetzt sind.

**Externer Taster:** `J3` (zwei Pads, Footprint `PinHeader_1x02_P2.54mm_Vertical`) liegt parallel zu SW1 an BTN_A und GND. Ein externer Schliesser (Taster mit Arbeitskontakt) hat damit dieselbe Funktion wie SW1 (Einschalten und Shutdown). Bei langen Leitungen sind Störungen und ESD am Eingang möglich, kurze oder geschirmte Leitungen sind vorzuziehen.

Änderungen im Schaltplan werden über *Tools → Update PCB from Schematic* in die Platine übernommen. Die Footprints sind mit den Schaltplan-Symbolen verknüpft.

### Offene Punkte

- **Routing:** Die Platine ist nur platziert. Die 5V-Pfade (VBUS, 5V_SW) brauchen breite Leiterbahnen oder Kupferflächen, bei 2 A etwa 1 mm oder mehr. Die GND-Flächen sind angelegt, aber noch ohne Stitching-Vias, die beide Lagen verbinden. Zusätzlich fehlen Vias unter dem Exposed Pad und in der Nähe von Q1, PTC, Elkos und Header. Nach dem Routen sind die Zonen neu zu füllen (Taste `B`).
- **Platinenform:** Umriss und Platzierung sind eine grobe Annahme. Die Form des Pimoroni-SHIM und Montagelöcher sind nicht nachgebaut.
- **GPIO-Belegung:** GPIO4, 17 und 27 stammen aus der Erinnerung und sind gegen das [Pinout](https://pinout.xyz/pinout/onoff_shim) zu prüfen.
- **Footprints:** Der Header nutzt den Male-Header `PinHeader_2x20`. Ob Stift- oder Buchsenleiste passt, hängt vom Aufbau ab. Der Taster ist ein `SW_SPST_PTS810`, die Dioden sind `BAT54WS` in SOD-323 und der USB-C-Stecker ist ein GCT `USB4105`. Das sind Vorschläge.

## KiCad-Umsetzung 5A

Die zweite Variante liegt in [kicad5A/](kicad5A/) und wird mit `RaspiShime5A.kicad_pro` geöffnet. Sie ist für 5 V bei 5 A (25 W) ausgelegt, also für den Pi 5 mit voller Leistung. Das Prinzip mit Taster, Selbsthaltung, LED und Shutdown-Signal ist unverändert.

### Unterschiede zur 3-A-Variante

| Bereich | 3 A ([kicad/](kicad/)) | 5 A ([kicad5A/](kicad5A/)) |
|---|---|---|
| USB-C | 16-poliger Stecker, 5.1 kΩ an CC1/CC2 (Netzteil liefert höchstens 3 A) | 6-poliger Power-only-Stecker, CC1/CC2 an einen PD-Controller |
| Leistungsaushandlung | keine | STUSB4500 fordert 5 V/5 A per USB-PD an |
| Sicherung | PTC 2.5 A | PTC 6 A (Haltestrom), Bauform 2920 |
| Hauptschalter Q1 | AO3401A (SOT-23, ca. 50 mΩ) | DMP3013SFV (PowerDI3333, ca. 10 bis 13 mΩ) |
| Kondensatoren | 100 µF am Ausgang | 220 µF und 22 µF am Ausgang, 10 µF am Eingang |
| Platine | 65 × 42 mm, Netzklasse `Power3A` mit 1.5 mm Leiterbahnbreite für VBUS_RAW, VBUS und 5V_SW | 65 × 52 mm, Netzklasse `Power5A` mit 2 mm Leiterbahnbreite für VBUS_RAW, VBUS und 5V_SW |

Der STUSB4500 wird direkt aus VBUS versorgt (VDD, VSYS an GND). Seine Ausgänge VBUS_EN_SNK, ATTACH, POWER_OK2/3, GPIO und ALERT bleiben unbenutzt, weil Q1 den Strompfad schaltet. I2C (SDA/SCL) liegt auf den Pi-Pins 3 und 5, damit sich der Chip vom Pi aus programmieren lässt.

### STUSB4500 programmieren (zwingend vor dem ersten Einsatz)

Laut Datenblatt (DS12499, Tabelle 16) verhandelt der STUSB4500 ab Werk bis zu 3 Profile bis 20 V (Standard: PDO2 15 V, PDO3 20 V). An einem PD-Netzteil würde der Pi dann mit bis zu 20 V versorgt und zerstört. Der Chip muss deshalb per I2C im NVM konfiguriert werden:

- `SNK_PDO_NUMB` = 1 (nur PDO1, fest 5 V)
- Strom von PDO1 = 5 A

Ablauf:

1. Beim ersten Einschalten nur ein einfaches 5-V-Netzteil ohne PD verwenden, zum Beispiel ein USB-A-auf-USB-C-Kabel an einem normalen Ladegerät.
2. Taster drücken, der Pi bootet. Der Chip ist über VBUS versorgt und per I2C (Bus 1, GPIO2/3) erreichbar.
3. NVM schreiben, zum Beispiel mit einer STUSB4500-Bibliothek für Python oder Arduino, und mit Aus- und Einschalten prüfen.
4. Erst danach ein PD-Netzteil anschliessen.

Findet der Chip beim Netzteil kein Profil mit 5 V und 5 A, bleibt es laut Datenblatt bei einem Vertrag über 5 V mit dem Strom, den das Netzteil anbietet (zum Beispiel 3 A). Die Schaltung läuft dann, liefert aber nur diesen Strom.

### Voraussetzungen und Grenzen

- **Netzteil und Kabel:** Für 5 V/5 A braucht es ein Netzteil mit 5-V/5-A-Profil (wie das offizielle 27-W-Netzteil des Pi 5) und ein e-marked Kabel für 5 A.
- **Stecker:** Die Strombelastbarkeit des gewählten Steckers (GCT USB4125, 6-polig) ist vor der Bestellung im Datenblatt zu prüfen. Nicht jeder USB-C-Stecker ist für 5 A Dauerstrom ausgelegt.
- **GPIO-Header:** Die 5 V gehen nur über die Pins 2 und 4 zum Pi, bei 5 A also etwa 2.5 A pro Pin. Das liegt nahe am üblichen Grenzwert von Stiftleisten (etwa 3 A pro Pin).
- **Leiterbahnen:** Für 5 A sind breite Leiterbahnen (2 mm oder mehr) oder Kupferflächen auf beiden Lagen und 2 oz Kupfer sinnvoll. Im Platinenaufbau der 5-A-Platine sind 2 oz (0.07 mm) für beide Kupferlagen eingetragen (Dielektrikum 1.46 mm, Gesamtdicke 1.6 mm). Das dokumentiert die Wahl nur, das Kupfergewicht ist bei der Bestellung beim Hersteller zusätzlich auszuwählen. Unter Q1 und dem PTC ist Kupferfläche zur Wärmeabfuhr nötig. Die Verlustleistung von PTC und Q1 beträgt zusammen grob 0.7 W.
- **Pi-Konfiguration:** Der Pi bekommt über GPIO keine PD-Information. Für die volle Leistung ist in der EEPROM-Konfiguration `PSU_MAX_CURRENT=5000` zu setzen. Für USB-Geräte mit hohem Strombedarf kann zusätzlich `usb_max_current_enable=1` in der `config.txt` nötig sein.

### Stand

Geprüft wurde nur mit `kicad-cli`: Der Schaltplan hat im ERC 0 Verstösse, die Netzliste stimmt mit dem Entwurf überein, und der DRC meldet noch 51 offene, nicht geroutete Verbindungen und 2 Wärmefallen mit zu wenig Anbindung. Auf `F.Cu` und `B.Cu` liegt je eine GND-Fläche über den ganzen Umriss. Die Schaltplanseite wurde als PDF gerendert und optisch kontrolliert, die Platine als 3D-Bild. Die Schaltung wurde nicht aufgebaut oder getestet.

**Externer Taster:** Wie bei der 3-A-Variante liegt `J3` (zwei Pads, `PinHeader_1x02_P2.54mm_Vertical`) parallel zu SW1 an BTN_A und GND und ist für einen externen Schliesser gedacht. Bei langen Leitungen sind Störungen und ESD am Eingang möglich.

### Offene Punkte

- **STUSB4500-Beschaltung:** Die Werte stammen aus der Referenzschaltung im Datenblatt (Abschnitt 6.2, Bild 9): 1 µF an VREG_1V2 und VREG_2V7, 470 Ω an VBUS_VS_DISCH, 1 kΩ an DISCH, 100 kΩ nach GND an ADDR0, ADDR1 und RESET. Die Zeichnung im Datenblatt war als Text nur teilweise lesbar. Die genaue Verdrahtung (zum Beispiel VDD direkt an VBUS mit 1 µF) ist deshalb gegen Bild 9 zu prüfen.
- **CC-Schutz:** ESD-Schutz an CC1/CC2 (im Datenblatt ein ESDA25W) ist nicht vorgesehen.
- **Routing und Platine:** Die Platine ist nur platziert. Es gibt weder Leiterbahnen noch Stitching-Vias, die Leistungsnetze (VBUS_RAW, VBUS, 5V_SW) haben keine eigene Fläche, und die Platinenform ist eine grobe Annahme.
- **GPIO-Belegung:** Wie bei der 3-A-Variante gegen das [Pinout](https://pinout.xyz/pinout/onoff_shim) zu prüfen.

## Mechanischer Aufbau mit Buchsenleiste

Statt einer Stiftleiste kann an der Unterseite eine 2×20-Buchsenleiste mit extra langen Pins (Stacking-Header) sitzen. Die Buchse steckt dann auf dem Pi, und die langen Pins ragen oben durch die Platine, sodass dort wieder eine Stiftleiste für weitere Platinen oder Kabel zur Verfügung steht.

- **Footprint:** Der Footprint `PinSocket_2x20_P2.54mm_Vertical` ist das Spiegelbild von `PinHeader_2x20_P2.54mm_Vertical` (bei der Buchsenleiste liegt Pin 2 links von Pin 1). Er muss deshalb auf die Unterseite (`B.Cu`) gelegt werden, dann liegen alle Pad-Nummern wieder an denselben Koordinaten wie bei der Stiftleiste und passen zu den Pins am Pi. Auf der Oberseite würde die Belegung gespiegelt. In beiden Platinen (3 A und 5 A) liegt J2 so auf der Unterseite. Die Pad-Koordinaten sind gegenüber der früheren Stiftleiste unverändert.
- **Pinlänge oben:** Die Pins müssen über das höchste Bauteil auf der Oberseite hinausragen, damit eine weitere Platine darüber Platz hat. Das höchste Bauteil sind die Elektrolytkondensatoren (Bauhöhe etwa 5.4 mm, `CP_Elec_6.3x5.4`). Die genaue Pinlänge ist im Datenblatt des gewählten Stacking-Headers zu prüfen.
- **Abstand zum Pi:** Bei einer Buchsenleiste mit üblicher Bauhöhe von etwa 8.5 mm liegt die Platine rund 11 mm über dem Pi. Die Platine deckt den Pi grossflächig ab (65 × 42 mm bei 3 A, 65 × 52 mm bei 5 A). Beim Pi 5 mit Kühler oder aktivem Lüfter kann das zu eng werden. Dann ist ein Header mit höherem Buchsenkörper nötig, oder die Platine bekommt einen Ausschnitt über dem Kühler.
- **Unterseite:** Auf der Unterseite sitzen keine Bauteile. Der Buchsenkörper liegt auf der GND-Fläche von `B.Cu`, das ist unkritisch.
- **Strom:** Die 5 V laufen weiter nur über die Pins 2 und 4. Die Kontakte einer Buchsenleiste sind meist mit etwa 3 A pro Pin angegeben. Das ist bei der 5-A-Variante ein knapper Wert (siehe oben).
- **Rückwirkung:** Über die oberen Pins ist 5V_SW zugänglich. Eine aufgesteckte Platine darf nicht ebenfalls 5 V einspeisen, sonst speisen zwei Quellen dasselbe Netz.
- **3D-Ansicht:** KiCad enthält kein 3D-Modell für eine Buchsenleiste mit durchgehenden langen Stiften (Stacking-Header). Für J2 gibt es deshalb ein eigenes Modell [3d/stacking_header_2x20.step](3d/stacking_header_2x20.step). Es wird mit dem CadQuery-Skript [3d/stacking_header_2x20.py](3d/stacking_header_2x20.py) erzeugt (`python stacking_header_2x20.py 15`, Argument = Stiftlänge über der Platinenoberseite in mm, Standard 15 mm). Das Modell enthält den Buchsenkörper (8.5 mm hoch, schwarz) und 40 durchgehende Stifte (0.64 mm quadratisch, golden). Der Ursprung liegt in der Mitte von Pin 1, Pin 2 bei X = -2.54 mm wie beim Footprint `PinSocket_2x20_P2.54mm_Vertical`. Z = 0 ist die Platinenfläche auf der Bestückungsseite, der Körper liegt bei Z = 0 bis 8.5 mm und wird bei `B.Cu` automatisch nach unten gespiegelt. Die Stifte reichen von Z = 2 mm bis 16.6 mm unter Z = 0 (Platinendicke 1.6 mm plus 15 mm). Beide Platinen binden das Modell bei J2 über `${KIPRJMOD}/../3d/stacking_header_2x20.step` ein und verwenden es anstelle der beiden Standardmodelle. Die Einbindung ist nur in der Platine eingetragen (nicht in der Footprint-Bibliothek) und hat keinen Einfluss auf Netze oder Fertigungsdaten.
- **GPIO-Prüfung (pinout.xyz):** Die Seite nennt für den OnOff SHIM GPIO4 (Pin 7, "Shutdown") und GPIO17 (Pin 11, "Power Button") und gibt "Uses 2 GPIO pins" an. Damit stimmen GPIO4 und GPIO17 mit dieser Umsetzung überein. Die Seite nennt keinen GPIO für die rote LED und keine Signalpolarität. GPIO27 für die LED (Q3, R5) ist deshalb eine eigene Erweiterung dieser Umsetzung und kein Merkmal des Originals. Die Polarität von GPIO4 und GPIO17 ist gegen das Skript von Pimoroni (`get.pimoroni.com/onoffshim`) zu prüfen, bevor die `dtoverlay`-Zeilen in `config.txt` als gesichert gelten.
- **Polaritätsprüfung (Pimoroni-Daemon):** Der Installer `get.pimoroni.com/onoffshim` richtet den Bash-Daemon `cleanshutd` aus dem Repository `pimoroni/clean-shutdown` ein und schreibt nichts in `config.txt`. `setup.sh` setzt für den OnOff SHIM `trigger_pin 17`, `poweroff_pin 4`, `led_pin 17`, `hold_time 1`. GPIO17 ist ein Eingang mit Pull-up (`raspi-gpio set 17 ip pu`), der gedrückte Taster liest sich als Low (aktiv Low), und der Daemon fährt nach 1 s Low herunter. Dieselbe Leitung dient im Original auch als LED-Ausgang (Blinken). GPIO4 wird beim Ausschalten als Ausgang auf Low gelegt (0.5 s, ohne Pull-Einstellung). Im Ruhezustand liegt GPIO4 durch den Standard-Pull-up auf High. Das passt zu dieser Schaltung: High an GPIO4 hält Q2 durchgeschaltet (Strom bleibt an), Low gibt ihn frei. Die Zeilen `gpio-shutdown,gpio_pin=17,active_low=1,gpio_pull=up` und `gpio-poweroff,gpiopin=4,active_low=1` sind damit polaritätsrichtig. `gpio-poweroff` mit `active_low=1` legt den Pin beim Start auf High und beim Ausschalten auf Low.
- **Unterschiede zum Original:** Das Original wertet GPIO17 erst nach 1 s Low aus. Das Overlay `gpio-shutdown` löst dagegen sofort nach dem Entprellen aus. Ein längeres Halten lässt sich über den Parameter `debounce` (in Millisekunden) nachbilden, zum Beispiel `debounce=1000`, falls das gewünscht ist. Die LED hängt hier an GPIO27 statt an GPIO17, und GPIO17 ist nur ein Eingang.

## Gerber-Dateien für die Fertigung

### Voraussetzungen vor der Ausgabe

- DRC der Platine ohne Fehler und ohne unverbundene Elemente. Stand: 3 A erfüllt dies, 5 A noch nicht (offene Verbindungen).
- ERC des Schaltplans ohne Fehler.
- GPIO-Belegung gegen das Pinout geprüft (siehe Abschnitt "Mechanischer Aufbau mit Buchsenleiste", Punkte zur GPIO-Prüfung).
- Platine in KiCad gespeichert und die Zonen neu gefüllt (Taste `B`), damit die Gerber-Dateien den aktuellen Stand enthalten.

### Ausgabe in KiCad 10

1. Im Platineneditor *Datei → Fertigungsausgaben → Gerber (.gbr)* öffnen und einen Ausgabeordner wählen, zum Beispiel `gerber/`.
2. Lagen: `F.Cu`, `B.Cu`, `F.Paste`, `B.Paste`, `F.Silkscreen`, `B.Silkscreen`, `F.Mask`, `B.Mask`, `Edge.Cuts`.
3. Gerber-X2-Attribute aktiv lassen und keine Protel-Dateiendungen verwenden. Dann *Plot* ausführen.
4. *Bohrdateien erzeugen*: Format Excellon, PTH und NPTH in getrennten Dateien, absolutes Bohrkoordinatensystem.
5. Den Ordner als ZIP-Datei packen und beim Fertiger hochladen.

### Ausgabe per Kommandozeile

Aufruf im jeweiligen Projektordner (`kicad/` oder `kicad5A/`, Dateiname entsprechend `RaspiShime.kicad_pcb` beziehungsweise `RaspiShime5A.kicad_pcb`):

```powershell
& "C:\Program Files\KiCad\10.0\bin\kicad-cli.exe" pcb export gerbers -o gerber/ --layers "F.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts" RaspiShime.kicad_pcb
& "C:\Program Files\KiCad\10.0\bin\kicad-cli.exe" pcb export drill -o gerber/ --format excellon --generate-map RaspiShime.kicad_pcb
```

`kicad-cli.exe` liegt unter `C:\Program Files\KiCad\10.0\bin`. In PowerShell ist vor einem in Anführungszeichen stehenden Pfad der Aufrufoperator `&` nötig, sonst meldet PowerShell den Fehler "Unerwartetes Token". In der Eingabeaufforderung (`cmd`) und in Git Bash entfällt das `&` (in Git Bash lautet der Pfad `"/c/Program Files/KiCad/10.0/bin/kicad-cli.exe"`).

### Angaben bei der Bestellung

- **Lagen und Dicke:** 2 Lagen, 1.6 mm.
- **Kupfergewicht:** 3 A: Standard (1 oz). 5 A: 2 oz auf beiden Lagen. Das Kupfergewicht steht nicht in den Gerber-Dateien, sondern nur im Bestellformular (die Angabe im Stackup der Platine dient nur der Dokumentation).
- **Oberfläche:** HASL bleifrei oder ENIG. Wegen der feinen Pads des USB-C-Steckers ist ENIG vorzuziehen.
- **Bestückung durch den Fertiger:** Zusätzlich BOM und Bestückungsdaten (*Datei → Fertigungsausgaben → Bestückungsdaten*) erzeugen. Die vorhandenen CSV-Dateien im Projekt sind veraltet (J3 und PinSocket fehlen) und vorher neu zu exportieren.
- **J2:** Die Buchsenleiste mit langen Stiften liegt auf der Unterseite und wird in der Regel von Hand gelötet.

## Lizenz

Das Projekt steht unter der MIT-Lizenz (siehe [LICENSE](LICENSE)). Sie gilt für alle Dateien dieses Repositorys, also auch für die KiCad-Projekte, das CadQuery-Skript und das daraus erzeugte 3D-Modell. Das Urheberrechtsfeld nennt "internauten" als Inhaber. Die Lizenz betrifft nur diese Nachbildung. Entwurf und Marke des Pimoroni OnOff SHIM bleiben beim Hersteller, und die von KiCad verwendeten Bibliotheken (Symbole, Footprints, 3D-Modelle) stehen unter deren eigenen Lizenzen.

Copyright (c) 2026 die.internauten.ch GmbH

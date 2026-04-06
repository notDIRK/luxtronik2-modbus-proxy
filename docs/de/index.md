# luxtronik2-modbus-proxy

**luxtronik2-modbus-proxy** ubersetzt das proprietare Luxtronik 2.0 Binarprokoll (TCP-Port 8889)
in Standard-Modbus-TCP (Port 502) und ermoglicht es evcc, Home Assistant und anderen
Modbus-fahigen Energiemanagementsystemen, altere Warmepumpen ohne native Modbus-Schnittstelle
auszulesen und zu steuern.
Das Projekt richtet sich an Besitzer von Warmepumpen der Hersteller Alpha Innotec, Novelan,
Buderus, Nibe, Roth, Elco und Wolf mit Luxtronik 2.0 Regler — Tausende Gerate ohne
Moglichkeit eines Firmware-Updates.

## Funktionen

- **Modbus-TCP-Server auf Port 502** — gibt Warmepumpenzustand und Steuerbefehle uber Standard-
  Modbus-Halteregister (FC3 Lesen, FC6/FC16 Schreiben) weiter
- **Verbinden-Lesen-Trennen-Polling** — verbindet sich kurz mit dem Luxtronik-Regler, liest
  oder schreibt, und trennt dann die Verbindung; koexistiert sicher mit der BenPru-Integration
  in Home Assistant am selben Regler
- **Virtuelles SG-Ready-Register** — die Modi 0–3 werden uber ein einzelnes Modbus-Register
  geschrieben; evcc nutzt dies, um den Warmepumpenbetrieb in Zeiten mit Solaruberschuss zu
  verlagern
- **Konfigurierbares Register-Mapping** — weitere Luxtronik-Parameter konnen in `config.yaml`
  uber ihren symbolischen Namen hinzugefugt werden; alle 1.126 Parameter stehen zur Verfugung
- **Docker- und systemd-Betrieb** — Ausfuhrung als Container oder nativer Systemdienst;
  Konfiguration uber `config.yaml` mit Umgebungsvariablen fur Docker

## Erste Schritte

Wahle deinen Einstiegspunkt:

- **Entwickler / Beitragende:** [Quick Start](quickstart.md) — Repository klonen, installieren,
  aus dem Quellcode starten
- **Endnutzer / ohne Python-Kenntnisse:** [Benutzerhandbuch](user-guide.md) — Docker-Setup,
  keine Python-Kenntnisse erforderlich

## Integrationsanleitungen

- [evcc-Integration](evcc-integration.md) — evcc fur die Nutzung des Proxys als Modbus-Warmepumpe
  konfigurieren
- [HA-Koexistenz](ha-coexistence.md) — Proxy zusammen mit der HA BenPru/luxtronik-Integration
  betreiben

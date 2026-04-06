# Schnellstart

luxtronik2-modbus-proxy in unter 15 Minuten aus dem Quellcode zum Laufen bringen.

## Voraussetzungen

- Python 3.10 oder neuer
- `pip` (kommt mit Python)
- `git`
- Docker (optional, fuer den Docker-Track unter [Docker-Alternative](#docker-alternative))

## Klonen und Installieren

```bash
git clone https://github.com/OWNER/PUBLIC-luxtronik2-modbus-proxy.git
cd PUBLIC-luxtronik2-modbus-proxy
pip install -e ".[dev]"
```

Das `[dev]`-Extra installiert `pytest`, `ruff` und `mypy` fuer die Entwicklung. Weglassen, wenn nur der Proxy betrieben werden soll.

## Konfigurieren

```bash
cp config.example.yaml config.yaml
```

`config.yaml` im Texteditor oeffnen und `luxtronik_host` auf die IP-Adresse der Waermepumpe setzen:

```yaml
luxtronik_host: "192.168.x.x"   # Durch die IP-Adresse der Waermepumpe ersetzen
```

Alle anderen Standardwerte sind fuer die meisten Installationen geeignet. Eine vollstaendige Beschreibung aller Konfigurationsfelder findet sich im [Benutzerhandbuch](user-guide.md).

## Starten

```bash
luxtronik2-modbus-proxy --config config.yaml
```

Beim Start erscheint strukturierte Log-Ausgabe. Erwartete Ereignisse:

```
{"event": "proxy_starting", "modbus_port": 502, "luxtronik_host": "192.168.x.x", ...}
{"event": "proxy_running", "poll_interval": 30, ...}
```

Nach Abschluss des ersten Poll-Zyklus:

```
{"event": "poll_cycle_complete", "registers_updated": 12, ...}
```

Der Proxy lauscht jetzt auf Port 502 auf eingehende Modbus TCP-Verbindungen.

## Funktionstest

Mit `modpoll` (einem Modbus-Kommandozeilenclient) pruefen, ob der Proxy antwortet:

```bash
modpoll -m tcp -a 1 -r 1 -c 5 -t 4:int 127.0.0.1
```

Dieser Befehl liest 5 Holding-Register ab Adresse 1, die Temperaturwerten entsprechen. Die Ausgabe sollte fuenf Ganzzahlen enthalten.

modpoll installieren: `pip install modpoll` oder herunterladen von [https://www.modbusdriver.com/modpoll.html](https://www.modbusdriver.com/modpoll.html).

## Tests ausfuehren

```bash
pytest
```

Mit Coverage-Bericht:

```bash
pytest --cov=src
```

Die Testsuite verwendet `pytest-asyncio` mit `asyncio_mode = auto`; fuer asynchrone Tests sind keine zusaetzlichen Flags erforderlich.

## Docker-Alternative

Wenn der Betrieb in einem Container bevorzugt wird:

```bash
docker compose up -d
docker compose logs -f proxy
```

Der Container liest `config.yaml` aus dem aktuellen Verzeichnis. Diese muss vor dem Start erstellt und konfiguriert werden.

## Naechste Schritte

- **[Benutzerhandbuch](user-guide.md)** — vollstaendige Konfigurationsreferenz, Docker-Installationsanleitung und Fehlerbehebung
- **[evcc-Integrationsanleitung](evcc-integration.md)** — evcc konfigurieren, um die Waermepumpe ueber SG-Ready zu steuern
- **[Parallelbetrieb mit Home Assistant](ha-coexistence.md)** — Proxy zusammen mit der BenPru Home Assistant-Integration ohne Verbindungskonflikte betreiben

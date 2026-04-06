# Benutzerhandbuch

luxtronik2-modbus-proxy installieren und konfigurieren, um die Luxtronik 2.0-Waermepumpe mit evcc oder Home Assistant zu verbinden.

## Was macht dieser Proxy?

Der Waermepumpenregler spricht ein proprietaeres Binaerprotokoll, das nur Luxtronik-spezifische Software versteht. Tools wie evcc und Home Assistant verwenden einen voellig anderen Standard namens Modbus. Dieser Proxy sitzt zwischen beiden: Er kommuniziert mit der Waermepumpe in deren eigener Sprache und mit evcc oder Home Assistant in Modbus. Es ist kein Verstaendnis beider Protokolle notwendig. Sobald der Proxy laeuft, erscheint die Waermepumpe gegenueber evcc und Home Assistant wie ein beliebiges anderes Modbus-Geraet.

## Voraussetzungen

- **Docker** (empfohlen): Docker Desktop oder Docker Engine installieren von [https://docs.docker.com/get-docker/](https://docs.docker.com/get-docker/)
- **Alternative ohne Docker**: Siehe [systemd-Dienst](systemd.md) fuer den Betrieb unter Linux ohne Container
- Die Waermepumpe muss im lokalen Netzwerk erreichbar sein (die IP-Adresse wird benoetigt)

## Installation (Docker)

### Schritt 1: Konfigurationsvorlage herunterladen

```bash
cp config.example.yaml config.yaml
```

Bei Docker-Installation ohne Klon des Repositories die Beispieldatei direkt herunterladen:

```bash
curl -o config.yaml https://raw.githubusercontent.com/OWNER/PUBLIC-luxtronik2-modbus-proxy/main/config.example.yaml
```

### Schritt 2: Konfiguration bearbeiten

`config.yaml` in einem Texteditor oeffnen. Beschreibung aller Felder:

#### `luxtronik_host`

```yaml
luxtronik_host: "192.168.x.x"
```

Die IP-Adresse des Waermepumpenreglers. Dies ist die wichtigste Einstellung. Die IP-Adresse der Waermepumpe in der Geraete-Liste des Routers oder im Luxtronik-Webinterface unter Einstellungen > Netzwerk finden.

#### `luxtronik_port`

```yaml
luxtronik_port: 8889
```

Der vom Luxtronik-Binaerprotokoll verwendete Port. Diesen Wert bei 8889 belassen, es sei denn, der Regler wurde speziell fuer einen anderen Port konfiguriert. Das ist bei fast niemandem der Fall.

#### `modbus_port`

```yaml
modbus_port: 502
```

Der Port, auf dem der Proxy auf eingehende Modbus TCP-Verbindungen lauscht. Port 502 ist der Modbus-Standard. Diesen nur aendern, wenn bereits ein anderer Dienst Port 502 auf dem System belegt.

#### `bind_address`

```yaml
bind_address: "0.0.0.0"
```

Die Netzwerkschnittstelle, auf der der Proxy lauscht. `0.0.0.0` belassen, um Verbindungen von beliebigen Geraeten im Netzwerk zu ermoeglichen. Auf eine bestimmte IP-Adresse (z.B. `192.168.x.x`) setzen, um den Zugriff auf eine einzelne Schnittstelle zu beschraenken.

#### `poll_interval`

```yaml
poll_interval: 30
```

Wie oft der Proxy Daten von der Waermepumpe liest, in Sekunden. Der Proxy verbindet sich mit der Waermepumpe, liest alle zugeordneten Register, aktualisiert seinen internen Zustand und trennt die Verbindung dann wieder. Ein Wert von 30 Sekunden wird fuer die meisten Setups empfohlen, insbesondere wenn auch die Home Assistant BenPru-Integration betrieben wird. Zu niedrige Werte koennen Verbindungskonflikte verursachen.

#### `log_level`

```yaml
log_level: "INFO"
```

Steuert, wie viele Informationen der Proxy protokolliert. `INFO` fuer den normalen Betrieb verwenden. Bei der Fehlerbehebung auf `DEBUG` setzen — das erzeugt deutlich detailliertere Ausgaben. Andere Optionen sind `WARNING` und `ERROR` fuer weniger Protokollausgaben.

#### `enable_writes`

```yaml
enable_writes: false
```

Auf `true` setzen, wenn evcc die Waermepumpe steuern soll (z.B. um zwischen SG-Ready-Modi fuer das Lastmanagement zu wechseln). Bei `false` ist der Proxy schreibgeschuetzt und evcc kann keine Einstellungen aendern. Mit `false` beginnen und vor der Aktivierung von Schreibzugriffen sorgfaeltig testen.

#### `write_rate_limit`

```yaml
write_rate_limit: 60
```

Die Mindestanzahl an Sekunden zwischen Schreibbefehlen an dasselbe Register. Dies schuetzt den NAND-Flash-Speicher im Waermepumpenregler vor zu haeufigen Schreibvorgaengen. Der Standardwert von 60 Sekunden ist fuer das Umschalten des SG-Ready-Modus angemessen. Diesen Wert nicht unter 10 Sekunden setzen.

#### `registers.parameters` (optional, fuer Fortgeschrittene)

```yaml
# registers:
#   parameters:
#     - ID_Einst_WK_akt
#     - ID_Ba_Hz_MK3_akt
```

Zusaetzliche Luxtronik-Parameter, die als Modbus-Register verfuegbar gemacht werden sollen, ueber den vordefinierten Standardsatz hinaus. Die Standardwerte decken alle fuer evcc und Home Assistant benoetigen Register ab. `luxtronik2-modbus-proxy list-params --search <Begriff>` verwenden, um die vollstaendige Liste der 1.126 verfuegbaren Parameter zu durchsuchen.

#### `sg_ready_mode_map` (optional, fuer Fortgeschrittene)

```yaml
# sg_ready_mode_map: ...
```

Benutzerdefinierte SG-Ready-Modusbelegung fuer nicht standardmaessige Waermepumpenkonfigurationen. Auskommentiert lassen, es sei denn, die Waermepumpe verwendet nicht-standardmaessige Parameter-IDs fuer die SG-Ready-Signalisierung.

### Schritt 3: Proxy starten

```bash
docker compose up -d
```

### Schritt 4: Logs pruefen

```bash
docker compose logs -f proxy
```

## Funktionstest

Nach dem Start sollten folgende Log-Nachrichten erscheinen:

```
{"event": "proxy_starting", "modbus_port": 502, ...}
{"event": "proxy_running", "poll_interval": 30, ...}
```

Nach dem ersten Poll-Zyklus (innerhalb von `poll_interval` Sekunden):

```
{"event": "poll_cycle_complete", "registers_updated": 12, ...}
```

Alle 30 Sekunden (oder im eingestellten `poll_interval`-Abstand) sollte eine neue `poll_cycle_complete`-Nachricht erscheinen. Erscheint das Ereignis nie, im Abschnitt Fehlerbehebung nachsehen.

## evcc verbinden

Vollstaendige YAML-Konfiguration fuer das evcc-Setup in der [evcc-Integrationsanleitung](evcc-integration.md).

## Home Assistant verbinden

Hinweise zum Betrieb des Proxys zusammen mit der BenPru-Integration ohne Verbindungskonflikte in der [Anleitung zum Parallelbetrieb mit Home Assistant](ha-coexistence.md).

## Fehlerbehebung

### "Connection refused" oder "Could not connect" auf Port 8889

Der Proxy kann die Waermepumpe nicht erreichen. Pruefen:
- Die IP-Adresse in `config.yaml` ist korrekt
- Der Waermepumpenregler ist eingeschaltet
- Der Computer oder Server kann die Waermepumpe im Netzwerk erreichen (versuchen: `ping 192.168.x.x`)
- Keine Firewall blockiert Port 8889

### "Address already in use" auf Port 502

Ein anderer Dienst lauscht bereits auf dem Modbus-Port 502. Diesen Dienst beenden oder `modbus_port` in `config.yaml` auf einen anderen Port (z.B. 5020) aendern und die evcc-/HA-Konfiguration entsprechend aktualisieren.

### "Poll cycle failed" in den Logs

Ein voruebergehender Verbindungsfehler beim Lesen von der Waermepumpe. Der Proxy wiederholt den Versuch im naechsten Poll-Zyklus. Bei wiederholten Fehlern die Einstellung `luxtronik_host` und die Netzwerkverbindung pruefen.

### Der Proxy startet, aber Register zeigen Null- oder veraltete Werte

Der erste Poll-Zyklus ist moeglicherweise noch nicht abgeschlossen. Nach dem Start bis zu `poll_interval` Sekunden warten. Bleiben die Werte nach einem vollstaendigen Zyklus bei Null, `DEBUG`-Logging aktivieren, um detaillierte Leseausgaben zu sehen.

## Alternative: systemd-Dienst

Fuer den Betrieb ohne Docker: [systemd-Dienst](systemd.md) als native Linux-Dienstinstallation.

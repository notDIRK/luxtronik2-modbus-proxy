# systemd-Dienst

luxtronik2-modbus-proxy als systemd-Dienst unter Linux betreiben.

## Wann systemd verwenden?

**systemd** verwenden, wenn:
- Ein Linux-Server (Raspberry Pi, NAS, Heimserver) vorhanden ist, der kein Docker betreibt
- Natives Dienst-Management mit `systemctl` bevorzugt wird
- Der Proxy ohne Container-Laufzeitumgebung automatisch beim Systemstart starten soll

**Docker** verwenden, wenn:
- Docker bereits auf dem Server laeuft
- Container-Isolation und einfache Updates gewuenscht sind
- Eine einzelne Datei mit `docker compose` fuer das Deployment bevorzugt wird

Den Docker-Installationsweg im [Benutzerhandbuch](user-guide.md) finden.

## Voraussetzungen

- Ein Linux-System mit systemd (die meisten modernen Linux-Distributionen)
- Python 3.10 oder neuer
- `pip`
- `sudo`-Rechte zur Installation der Service-Datei

## Proxy installieren

Installation von PyPI:

```bash
pip install luxtronik2-modbus-proxy
```

Oder direkt aus dem GitHub-Repository installieren:

```bash
pip install git+https://github.com/OWNER/PUBLIC-luxtronik2-modbus-proxy.git
```

Nach der Installation pruefen, ob der Befehl verfuegbar ist:

```bash
luxtronik2-modbus-proxy --version
```

## Systembenutzer erstellen

Den Proxy als dedizierten Nicht-Root-Systembenutzer aus Sicherheitsgruenden betreiben:

```bash
sudo useradd -r -s /bin/false luxtronik-proxy
```

Dieser Befehl erstellt ein Systemkonto (`-r`) ohne Login-Shell (`-s /bin/false`). Der Proxy-Prozess laeuft als dieser Benutzer.

## Konfiguration installieren

Das Konfigurationsverzeichnis erstellen und die Beispieldatei kopieren:

```bash
sudo mkdir -p /etc/luxtronik2-modbus-proxy
sudo cp config.example.yaml /etc/luxtronik2-modbus-proxy/config.yaml
sudo nano /etc/luxtronik2-modbus-proxy/config.yaml
```

Mindestens `luxtronik_host` auf die IP-Adresse der Waermepumpe setzen:

```yaml
luxtronik_host: "192.168.x.x"   # Durch die IP-Adresse der Waermepumpe ersetzen
```

Eine Beschreibung aller Konfigurationsfelder im [Benutzerhandbuch](user-guide.md).

Dem Dienstbenutzer Lesezugriff auf die Konfigurationsdatei erteilen:

```bash
sudo chown root:luxtronik-proxy /etc/luxtronik2-modbus-proxy/config.yaml
sudo chmod 640 /etc/luxtronik2-modbus-proxy/config.yaml
```

## Service-Datei installieren

Die bereitgestellte Service-Datei-Vorlage in das systemd-Verzeichnis kopieren:

```bash
sudo cp contrib/luxtronik2-modbus-proxy.service /etc/systemd/system/
```

Bei Installation von PyPI ohne Klon des Repositories die Service-Datei direkt herunterladen:

```bash
sudo curl -o /etc/systemd/system/luxtronik2-modbus-proxy.service \
  https://raw.githubusercontent.com/OWNER/PUBLIC-luxtronik2-modbus-proxy/main/contrib/luxtronik2-modbus-proxy.service
```

systemd neu laden und den Dienst fuer den Autostart einrichten:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now luxtronik2-modbus-proxy
```

Das `--now`-Flag startet den Dienst sofort und aktiviert ihn zusaetzlich fuer den Autostart.

## Status pruefen

```bash
sudo systemctl status luxtronik2-modbus-proxy
```

Ein gesunder Dienst zeigt `active (running)`. Bei `failed` die Logs pruefen (siehe unten).

## Logs anzeigen

Laufende Log-Ausgabe verfolgen:

```bash
journalctl -u luxtronik2-modbus-proxy -f
```

Die letzten 50 Log-Zeilen anzeigen:

```bash
journalctl -u luxtronik2-modbus-proxy -n 50
```

Der Proxy verwendet structlog mit JSON-Ausgabe, die journald automatisch erfasst. Die Ereignisse `proxy_starting`, `proxy_running` und wiederkehrende `poll_cycle_complete`-Ereignisse sollten sichtbar sein.

## Umgebungsvariablen

Konfigurationswerte koennen ueber Umgebungsvariablen ueberschrieben werden, ohne `config.yaml` zu bearbeiten. Dies ist nuetzlich, wenn dieselbe Konfigurationsdatei in mehreren Umgebungen verwendet wird.

Eine Umgebungsdatei unter `/etc/luxtronik2-modbus-proxy/env` erstellen:

```bash
sudo nano /etc/luxtronik2-modbus-proxy/env
```

`KEY=VALUE`-Paare mit dem Praefix `LUXTRONIK_` hinzufuegen. Beispiel:

```
LUXTRONIK_HOST=192.168.x.x
LUXTRONIK_POLL_INTERVAL=60
LUXTRONIK_LOG_LEVEL=DEBUG
```

Die Service-Datei enthaelt bereits `EnvironmentFile=-/etc/luxtronik2-modbus-proxy/env` (das `-`-Praefix macht die Datei optional — der Dienst startet auch, wenn die Datei nicht existiert).

Nach dem Bearbeiten der Umgebungsdatei den Dienst neu starten:

```bash
sudo systemctl restart luxtronik2-modbus-proxy
```

## Fehlerbehebung

### Dienst startet nicht

Die vollstaendige Log-Ausgabe unmittelbar nach dem Fehler pruefen:

```bash
journalctl -u luxtronik2-modbus-proxy -n 100 --no-pager
```

Nach `error`- oder `exception`-Ereignissen suchen. Haeufige Ursachen:
- Konfigurationsdatei nicht gefunden: pruefen, ob `/etc/luxtronik2-modbus-proxy/config.yaml` existiert und vom Benutzer `luxtronik-proxy` gelesen werden kann
- Ungueltiges YAML: die Konfigurationsdatei oeffnen und auf Einrueckung oder Syntaxfehler pruefen
- Python nicht am in `ExecStart` angegebenen Pfad gefunden: `which luxtronik2-modbus-proxy` als root ausfuehren, um den korrekten Pfad zu finden, und die Service-Datei entsprechend aktualisieren

### "Permission denied" beim Binden von Port 502

Port 502 ist ein privilegierter Port (unter 1024), der Root-Rechte oder eine Capability-Vergabe erfordert. Optionen:

1. Die Capability dem Python-Binary erteilen (empfohlen):
   ```bash
   sudo setcap 'cap_net_bind_service=+ep' $(which python3)
   ```
2. Oder `modbus_port` in `config.yaml` auf einen nicht-privilegierten Port aendern (z.B. 5020) und die evcc-/HA-Konfiguration entsprechend anpassen.

### Konfigurationsdatei beim Start nicht gefunden

Den Pfad in der Service-Datei mit dem Speicherort von `config.yaml` abgleichen:

```bash
grep ExecStart /etc/systemd/system/luxtronik2-modbus-proxy.service
```

Bei Abweichung die Service-Datei bearbeiten und neu laden:

```bash
sudo systemctl daemon-reload
sudo systemctl restart luxtronik2-modbus-proxy
```

### Dienst startet zu oft neu und wird gedrosselt

systemd begrenzt die Neustartrate von Diensten, die wiederholt neu starten. Die Service-Datei enthaelt `StartLimitIntervalSec=60` und `StartLimitBurst=3`, um Neustart-Schleifen zu verhindern. Bei Startfehlern aufgrund eines Konfigurationsfehlers diesen zuerst beheben, bevor ein Neustart versucht wird:

```bash
journalctl -u luxtronik2-modbus-proxy -n 50
# Konfigurationsfehler beheben, dann:
sudo systemctl reset-failed luxtronik2-modbus-proxy
sudo systemctl start luxtronik2-modbus-proxy
```

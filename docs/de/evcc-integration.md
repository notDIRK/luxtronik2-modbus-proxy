# evcc-Integrationsanleitung

Diese Anleitung erklaert, wie [evcc](https://evcc.io/) konfiguriert wird, um die Luxtronik 2.0-Waermepumpe ueber den luxtronik2-modbus-proxy zu steuern. Der Proxy stellt eine Modbus TCP-Schnittstelle auf Port 502 bereit, die evcc zum Lesen des Betriebszustands und zum Schreiben von SG-Ready-Moduskommandos verwendet.

## Voraussetzungen

- luxtronik2-modbus-proxy laeuft und ist vom evcc-Host erreichbar
- evcc ist installiert und laeuft (siehe [evcc-Dokumentation](https://docs.evcc.io/))
- Netzwerkverbindung zwischen evcc und dem Proxy (TCP-Port 502)
- `enable_writes: true` in der Proxy-Datei `config.yaml` gesetzt (erforderlich fuer SG-Ready-Schreibvorgaenge)

## evcc-Konfiguration

Folgendes zur `evcc.yaml` hinzufuegen. `192.168.x.x` durch die IP-Adresse des Rechners ersetzen, auf dem der Proxy laeuft.

```yaml
# evcc.yaml — Luxtronik2 Modbus Proxy integration
# Add this block to your evcc.yaml heatsources or chargers section

heatsources:
  - name: heat_pump
    type: custom

    # SG-ready mode write (FC6 write holding register 5000)
    setmode:
      source: modbus
      uri: 192.168.x.x:502   # Replace with your proxy host IP and Modbus port
      id: 1
      register:
        address: 5000         # SG-ready virtual register (0-based)
        type: writeholding
        decode: uint16

    # SG-ready mode read (FC3 read holding register 5000)
    getmode:
      source: modbus
      uri: 192.168.x.x:502   # Replace with your proxy host IP and Modbus port
      id: 1
      register:
        address: 5000         # SG-ready virtual register (0-based)
        type: holding
        decode: uint16

    # Optional: read current heat pump power consumption (input register 257)
    power:
      source: modbus
      uri: 192.168.x.x:502
      id: 1
      register:
        address: 257          # Heat output (watts, input register, 0-based)
        type: input
        decode: uint16
```

> **Hinweis:** Alle Registeradressen sind 0-basiert (die Modbus-Wire-Adresse). evcc verwendet dieselbe 0-basierte Konvention. Diese Adressen nicht um 1 erhoehen.

## SG-Ready-Modusbelegung

Der Proxy uebersetzt den SG-Ready-Modus von evcc (0–3) in Luxtronik HeatingMode- und HotWaterMode-Parameterschreibvorgaenge:

| evcc-Modus | Name | HeatingMode (Param 3) | HotWaterMode (Param 4) | Beschreibung |
|-----------|------|-----------------------|------------------------|-------------|
| 0 | EVU-Sperre | Aus (4) | Aus (4) | Netzbetreiber-Sperre — Waermepumpe gesperrt |
| 1 | Normal | Automatisch (0) | Automatisch (0) | Normalbetrieb |
| 2 | Empfohlen | Party (2) | Automatisch (0) | Erhoehter Verbrauch empfohlen |
| 3 | Zwangsbetrieb | Automatisch (0) | Party (2) | Maximaler Verbrauch (Ueberschussenergie) |

Das Lesen von Register 5000 gibt den zuletzt erfolgreich angewendeten Modus zurueck. Das Register wird beim Proxy-Start mit Modus 1 (Normal) initialisiert.

## Wichtige Hinweise

### Schreibzugriffe muessen aktiviert sein

SG-Ready-Schreibvorgaenge erfordern `enable_writes: true` in der Proxy-Datei `config.yaml`:

```yaml
# config.yaml
enable_writes: true
write_rate_limit: 60   # Minimum seconds between writes to the same register
```

Ohne diese Einstellung werden alle Schreibkommandos mit einer Modbus-Ausnahme abgelehnt.

### Modusbelegung ist angenommen

Die Modus-zu-Parameter-Zuordnung basiert auf dem Konsens der evcc- und Home Assistant-Foren und ist mit **[ASSUMED]** markiert. Das Verhalten auf der eigenen Hardware validieren (insbesondere den EVU-Sperrmodus 0), bevor dieses in der Produktion eingesetzt wird.

### Benutzerdefinierte Modusbelegung

Wenn die Waermepumpe andere Parameterwerte benoetigt, eine benutzerdefinierte Modusbelegung in `config.yaml` konfigurieren:

```yaml
# config.yaml — Custom SG-ready mode map example
sg_ready_mode_map:
  0: {3: 4, 4: 4}   # EVU lock: HeatingMode=Off, HotWaterMode=Off
  1: {3: 0, 4: 0}   # Normal: HeatingMode=Auto, HotWaterMode=Auto
  2: {3: 2, 4: 0}   # Recommended: HeatingMode=Party, HotWaterMode=Auto
  3: {3: 0, 4: 2}   # Force on: HeatingMode=Auto, HotWaterMode=Party
```

Schluessel sind Luxtronik-Parameterindizes (3 = HeatingMode, 4 = HotWaterMode). Werte sind die rohen Ganzzahlen aus den Luxtronik-Bibliotheks-Enums.

### Schreibraten-Begrenzung

Jedes Register ist auf einen Schreibvorgang pro `write_rate_limit` Sekunden begrenzt (Standard: 60s). Schnelle SG-Ready-Moduswechsel von evcc werden fuer die zugrunde liegenden Parameter (Adressen 3 und 4) ratenbegrenzt. Das virtuelle SG-Ready-Register (Adresse 5000) selbst wird nicht ratenbegrenzt — die Begrenzung gilt fuer die Schreibvorgaenge an den Luxtronik-Regler.

## Weitere Register

Neben SG-Ready stellt der Proxy folgende Register bereit, die evcc oder andere Tools lesen koennen:

### Temperaturregister (Eingangsregister, FC4, Einheit: °C × 10)

| Adresse | Parameter | Einheit | Beschreibung |
|---------|-----------|---------|-------------|
| 10 | Vorlauftemperatur | °C × 10 (int16) | Waermetraeger-Vorlauftemperatur |
| 11 | Ruecklauftemperatur | °C × 10 (int16) | Waermetraeger-Ruecklauftemperatur |
| 15 | Aussentemperatur | °C × 10 (int16) | Aussenlufttemperatur |
| 17 | Warmwassertemperatur | °C × 10 (int16) | Warmwasser-Isttemperatur |

Den rohen Registerwert durch 10 dividieren, um Grad Celsius zu erhalten. Beispiel: Wert 215 = 21,5 °C.

### Betriebszustandsregister (Eingangsregister, FC4)

| Adresse | Parameter | Einheit | Beschreibung |
|---------|-----------|---------|-------------|
| 80 | Betriebsmodus | uint16 | Aktueller Betriebszustand der Waermepumpe |
| 257 | Waermeleistung | Watt (uint16) | Aktuelle Waermeleistung |

### Beschreibbare Modusregister (Halteregister, FC3/FC6)

| Adresse | Parameter | Erlaubte Werte | Beschreibung |
|---------|-----------|----------------|-------------|
| 3 | HeatingMode | 0–4 | 0=Auto, 1=Zweitwaerme, 2=Party, 3=Ferien, 4=Aus |
| 4 | HotWaterMode | 0–4 | 0=Auto, 1=Zweitwaerme, 2=Party, 3=Ferien, 4=Aus |
| 5000 | SG-Ready-Modus | 0–3 | Virtuelles Register: uebersetzt in obige Modi |

## Fehlerbehebung

### Schreibvorgang abgelehnt (Modbus-Ausnahme-Antwort)

**Symptom:** evcc meldet einen Schreibfehler beim Setzen des SG-Ready-Modus.

**Ursache 1:** `enable_writes` ist in der Proxy-Konfiguration `false`.
**Behebung:** `enable_writes: true` in `config.yaml` setzen und den Proxy neu starten.

**Ursache 2:** Moduswert ausserhalb 0–3.
**Behebung:** Sicherstellen, dass evcc nur Ganzzahlwerte 0, 1, 2 oder 3 sendet.

### Ungueltiger Datenbereich (Modbus-Ausnahme-Code 2)

**Symptom:** Modbus-Client meldet "Illegal data address" fuer ein Register.

**Ursache:** Die Registeradresse liegt ausserhalb des zugeordneten Bereichs des Proxys, oder es wird eine 1-basierte Adresse anstelle einer 0-basierten verwendet.
**Behebung:** Sicherstellen, dass die Registeradresse 0-basiert ist. Der Proxy verwendet 0-basierte Adressierung. Register 5000 (0-basiert) ist das SG-Ready-Register.

### Verbindung verweigert

**Symptom:** evcc kann keine Verbindung zum Proxy herstellen.

**Ursache:** Proxy laeuft nicht oder falscher Host/Port konfiguriert.
**Behebung:** Pruefen, ob der Proxy laeuft (`docker ps` oder `systemctl status`) und ob Port 502 vom evcc-Host erreichbar ist. Proxy-Logs auf Startfehler pruefen.

### Schreibraten-Warnung in Proxy-Logs

**Symptom:** Proxy-Logs zeigen `write_rate_limited`-Warnungen.

**Ursache:** evcc hat mehrere SG-Ready-Moduswechsel innerhalb des `write_rate_limit`-Fensters gesendet (Standard: 60 Sekunden).
**Behebung:** Dies ist normales Verhalten — die Ratenbegrenzung schuetzt den NAND-Flash-Speicher des Reglers. Der letzte Moduswechsel wird bei der naechsten uneingeschraenkten Schreibmoeglichkeit angewendet. Fuer schnellere Reaktion `write_rate_limit` reduzieren (Minimum: 10 Sekunden).

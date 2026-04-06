# Parallelbetrieb mit Home Assistant

Diese Anleitung erklaert, wie luxtronik2-modbus-proxy zusammen mit der
[Home Assistant BenPru/luxtronik-Integration](https://github.com/BenPru/luxtronik)
(auch als HA HACS-Integration bekannt) betrieben wird. Beide Systeme koennen denselben
Luxtronik 2.0-Regler ohne Konflikte nutzen, solange die Einzel-Verbindungs-Einschraenkung
beachtet wird.

## Hintergrund: Die Einzel-Verbindungs-Einschraenkung

Luxtronik 2.0-Regler (Port 8889) erlauben **genau eine TCP-Verbindung gleichzeitig**. Jeder
zweite Verbindungsversuch, waehrend der Port belegt ist, wird abgelehnt. Dies ist eine
Hardware-Einschraenkung, die sich nicht per Konfiguration oder Firmware aendern laesst.

Sowohl der Proxy als auch die HA BenPru-Integration bewaeltigen dies korrekt durch das
**Connect-Read/Write-Disconnect**-Muster: Jedes Tool verbindet sich kurz, liest oder schreibt
was benoetigt wird, und trennt die Verbindung dann sofort. Kein Tool haelt die Verbindung
zwischen Operationen offen.

## Wie der Parallelbetrieb funktioniert

```
Zeitstrahl:

[proxy]     CONNECT → READ → DISCONNECT ... (30s Pause) ... CONNECT → READ → DISCONNECT
[HA BenPru]                       CONNECT → READ → DISCONNECT ... (30s Pause) ...
```

Da beide Systeme nach jeder Operation sofort trennen, wechseln sie sich natuerlich ab,
ohne sich gegenseitig zu blockieren. Die Verbindung wird typischerweise weniger als eine
Sekunde pro Zyklus gehalten.

**Port-Trennung:**

- Der Proxy verbindet sich **ausgehend** mit dem Luxtronik-Regler auf Port 8889.
- Der Proxy bedient Modbus TCP-Clients **eingehend** auf Port 502.
- HA BenPru verbindet sich **ausgehend** mit dem Luxtronik-Regler auf Port 8889.
- Die HA Modbus-Integration (falls verwendet) verbindet sich **eingehend** mit dem Proxy auf Port 502.

Es gibt keinen Port-Konflikt: Port 8889 wird gemeinsam genutzt (kurz, sequenziell); Port 502
wird nur vom Proxy bedient.

## Was jedes System liest und schreibt

| System | Rolle | Port | Datentypen |
|--------|------|------|------------|
| Proxy | Ausgehender Client zu Luxtronik | 8889 (ausgehend) | Parameter (Lesen/Schreiben), Berechnungen (nur Lesen), Sichtbarkeiten (nur Lesen) |
| HA BenPru | Ausgehender Client zu Luxtronik | 8889 (ausgehend) | Parameter, Berechnungen |
| evcc | Eingehender Modbus-Client zum Proxy | 502 (eingehend zum Proxy) | Halteregister (SG-Ready, Modi) |
| HA Modbus-Integration | Eingehender Modbus-Client zum Proxy | 502 (eingehend zum Proxy) | Halte- und Eingangsregister |

Proxy und HA BenPru lesen beide von Port 8889 am Luxtronik-Regler. Der Proxy puffert
zusaetzlich die Werte und stellt sie Modbus-Clients auf Port 502 bereit.

## Empfohlene Konfiguration

### Proxy `poll_interval`

Das Polling-Intervall des Proxys steuert, wie oft er sich mit Port 8889 verbindet. Der Standard
(30s) ist so ausgelegt, dass ausreichend Raum fuer HA BenPru zum Wechseln bleibt.

```yaml
# config.yaml
poll_interval: 30   # Recommended for coexistence with HA BenPru
```

- **30 Sekunden**: Standard, gut fuer die meisten Setups. Laesst ~29 Sekunden Pause pro Zyklus.
- **60 Sekunden**: Konservativ; verwenden, wenn wiederholte Verbindungsfehler in Proxy-Logs auftreten.
- **15 Sekunden**: Empfohlenes Minimum fuer den Parallelbetrieb. Darunter werden Kollisionen wahrscheinlich.
- **10 Sekunden**: Absolutes Minimum (der Proxy erzwingt diesen Grenzwert). Nicht empfohlen mit HA BenPru.

### HA BenPru-Scan-Intervall

Die BenPru-Integration pollt nach eigenem Zeitplan (typischerweise standardmaessig 30–60 Sekunden).
Eine Aenderung ist nicht notwendig. Solange beide Systeme das Connect-Disconnect-Muster verwenden
(was sie tun), staffeln sich die Zeitpunkte natuerlich ueber die Zeit.

Um garantiert keine Ueberschneidungen zu haben, Startzeiten versetzen (Proxy einige Sekunden
vor HA starten), sodass die Poll-Zyklen versetzt sind. Dies ist optional.

## Konfliktbehandlung bei Schreibvorgaengen

Sowohl der Proxy (ueber evcc) als auch HA BenPru koennen Luxtronik-Parameter schreiben. Das
gleichzeitige Schreiben desselben Parameters von zwei Systemen kann zu unvorhersehbarem
Verhalten fuehren — der Wert jedes Systems ueberschreibt den des anderen.

### Empfohlene Schreib-Trennung

| System | Sollte schreiben | Sollte nicht schreiben |
|--------|-------------|------------------|
| Proxy (ueber evcc SG-Ready) | HeatingMode (Param 3), HotWaterMode (Param 4) | — |
| HA BenPru-Automationen | Betriebsmodi fuer Zeitplaene, Sollwerte | HeatingMode, HotWaterMode wenn Proxy/evcc SG-Ready verwaltet |

**Faustregel:** Jeden schreibbaren Parameter genau einem Controller zuweisen. Wenn evcc
SG-Ready verwaltet (was HeatingMode und HotWaterMode schreibt), diese Parameter nicht
zusaetzlich von HA-Automationen schreiben.

### SG-Ready-spezifische Hinweise

Wenn evcc ein SG-Ready-Moduskommando an den Proxy sendet, schreibt der Proxy in:
- Parameter 3 (HeatingMode)
- Parameter 4 (HotWaterMode)

Wenn HA gleichzeitig in einen dieser Parameter schreibt, gewinnt das letzte Schreiben
und das System kann in einem inkonsistenten Zustand sein. Eine der folgenden Optionen waehlen:

1. **evcc verwaltet SG-Ready**: evcc schreibt Modi ueber den Proxy. HA BenPru liest nur.
   HA-Automationen schreiben HeatingMode oder HotWaterMode nicht, waehrend evcc aktiv ist.

2. **HA verwaltet Betriebsmodi**: HA BenPru schreibt HeatingMode und HotWaterMode direkt.
   evcc SG-Ready wird nicht verwendet. Der Proxy ist aus evcc-Perspektive schreibgeschuetzt.

3. **Koordiniert ueber HA**: HA empfaengt sowohl das Tibber-/Netzsignal als auch den
   Waermepumpenstatus. HA-Automation entscheidet, welchen Modus zu setzen, entweder direkt
   ueber BenPru oder durch Schreiben des SG-Ready-Registers ueber die Modbus-Schnittstelle
   des Proxys. Dies bietet vollstaendige Kontrolle an einer Stelle.

## Fehlerbehebung bei Verbindungsproblemen

### Proxy-Logs zeigen wiederholte Verbindungsfehler

**Symptom:** Proxy-Logs enthalten `poll_cycle_failed` mit "Connection refused"-Fehlern
alle 30 Sekunden.

**Ursache:** HA BenPru haelt den Luxtronik-Socket zum selben Zeitpunkt belegt, zu dem
der Proxy eine Verbindung versucht. Dies ist selten, kann aber auftreten, wenn sich HAs
Polling-Zyklus mit dem des Proxys deckt.

**Behebung:**
1. Proxy `poll_interval` von 30s auf 60s erhoehen, um die Kollisionswahrscheinlichkeit
   zu reduzieren.
2. Den Proxy einige Sekunden nach HA neu starten, um die Zyklen zu staffeln.
3. Pruefen, ob HA-Automationen die Verbindung der BenPru-Integration durch viele
   schnelle Lesevorgaenge offenhalten.

Der Proxy ist resilient gegenueber Verbindungsfehlern — er protokolliert den Fehler,
markiert seinen Cache als veraltet und wiederholt den Versuch im naechsten Zyklus.
Einige verpasste Polls verursachen keinen Datenverlust.

### HA BenPru zeigt Entitaet als "nicht verfuegbar"

**Symptom:** HA-Entitaeten der BenPru-Integration zeigen zeitweise "unavailable".

**Ursache:** Der Proxy hat sich zum Luxtronik-Socket verbunden, als HA BenPru seinen
Poll versuchte. BenPrus Verbindung wurde abgelehnt, was zu voruebergehender Nichtverfuegbarkeit
fuehrte.

**Behebung:** Dies ist meistens voruebergehend (ein verpasster Poll = ~30s Nichtverfuegbarkeit).
Bei haeufigem Auftreten den Proxy `poll_interval` auf 60s erhoehen, um Ueberschneidungen
zu reduzieren.

Der Proxy gibt den Socket innerhalb eines Bruchteils einer Sekunde pro Zyklus frei,
sodass eine langfristige Blockierung von HA BenPru mit `poll_interval >= 30s` nicht
auftreten sollte.

### Beide Systeme zeigen veraltete Daten

**Symptom:** Sowohl der Proxy-Cache als auch HA BenPru-Entitaeten zeigen veraltete Werte.

**Ursache:** Der Luxtronik-Regler ist nicht erreichbar (Netzwerkproblem, Regler-Neustart
oder Stromausfall).

**Behebung:** Pruefen, ob der Luxtronik-Regler auf Port 8889 sowohl vom Proxy-Host als
auch vom HA-Host erreichbar ist. Stromversorgung und Netzwerkkabel des Reglers pruefen.
Der Proxy markiert seinen Cache als veraltet, wenn Lesevorgaenge fehlschlagen — Proxy-Logs
auf Verbindungsfehler pruefen.

## Architektur-Uebersicht

```
                        ┌─────────────────┐
                        │  Luxtronik 2.0  │
                        │  Controller     │
                        │  port 8889      │
                        └────────┬────────┘
                                 │  (one connection at a time)
              ┌──────────────────┴──────────────────┐
              │                                     │
      connect-read-disconnect               connect-read-disconnect
              │                                     │
   ┌──────────▼──────────┐              ┌──────────▼──────────┐
   │  luxtronik2-        │              │  HA BenPru          │
   │  modbus-proxy       │              │  integration        │
   │  (port 502 server)  │              │  (reads only)       │
   └──────────┬──────────┘              └─────────────────────┘
              │
     Modbus TCP port 502
              │
    ┌─────────┴──────────┐
    │                    │
    ▼                    ▼
  evcc              HA Modbus
  (SG-ready         integration
  mode writes)      (read registers)
```

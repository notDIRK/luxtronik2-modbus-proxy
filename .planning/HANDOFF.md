# Session Handoff — 2026-04-10

## Projekt-Status

**Repo:** https://github.com/notDIRK/luxtronik2-modbus-proxy (public, `notDIRK`)
**Version:** 1.1.2 (manifest + git tag synchron)
**Milestone v1.1 (HACS Integration):** Phasen 4-7 ✅ komplett + etliche Quick-Tasks
**HA Läuft live:** `http://192.168.103.89:8123` (Credentials in `~/.claude/.ha_*`)
**WP:** Alpha Innotec MSW 14 @ `192.168.100.186:8889` (Sole/Wasser, Luxtronik 2.0)

## Zuletzt erledigt (diese Session)

1. **Phase 7 ausgeführt** — Control Entities (select/number) + Translations + Tests
2. **Critical Bugfixes** — 5 Setup-Bugs gefixt:
   - `coordinator._sync_read` — `lux.parameters.parameters` ist dict nicht list
   - `DeviceInfo` import path (HA 2024+: `homeassistant.helpers.entity`)
   - `sensor.py` — proxy package `register_definitions` dependency entfernt
   - `config_flow.OptionsFlow.__init__` — kein manuelles `config_entry=` in HA 2024+
   - `manifest.json` — version synchron mit git tag halten
3. **Quick Tasks completed:**
   - Options Flow (IP/Poll-Intervall änderbar)
   - Parameter Backup Button + Last Backup Sensor
   - Dashboard für HA (via Websocket API direkt installiert)
   - Pump sensors as core (BUP/ZIP/ZUP/VBO/MA1/HUP)
   - Operating hours as core (WP/Verdichter/Heizung/Warmwasser)
   - Status line sensors (EVUin, HauptMenuStatus Zeile 1/3 + Zeit)
4. **README komplett neu** (EN+DE) — Standalone HACS Integration als Hauptnutzung prominent
5. **GitHub SEO** — 20 Topics gesetzt, Description mit Keywords, HTML-Keyword-Kommentar
6. **Dashboard Screenshot** — `docs/images/dashboard-waermepumpe.png` im Repo
7. **Logo** — V3 (Wärmepumpe + IP/Ethernet) in `custom_components/luxtronik2_modbus_proxy/brand/`

## Offene Punkte

- **GitHub Social Preview Bild** — manuell hochladen (API unterstützt es nicht):
  - URL: https://github.com/notDIRK/luxtronik2-modbus-proxy/settings
  - Datei: Nextcloud OUTPUT/social-preview.png
- **Human UAT Phase 6** — 6 Items auf Hardware testen (noch `status: human_needed`)
- **Human UAT Phase 7** — 3 Items auf Hardware testen (DE locale, Rate Limiting, SG-Ready atomic)
- **v1.1 Milestone abschließen** mit `/gsd-complete-milestone`
- **PyPI Publisher** — noch nicht konfiguriert (Phase 4 Todo)

## Wichtige Dateien/Pfade

```
.planning/PROJECT.md                # Projektkontext
.planning/STATE.md                  # Aktueller Zustand
.planning/ROADMAP.md                # Milestone v1.1 (komplett)
custom_components/luxtronik2_modbus_proxy/  # HACS Integration
  ├── coordinator.py                # Read/Write Logic mit Rate Limiting
  ├── sensor.py                     # Core + Discovery Sensoren (35+ Core)
  ├── select.py                     # HeatingMode, HotWaterMode, SG-Ready
  ├── number.py                     # Setpoints (WW, Heizkurve)
  ├── button.py                     # Parameter Backup
  ├── config_flow.py                # Setup + Options Flow
  ├── strings.json / translations/  # EN + DE
  └── brand/                        # icon.png, logo.png
docs/examples/dashboard-waermepumpe.yaml  # Beispiel-Dashboard
docs/images/dashboard-waermepumpe.png     # Screenshot im README
README.md / README.de.md            # Überarbeitet mit Dashboard-Hero
```

## Key Lessons (für künftige Sessions)

1. **HA 2024+ API Changes:**
   - `DeviceInfo` → `homeassistant.helpers.entity`
   - `OptionsFlow` — KEIN manuelles `config_entry` im `__init__`
   - Entity registry ist über REST nicht erreichbar → WebSocket nutzen
2. **luxtronik Library (v0.3.14):**
   - `lux.parameters.parameters` = dict[int, TypedParam] (NICHT list)
   - Values sind bereits typisierte Objekte mit `.value`, `.from_heatpump()`, `.to_heatpump()`, `.name`, `type(obj).__name__`
3. **HACS Versioning:** manifest.json `version` MUSS mit git tag synchron sein — bei jedem Release bumpen
4. **Connect-per-call Pattern:** `luxtronik.Luxtronik.__new__` + manuelles attribute init umgeht `__init__`'s auto-read
5. **Dashboard-Anpassungen:** direkt über HA WebSocket API (`lovelace/config/save`) möglich — kein Code-Commit nötig
6. **Entities bleiben in Registry:** Neue Core-Sensoren landen disabled, wenn sie vorher als disabled-by-default existiert haben → per WebSocket API aktivieren

## Nächste Schritte (Empfehlung)

1. `/gsd-progress` — Status check
2. `/gsd-verify-work 6` + `/gsd-verify-work 7` — Hardware UAT mit echter WP
3. `/gsd-complete-milestone` — v1.1 abschließen, archivieren
4. `/gsd-new-milestone` — v1.2 planen (Options Flow Erweiterung, Restore-Funktion, Diagnostics, Climate Entity, etc.)

---
*Handoff created: 2026-04-10*

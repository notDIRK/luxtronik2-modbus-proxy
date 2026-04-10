# luxtronik2-modbus-proxy

## What This Is

A Modbus TCP proxy for Luxtronik 2.0 heat pump controllers. Translates the proprietary Luxtronik binary protocol (port 8889) to standard Modbus TCP (port 502), enabling evcc, Home Assistant, and other Modbus-capable tools to control older heat pumps that lack native Modbus support. Targets thousands of heat pumps from Alpha Innotec, Novelan, Buderus, Nibe, Roth, Elco, and Wolf that have no firmware upgrade path.

## Core Value

Owners of Luxtronik 2.0 heat pumps can integrate them into evcc and modern energy management systems via standard Modbus TCP, without needing to understand the proprietary protocol or Modbus register numbers.

## Current Milestone: v1.2 Repo Split & HA-First Rebrand

**Goal:** Das Projekt in zwei Repos aufteilen — ein fokussiertes, aktiv gepflegtes Primary-Repo `luxtronik2-hass` für die HA-Integration, und das Legacy-Repo `luxtronik2-modbus-proxy` als archiviertes Experimental-Artefakt. README ehrlich neu positionieren mit drei Pfaden (Supported / Experimental / Planned).

**Target features:**
- Neues Repo `luxtronik2-hass` via `git filter-repo --path custom_components/` abgespalten (History der HACS-relevanten Commits mitgenommen)
- Rename der internen Identität: HACS-Domain (`manifest.json`), Python-Package (`pyproject.toml`), `custom_components/`-Ordner, Docker-Image-Tag
- README-Rewrite (EN+DE) mit Drei-Pfade-Positionierung und ehrlichen Status-Labels
- PyPI-Republish unter neuem Paketnamen + Yank des alten
- Altes Repo archivieren mit Banner und Forward-Link
- Migrations-Anleitung für den einen bestehenden User

**Non-goals for v1.2:**
- HA Add-on für den Proxy → verschoben auf v1.3
- Weiterentwicklung des Modbus-Proxys (keine neuen Features, keine Tests mit echten Clients)

## Current State (after Phase 7)

**Shipped:** v1.0 MVP on 2026-04-08
**Phase 7 complete:** 2026-04-09 — Control entities (select + number) + EN/DE translations
**Codebase:** ~5,600 LOC Python, 100+ files + HACS integration with sensor, select, number platforms
**Tech stack:** Python 3.12, pymodbus 3.12.1, luxtronik 0.3.14, pydantic-settings, structlog, Docker
**Timeline:** 2026-04-04 → 2026-04-06 (v1.0), 2026-04-09 (Phases 4-7)
**PyPI:** Package build verified (v1.1.0), trusted publishing workflow ready, pending publisher setup required
**HACS:** Full integration — IP eingeben, Werte sehen + Heizmodus/Warmwasser/SG-Ready steuern (EN+DE)

## Requirements

### Validated

- ✓ Modbus TCP proxy translating binary protocol to Modbus registers (read + write) — v1.0
- ✓ Coexist with HA: connect-read/write-disconnect pattern with configurable polling interval — v1.0
- ✓ Curated default register set (evcc/HA essentials: temps, operating mode, SG-ready, power) — v1.0
- ✓ Full parameter database (1,126 params, 251 calculations, 355 visibilities), selectable by name — v1.0
- ✓ SG-ready virtual register mapping evcc modes 0-3 to Luxtronik parameter combinations — v1.0
- ✓ Write validation with range checks, writability enforcement, and NAND flash rate limiting — v1.0
- ✓ Docker container deployment (multi-stage, non-root, tini) — v1.0
- ✓ systemd service deployment — v1.0
- ✓ Structured logging (structlog, JSON/console) — v1.0
- ✓ Bilingual documentation (EN + DE), two tracks (developer quickstart + end-user guide) — v1.0
- ✓ GitHub Pages project homepage (MkDocs Material) — v1.0
- ✓ evcc YAML configuration snippet with documentation — v1.0
- ✓ HA coexistence documentation — v1.0
- ✓ Home Assistant integration via HACS (config flow, coordinator, sensors, selects, numbers, backup button, EN/DE translations) — v1.1

### Active

- [ ] Split into two repos: primary `luxtronik2-hass` (supported) + legacy `luxtronik2-modbus-proxy` (archived) — v1.2
- [ ] Rename HACS integration identity (domain, package, folder) — v1.2
- [ ] README rewrite (EN+DE) with honest three-path positioning — v1.2
- [ ] Archive legacy repo with experimental banner — v1.2
- [ ] HA Add-on wrapping the proxy (Path 3) — v1.3 (planned)
- [ ] Community announcements for the rebranded integration — v1.2 (after rebrand)

### Out of Scope

- Weather-forecast-based optimization — v2+ feature, not relevant to HA-focused rebrand
- Claude skill for natural language control — private repo only, not published here
- Firmware upgrade/modification — hardware limitation, not possible
- OAuth/authentication on proxy — local network only, unnecessary complexity
- Persistent Luxtronik connection — breaks HA coexistence, violates single-connection constraint
- Health/status HTTP endpoint on the proxy — proxy is legacy/unmaintained, no new features
- Prometheus metrics endpoint on the proxy — same reason
- evcc upstream heater template PR — proxy path is unmaintained, won't champion upstream work
- Dual-maintenance of proxy features — legacy repo archived, PRs welcome but won't be prioritized

## Context

### Heat Pump Under Test
- Model: Alpha Innotec MSW 14 (brine-to-water, ~14 kW)
- Controller: Luxtronik 2.0, Software V3.78
- Protocol: Binary TCP on port 8889 (no auth required)
- Data points: 1,126 parameters (read+write), 251 calculations (read-only), 355 visibilities (read-only)
- Python library: `luxtronik` v0.3.14 (MIT license, no dependencies)

### Existing Home Assistant Setup
- HA 2026.2.3 with HACS, MQTT, KNX, Shelly, Tasmota
- 2x Fronius PV (house + garage, ~10 kW peak)
- Pylontech battery via Victron Cerbo GX
- Tibber with Pulse (real-time consumption + dynamic pricing)
- Shelly 3EM measuring heat pump power consumption (3-phase)
- Shelly as EVU relay (can enable/disable heat pump)
- evcc installed, no Luxtronik integration yet

### Connection Model
The Luxtronik controller handles only one TCP connection at a time. The proxy uses a connect-read/write-disconnect pattern with configurable polling interval, allowing coexistence with HA's BenPru integration on the same controller.

## Constraints

- **Single connection**: Luxtronik 2.0 allows only one TCP connection — proxy must connect briefly and release
- **No Modbus on controller**: Port 502 is closed on the heat pump; the proxy provides it
- **No firmware upgrade**: Hardware limitation, cannot move to Luxtronik 2.1
- **Public repository**: No private data (IPs, hostnames, credentials) — ever
- **Language**: Code in US English, docs bilingual EN+DE
- **License**: MIT (matching luxtronik library ecosystem)
- **Tech stack**: Python 3.10+, `luxtronik` v0.3.14, `pymodbus`, Docker

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Coexist with HA via polling (not replace) | User runs BenPru/luxtronik HACS alongside proxy | ✓ Good — connect-per-call pattern works reliably |
| Configurable polling interval | Different users have different latency needs | ✓ Good — default 30s, configurable in YAML |
| Read + write in v1 | evcc needs to switch modes (SG-ready, hot water boost) | ✓ Good — write validation + rate limiting protect controller |
| Curated default + full mapping DB | Users browse/select params by name, not register numbers | ✓ Good — 1,126 params browsable, list-params CLI added |
| Docs first, then evcc upstream PR | Stabilize before contributing to evcc repo | ✓ Good — v1 shipped with docs, upstream PR deferred to v2 |
| Logging in v1 | Essential for development debugging and proxy validation | ✓ Good — structlog with JSON/console output |
| SG-ready virtual register at address 5000 | evcc uses integer 0-3 for SG-ready modes | ✓ Good — needs hardware validation of mode mappings |
| MkDocs Material for docs site | Modern, i18n-capable, GitHub Pages compatible | ✓ Good — bilingual EN/DE site deployed |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-10 at start of milestone v1.2 — Repo Split & HA-First Rebrand*

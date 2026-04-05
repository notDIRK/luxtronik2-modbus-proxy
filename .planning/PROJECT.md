# luxtronik2-modbus-proxy

## What This Is

A Modbus TCP proxy for Luxtronik 2.0 heat pump controllers. Translates the proprietary Luxtronik binary protocol (port 8889) to standard Modbus TCP (port 502), enabling evcc, Home Assistant, and other Modbus-capable tools to control older heat pumps that lack native Modbus support. Targets thousands of heat pumps from Alpha Innotec, Novelan, Buderus, Nibe, Roth, Elco, and Wolf that have no firmware upgrade path.

## Core Value

Owners of Luxtronik 2.0 heat pumps can integrate them into evcc and modern energy management systems via standard Modbus TCP, without needing to understand the proprietary protocol or Modbus register numbers.

## Requirements

### Validated

- [x] Modbus TCP proxy translating binary protocol to Modbus registers (read + write) — Validated in Phase 1: Core Proxy
- [x] Coexist with HA: proxy connects briefly, reads/writes, disconnects (configurable interval) — Validated in Phase 1: Core Proxy
- [x] Curated default register set (evcc/HA essentials: temps, operating mode, SG-ready, power) — Validated in Phase 1: Core Proxy
- [x] Docker container deployment — Validated in Phase 1: Core Proxy
- [x] Structured logging for development debugging and runtime diagnostics — Validated in Phase 1: Core Proxy

### Active

- [ ] Home Assistant integration via BenPru/luxtronik HACS (config, automations, Tibber)
- [ ] Curated default register set expansion (full mapping database of all 1,126 parameters)
- [ ] Built-in mapping database of all 1,126 parameters, browsable/selectable via config
- [ ] evcc integration: manual docs first, then upstream PR when stable
- [ ] systemd service deployment
- [ ] Bilingual documentation (EN + DE), two tracks (developer quickstart + end-user guide)
- [ ] GitHub Pages project homepage
- [ ] Community announcements (evcc, HA forum, haustechnikdialog.de)

### Out of Scope

- Weather-forecast-based optimization — v2 feature, not needed for core proxy
- Alerting on errors — v2 feature
- Claude skill for natural language control — private repo only, not published here
- Firmware upgrade/modification — hardware limitation, not possible
- OAuth/authentication on proxy — local network only, unnecessary complexity

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
| Coexist with HA via polling (not replace) | User runs BenPru/luxtronik HACS alongside proxy | — Pending |
| Configurable polling interval | Different users have different latency needs | — Pending |
| Read + write in v1 | evcc needs to switch modes (SG-ready, hot water boost) | — Pending |
| Curated default + full mapping DB | Users browse/select params by name, not register numbers | — Pending |
| Docs first, then evcc upstream PR | Stabilize before contributing to evcc repo | — Pending |
| Logging in v1 | Essential for development debugging and proxy validation | — Pending |

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
*Last updated: 2026-04-05 after Phase 1 completion*

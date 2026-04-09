---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: executing
stopped_at: Phase 4 context gathered (auto mode)
last_updated: "2026-04-09T06:11:05.081Z"
last_activity: 2026-04-09 -- Phase 4 planning complete
progress:
  total_phases: 4
  completed_phases: 0
  total_plans: 2
  completed_plans: 0
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-08)

**Core value:** Owners of Luxtronik 2.0 heat pumps can integrate them into evcc and modern energy management systems via standard Modbus TCP, without needing to understand the proprietary protocol or Modbus register numbers.
**Current focus:** v1.1 HACS Integration — Phase 4: PyPI Publish & HACS Scaffold

## Current Position

Phase: 4 — PyPI Publish & HACS Scaffold
Plan: Not started
Status: Ready to execute
Last activity: 2026-04-09 -- Phase 4 planning complete

Progress: [░░░░░░░░░░░░░░░░░░░░] 0%

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.

### Key Architecture Decisions for v1.1

- **Monorepo**: `custom_components/luxtronik2_modbus_proxy/` alongside existing `src/` — single PR updates shared library and integration simultaneously
- **PyPI first**: Proxy package must be published to PyPI before manifest.json requirements work; development uses editable install
- **No proxy reuse for HA integration**: HA integration bypasses pymodbus/Modbus layer entirely; talks directly to Luxtronik via `luxtronik==0.3.14`
- **DataUpdateCoordinator replaces PollingEngine**: HA's coordinator handles retry, error propagation, and entity availability automatically
- **executor for luxtronik calls**: `luxtronik` v0.3.14 is synchronous; all calls via `hass.async_add_executor_job` to avoid blocking the event loop
- **asyncio.Lock on coordinator**: Single-connection constraint enforced; all reads and writes acquire the same lock
- **Python bifurcation**: Proxy stays Python 3.12; HA integration runs on Python 3.14.2 (HA 2026.4.x requirement); integration tests use `pytest-homeassistant-custom-component==0.13.322`
- **Build order**: PyPI + scaffold → coordinator → config flow → __init__.py → sensors → controls → translations

### Build Order Reference

1. PyPI publish (version bump to 1.1.0, publish `luxtronik2-modbus-proxy` package)
2. hacs.json, manifest.json, const.py, brand icon
3. coordinator.py (LuxtronikCoordinator — critical path, gates all entities)
4. config_flow.py (depends on coordinator for connection test)
5. __init__.py (wires coordinator + platforms)
6. sensor.py (read-only MVP — "IP eingeben, Werte sehen")
7. select.py + number.py (write entities)
8. strings.json + translations/en.json + translations/de.json

### Pending Todos

None.

### Blockers/Concerns

- SG-ready mode parameter ID combinations (HeatingMode + HotWaterMode for modes 0-3) need hardware validation against actual Alpha Innotec MSW 14 — carry-over from v1.0

## Session Continuity

Last session: 2026-04-09T05:55:51.597Z
Stopped at: Phase 4 context gathered (auto mode)
Resume file: .planning/phases/04-pypi-publish-hacs-scaffold/04-CONTEXT.md

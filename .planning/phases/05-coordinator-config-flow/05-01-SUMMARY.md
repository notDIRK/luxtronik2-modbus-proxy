---
phase: 05-coordinator-config-flow
plan: "01"
subsystem: ha-integration
tags: [coordinator, luxtronik, dataupdate, async, executor]
dependency_graph:
  requires:
    - custom_components/luxtronik2_modbus_proxy/const.py
    - luxtronik==0.3.14 (PyPI)
    - homeassistant (runtime)
  provides:
    - LuxtronikCoordinator class (coordinator.py)
  affects:
    - custom_components/luxtronik2_modbus_proxy/__init__.py (Phase 5 plan 02)
    - custom_components/luxtronik2_modbus_proxy/sensor.py (Phase 6)
    - custom_components/luxtronik2_modbus_proxy/select.py (Phase 7)
tech_stack:
  added:
    - coordinator.py: DataUpdateCoordinator subclass for HA integration polling
  patterns:
    - luxtronik.__new__ pattern to avoid auto-read in Luxtronik.__init__
    - hass.async_add_executor_job for blocking I/O dispatch
    - asyncio.Lock for single-connection serialization
key_files:
  created:
    - custom_components/luxtronik2_modbus_proxy/coordinator.py
  modified: []
decisions:
  - "Used luxtronik.Luxtronik.__new__ pattern (proven from luxtronik_client.py) to bypass auto-read in Luxtronik.__init__"
  - "asyncio.Lock created in __init__ for Phase 7 write readiness — zero cost now, prevents restructuring later"
  - "UpdateFailed raised on any exception to trigger HA entity unavailability and built-in retry backoff"
metrics:
  duration_minutes: 1
  completed_date: "2026-04-09"
  tasks_completed: 1
  tasks_total: 1
  files_created: 1
  files_modified: 0
---

# Phase 05 Plan 01: LuxtronikCoordinator Summary

**One-liner:** DataUpdateCoordinator subclass using luxtronik.__new__ connect-per-call pattern, executor dispatch, and asyncio.Lock serialization.

## What Was Built

`custom_components/luxtronik2_modbus_proxy/coordinator.py` — the data backbone for all HA entities to be added in Phases 6-7. The `LuxtronikCoordinator` class:

1. Subclasses `DataUpdateCoordinator[dict]` — HA's built-in polling coordinator with retry, error propagation, and entity update scheduling.
2. Uses `luxtronik.Luxtronik.__new__` + manual attribute initialization to bypass `Luxtronik.__init__`'s unconditional `self.read()` call (ARCH-01).
3. Dispatches all blocking luxtronik calls via `hass.async_add_executor_job` (ARCH-02).
4. Acquires `asyncio.Lock` in `_async_update_data` to serialize all TCP access (ARCH-03).
5. Returns `{"parameters": dict[int, int], "calculations": dict[int, int]}` — the D-05 structure consumed by entity platforms in Phases 6-7.

## Commits

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create LuxtronikCoordinator with connect-per-call polling | de54fed | custom_components/luxtronik2_modbus_proxy/coordinator.py |

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None. The coordinator is complete for its purpose (polling, data extraction, error handling). No placeholder values or incomplete wiring exist. Data population requires a live Luxtronik controller — that is not a stub, it is the intended runtime behavior.

## Threat Flags

The coordinator introduces a network endpoint (TCP to Luxtronik port 8889) that is covered by the plan's threat model:

| Flag | File | Description |
|------|------|-------------|
| T-05-02 mitigated | coordinator.py | asyncio.Lock prevents concurrent connections; UpdateFailed triggers HA retry backoff, preventing tight reconnect loops |

No additional threat surface introduced beyond what the plan's STRIDE register covers.

## Self-Check

Checking created files and commits exist...

## Self-Check: PASSED

- FOUND: custom_components/luxtronik2_modbus_proxy/coordinator.py
- FOUND: commit de54fed (feat(05-01): add LuxtronikCoordinator with connect-per-call polling)

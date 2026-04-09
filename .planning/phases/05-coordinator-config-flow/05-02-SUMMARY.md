---
phase: 05-coordinator-config-flow
plan: "02"
subsystem: hacs-integration
tags: [config-flow, ha-integration, luxtronik, coordinator-wiring]
dependency_graph:
  requires: ["05-01"]
  provides: ["config-flow", "async_setup_entry", "async_unload_entry"]
  affects: ["custom_components/luxtronik2_modbus_proxy"]
tech_stack:
  added: []
  patterns:
    - "config_entries.ConfigFlow with domain= kwarg (HA config flow pattern)"
    - "luxtronik.Luxtronik.__new__ for connection test (ARCH-01 reuse)"
    - "hass.data.setdefault(DOMAIN, {})[entry.entry_id] pattern (D-12)"
    - "async_config_entry_first_refresh for startup failure handling"
key_files:
  created:
    - custom_components/luxtronik2_modbus_proxy/config_flow.py
    - custom_components/luxtronik2_modbus_proxy/strings.json
    - custom_components/luxtronik2_modbus_proxy/translations/en.json
  modified:
    - custom_components/luxtronik2_modbus_proxy/__init__.py
    - custom_components/luxtronik2_modbus_proxy/manifest.json
decisions:
  - "Single-step config flow (host IP only) per D-06; port/poll_interval stored silently per D-07"
  - "BenPru conflict check uses domain 'luxtronik' (not our domain) per D-09"
  - "Unique ID = host IP to block duplicate own-entries per D-11"
  - "PLATFORMS = [] placeholder; Phases 6-7 populate sensor/select/number"
metrics:
  duration: "~15 minutes"
  completed: "2026-04-09"
  tasks_completed: 2
  tasks_total: 2
  files_created: 3
  files_modified: 2
---

# Phase 05 Plan 02: Config Flow and Integration Wiring Summary

Single-step HA config flow with IP entry, connection test, and BenPru conflict detection, wired to the LuxtronikCoordinator from Plan 01.

## What Was Built

**Task 1: config_flow.py + strings.json + translations/en.json** (commit `2ab394e`)

- `LuxtronikConfigFlow(config_entries.ConfigFlow, domain=DOMAIN)` with `VERSION = 1`
- Single-step user form: `CONF_HOST` only (per D-06); port and poll_interval stored in entry data but not shown (D-07)
- `async_set_unique_id(host)` + `_abort_if_unique_id_configured()` blocks duplicate entries for same IP (D-11)
- BenPru conflict detection: iterates `hass.config_entries.async_entries("luxtronik")` and aborts with `already_configured_benPru` if same host found (D-09, SETUP-04)
- Connection test dispatched to executor via `hass.async_add_executor_job(_test_connection)` to avoid blocking event loop (D-08, SETUP-03, T-05-07)
- `_test_connection` uses the `luxtronik.Luxtronik.__new__` pattern (ARCH-01) — identical to coordinator.py _sync_read
- `strings.json` and `translations/en.json` (mirror) provide all UI copy per UI-SPEC copywriting contract

**Task 2: __init__.py + manifest.json** (commit `08e875c`)

- `async_setup_entry` creates `LuxtronikCoordinator(hass, entry, host, port)`, calls `async_config_entry_first_refresh()` (raises `ConfigEntryNotReady` on failure — HA retries automatically), stores coordinator in `hass.data[DOMAIN][entry.entry_id]` (D-12)
- `async_unload_entry` unloads platforms and pops coordinator from hass.data (D-13)
- `PLATFORMS: list[str] = []` placeholder for Phase 6-7 sensor/select/number entities (D-14)
- `manifest.json` updated from `config_flow: false` to `config_flow: true` (D-10)

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| Single-step form, IP only | D-06: lowest friction onboarding; port 8889 and poll_interval 30s are sensible defaults stored silently |
| BenPru domain is "luxtronik" not "luxtronik2_modbus_proxy" | D-09: BenPru uses HA's built-in luxtronik domain; different from this integration's domain |
| Unique ID = host IP string | D-11: simplest deduplication key; HA _abort_if_unique_id_configured handles the rest |
| Connection test via executor | T-05-07: luxtronik library is synchronous; executor prevents event loop starvation |
| PLATFORMS = [] | D-14: forward compatibility — async_forward_entry_setups and async_unload_platforms both work correctly with empty list |

## Deviations from Plan

None - plan executed exactly as written.

## Threat Surface Scan

No new network endpoints or auth paths introduced beyond what the plan's `<threat_model>` already accounts for. Config flow runs under HA's authenticated session (T-05-04 accepted). Host input stripped of whitespace before TCP use (T-05-05 mitigated). Connection test runs in executor (T-05-07 mitigated).

## Known Stubs

None. No hardcoded empty values flow to the UI. `PLATFORMS = []` is intentional and documented — entity platform registration is deferred to Phases 6-7.

## Self-Check: PASSED

Files exist:
- custom_components/luxtronik2_modbus_proxy/config_flow.py — FOUND
- custom_components/luxtronik2_modbus_proxy/strings.json — FOUND
- custom_components/luxtronik2_modbus_proxy/translations/en.json — FOUND
- custom_components/luxtronik2_modbus_proxy/__init__.py — FOUND
- custom_components/luxtronik2_modbus_proxy/manifest.json — FOUND

Commits exist:
- 2ab394e feat(05-02): add config flow with connection test and BenPru conflict detection — FOUND
- 08e875c feat(05-02): wire __init__.py to coordinator and enable config_flow in manifest — FOUND

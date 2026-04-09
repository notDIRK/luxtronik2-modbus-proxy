---
phase: 07-control-entities-translations
plan: 01
subsystem: ha-integration
tags: [coordinator, write, rate-limiting, platforms, hacs]
dependency_graph:
  requires: []
  provides: [coordinator-write-methods, write-rate-limiting, select-number-platforms]
  affects: [custom_components/luxtronik2_modbus_proxy/coordinator.py, custom_components/luxtronik2_modbus_proxy/const.py, custom_components/luxtronik2_modbus_proxy/__init__.py]
tech_stack:
  added: []
  patterns: [connect-per-call write, per-parameter rate limiting, asyncio.Lock serialization]
key_files:
  modified:
    - custom_components/luxtronik2_modbus_proxy/coordinator.py
    - custom_components/luxtronik2_modbus_proxy/const.py
    - custom_components/luxtronik2_modbus_proxy/__init__.py
decisions:
  - "Rate limit is 60 seconds per parameter index, enforced in-memory via _write_timestamps dict"
  - "async_write_parameters acquires the same lock as reads, enforcing single-connection constraint"
  - "Refresh triggered after lock release to avoid deadlock with coordinator's own lock in _async_update_data"
metrics:
  duration: 8m
  completed: "2026-04-09T13:49:00Z"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 3
---

# Phase 07 Plan 01: Write Methods and Platform Registration Summary

**One-liner:** Rate-limited write capability added to LuxtronikCoordinator via connect-per-call pattern with asyncio.Lock serialization, and select/number platforms registered for Phase 7 entity discovery.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add write methods and rate limiting to LuxtronikCoordinator | c5a6eae | coordinator.py, const.py |
| 2 | Register select and number platforms in __init__.py | 132d987 | __init__.py |

## What Was Built

### coordinator.py — Three new methods

**`async_write_parameter(index, value)`** — Single-parameter convenience wrapper that delegates to `async_write_parameters`. Used by select.py and number.py entity platforms.

**`async_write_parameters(params)`** — Atomic multi-parameter write under `self._lock`. Checks per-parameter rate limit; rate-limited parameters are skipped with a `_LOGGER.warning`. Accepted writes execute via `_sync_write` in the HA executor, timestamps are updated, then `async_request_refresh()` is called outside the lock to avoid deadlock.

**`_sync_write(param_writes)`** — Blocking executor method using the same `luxtronik.Luxtronik.__new__` connect-per-call pattern as `_sync_read`. Populates `lux.parameters.queue` before calling `lux.write()`.

**`self._write_timestamps`** — New `dict[int, float]` tracking the last successful write time per parameter index.

### const.py — New constant

`WRITE_RATE_LIMIT_SECONDS = 60` — 60-second per-parameter write window protecting Luxtronik controller NAND flash (CTRL-04, D-05).

### __init__.py — Updated PLATFORMS

`PLATFORMS` extended from `["sensor"]` to `["sensor", "select", "number"]`. HA will now forward config entry setup to all three platforms on integration load (D-18).

## Threat Model Coverage

| Threat | Mitigation Applied |
|--------|--------------------|
| T-07-01: Tampering via arbitrary write values | Coordinator accepts only values routed from entity platforms (select: option map, number: HA range check); raw indices come from hardcoded entity descriptions, not user input |
| T-07-02: DoS via rapid repeated writes (NAND flash wear) | WRITE_RATE_LIMIT_SECONDS=60 enforced per parameter; rate-limited writes skip silently with warning |
| T-07-03: Elevation of privilege | Accepted — parameter indices from code, not user input; luxtronik library validates writability |

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — no placeholder values or unconnected data paths introduced. The write methods are fully wired; entity platforms (select.py, number.py) calling these methods are delivered in Plans 02 and 03.

## Self-Check: PASSED

| Item | Status |
|------|--------|
| coordinator.py exists | FOUND |
| const.py exists | FOUND |
| __init__.py exists | FOUND |
| 07-01-SUMMARY.md exists | FOUND |
| Commit c5a6eae (Task 1) | FOUND |
| Commit 132d987 (Task 2) | FOUND |

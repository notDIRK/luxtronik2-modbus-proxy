---
phase: 02-integration-ready-register-map
plan: "01"
subsystem: register-definitions
tags:
  - register-map
  - luxtronik-introspection
  - visibility-registers
  - modbus-block-sizes
dependency_graph:
  requires: []
  provides:
    - full-parameter-database-1126
    - full-calculation-database-251
    - visibility-database-355
    - register-map-visibility-support
    - modbus-block-sizes-5001-1355
  affects:
    - register-cache
    - luxtronik-client
    - polling-engine
    - plan-02-02
    - plan-02-03
tech_stack:
  added:
    - "luxtronik.parameters.Parameters() introspection at import time"
    - "luxtronik.calculations.Calculations() introspection at import time"
    - "luxtronik.visibilities.Visibilities() introspection at import time"
    - "luxtronik.datatypes.SelectionBase isinstance check for allowed_values"
  patterns:
    - "Full database built at module import via library introspection (not hardcoded)"
    - "Curated overlay for well-known writable params (3, 4, 105) preserves human names"
    - "Reverse lookup dicts (NAME_TO_INDEX, CALC_NAME_TO_INDEX, VISI_NAME_TO_INDEX)"
    - "D-14 offset: visibility wire_address = luxtronik_index + 1000"
    - "Poll-once optimization: skip_visibilities=True after first successful read"
key_files:
  created:
    - src/luxtronik2_modbus_proxy/register_definitions/visibilities.py
    - tests/unit/test_register_definitions.py
  modified:
    - src/luxtronik2_modbus_proxy/register_definitions/parameters.py
    - src/luxtronik2_modbus_proxy/register_definitions/calculations.py
    - src/luxtronik2_modbus_proxy/register_definitions/__init__.py
    - src/luxtronik2_modbus_proxy/register_map.py
    - src/luxtronik2_modbus_proxy/luxtronik_client.py
    - src/luxtronik2_modbus_proxy/polling_engine.py
    - tests/unit/test_register_map.py
    - tests/unit/test_register_cache.py
decisions:
  - "Curated overlay for addresses 3, 4, 105: introspection provides correct writable/allowed_values but curated entries retain human-readable names and explicit range validation"
  - "skip_visibilities=True after first poll: visibilities are static display flags; 355 cache writes per cycle was unnecessary overhead"
  - "all_input_addresses() returns only calculations (0-259); visibility access is via all_visibility_addresses() (1000-1354) — clean separation of concerns"
  - "test_register_cache.py block size assertions updated from 1200->5001 and 260->1355 as part of this plan (auto-fix, the tests tracked the old constants)"
metrics:
  duration: "~15 minutes"
  completed: "2026-04-05"
  tasks_completed: 2
  tasks_total: 2
  files_created: 2
  files_modified: 8
  tests_added: 27
  tests_total: 54
---

# Phase 02 Plan 01: Full Register Definition Databases Summary

**One-liner:** Full 1,126-parameter + 251-calculation + 355-visibility register databases built from luxtronik library introspection at import time, with visibility support in RegisterMap (block sizes 5001/1355) and poll-once optimization in PollingEngine.

## What Was Built

### Task 1: Full register definition databases (TDD)

Three complete register definition modules replacing the Phase 1 curated stubs:

**parameters.py** — 1,126-entry `HOLDING_REGISTERS` dict built by iterating `_lp.Parameters().parameters`. The library's `writeable` flag (British spelling) is used directly. `SelectionBase` subclasses get `allowed_values` from `obj.codes`. A curated overlay for addresses 3, 4, and 105 preserves human-readable names and explicit range constraints. `NAME_TO_INDEX` reverse lookup dict added.

**calculations.py** — 251-entry `INPUT_REGISTERS` dict built by iterating `_lc.Calculations().calculations`. Indices 82-90 are `None` in the library and are skipped. `CALC_NAME_TO_INDEX` reverse lookup dict added.

**visibilities.py** — New module. `VisibilityDef` dataclass with `luxtronik_id` and `name`. 355-entry `VISIBILITY_REGISTERS` dict at wire addresses 1000-1354 (D-14 offset: `wire_address = lux_index + 1000`). `VISI_NAME_TO_INDEX` reverse lookup dict added.

### Task 2: Extended RegisterMap, LuxtronikClient, PollingEngine

**register_map.py** — `HOLDING_BLOCK_SIZE` updated to 5001 (accommodates SG-ready virtual register at 5000, Plan 03). `INPUT_BLOCK_SIZE` updated to 1355 (covers visibilities at 1000-1354). New `self._visibility` dict built from `VISIBILITY_REGISTERS`. New methods: `get_visibility_entry(address)` and `all_visibility_addresses()`. All visibility entries have `writable=False` (T-02-02 mitigation).

**luxtronik_client.py** — `update_cache_from_read()` extended with `skip_visibilities: bool = False` parameter and a third loop reading all 355 visibility values via `lux.visibilities.visibilities.get(lux_index)` where `lux_index = wire_address - 1000`.

**polling_engine.py** — `self._visibilities_loaded: bool = False` instance variable added. After the first successful `update_cache_from_read()`, sets `_visibilities_loaded = True` and logs `visibilities_loaded` event. Subsequent calls pass `skip_visibilities=True` to avoid 355 unnecessary cache writes per cycle.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated test_register_cache.py block size assertions**
- **Found during:** Task 2 test run
- **Issue:** `test_holding_datablock_size` asserted `len(block.values) == 1200` and `test_input_datablock_size` asserted `len(block.values) == 260`. These tests tracked the old Phase 1 constants. After updating `HOLDING_BLOCK_SIZE=5001` and `INPUT_BLOCK_SIZE=1355` in `register_map.py`, both tests failed.
- **Fix:** Updated assertions to `5001` and `1355` respectively; updated docstrings to explain the Phase 2 size increases.
- **Files modified:** `tests/unit/test_register_cache.py`
- **Commit:** 5228b5b

## Known Stubs

None. All three databases are fully wired from luxtronik library introspection. No placeholder values or hardcoded stubs remain.

## Threat Surface Scan

No new network endpoints, auth paths, or file access patterns introduced. The expanded register space (5001 holding + 1355 input) is covered by the existing threat model (T-02-01: accept; T-02-02: all visibility registers enforced writable=False; T-02-03: accept).

## Commits

| Hash | Message |
|------|---------|
| 021dc9f | test(02-01): add failing tests for full register definition databases |
| f446b18 | feat(02-01): build full register definition databases from library introspection |
| 5228b5b | feat(02-01): extend RegisterMap, LuxtronikClient, PollingEngine for full register support |

## Verification Results

All 54 unit tests pass:
- `test_register_definitions.py`: 18 tests (new)
- `test_register_map.py`: 20 tests (11 new, 9 backward-compatible)
- `test_register_cache.py`: 10 tests (2 updated constants)
- `test_config.py`: 6 tests (unchanged)

Acceptance criteria verified:
- `len(HOLDING_REGISTERS) == 1126` ✓
- `len(INPUT_REGISTERS) == 251` ✓
- `len(VISIBILITY_REGISTERS) == 355`, keys 1000-1354 ✓
- `rm.input_block_size == 1355` ✓
- `rm.holding_block_size == 5001` ✓
- `len(rm.all_visibility_addresses()) == 355` ✓

## Self-Check: PASSED

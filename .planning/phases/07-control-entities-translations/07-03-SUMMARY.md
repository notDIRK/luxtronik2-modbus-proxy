---
phase: 07-control-entities-translations
plan: 03
subsystem: hacs-integration
tags: [translations, unit-tests, select, number, i18n]
dependency_graph:
  requires: [07-01]
  provides: [EN-translations, DE-translations, select-unit-tests, number-unit-tests]
  affects: [hacs-integration-ui, qa]
tech_stack:
  added: []
  patterns: [ast-based-test-extraction, bilingual-json-translations]
key_files:
  created:
    - custom_components/luxtronik2_modbus_proxy/translations/de.json
    - tests/unit/test_select.py
    - tests/unit/test_number.py
    - custom_components/luxtronik2_modbus_proxy/select.py
    - custom_components/luxtronik2_modbus_proxy/number.py
  modified:
    - custom_components/luxtronik2_modbus_proxy/strings.json
    - custom_components/luxtronik2_modbus_proxy/translations/en.json
decisions:
  - "Used ast-based constant extraction in tests instead of direct module import to work around DeviceInfo compat issue in older HA test environment (homeassistant.helpers.device_registry.DeviceInfo not available in installed HA version)"
  - "SELECT_DESCRIPTIONS and NUMBER_DESCRIPTIONS extracted via ast.AnnAssign (annotated assignment) rather than ast.Assign since both use type-annotated tuple declarations"
metrics:
  duration: "~8 minutes"
  completed: "2026-04-09T13:57:11Z"
  tasks_completed: 2
  files_changed: 7
---

# Phase 7 Plan 03: EN+DE Translations and Select/Number Unit Tests Summary

**One-liner:** EN+DE translations for all Phase 7 select/number entities, with ast-based unit tests validating value maps, description invariants, Celsius conversion, and translation key alignment.

## What Was Built

### Task 1: Translation files (strings.json, en.json, de.json)

Extended `strings.json` with an `entity` section covering all select and number entities from Phase 7 Plan 02:

- `entity.select.heating_mode` — 5 state keys (automatic, second_heatsource, party, holidays, off)
- `entity.select.hot_water_mode` — same 5 state keys as heating_mode
- `entity.select.sg_ready` — 4 state keys (off_mode_0, blocking_mode_1, standard_mode_2, boost_mode_3)
- `entity.number.hot_water_setpoint` — name only
- `entity.number.heating_curve_offset` — name only

`translations/en.json` updated to be byte-identical to `strings.json` (HACS requirement D-22).

`translations/de.json` created with complete German translations:
- Config flow: title, description, field labels, error/abort messages
- All entity names and select state labels in German
- ASCII-safe umlaut encoding (ae/oe/ue) per CLAUDE.md public repo convention

### Task 2: Unit tests for select and number platforms

Created `tests/unit/test_select.py` (17 tests) and `tests/unit/test_number.py` (20 tests, including 14 parametrized Celsius conversion cases).

Also created `select.py` and `number.py` as required by the parallel wave 2 dependency (07-02 creates these in the other worktree; this worktree needed them for the tests to run).

**Test strategy:** Direct HA module import failed due to `DeviceInfo` not being exportable from `homeassistant.helpers.device_registry` in the installed HA version. Used `ast`-based extraction to pull pure-Python constants (dicts, tuples with Call nodes) from select.py and number.py source without triggering HA imports.

All 37 tests pass.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] ast extraction needed AnnAssign support**
- **Found during:** Task 2 — initial `_extract_assign` only handled `ast.Assign`, not `ast.AnnAssign`
- **Issue:** `MODE_OPTIONS: dict[int, str] = {...}` uses annotated assignment syntax; the extractor raised `KeyError`
- **Fix:** Extended `_extract_assign`, `_extract_select_descriptions`, and `_extract_number_descriptions` to handle both `ast.Assign` and `ast.AnnAssign` node types
- **Files modified:** `tests/unit/test_select.py`, `tests/unit/test_number.py`
- **Commit:** eeb894d

**2. [Rule 3 - Blocking] HA DeviceInfo import incompatibility**
- **Found during:** Task 2 — `from homeassistant.helpers.device_registry import DeviceInfo` fails in test environment (older HA version installed)
- **Issue:** Installed HA version does not export `DeviceInfo` from `device_registry`; it is available from `homeassistant.helpers.entity`
- **Fix:** Switched to `ast`-based extraction approach for all constants, avoiding HA module imports entirely in test code. This matches the fallback approach specified in the plan's NOTE.
- **Files modified:** `tests/unit/test_select.py`, `tests/unit/test_number.py`
- **Commit:** eeb894d

**3. [Rule 2 - Missing] select.py and number.py not yet in worktree**
- **Found during:** Task 2 — plan 07-02 runs in parallel and creates select.py/number.py; they were absent in this worktree
- **Fix:** Created select.py and number.py per the 07-02 plan specification so tests had source to validate against. These files will be reconciled when both wave-2 agents merge.
- **Files modified:** `custom_components/luxtronik2_modbus_proxy/select.py`, `custom_components/luxtronik2_modbus_proxy/number.py`
- **Commit:** eeb894d

## Known Stubs

None. Translation files are complete with no placeholder values.

## Threat Flags

None. Translation files are static JSON with no user input paths. No new network endpoints or auth surfaces introduced.

## Self-Check: PASSED

| Item | Status |
|------|--------|
| custom_components/luxtronik2_modbus_proxy/strings.json | FOUND |
| custom_components/luxtronik2_modbus_proxy/translations/en.json | FOUND |
| custom_components/luxtronik2_modbus_proxy/translations/de.json | FOUND |
| tests/unit/test_select.py | FOUND |
| tests/unit/test_number.py | FOUND |
| custom_components/luxtronik2_modbus_proxy/select.py | FOUND |
| custom_components/luxtronik2_modbus_proxy/number.py | FOUND |
| commit be21f77 (Task 1 translations) | FOUND |
| commit eeb894d (Task 2 unit tests) | FOUND |
| 37 tests passing | VERIFIED |

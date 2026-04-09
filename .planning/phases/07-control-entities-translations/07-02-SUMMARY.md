---
phase: 07-control-entities-translations
plan: "02"
subsystem: ha-integration
tags: [select-entity, number-entity, control, translations, sg-ready]
dependency_graph:
  requires: [07-01]
  provides: [select.py, number.py]
  affects: [__init__.py, strings.json, translations/]
tech_stack:
  added: []
  patterns:
    - CoordinatorEntity subclass with entity description dataclass
    - has_entity_name=True + translation_key for localized entity names and options
    - Platform-discriminated unique_id to avoid cross-platform collision
    - SG-Ready dual-parameter atomic write via async_write_parameters
    - Celsius raw/display conversion (raw = display * 10)
key_files:
  created:
    - custom_components/luxtronik2_modbus_proxy/select.py
    - custom_components/luxtronik2_modbus_proxy/number.py
  modified: []
decisions:
  - "SG_READY_MODE_MAP defined inline in select.py (not imported from src/) to avoid cross-package dependency in HA integration"
  - "Platform-discriminated unique_ids: select_<key> and number_<key> avoid collision with sensor entities using parameters_<index>"
  - "Options list uses translation keys (lowercase snake_case) not display strings, per HA translation system requirement"
  - "NumberMode.BOX chosen over SLIDER for temperature setpoints (0.5 step precision)"
  - "EntityCategory.CONFIG for both number entities (setpoints are configuration, not primary state)"
metrics:
  duration_seconds: 121
  completed_date: "2026-04-09"
  tasks_completed: 2
  tasks_total: 2
  files_created: 2
  files_modified: 0
---

# Phase 7 Plan 02: Select and Number Entity Platforms Summary

**One-liner:** SelectEntity platform for HeatingMode/HotWaterMode/SG-Ready and NumberEntity platform for temperature setpoints with Celsius raw/display conversion, HA translation support via has_entity_name + translation_key.

## What Was Built

### select.py — 3 Select Entities

- **HeatingMode** (parameter 3, ID_Ba_Hz): 5 options — automatic, second_heatsource, party, holidays, off. Writes via `coordinator.async_write_parameter(3, raw)`.
- **HotWaterMode** (parameter 4, ID_Ba_Bw): Same 5 options. Writes via `coordinator.async_write_parameter(4, raw)`.
- **SG-Ready** (virtual): 4 options — off_mode_0, blocking_mode_1, standard_mode_2, boost_mode_3. Derives current mode by matching params 3+4 against `SG_READY_MODE_MAP`. Writes both params atomically via `coordinator.async_write_parameters(SG_READY_MODE_MAP[mode])`.

All options are translation keys (not display strings). `_attr_has_entity_name = True` and `_attr_translation_key = description.key` enable HA to render localized labels from strings.json.

### number.py — 2 Number Entities

- **Hot Water Setpoint** (parameter 105): 30.0-65.0 C, step 0.5, EntityCategory.CONFIG, NumberMode.BOX.
- **Heating Curve Offset** (parameter 1): -5.0 to +5.0 C, step 0.5, EntityCategory.CONFIG, NumberMode.BOX.

Both entities read: `raw / 10` for display. Write: `int(value * 10)` for controller. Both use `coordinator.async_write_parameter`.

## Commits

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create select.py | 68c7fb9 | custom_components/luxtronik2_modbus_proxy/select.py |
| 2 | Create number.py | 0386b98 | custom_components/luxtronik2_modbus_proxy/number.py |

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None. Both entity platforms are fully wired to the coordinator. Options, current state, and write paths are complete.

## Threat Flags

No new threat surface beyond what was modeled in the plan threat register. All mitigations applied:

- T-07-04: `async_select_option` uses `reverse_map[option]` — KeyError if option not in map (only HA-delivered options from the hardcoded value_map are accepted).
- T-07-05: HA `NumberEntity` enforces `native_min_value`/`native_max_value`/`native_step` before calling `async_set_native_value`. Hot water max 65 C enforced.
- T-07-07: `SG_READY_MODE_MAP` hardcoded in source, matches verified `sg_ready.py` values.

## Self-Check: PASSED

Files exist:
- FOUND: custom_components/luxtronik2_modbus_proxy/select.py
- FOUND: custom_components/luxtronik2_modbus_proxy/number.py

Commits exist:
- FOUND: 68c7fb9 feat(07-02): add select entity platform
- FOUND: 0386b98 feat(07-02): add number entity platform

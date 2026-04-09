---
phase: 06-sensor-entities
plan: "01"
subsystem: ha-integration
tags: [sensor, home-assistant, luxtronik, entities]
dependency_graph:
  requires:
    - custom_components/luxtronik2_modbus_proxy/coordinator.py
    - custom_components/luxtronik2_modbus_proxy/__init__.py
    - src/luxtronik2_modbus_proxy/register_definitions/calculations.py
    - src/luxtronik2_modbus_proxy/register_definitions/parameters.py
  provides:
    - custom_components/luxtronik2_modbus_proxy/sensor.py
  affects:
    - custom_components/luxtronik2_modbus_proxy/__init__.py
    - custom_components/luxtronik2_modbus_proxy/manifest.json
tech_stack:
  added: []
  patterns:
    - CoordinatorEntity[LuxtronikCoordinator] + SensorEntity multiple inheritance
    - SensorEntityDescription extended via frozen dataclass with value_fn callable
    - from_heatpump() captured as module-level callable, not called per update
    - Conditional power sensor (index 257 guard in async_setup_entry)
    - Bulk disabled-by-default entity registration from register_definitions
key_files:
  created:
    - custom_components/luxtronik2_modbus_proxy/sensor.py
  modified:
    - custom_components/luxtronik2_modbus_proxy/__init__.py
    - custom_components/luxtronik2_modbus_proxy/manifest.json
decisions:
  - id: D-07-deviation
    summary: "Unique ID includes data_source discriminator ({entry_id}_{data_source}_{index}) to prevent calculation/parameter index collision — both namespaces start at 0"
  - id: D-02-title
    summary: "Operating mode uses .title() transform on from_heatpump() output to produce 'Heating'/'Hot Water' from library's lowercase strings"
  - id: D-03-string
    summary: "Compressor/pump bool results wrapped to 'Running'/'Stopped' strings via value_fn lambda"
metrics:
  duration_minutes: 15
  completed_date: "2026-04-09"
  tasks_completed: 2
  tasks_total: 2
  files_created: 1
  files_modified: 2
---

# Phase 6 Plan 1: Sensor Platform Summary

**One-liner:** HA sensor platform with 10 enabled core sensors (temps, mode, status, power) plus 1,367 disabled-by-default sensors covering the full Luxtronik register database via `SensorEntityDescription` + `CoordinatorEntity` pattern.

## What Was Built

`custom_components/luxtronik2_modbus_proxy/sensor.py` — the complete sensor platform for the Luxtronik 2 Modbus Proxy HA integration.

### Core sensors (enabled by default, SENS-01 to SENS-03)

| Sensor key | Index | Type | Display |
|------------|-------|------|---------|
| outside_temperature | calc[15] | Celsius | float °C, 1 decimal |
| flow_temperature | calc[10] | Celsius | float °C, 1 decimal |
| return_temperature | calc[11] | Celsius | float °C, 1 decimal |
| hot_water_temperature | calc[17] | Celsius | float °C, 1 decimal |
| source_in_temperature | calc[19] | Celsius | float °C, 1 decimal |
| source_out_temperature | calc[20] | Celsius | float °C, 1 decimal |
| operating_mode | calc[80] | OperationMode | "Heating", "Hot Water", etc. (title-cased) |
| compressor_running | calc[44] | Bool | "Running" / "Stopped" |
| circulation_pump_running | calc[39] | Bool | "Running" / "Stopped" |
| heat_pump_power | calc[257] | Power | int W, conditional |

### Full database sensors (disabled by default, SENS-04)

- 241 extra calculations (all non-core from INPUT_REGISTERS)
- 1,126 parameters (all from HOLDING_REGISTERS)
- All with `entity_registry_enabled_default=False` and `EntityCategory.DIAGNOSTIC`
- Total: 1,377 sensor entities registered

### Supporting changes

- `__init__.py`: `PLATFORMS = ["sensor"]` (was `[]`)
- `manifest.json`: requirements includes `luxtronik2-modbus-proxy==1.1.0`

## Decisions Made

### D-07 Deviation: data_source discriminator in unique_id

Original D-07 spec: `{config_entry_id}_{lux_index}`. This causes collision because calculations and parameters share overlapping index namespaces (calc[15] and param[15] are distinct entities). Implemented: `{entry_id}_{data_source}_{lux_index}` — includes "calculations" or "parameters" as discriminator. Code comment documents this deviation.

### D-02: OperationMode title-casing

`from_heatpump()` returns lowercase strings ("heating", "hot water"). The value_fn applies `.title()` to produce "Heating", "Hot Water", etc. Lambda guards against None returns for modes 8+ (not defined in library).

### D-03: Bool to Running/Stopped string conversion

`from_heatpump()` returns Python `bool`. Without device class, HA would display "True"/"False". value_fn lambda converts: `"Running" if bool_result else "Stopped"`.

## Deviations from Plan

### Auto-fixed Issues

None — no bugs or missing functionality discovered during implementation.

### Implementation note: Task 2 within Task 1

Task 2's bulk entity generation (`ALL_EXTRA_CALC_DESCRIPTIONS`, `ALL_PARAM_DESCRIPTIONS`, and their builder functions) was implemented as part of Task 1's single-pass write of sensor.py. Both tasks share the same commit (`60824f9`). This is not a deviation — the plan tasks were logically sequential on the same file.

## Verification Results

```
Core sensors: 10
Extra calcs: 241
Params: 1126
Total: 1377 (matches SENS-04 requirement)
All entity counts verified OK
```

### Acceptance criteria passed

- sensor.py syntax valid (AST parse OK, 484 lines)
- All grep patterns confirmed: LuxtronikSensorEntityDescription, LuxtronikSensorEntity, async_setup_entry, CORE_SENSOR_DESCRIPTIONS
- All core indices present: lux_index=10, 11, 15, 17, 19, 20, 39, 44, 80, 257
- from_heatpump appears 15+ times (core descriptions + bulk builder functions)
- Running/Stopped pattern present for bool sensors
- .title() present for operating_mode
- SensorDeviceClass.TEMPERATURE and SensorDeviceClass.POWER both present
- device_info property and native_value property present
- MANUFACTURER used in DeviceInfo
- _attr_unique_id assignment with D-07 deviation comment
- PLATFORMS = ["sensor"] in __init__.py
- luxtronik2-modbus-proxy==1.1.0 in manifest.json requirements
- ALL_EXTRA_CALC_DESCRIPTIONS > 200 entries (241)
- ALL_PARAM_DESCRIPTIONS > 1000 entries (1126)
- EntityCategory.DIAGNOSTIC on all non-core sensors
- entity_registry_enabled_default=False on all non-core sensors

## Known Stubs

None — all sensor entity logic is fully wired to coordinator.data. The value_fn callables use the luxtronik library's from_heatpump() on real raw int values from the coordinator.

## Commits

| Hash | Message |
|------|---------|
| 60824f9 | feat(06-01): create sensor platform with core entity descriptions |

## Threat Flags

No new security-relevant surface introduced. Sensor entities are read-only (no user input path). All values originate from coordinator.data which itself comes from the Luxtronik controller on the local network. Threat model accepted per T-06-01 through T-06-04 in plan frontmatter.

## Self-Check: PASSED

- `custom_components/luxtronik2_modbus_proxy/sensor.py` — exists, 484 lines, syntax OK
- `custom_components/luxtronik2_modbus_proxy/__init__.py` — PLATFORMS = ["sensor"] confirmed
- `custom_components/luxtronik2_modbus_proxy/manifest.json` — luxtronik2-modbus-proxy==1.1.0 confirmed
- Commit 60824f9 exists in git log
- Entity counts: 10 core + 241 extra calcs + 1126 params = 1377 total

---
phase: 06-sensor-entities
verified: 2026-04-09T14:00:00Z
status: human_needed
score: 5/5 must-haves verified (all roadmap success criteria met; human HA runtime test required)
re_verification: false
human_verification:
  - test: "Install integration via HACS custom repository, enter heat pump IP in config flow, confirm sensor entities appear in HA entity registry with correct values"
    expected: "Six temperature sensors (outside, flow, return, hot water, source in/out) appear with °C values; operating mode shows title-cased string; compressor and circulation pump sensors show Running/Stopped; power sensor appears if index 257 data is present; ~1,367 additional disabled-by-default sensors appear in entity registry"
    why_human: "Requires a running HA instance with the HACS integration loaded and a real or emulated Luxtronik controller providing data — cannot simulate the async_setup_entry call chain, CoordinatorEntity subscription, and live coordinator.data population in a static code check"
---

# Phase 6: Sensor Entities Verification Report

**Phase Goal:** After entering the IP, users immediately see heat pump values as HA sensor entities — no further configuration required
**Verified:** 2026-04-09T14:00:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Temperature sensors (outside, flow, return, hot water, source in/out) appear with correct °C values | VERIFIED | `CORE_SENSOR_DESCRIPTIONS` has 6 entries at lux_index 10, 11, 15, 17, 19, 20; all use `SensorDeviceClass.TEMPERATURE`, `native_unit_of_measurement="°C"`, `SensorStateClass.MEASUREMENT`, `suggested_display_precision=1`; value_fn calls `_lux_calcs.calculations[idx].from_heatpump` (divides by 10); test `test_temperature_value_conversion` confirms raw 200 → 20.0 |
| 2 | Operating mode sensor shows human-readable title-cased string (Heating, Hot Water, Defrost) | VERIFIED | lux_index=80; value_fn applies `.title()` to library output; test `test_operating_mode_conversion` confirms: raw 0 → "Heating", raw 1 → "Hot Water", raw 4 → "Defrost" |
| 3 | Compressor and circulation pump sensors show Running/Stopped strings | VERIFIED | lux_index=44 (compressor), lux_index=39 (pump); value_fn lambda: `"Running" if from_heatpump(raw) else "Stopped"`; tests `test_bool_sensor_raw_conversion` and `test_bool_sensor_conversion` confirm correct string output |
| 4 | Power sensor is created only when calculation index 257 exists in coordinator data | VERIFIED | `async_setup_entry` at line 456 explicitly checks `257 not in coordinator.data.get("calculations", {})` and skips; lux_index=257 confirmed as `data_type="Power"` in INPUT_REGISTERS; test `test_power_sensor_metadata` and `test_power_value_conversion` pass |
| 5 | 1,367+ disabled-by-default sensors (241 extra calcs + 1,126 params) expose full register database | VERIFIED | `ALL_EXTRA_CALC_DESCRIPTIONS` built from `INPUT_REGISTERS` minus 10 core indices = 241 entries; `ALL_PARAM_DESCRIPTIONS` built from all `HOLDING_REGISTERS` = 1,126 entries; all have `entity_registry_enabled_default=False` and `EntityCategory.DIAGNOSTIC`; 27 unit tests pass in 0.30s |

**Score:** 5/5 truths verified (all roadmap success criteria supported)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `custom_components/luxtronik2_modbus_proxy/sensor.py` | All sensor entity logic | VERIFIED | 484 lines; exports `async_setup_entry`, `LuxtronikSensorEntity`, `LuxtronikSensorEntityDescription`, `CORE_SENSOR_DESCRIPTIONS`, `ALL_EXTRA_CALC_DESCRIPTIONS`, `ALL_PARAM_DESCRIPTIONS` |
| `custom_components/luxtronik2_modbus_proxy/__init__.py` | Platform registration with "sensor" | VERIFIED | Line 29: `PLATFORMS: list[str] = ["sensor"]`; line 67: `async_forward_entry_setups(entry, PLATFORMS)` |
| `custom_components/luxtronik2_modbus_proxy/manifest.json` | Requirements include proxy package | VERIFIED | `"requirements": ["luxtronik==0.3.14", "luxtronik2-modbus-proxy==1.1.0"]` |
| `tests/unit/test_sensor.py` | 80+ lines, 14+ tests | VERIFIED | 432 lines; 27 tests; all pass in 0.30s |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `sensor.py async_setup_entry` | `hass.data[DOMAIN][entry.entry_id]` | coordinator retrieval | WIRED | Line 445: `coordinator: LuxtronikCoordinator = hass.data[DOMAIN][entry.entry_id]` |
| `sensor.py LuxtronikSensorEntity.native_value` | `coordinator.data` | reads raw int, calls `value_fn` | WIRED | Lines 415–421: `data_dict = self.coordinator.data.get(desc.data_source, {})` → `raw_val = data_dict.get(desc.lux_index)` → `desc.value_fn(raw_val)` |
| `__init__.py PLATFORMS` | `sensor.py async_setup_entry` | HA platform forwarding | WIRED | `PLATFORMS = ["sensor"]` forwarded via `async_forward_entry_setups`; HA routes to `sensor.py async_setup_entry` by convention |
| `sensor.py bulk entity generation` | `luxtronik2_modbus_proxy.register_definitions` | import from proxy package in manifest | WIRED | Lines 43–44: `from luxtronik2_modbus_proxy.register_definitions.calculations import INPUT_REGISTERS` and `from luxtronik2_modbus_proxy.register_definitions.parameters import HOLDING_REGISTERS`; manifest.json declares `luxtronik2-modbus-proxy==1.1.0` |
| `tests/unit/test_sensor.py` | `sensor.py` behaviors | tests luxtronik library objects directly | WIRED | Imports `INPUT_REGISTERS`, `HOLDING_REGISTERS`, `_lc.Calculations()`, `_lp.Parameters()` — the same objects sensor.py wraps |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `sensor.py LuxtronikSensorEntity` | `coordinator.data["calculations"][lux_index]` | `coordinator.py _sync_read()` reads all Luxtronik calculations via `lux.calculations.calculations` loop (lines 154–159) | Yes — loops all calc indices, stores `int(raw)` from `to_heatpump()` | FLOWING |
| `sensor.py LuxtronikSensorEntity` | `coordinator.data["parameters"][lux_index]` | `coordinator.py _sync_read()` reads all Luxtronik parameters via `lux.parameters.parameters` loop (lines 147–151) | Yes — loops all param indices, stores `int(raw)` from `to_heatpump()` | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Register databases have expected counts | `python3 -c "from luxtronik2_modbus_proxy.register_definitions.calculations import INPUT_REGISTERS; print(len(INPUT_REGISTERS))"` | 251 | PASS |
| Parameter database has expected count | `python3 -c "from luxtronik2_modbus_proxy.register_definitions.parameters import HOLDING_REGISTERS; print(len(HOLDING_REGISTERS))"` | 1126 | PASS |
| All 27 unit tests pass | `python3 -m pytest tests/unit/test_sensor.py -v` | 27 passed in 0.30s | PASS |
| sensor.py imports without error (HA runtime not available) | N/A — requires HA package | Skipped — HA runtime not present in test environment | SKIP |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| SETUP-01 | 06-01-PLAN.md (via ROADMAP) | User can install via HACS (custom repository) | SATISFIED | `hacs.json` exists with valid schema; `manifest.json` has `"config_flow": true`, `"integration_type": "hub"`, `"iot_class": "local_polling"`; brand icon at `custom_components/luxtronik2_modbus_proxy/brand/icon.png`; `validate.yml` GitHub Action present. HACS-installability infrastructure from Phase 4 confirmed present. Actual install requires human test. |
| SENS-01 | 06-01-PLAN.md | Core temperature sensors (outside, flow, return, hot water, source in/out) | SATISFIED | 6 `LuxtronikSensorEntityDescription` entries at lux_index 10, 11, 15, 17, 19, 20 with `SensorDeviceClass.TEMPERATURE`, `°C`, `MEASUREMENT`; value_fn verified correct |
| SENS-02 | 06-01-PLAN.md | Operating mode and compressor/pump status sensors | SATISFIED | lux_index 80 (operating mode, title-cased), 44 (compressor), 39 (pump); bool → "Running"/"Stopped" confirmed |
| SENS-03 | 06-01-PLAN.md | Power sensor if calculation available | SATISFIED | lux_index 257 with conditional guard in `async_setup_entry`; `data_type="Power"` confirmed in INPUT_REGISTERS |
| SENS-04 | 06-01-PLAN.md | Full parameter database exposed via entity registry | SATISFIED | 241 extra calc descriptions + 1,126 param descriptions; all `entity_registry_enabled_default=False`, `EntityCategory.DIAGNOSTIC` |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `tests/unit/test_sensor.py` | 378–403 | `test_all_descriptions_have_valid_data_source` tests only that the strings "calculations" and "parameters" are in a local set — it does not verify actual sensor.py description objects use correct data_source values | Info | Weak test coverage; actual sensor.py descriptions are verified by code inspection but not by this test function. No blocker — sensor.py code is structurally correct. |

No stub patterns, placeholder comments, empty returns, or hardcoded empty data found in `sensor.py`, `__init__.py`, or `manifest.json`.

### Human Verification Required

#### 1. End-to-End HA Integration Test

**Test:** Install the integration via HACS as a custom repository, navigate to Settings > Integrations, add "Luxtronik 2 Modbus Proxy" by entering the heat pump IP address, wait for the coordinator's first poll cycle to complete, then open the entity registry.

**Expected:**
- Six temperature sensor entities appear enabled with °C values (outside, flow, return, hot water, source inlet, source outlet)
- Operating mode entity shows a title-cased string ("Heating", "Hot Water", "Defrost", "Cooling", or "No Request")
- Compressor entity shows "Running" or "Stopped"
- Circulation pump entity shows "Running" or "Stopped"
- Power entity appears if the controller provides calculation index 257 (Heat_Output)
- Approximately 1,367 additional sensor entities appear in the entity registry as disabled — user can enable any of them from the UI with no code changes

**Why human:** Requires a running HA instance (2024.1.0+) with the HACS plugin, a real Luxtronik 2.0 controller at the IP entered (or a network-level emulator), and the proxy package at `luxtronik2-modbus-proxy==1.1.0` installed from PyPI. Cannot simulate HA's platform loading, entity registry writes, or coordinator polling in a static analysis check.

### Gaps Summary

No gaps found. All five roadmap success criteria are met by the implementation. The human_needed status reflects that the phase goal ("users immediately see heat pump values") is an end-user experience assertion that requires a running HA instance to confirm — not a deficiency in the code.

---

_Verified: 2026-04-09T14:00:00Z_
_Verifier: Claude (gsd-verifier)_

# Phase 6: Sensor Entities - Context

**Gathered:** 2026-04-09 (auto mode)
**Status:** Ready for planning

<domain>
## Phase Boundary

After entering the IP, users immediately see heat pump values as HA sensor entities — no further configuration required. This phase creates sensor.py with core temperature, mode, and status sensors, plus a mechanism for users to enable additional sensors from the full parameter database via the entity registry. It does NOT create control entities (selects, numbers) — those are Phase 7.

</domain>

<decisions>
## Implementation Decisions

### Core Sensor Set (created by default, enabled)
- **D-01:** Temperature sensors (SENS-01): outside_temperature, flow_temperature, return_temperature, hot_water_temperature, source_in_temperature, source_out_temperature — all from Luxtronik calculations, displayed in °C with one decimal
- **D-02:** Operating mode sensor (SENS-02): operating_mode from calculations — displays as human-readable string (e.g., "Heating", "Hot Water", "Defrost", "Swimming Pool")
- **D-03:** Compressor/pump status sensors (SENS-02): compressor_running and circulation_pump_running from calculations — binary state as "Running"/"Stopped"
- **D-04:** Power consumption sensor (SENS-03): heat_pump_power from calculations — displayed in W or kW, only created if the calculation index exists (not all controllers provide this)

### Entity Naming & IDs
- **D-05:** Entity ID pattern: `sensor.luxtronik2_modbus_proxy_{snake_case_name}` — follows HA convention using DOMAIN as prefix
- **D-06:** Friendly name pattern: "Luxtronik {Descriptive Name}" (e.g., "Luxtronik Outside Temperature")
- **D-07:** Unique ID pattern: `{config_entry_id}_{calculation_or_parameter_index}` — stable across restarts

### Additional Sensor Discovery (SENS-04)
- **D-08:** All 251 calculations and all 1,126 parameters registered as sensor entities but disabled by default (`entity_registry_enabled_default=False`)
- **D-09:** Core sensors (D-01 through D-04) are enabled by default (`entity_registry_enabled_default=True`)
- **D-10:** User enables additional sensors via HA entity registry UI (Settings > Devices & Services > Entities) — no code changes needed
- **D-11:** Each additional sensor's friendly name derived from the luxtronik library's parameter/calculation name (e.g., `ID_WEB_Temperatur_TVL` → "TVL Temperature")

### Data Consumption from Coordinator
- **D-12:** Sensors read from `coordinator.data["parameters"]` and `coordinator.data["calculations"]` (dict[int, int] of raw values, as defined in Phase 5 D-05)
- **D-13:** Raw integer values converted to display values using the luxtronik library's `from_heatpump()` method for temperature scaling (raw 200 → 20.0°C) and enum-to-string mapping

### Device Info
- **D-14:** Single device per config entry in HA device registry: manufacturer=MANUFACTURER, model=MODEL (from const.py), name="Luxtronik 2.0", sw_version from luxtronik library if available
- **D-15:** All sensor entities belong to this device entry

### HA Sensor Configuration
- **D-16:** Temperature sensors: `SensorDeviceClass.TEMPERATURE`, `native_unit_of_measurement="°C"`, `SensorStateClass.MEASUREMENT`
- **D-17:** Power sensor: `SensorDeviceClass.POWER`, native unit W or kW, `SensorStateClass.MEASUREMENT`
- **D-18:** Mode/status sensors: no device class (string state), `SensorStateClass` not set (diagnostic)

### Platform Registration
- **D-19:** Add `"sensor"` to `PLATFORMS` list in `__init__.py` (currently empty per Phase 5 D-14)
- **D-20:** `async_setup_entry` in sensor.py receives coordinator from `hass.data[DOMAIN][entry.entry_id]`

### Claude's Discretion
- Exact luxtronik calculation/parameter indices for each core sensor (map by name at research time)
- Icon selection for each sensor type (mdi icons)
- Whether to add `suggested_display_precision` for temperature sensors
- Entity category (diagnostic vs None) for non-core sensors
- Whether to batch-create all 1,377 entities at startup or lazy-create on enable

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project architecture
- `.planning/PROJECT.md` — Core value, constraints, connection model
- `.planning/STATE.md` — v1.1 architecture decisions, build order
- `.planning/REQUIREMENTS.md` — SETUP-01, SENS-01, SENS-02, SENS-03, SENS-04 acceptance criteria

### Phase 5 outputs (coordinator)
- `custom_components/luxtronik2_modbus_proxy/coordinator.py` — LuxtronikCoordinator, coordinator.data structure
- `custom_components/luxtronik2_modbus_proxy/__init__.py` — async_setup_entry, PLATFORMS list, hass.data storage
- `custom_components/luxtronik2_modbus_proxy/const.py` — DOMAIN, MANUFACTURER, MODEL constants
- `.planning/phases/05-coordinator-config-flow/05-CONTEXT.md` — Phase 5 locked decisions (esp. D-05 data structure)

### Proxy register definitions (reference for parameter/calculation names)
- `src/luxtronik2_modbus_proxy/register_definitions/parameters.py` — Full 1,126 parameter database with names and types
- `src/luxtronik2_modbus_proxy/register_definitions/calculations.py` — Full 251 calculation database with names and types

### External references (not in repo)
- HA developer docs: SensorEntity, SensorDeviceClass, SensorStateClass, entity_registry_enabled_default
- `luxtronik` library v0.3.14: Calculations, Parameters, from_heatpump/to_heatpump conversion API

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `coordinator.py` — LuxtronikCoordinator already provides `coordinator.data["parameters"]` and `coordinator.data["calculations"]` with raw int values
- `const.py` — DOMAIN, MANUFACTURER, MODEL ready for device_info
- `register_definitions/parameters.py` — Full parameter database with names, types, writability flags; NAME_TO_INDEX reverse lookup
- `register_definitions/calculations.py` — Full calculation database with names and types
- `luxtronik_client.py` — Shows `from_heatpump()`/`to_heatpump()` conversion pattern for raw ↔ display values

### Established Patterns
- Coordinator data is raw integers — entity platforms handle display conversion
- `__init__.py` PLATFORMS list controls which platforms are loaded
- Phase 5 established: coordinator in `hass.data[DOMAIN][entry.entry_id]`

### Integration Points
- `__init__.py` PLATFORMS list: add "sensor"
- `sensor.py` `async_setup_entry`: receives `hass` and `entry`, gets coordinator from `hass.data`
- Entity registry: `entity_registry_enabled_default` controls default visibility

</code_context>

<specifics>
## Specific Ideas

No specific requirements — follow standard HA sensor entity patterns. Core sensors should match what evcc and typical HA energy dashboards expect.

</specifics>

<deferred>
## Deferred Ideas

- Select entities for HeatingMode/HotWaterMode — Phase 7
- Number entities for temperature setpoints — Phase 7
- SG-Ready select entity — Phase 7
- Write rate limiting — Phase 7
- Translations (DE) — Phase 7

None — analysis stayed within phase scope.

</deferred>

---

*Phase: 06-sensor-entities*
*Context gathered: 2026-04-09*

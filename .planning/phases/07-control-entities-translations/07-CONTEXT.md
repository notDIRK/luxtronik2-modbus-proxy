# Phase 7: Control Entities & Translations - Context

**Gathered:** 2026-04-09 (assumptions mode, auto)
**Status:** Ready for planning

<domain>
## Phase Boundary

Users can control heating mode, hot water mode, SG-ready state, and temperature setpoints from HA, with write protection guarding the controller NAND flash — and all UI text is available in EN and DE. This phase creates `select.py` (CTRL-01, CTRL-02), `number.py` (CTRL-03), extends the coordinator with write capability and rate limiting (CTRL-04), and adds full EN+DE translations (HACS-02).

</domain>

<decisions>
## Implementation Decisions

### Write Method in Coordinator
- **D-01:** Add `async_write_parameter(index, value)` to `LuxtronikCoordinator` that acquires `self._lock`, runs blocking luxtronik write via `async_add_executor_job`, and triggers a coordinator refresh so entities reflect the new value immediately
- **D-02:** Write pattern replicates `LuxtronikClient` approach: `__new__` + `parameters.queue(index, value)` + `lux.write()` (connect-per-call, no persistent socket)

### Write Rate Limiting (CTRL-04)
- **D-03:** Rate limiting lives in the coordinator's write method (not per-entity) — all platforms benefit from a single enforcement point
- **D-04:** Per-parameter timestamp dict tracking last write time, same pattern as `PollingEngine._write_timestamps`
- **D-05:** Configurable window (default 60s from `const.py`), writes within the window are silently deferred (not rejected with error), matching ROADMAP success criterion #4

### Select Entities — HeatingMode & HotWaterMode (CTRL-01)
- **D-06:** `select.py` with `LuxtronikSelectEntity` extending `CoordinatorEntity` and `SelectEntity`
- **D-07:** HeatingMode maps to parameter 3 (`ID_Ba_Hz`) — options from luxtronik library enum (Automatic, Second heatsource, Party, Holidays, Off)
- **D-08:** HotWaterMode maps to parameter 4 (`ID_Ba_Bw`) — same option set as HeatingMode
- **D-09:** `async_select_option()` calls `coordinator.async_write_parameter()` with the enum's `to_heatpump()` value

### Select Entity — SG-Ready (CTRL-02)
- **D-10:** SG-Ready as a select entity in `select.py` with options: "Off (Mode 0)", "Blocking (Mode 1)", "Standard (Mode 2)", "Boost (Mode 3)"
- **D-11:** SG-Ready writes TWO parameters simultaneously (3 and 4) using the mode map from `sg_ready.py` lines 61-66 — special handling in `async_select_option()`
- **D-12:** Coordinator needs a method to write multiple parameters atomically within a single lock acquisition

### Number Entities — Temperature Setpoints (CTRL-03)
- **D-13:** `number.py` with `LuxtronikNumberEntity` extending `CoordinatorEntity` and `NumberEntity`
- **D-14:** Hot water setpoint: parameter 105 (`ID_Soll_BWS_akt`), range 30.0-65.0°C, step 0.5
- **D-15:** Flow/heating setpoint: parameter 1 (`ID_Einst_WK_akt`), heating curve offset — exact range needs research confirmation
- **D-16:** `native_min_value`/`native_max_value` in display units (°C), `set_native_value()` converts via `to_heatpump()` (multiply by 10 for raw integer)

### Entity Platform Structure
- **D-17:** Two new files: `select.py` and `number.py`
- **D-18:** Add `"select"` and `"number"` to PLATFORMS list in `__init__.py`
- **D-19:** Follow sensor.py pattern: custom entity description dataclass, CoordinatorEntity subclass, `async_setup_entry` wiring from `hass.data[DOMAIN]`

### Translations (HACS-02)
- **D-20:** Extend existing `strings.json` with `entity.select.<key>.state` entries for select option labels and `entity.number.<key>.name` entries
- **D-21:** Create `translations/de.json` with full German translations for config flow labels, entity names, and select option labels
- **D-22:** Update existing `translations/en.json` to match extended `strings.json`
- **D-23:** Translation keys for HeatingMode options: "automatic", "second_heatsource", "party", "holidays", "off" (matching luxtronik library enum names)

### Claude's Discretion
- Exact SG-Ready option label wording (as long as modes 0-3 are clear)
- Icon selection for select and number entities (mdi icons)
- Whether to add `entity_category = EntityCategory.CONFIG` for setpoint entities
- Internal logging verbosity for write operations
- Whether deferred writes should queue or simply drop

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase 5-6 outputs (coordinator + sensor pattern)
- `custom_components/luxtronik2_modbus_proxy/coordinator.py` — LuxtronikCoordinator with `_lock`, `_async_update_data()`, connect-per-call pattern; write method to be added here
- `custom_components/luxtronik2_modbus_proxy/sensor.py` — Entity description pattern, CoordinatorEntity subclass, `async_setup_entry` wiring to replicate for select.py and number.py
- `custom_components/luxtronik2_modbus_proxy/__init__.py` — PLATFORMS list, `hass.data[DOMAIN]` storage
- `custom_components/luxtronik2_modbus_proxy/const.py` — DOMAIN, constants; needs WRITE_RATE_LIMIT_SECONDS
- `custom_components/luxtronik2_modbus_proxy/strings.json` — Current config flow EN strings, to be extended with entity strings
- `custom_components/luxtronik2_modbus_proxy/translations/en.json` — Current EN translations, to be updated

### Proxy write patterns (reference implementation)
- `src/luxtronik2_modbus_proxy/luxtronik_client.py` — `async_write()` method: `__new__` + `parameters.queue()` + `lux.write()` pattern
- `src/luxtronik2_modbus_proxy/polling_engine.py` — `_write_timestamps` dict, `_check_write_rate_limit()`, `_process_write_queue()` pattern
- `src/luxtronik2_modbus_proxy/sg_ready.py` — SG-Ready mode map: mode 0-3 → parameter 3+4 value combinations
- `src/luxtronik2_modbus_proxy/write_validator.py` — Write validation, range checking, writability enforcement

### Register definitions
- `src/luxtronik2_modbus_proxy/register_definitions/parameters.py` — Parameter 1 (ID_Einst_WK_akt), 3 (ID_Ba_Hz), 4 (ID_Ba_Bw), 105 (ID_Soll_BWS_akt) with types and ranges

### Requirements
- `.planning/REQUIREMENTS.md` — CTRL-01, CTRL-02, CTRL-03, CTRL-04, HACS-02 acceptance criteria
- `.planning/phases/05-coordinator-config-flow/05-CONTEXT.md` — Phase 5 locked decisions (esp. D-03 lock, D-05 data structure)
- `.planning/phases/06-sensor-entities/06-CONTEXT.md` — Phase 6 locked decisions (entity pattern, naming conventions)

### External references (not in repo)
- HA developer docs: SelectEntity, NumberEntity, entity translations (strings.json entity section format)
- `luxtronik` library v0.3.14: Parameters.queue(), Luxtronik.write(), enum types for heating/hot water modes

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `coordinator.py` `self._lock` (asyncio.Lock): Already exists for read serialization; write method acquires the same lock
- `sensor.py` entity pattern: `LuxtronikSensorEntityDescription` dataclass + `LuxtronikSensorEntity(CoordinatorEntity)` — select.py and number.py replicate this pattern
- `sg_ready.py` `SG_READY_MODES`: Complete mode-to-parameter mapping (mode 0→{3:4,4:4}, mode 1→{3:0,4:0}, etc.)
- `polling_engine.py` `_write_timestamps`: Exact rate limiting pattern to port to coordinator
- `write_validator.py` `WritableParam` definitions: Range constraints for all writable parameters

### Established Patterns
- Connect-per-call: New `luxtronik.Luxtronik` instance per write, no socket reuse
- Raw integer storage: `coordinator.data` stores raw ints, entities handle display conversion
- Entity description dataclass: Custom dataclass per platform with `luxtronik_index`, `value_fn`, etc.
- Platform registration: PLATFORMS list in `__init__.py`, `async_setup_entry` per platform

### Integration Points
- `__init__.py` PLATFORMS: add "select", "number"
- `coordinator.py`: add `async_write_parameter()` and `_write_timestamps` dict
- `const.py`: add `WRITE_RATE_LIMIT_SECONDS = 60`
- `strings.json` + `translations/`: extend with entity strings
- `manifest.json`: no changes needed (config_flow already true)

</code_context>

<specifics>
## Specific Ideas

- SG-Ready select entity should clearly label what each mode does (e.g., "Boost (Mode 3)" not just "3") since users may not know the SG-Ready standard
- HeatingMode/HotWaterMode options should match the German-language labels that heat pump owners are familiar with (via DE translations)
- Rate limiting should log when a write is deferred so users can see it in HA logs

</specifics>

<deferred>
## Deferred Ideas

- Options Flow for reconfiguring poll interval, rate limit window, enabled entities — v2 (CONF-10)
- Climate entity for heating/cooling control — v2 (ENT-10), complex UX for heat pumps
- Binary sensor entities for error states and alarms — v2 (ENT-11)
- HACS default store submission — after community validation (INTEG-10)

None — analysis stayed within phase scope.

</deferred>

---

*Phase: 07-control-entities-translations*
*Context gathered: 2026-04-09*

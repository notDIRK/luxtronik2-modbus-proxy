# Phase 7: Control Entities & Translations - Research

**Researched:** 2026-04-09
**Domain:** Home Assistant SelectEntity, NumberEntity, coordinator write methods, entity translations
**Confidence:** HIGH

## Summary

Phase 7 adds write capability to the HA integration: select entities for HeatingMode, HotWaterMode, and SG-Ready (CTRL-01, CTRL-02), number entities for temperature setpoints (CTRL-03), rate-limited writes in the coordinator (CTRL-04), and bilingual EN+DE translations (HACS-02). All patterns are well-established in the existing codebase -- the sensor.py entity pattern from Phase 6 provides a direct template for select.py and number.py, and the proxy-side `luxtronik_client.py` + `polling_engine.py` provide verified write and rate-limiting patterns to port into the coordinator.

The critical architectural finding is that `has_entity_name = True` and `translation_key` are **required** for entity name translations to work in HA. The current sensor.py does NOT use this pattern -- it uses hardcoded `name` strings. Phase 7 entities MUST use `has_entity_name = True` + `translation_key` from the start so translations work. Retrofitting sensor.py is out of scope for Phase 7 (it would change existing entity IDs).

**Primary recommendation:** Follow the established sensor.py CoordinatorEntity pattern for select.py and number.py, port the write + rate-limiting from polling_engine.py into coordinator.py, and use `has_entity_name = True` + `translation_key` for all new entities.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Add `async_write_parameter(index, value)` to `LuxtronikCoordinator` that acquires `self._lock`, runs blocking luxtronik write via `async_add_executor_job`, and triggers a coordinator refresh so entities reflect the new value immediately
- **D-02:** Write pattern replicates `LuxtronikClient` approach: `__new__` + `parameters.queue(index, value)` + `lux.write()` (connect-per-call, no persistent socket)
- **D-03:** Rate limiting lives in the coordinator's write method (not per-entity) -- all platforms benefit from a single enforcement point
- **D-04:** Per-parameter timestamp dict tracking last write time, same pattern as `PollingEngine._write_timestamps`
- **D-05:** Configurable window (default 60s from `const.py`), writes within the window are silently deferred (not rejected with error)
- **D-06:** `select.py` with `LuxtronikSelectEntity` extending `CoordinatorEntity` and `SelectEntity`
- **D-07:** HeatingMode maps to parameter 3 (`ID_Ba_Hz`) -- options from luxtronik library enum (Automatic, Second heatsource, Party, Holidays, Off)
- **D-08:** HotWaterMode maps to parameter 4 (`ID_Ba_Bw`) -- same option set as HeatingMode
- **D-09:** `async_select_option()` calls `coordinator.async_write_parameter()` with the enum's `to_heatpump()` value
- **D-10:** SG-Ready as a select entity in `select.py` with options: "Off (Mode 0)", "Blocking (Mode 1)", "Standard (Mode 2)", "Boost (Mode 3)"
- **D-11:** SG-Ready writes TWO parameters simultaneously (3 and 4) using the mode map from `sg_ready.py` lines 61-66
- **D-12:** Coordinator needs a method to write multiple parameters atomically within a single lock acquisition
- **D-13:** `number.py` with `LuxtronikNumberEntity` extending `CoordinatorEntity` and `NumberEntity`
- **D-14:** Hot water setpoint: parameter 105 (`ID_Soll_BWS_akt`), range 30.0-65.0 C, step 0.5
- **D-15:** Flow/heating setpoint: parameter 1 (`ID_Einst_WK_akt`), heating curve offset -- exact range needs research confirmation
- **D-16:** `native_min_value`/`native_max_value` in display units (C), `set_native_value()` converts via `to_heatpump()` (multiply by 10 for raw integer)
- **D-17:** Two new files: `select.py` and `number.py`
- **D-18:** Add `"select"` and `"number"` to PLATFORMS list in `__init__.py`
- **D-19:** Follow sensor.py pattern: custom entity description dataclass, CoordinatorEntity subclass, `async_setup_entry` wiring from `hass.data[DOMAIN]`
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

### Deferred Ideas (OUT OF SCOPE)
- Options Flow for reconfiguring poll interval, rate limit window, enabled entities -- v2 (CONF-10)
- Climate entity for heating/cooling control -- v2 (ENT-10), complex UX for heat pumps
- Binary sensor entities for error states and alarms -- v2 (ENT-11)
- HACS default store submission -- after community validation (INTEG-10)

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CTRL-01 | Select entities for HeatingMode and HotWaterMode | D-06 through D-09; HeatingMode/HotWaterMode enum verified in luxtronik library with codes {0-4}; SelectEntity API researched |
| CTRL-02 | SG-Ready select entity (modes 0-3) translating to correct parameter combinations | D-10 through D-12; SG_READY_MODE_MAP verified in sg_ready.py; dual-parameter atomic write pattern documented |
| CTRL-03 | Number entities for temperature setpoints (flow, hot water) | D-13 through D-16; Param 105 range verified (raw 300-650 = 30.0-65.0 C); Param 1 is Celsius type, writable; NumberEntity API researched |
| CTRL-04 | Write operations are rate-limited to protect controller NAND flash | D-03 through D-05; polling_engine._write_timestamps pattern verified; per-parameter timestamp dict with configurable window |
| HACS-02 | Integration has translations for EN and DE | D-20 through D-23; strings.json entity translation format researched; has_entity_name + translation_key requirement discovered |

</phase_requirements>

## Standard Stack

No new dependencies required. Phase 7 uses only existing project dependencies and HA core APIs.

### HA Core APIs Used

| API | Import Path | Purpose |
|-----|-------------|---------|
| `SelectEntity` | `homeassistant.components.select` | Base class for HeatingMode, HotWaterMode, SG-Ready select entities |
| `NumberEntity` | `homeassistant.components.number` | Base class for temperature setpoint entities |
| `NumberMode` | `homeassistant.components.number` | `NumberMode.BOX` for temperature input (slider not suitable for 0.5 step precision) |
| `CoordinatorEntity` | `homeassistant.helpers.update_coordinator` | Base class providing coordinator data binding (already used in sensor.py) |
| `EntityCategory` | `homeassistant.const` | `EntityCategory.CONFIG` for setpoint entities (Claude's discretion -- recommended) |

[VERIFIED: codebase sensor.py imports]

### Luxtronik Library Types Used

| Type | Module | Purpose | Verified |
|------|--------|---------|----------|
| `HeatingMode` | `luxtronik.datatypes` | Enum with codes `{0: 'Automatic', 1: 'Second heatsource', 2: 'Party', 3: 'Holidays', 4: 'Off'}` | [VERIFIED: Python introspection of luxtronik library] |
| `HotWaterMode` | `luxtronik.datatypes` | Same codes as HeatingMode: `{0: 'Automatic', 1: 'Second heatsource', 2: 'Party', 3: 'Holidays', 4: 'Off'}` | [VERIFIED: Python introspection of luxtronik library] |
| `Celsius` (param 105) | `luxtronik.datatypes` | `from_heatpump(500) = 50.0`, `to_heatpump(50.0) = 500` (raw = display * 10) | [VERIFIED: Python introspection] |
| `Celsius` (param 1) | `luxtronik.datatypes` | Same Celsius type; writable; heating curve offset | [VERIFIED: Python introspection] |
| `Parameters.queue` | `luxtronik` | Dict assigned before `lux.write()` to queue parameter writes | [VERIFIED: codebase luxtronik_client.py line 143] |

## Architecture Patterns

### Project Structure (files to create/modify)

```
custom_components/luxtronik2_modbus_proxy/
  __init__.py            # MODIFY: add "select", "number" to PLATFORMS
  const.py               # MODIFY: add WRITE_RATE_LIMIT_SECONDS = 60
  coordinator.py         # MODIFY: add async_write_parameter(), async_write_parameters(), _write_timestamps
  select.py              # CREATE: HeatingMode, HotWaterMode, SG-Ready select entities
  number.py              # CREATE: temperature setpoint number entities
  strings.json           # MODIFY: add entity.select and entity.number translation keys
  translations/
    en.json              # MODIFY: add entity translations (match strings.json)
    de.json              # CREATE: full German translations
```

### Pattern 1: Coordinator Write Method

**What:** Add `async_write_parameter(index, value)` and `async_write_parameters(params: dict[int, int])` to `LuxtronikCoordinator`.
**When to use:** All entity write operations route through coordinator.
**Example:**

```python
# Source: ported from luxtronik_client.py async_write() + polling_engine._drain_and_write()
async def async_write_parameter(self, index: int, value: int) -> None:
    """Write a single parameter to the Luxtronik controller with rate limiting.

    Acquires the serialization lock, checks rate limit, creates a fresh
    Luxtronik instance, queues the write, executes it, and triggers a
    coordinator refresh so entities reflect the new value immediately.
    """
    await self.async_write_parameters({index: value})

async def async_write_parameters(self, params: dict[int, int]) -> None:
    """Write multiple parameters atomically within a single lock acquisition.

    Used by SG-Ready which writes parameters 3 and 4 simultaneously.
    Rate limiting is checked per-parameter; any rate-limited parameter is
    silently skipped (deferred, not rejected).
    """
    async with self._lock:
        now = time.time()
        writes_to_send: dict[int, int] = {}
        for index, value in params.items():
            last_write = self._write_timestamps.get(index, 0.0)
            if now - last_write < WRITE_RATE_LIMIT_SECONDS:
                _LOGGER.warning(
                    "Write to parameter %d rate-limited (%.1fs remaining)",
                    index,
                    WRITE_RATE_LIMIT_SECONDS - (now - last_write),
                )
                continue
            writes_to_send[index] = value

        if not writes_to_send:
            return

        await self.hass.async_add_executor_job(
            self._sync_write, writes_to_send
        )
        # Update timestamps for accepted writes
        for index in writes_to_send:
            self._write_timestamps[index] = now

    # Trigger immediate refresh so entities reflect the new value
    await self.async_request_refresh()
```

[VERIFIED: pattern derived from codebase luxtronik_client.py + polling_engine.py]

### Pattern 2: Select Entity with Translation Keys

**What:** Select entity using `has_entity_name = True` + `translation_key` for localized names and option labels.
**When to use:** All Phase 7 select and number entities.
**Example:**

```python
# Source: HA developer docs + sensor.py pattern
@dataclass(frozen=True)
class LuxtronikSelectEntityDescription(SelectEntityDescription):
    """Extends HA SelectEntityDescription with Luxtronik-specific fields."""
    lux_index: int = 0
    value_map: dict[int, str] = field(default_factory=dict)  # raw int -> option string
    reverse_map: dict[str, int] = field(default_factory=dict)  # option string -> raw int

class LuxtronikSelectEntity(CoordinatorEntity[LuxtronikCoordinator], SelectEntity):
    """Select entity backed by the DataUpdateCoordinator."""

    _attr_has_entity_name = True  # REQUIRED for translation_key to work
    entity_description: LuxtronikSelectEntityDescription

    def __init__(self, coordinator, entry, description):
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_parameters_{description.lux_index}"
        self._attr_translation_key = description.key  # maps to strings.json

    @property
    def options(self) -> list[str]:
        return list(self.entity_description.value_map.values())

    @property
    def current_option(self) -> str | None:
        raw = self.coordinator.data.get("parameters", {}).get(
            self.entity_description.lux_index
        )
        if raw is None:
            return None
        return self.entity_description.value_map.get(raw)

    async def async_select_option(self, option: str) -> None:
        raw_value = self.entity_description.reverse_map[option]
        await self.coordinator.async_write_parameter(
            self.entity_description.lux_index, raw_value
        )
```

[CITED: developers.home-assistant.io/docs/core/entity/select/ and developers.home-assistant.io/docs/internationalization/core/]

### Pattern 3: SG-Ready Dual-Parameter Write

**What:** SG-Ready writes two parameters (3 and 4) atomically using `async_write_parameters()`.
**When to use:** SG-Ready select entity only.
**Example:**

```python
# Source: sg_ready.py SG_READY_MODE_MAP
SG_READY_MODE_MAP = {
    0: {3: 4, 4: 4},   # EVU lock: HeatingMode=Off, HotWaterMode=Off
    1: {3: 0, 4: 0},   # Normal: HeatingMode=Automatic, HotWaterMode=Automatic
    2: {3: 2, 4: 0},   # Recommended: HeatingMode=Party, HotWaterMode=Automatic
    3: {3: 0, 4: 2},   # Force on: HeatingMode=Automatic, HotWaterMode=Party
}

# In SG-Ready select entity's async_select_option:
async def async_select_option(self, option: str) -> None:
    mode = self._option_to_mode[option]  # e.g., "Boost (Mode 3)" -> 3
    param_writes = SG_READY_MODE_MAP[mode]
    await self.coordinator.async_write_parameters(param_writes)
```

[VERIFIED: codebase sg_ready.py lines 61-66]

### Pattern 4: Number Entity with Unit Conversion

**What:** Number entity using display units (C) with raw-int conversion for writes.
**When to use:** Temperature setpoint entities.
**Example:**

```python
class LuxtronikNumberEntity(CoordinatorEntity[LuxtronikCoordinator], NumberEntity):
    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = "°C"
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_mode = NumberMode.BOX  # precise step values need box, not slider

    @property
    def native_value(self) -> float | None:
        raw = self.coordinator.data.get("parameters", {}).get(self._lux_index)
        if raw is None:
            return None
        return raw / 10.0  # Celsius type: raw 500 -> 50.0

    async def async_set_native_value(self, value: float) -> None:
        raw = int(value * 10)  # 50.0 -> 500
        await self.coordinator.async_write_parameter(self._lux_index, raw)
```

[VERIFIED: from_heatpump/to_heatpump conversion confirmed by Python introspection]

### Pattern 5: Translation File Structure (strings.json)

**What:** Entity translations with `entity.select.<key>.state` for option labels.
**Example:**

```json
{
  "config": { ... existing config flow strings ... },
  "entity": {
    "select": {
      "heating_mode": {
        "name": "Heating Mode",
        "state": {
          "automatic": "Automatic",
          "second_heatsource": "Second Heatsource",
          "party": "Party",
          "holidays": "Holidays",
          "off": "Off"
        }
      },
      "hot_water_mode": {
        "name": "Hot Water Mode",
        "state": {
          "automatic": "Automatic",
          "second_heatsource": "Second Heatsource",
          "party": "Party",
          "holidays": "Holidays",
          "off": "Off"
        }
      },
      "sg_ready": {
        "name": "SG Ready",
        "state": {
          "off_mode_0": "Off (Mode 0)",
          "blocking_mode_1": "Blocking (Mode 1)",
          "standard_mode_2": "Standard (Mode 2)",
          "boost_mode_3": "Boost (Mode 3)"
        }
      }
    },
    "number": {
      "hot_water_setpoint": {
        "name": "Hot Water Setpoint"
      },
      "heating_curve_offset": {
        "name": "Heating Curve Offset"
      }
    }
  }
}
```

[CITED: developers.home-assistant.io/docs/internationalization/core/]

**CRITICAL:** When `has_entity_name = True` and `translation_key` is set, the `options` list in `SelectEntity.options` must use the **translation keys** (e.g., `"automatic"`, `"party"`), NOT the display strings. HA looks up the display string from `strings.json` `entity.select.<translation_key>.state.<option_key>`. The `current_option` property must also return the translation key, not the display label.

[CITED: developers.home-assistant.io/docs/internationalization/core/]

### Anti-Patterns to Avoid

- **Hardcoded English option labels in `options` property:** When using `translation_key`, options must be translation keys, not display strings. HA renders the localized label from strings.json.
- **Using `name` attribute with `translation_key`:** If `translation_key` is set, `name` in the EntityDescription is ignored. Do not set both.
- **Single-parameter SG-Ready writes:** SG-Ready MUST write parameters 3 and 4 atomically. Writing only one would leave the heat pump in an inconsistent state.
- **Persistent Luxtronik connection for writes:** Every write must create a new `Luxtronik.__new__()` instance, write, and discard. Never hold the socket open.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Rate limiting | Custom async queue/timer | Simple per-param timestamp dict + `time.time()` comparison | polling_engine.py proves this works; no need for async queues or debounce libraries |
| Select option mapping | Custom enum classes | Dict-based value_map/reverse_map on entity description | HeatingMode codes are just `{int: str}` -- a dict is simpler and matches the luxtronik library exactly |
| Celsius conversion | Custom conversion functions | Direct `* 10` / `/ 10` arithmetic | luxtronik Celsius type is always raw = display * 10; `from_heatpump`/`to_heatpump` confirmed |
| SG-Ready mode translation | New translation function | Import `SG_READY_MODE_MAP` from proxy's `sg_ready.py` | The map already exists and is tested in `test_sg_ready.py` |

## Common Pitfalls

### Pitfall 1: Translation Keys vs Display Strings in SelectEntity.options

**What goes wrong:** If you put display strings like `"Automatic"` in the `options` list and also set `translation_key`, HA will look for `entity.select.<key>.state.Automatic` (uppercase) in strings.json and fail silently -- showing raw keys or no translation.
**Why it happens:** The HA translation system uses the values from `options` as lookup keys into `entity.select.<translation_key>.state.<option_value>`.
**How to avoid:** Use lowercase snake_case keys in `options` (e.g., `"automatic"`, `"second_heatsource"`) that exactly match the keys in `strings.json`.
**Warning signs:** Entity states display as raw keys in the UI instead of localized labels.

### Pitfall 2: has_entity_name Must Be True for Translations

**What goes wrong:** Entity name translations are silently ignored if `has_entity_name` is not `True`.
**Why it happens:** HA only consults `translation_key` for entity name resolution when the entity participates in the "entity naming" system (`has_entity_name = True`).
**How to avoid:** Set `_attr_has_entity_name = True` on all entity classes that use `translation_key`. Also ensure `device_info` is returned so the device name is prepended.
**Warning signs:** Entity names show as `None` or the translation key string.

### Pitfall 3: Write Queue Population Before lux.write()

**What goes wrong:** Setting `parameters.queue` after `write()` starts causes writes to be silently lost.
**Why it happens:** The luxtronik library reads `parameters.queue` synchronously at the start of `write()`.
**How to avoid:** Always set `lux.parameters.queue = {index: value, ...}` BEFORE dispatching `lux.write()` to the executor.
**Warning signs:** No error, but the heat pump state doesn't change after a write command.

[VERIFIED: codebase luxtronik_client.py line 141-143 comment: "CRITICAL: Populate the write queue BEFORE dispatching write()"]

### Pitfall 4: SG-Ready Partial Writes

**What goes wrong:** If parameters 3 and 4 are written in separate lock acquisitions, another read could occur between them, showing an inconsistent state.
**Why it happens:** SG-Ready requires simultaneous update of HeatingMode (param 3) and HotWaterMode (param 4).
**How to avoid:** Use `async_write_parameters()` which writes all params within a single lock acquisition before triggering refresh.
**Warning signs:** Briefly incorrect mode displayed in HA after SG-Ready change.

### Pitfall 5: Rate Limiting Should Defer, Not Reject

**What goes wrong:** If rate-limited writes raise exceptions or set entity state to error, the HA UI shows errors on rapid user interactions (e.g., quickly toggling modes).
**Why it happens:** Users naturally click quickly; NAND flash protection should be invisible.
**How to avoid:** Per D-05, rate-limited writes are silently deferred (skipped with a log warning). The entity state updates on the next coordinator refresh.
**Warning signs:** Error toasts in HA UI on rapid mode changes.

### Pitfall 6: Unique ID Collision Between Select and Sensor Entities

**What goes wrong:** Parameters 3 and 4 already have sensor entities (disabled by default, from SENS-04). If select entities use the same unique_id pattern, HA will reject the duplicate.
**Why it happens:** sensor.py uses `{entry_id}_parameters_{index}` as unique_id for parameter sensors.
**How to avoid:** Use a platform-discriminated unique_id for select entities: `{entry_id}_select_{index}` or `{entry_id}_parameters_{index}_select`. Alternatively, since the SENS-04 parameter sensors for indices 1, 3, 4, 105 are disabled by default, the select/number entities can coexist with a different unique_id prefix.
**Warning signs:** "Platform already has entity with unique_id" error in HA logs.

## Code Examples

### Coordinator _sync_write Method

```python
# Source: ported from luxtronik_client.py async_write()
def _sync_write(self, param_writes: dict[int, int]) -> None:
    """Write parameters to the Luxtronik controller (runs in executor).

    Creates a fresh Luxtronik instance, populates the write queue,
    and calls write(). Connect-per-call pattern. (ARCH-01, D-02)
    """
    lux = luxtronik.Luxtronik.__new__(luxtronik.Luxtronik)
    lux._host = self._host
    lux._port = self._port
    lux._socket = None
    lux.calculations = luxtronik.Calculations()
    lux.parameters = luxtronik.Parameters()
    lux.visibilities = luxtronik.Visibilities()

    # CRITICAL: Populate queue BEFORE calling write() (Pitfall 3)
    lux.parameters.queue = dict(param_writes)
    lux.write()
```

[VERIFIED: exact pattern from codebase luxtronik_client.py lines 131-146]

### HeatingMode/HotWaterMode Value Maps

```python
# Source: luxtronik library introspection
# Translation keys (used in options list and strings.json)
HEATING_MODE_OPTIONS = {
    0: "automatic",
    1: "second_heatsource",
    2: "party",
    3: "holidays",
    4: "off",
}
HEATING_MODE_REVERSE = {v: k for k, v in HEATING_MODE_OPTIONS.items()}
# HotWaterMode uses identical codes
```

[VERIFIED: Python introspection of luxtronik.parameters HeatingMode.codes]

### German Translation File (translations/de.json)

```json
{
  "config": {
    "step": {
      "user": {
        "title": "Verbindung zur Luxtronik 2.0",
        "description": "Geben Sie die IP-Adresse des Warmepumpen-Reglers ein.",
        "data": {
          "host": "IP-Adresse"
        },
        "data_description": {
          "host": "Lokale IP-Adresse des Luxtronik 2.0 Reglers (z.B. 192.168.x.x)"
        }
      }
    },
    "error": {
      "cannot_connect": "Verbindung zur Warmepumpe nicht moglich. Prufen Sie die IP-Adresse und stellen Sie sicher, dass der Regler auf Port 8889 erreichbar ist."
    },
    "abort": {
      "already_configured": "Diese Warmepumpe ist bereits konfiguriert.",
      "already_configured_benPru": "Eine BenPru/luxtronik-Integration ist bereits mit dieser IP-Adresse verbunden. Der gleichzeitige Betrieb beider Integrationen verursacht Verbindungskonflikte. Entfernen Sie zuerst die luxtronik-Integration."
    }
  },
  "entity": {
    "select": {
      "heating_mode": {
        "name": "Heizmodus",
        "state": {
          "automatic": "Automatik",
          "second_heatsource": "Zweiter Warmeerzeuger",
          "party": "Party",
          "holidays": "Urlaub",
          "off": "Aus"
        }
      },
      "hot_water_mode": {
        "name": "Warmwassermodus",
        "state": {
          "automatic": "Automatik",
          "second_heatsource": "Zweiter Warmeerzeuger",
          "party": "Party",
          "holidays": "Urlaub",
          "off": "Aus"
        }
      },
      "sg_ready": {
        "name": "SG Ready",
        "state": {
          "off_mode_0": "Aus (Modus 0)",
          "blocking_mode_1": "Sperrung (Modus 1)",
          "standard_mode_2": "Normal (Modus 2)",
          "boost_mode_3": "Verstarkt (Modus 3)"
        }
      }
    },
    "number": {
      "hot_water_setpoint": {
        "name": "Warmwasser-Solltemperatur"
      },
      "heating_curve_offset": {
        "name": "Heizkurven-Verschiebung"
      }
    }
  }
}
```

[ASSUMED: German translations based on standard German heat pump terminology]

## Parameter 1 (ID_Einst_WK_akt) Range Research

Parameter 1 is the heating curve offset (`ID_Einst_WK_akt`). It is of type `Celsius` and is writable.

**Verified facts:**
- Type: `Celsius` (same type as param 105) [VERIFIED: Python introspection]
- Writable: `True` [VERIFIED: Python introspection]
- Conversion: `from_heatpump(50) = 5.0`, `to_heatpump(5.0) = 50` (raw = display * 10) [VERIFIED: Python introspection]
- The luxtronik library does not enforce min/max on Celsius types [VERIFIED: no min_value/max_value attributes on Celsius type]

**Range recommendation:** The heating curve offset is typically -5.0 to +5.0 C (raw -50 to 50) for most Luxtronik 2.0 controllers. Some controllers may allow wider ranges. The proxy's `parameters.py` does not have an overlay for param 1 range (unlike param 105 which has min_value=300, max_value=650).

**Recommendation:** Use a conservative range of -5.0 to +5.0 C with step 0.5. This matches typical Luxtronik 2.0 controller limits for heating curve offset. Document that the range may vary by controller variant. [ASSUMED: range based on typical Luxtronik 2.0 heating curve offset limits]

## Discretion Recommendations

| Area | Recommendation | Rationale |
|------|----------------|-----------|
| SG-Ready option labels | "Off (Mode 0)", "Blocking (Mode 1)", "Standard (Mode 2)", "Boost (Mode 3)" | Clear for users unfamiliar with SG-Ready; mode number aids troubleshooting |
| Icons | Select: `mdi:heat-pump` for modes, `mdi:solar-power` for SG-Ready. Number: `mdi:thermometer` for setpoints | Consistent with sensor.py icons |
| entity_category for setpoints | `EntityCategory.CONFIG` | Setpoints are configuration, not primary state; keeps dashboards clean |
| Logging for writes | `_LOGGER.info()` for accepted writes, `_LOGGER.warning()` for rate-limited writes | INFO for normal audit trail; WARNING for rate limits draws attention in logs |
| Deferred writes behavior | Silently drop (do not queue) | Queueing deferred writes adds complexity and may cause unexpected delayed writes; the next poll cycle will show the current actual state |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Parameter 1 heating curve offset range is -5.0 to +5.0 C | Parameter 1 Range Research | User cannot set offset outside this range; too narrow = frustrating, too wide = potential damage |
| A2 | German translations use standard heat pump terminology | Code Examples (de.json) | German-speaking users see unfamiliar terms; easily fixed post-release |
| A3 | SG-Ready mode labels (Off/Blocking/Standard/Boost) are clear to users | Discretion Recommendations | User confusion about mode meaning; mitigated by including mode numbers |

## Open Questions

1. **Parameter 1 (ID_Einst_WK_akt) exact range**
   - What we know: It's a Celsius type, writable, raw = display * 10. Typical range is -5 to +5 C.
   - What's unclear: The exact min/max enforced by the Alpha Innotec MSW 14 controller hardware.
   - Recommendation: Use -5.0 to +5.0 C as default. This can be adjusted after hardware validation. Document the assumption.

2. **Unique ID collision between select and sensor entities for params 3, 4**
   - What we know: sensor.py creates disabled-by-default sensor entities for all 1,126 parameters including indices 1, 3, 4, 105. Select/number entities for these same indices must have different unique_ids.
   - What's unclear: Whether HA handles the case where a disabled sensor and an enabled select share the same underlying parameter gracefully.
   - Recommendation: Use platform-discriminated unique_ids: `{entry_id}_select_{index}` for select entities, `{entry_id}_number_{index}` for number entities. This avoids any collision with the existing `{entry_id}_parameters_{index}` sensor pattern.

## Project Constraints (from CLAUDE.md)

- **Public repository**: No real IPs, hostnames, credentials in any file
- **Language**: US English for all code, comments, variable names, commit messages
- **Documentation**: US English + German (docs/en/ and docs/de/)
- **Comments**: Every function, every module, complex logic explained
- **Docstrings**: US English, Google style
- **Pre-commit hook**: Do not bypass with --no-verify
- **Tech stack**: Python 3.10+, luxtronik v0.3.14, pymodbus, Docker
- **GSD Workflow**: Use GSD commands for all file changes

## Sources

### Primary (HIGH confidence)
- Codebase: `coordinator.py` -- existing lock, read pattern, data structure
- Codebase: `sensor.py` -- entity description pattern, CoordinatorEntity subclass, async_setup_entry
- Codebase: `luxtronik_client.py` -- write pattern with `__new__` + `parameters.queue` + `write()`
- Codebase: `polling_engine.py` -- `_write_timestamps` rate limiting pattern
- Codebase: `sg_ready.py` -- `SG_READY_MODE_MAP` with mode-to-parameter mapping
- Codebase: `register_definitions/parameters.py` -- ParameterDef for params 1, 3, 4, 105
- Python introspection: luxtronik library HeatingMode.codes, HotWaterMode.codes, Celsius conversion

### Secondary (MEDIUM confidence)
- [HA Developer Docs: SelectEntity](https://developers.home-assistant.io/docs/core/entity/select/) -- SelectEntity API
- [HA Developer Docs: NumberEntity](https://developers.home-assistant.io/docs/core/entity/number/) -- NumberEntity API
- [HA Developer Docs: Backend localization](https://developers.home-assistant.io/docs/internationalization/core/) -- strings.json entity translation format, has_entity_name requirement

### Tertiary (LOW confidence)
- Parameter 1 range (-5.0 to +5.0 C) -- based on general Luxtronik 2.0 knowledge, not verified on hardware

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all HA APIs well-documented, luxtronik library verified by introspection
- Architecture: HIGH -- all patterns directly ported from verified codebase implementations
- Pitfalls: HIGH -- identified from both codebase analysis and HA documentation
- Translations: MEDIUM -- strings.json format verified from HA docs, German text is assumed
- Parameter 1 range: LOW -- needs hardware validation

**Research date:** 2026-04-09
**Valid until:** 2026-05-09 (stable domain, HA core APIs stable across minor releases)

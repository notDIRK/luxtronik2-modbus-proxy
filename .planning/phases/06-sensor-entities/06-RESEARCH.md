# Phase 6: Sensor Entities - Research

**Researched:** 2026-04-09
**Domain:** Home Assistant SensorEntity platform, luxtronik calculation/parameter indices, CoordinatorEntity pattern
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Core Sensor Set (D-01 through D-04)**
- D-01: Temperature sensors: outside_temperature, flow_temperature, return_temperature, hot_water_temperature, source_in_temperature, source_out_temperature — from calculations, °C, one decimal
- D-02: Operating mode sensor: operating_mode from calculations — human-readable string ("Heating", "Hot Water", "Defrost", "Swimming Pool")
- D-03: Status sensors: compressor_running and circulation_pump_running from calculations — "Running"/"Stopped"
- D-04: Power sensor: heat_pump_power from calculations — W or kW, only if calculation index exists

**Entity Naming (D-05 through D-07)**
- D-05: Entity ID: `sensor.luxtronik2_modbus_proxy_{snake_case_name}`
- D-06: Friendly name: "Luxtronik {Descriptive Name}"
- D-07: Unique ID: `{config_entry_id}_{calculation_or_parameter_index}`

**Additional Sensor Discovery (D-08 through D-11)**
- D-08: All 251 calculations and all 1,126 parameters registered as sensor entities, disabled by default
- D-09: Core sensors enabled by default (entity_registry_enabled_default=True)
- D-10: User enables additional sensors via HA entity registry UI — no code changes
- D-11: Additional sensor names derived from luxtronik library's parameter/calculation name

**Data Consumption (D-12 through D-13)**
- D-12: Sensors read from coordinator.data["parameters"] and coordinator.data["calculations"] (dict[int, int])
- D-13: Raw integers converted via luxtronik library's from_heatpump() method

**Device Info (D-14 through D-15)**
- D-14: Single device per config entry: manufacturer=MANUFACTURER, model=MODEL, name="Luxtronik 2.0"
- D-15: All entities belong to this device

**HA Sensor Config (D-16 through D-18)**
- D-16: Temperature: SensorDeviceClass.TEMPERATURE, native_unit_of_measurement="°C", SensorStateClass.MEASUREMENT
- D-17: Power: SensorDeviceClass.POWER, native unit W, SensorStateClass.MEASUREMENT
- D-18: Mode/status: no device class, no SensorStateClass

**Platform Registration (D-19 through D-20)**
- D-19: Add "sensor" to PLATFORMS in __init__.py
- D-20: async_setup_entry receives coordinator from hass.data[DOMAIN][entry.entry_id]

### Claude's Discretion
- Exact luxtronik calculation/parameter indices for each core sensor (researched and resolved below)
- Icon selection for each sensor type (mdi icons)
- Whether to add suggested_display_precision for temperature sensors
- Entity category (diagnostic vs None) for non-core sensors
- Whether to batch-create all 1,377 entities at startup or lazy-create on enable

### Deferred Ideas (OUT OF SCOPE)
- Select entities for HeatingMode/HotWaterMode — Phase 7
- Number entities for temperature setpoints — Phase 7
- SG-Ready select entity — Phase 7
- Write rate limiting — Phase 7
- Translations (DE) — Phase 7
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SETUP-01 | User can install via HACS (custom repository) | Covered by existing hacs.json + manifest.json; no new work in this phase beyond verifying sensor.py loads correctly |
| SENS-01 | Sensor entities for core temperatures (outside, flow, return, hot water, source in/out) | Calculation indices verified: 15, 10, 11, 17, 19, 20 — all Celsius type, from_heatpump() returns float |
| SENS-02 | Sensor entities for operating mode and compressor/pump status | Calculation indices verified: 80 (OperationMode), 44 (VD1out/compressor), 39 (HUPout/pump) |
| SENS-03 | Power sensor (if available via calculations) | Calculation index 257 (Heat_Output, Power type) — conditional creation required |
| SENS-04 | User can enable additional sensors from full parameter database via entity registry | 251 calculations + 1,126 parameters = 1,377 total entities registered disabled; standard HA pattern |
</phase_requirements>

---

## Summary

This phase adds `sensor.py` to the HA custom integration. The coordinator (Phase 5) already provides all data as `coordinator.data["calculations"]` and `coordinator.data["parameters"]` — both are `dict[int, int]` of raw Luxtronik wire integers. The sensor layer's only job is converting those raw ints to display values via the luxtronik library's `from_heatpump()` method, then exposing them as standard HA SensorEntity instances.

All core calculation indices have been verified against the installed `luxtronik==0.3.14` library. The conversion chain is: coordinator stores `to_heatpump()` output (raw int) → entity `native_value` calls `from_heatpump(raw_int)` on a fresh datatype object → HA displays the result. The `from_heatpump()` calls are stateless (no shared object state), so calling them per-update is safe and efficient.

SENS-04 (full database exposure) is satisfied by registering all 251 calculations and 1,126 parameters as sensor entities with `entity_registry_enabled_default=False`. HA does not update disabled entities, so the registration cost is paid once at startup and has no per-poll overhead. Total entity count is 1,377. Creating them all at startup is the correct, standard HA approach.

**Primary recommendation:** One `sensor.py` file, one `LuxtronikSensorEntityDescription` dataclass, two `CoordinatorEntity`-based classes (or one flexible class), creation via `async_add_entities` in `async_setup_entry`. No lazy-load needed.

---

## Standard Stack

### Core (all already in requirements / installed)

| Library | Version | Purpose | Notes |
|---------|---------|---------|-------|
| `luxtronik` | 0.3.14 | from_heatpump() conversion; provides datatype objects | [VERIFIED: pypi registry, installed] |
| `homeassistant` | 2024.1+ | SensorEntity, CoordinatorEntity, SensorDeviceClass | [VERIFIED: hacs.json minimum version] |
| `homeassistant.components.sensor` | same | SensorDeviceClass, SensorEntity, SensorStateClass | [ASSUMED: standard HA module path] |
| `homeassistant.helpers.update_coordinator` | same | CoordinatorEntity base class | [ASSUMED: standard HA module path] |

### No new packages needed
All dependencies are already declared in `manifest.json` and installed in the HA environment.

---

## Architecture Patterns

### Recommended Project Structure (sensor.py only)

```
custom_components/luxtronik2_modbus_proxy/
├── __init__.py          # Add "sensor" to PLATFORMS
├── coordinator.py       # Unchanged — provides coordinator.data
├── const.py             # Unchanged — DOMAIN, MANUFACTURER, MODEL
└── sensor.py            # NEW — this phase's deliverable
```

### Pattern 1: CoordinatorEntity subclass with EntityDescription

**What:** Define a dataclass that describes each sensor (index, name, conversion function, device class, unit). Create two lists — `CORE_SENSOR_DESCRIPTIONS` (enabled by default) and generate `ALL_CALC_DESCRIPTIONS` / `ALL_PARAM_DESCRIPTIONS` at import time from the register definition modules.

**Why:** Separates sensor metadata from entity logic. Planner can reason about individual sensors without reading entity code.

```python
# Source: HA developer docs pattern (ASSUMED import paths — verify against HA 2024.x installed)
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity

import luxtronik.calculations as _lc
import luxtronik.parameters as _lp

from .const import DOMAIN, MANUFACTURER, MODEL
from .coordinator import LuxtronikCoordinator


@dataclass(frozen=True)
class LuxtronikSensorEntityDescription(SensorEntityDescription):
    """Extends HA SensorEntityDescription with Luxtronik-specific fields."""
    # "calc" or "param" — which dict in coordinator.data to read from
    data_source: str = "calculations"
    # Index in the coordinator.data[data_source] dict
    lux_index: int = 0
    # Callable: (raw_int) -> display_value — wraps from_heatpump()
    value_fn: Callable[[int], Any] | None = None
```

**Example for a temperature sensor description:**

```python
# Source: verified luxtronik library indices (see Core Sensor Index Map below)
_lux_calcs = _lc.Calculations()

OUTSIDE_TEMPERATURE = LuxtronikSensorEntityDescription(
    key="outside_temperature",
    name="Luxtronik Outside Temperature",
    device_class=SensorDeviceClass.TEMPERATURE,
    native_unit_of_measurement="°C",
    state_class=SensorStateClass.MEASUREMENT,
    suggested_display_precision=1,
    data_source="calculations",
    lux_index=15,
    value_fn=_lux_calcs.calculations[15].from_heatpump,
)
```

### Pattern 2: Conditional sensor for power (SENS-03)

**What:** Before adding the power sensor to the setup list, check that index 257 exists in `coordinator.data["calculations"]`.

**Why:** Not all Luxtronik 2.0 controllers provide calculation index 257 (Heat_Output). The D-04 decision requires conditional creation.

```python
# In async_setup_entry:
entities: list[LuxtronikSensorEntity] = [
    LuxtronikSensorEntity(coordinator, entry, desc)
    for desc in CORE_SENSOR_DESCRIPTIONS
    if desc.lux_index != 257  # add non-power sensors unconditionally
]

# Power sensor: only if index 257 is present in the first coordinator data
if 257 in coordinator.data.get("calculations", {}):
    entities.append(
        LuxtronikSensorEntity(coordinator, entry, POWER_SENSOR_DESCRIPTION)
    )
```

### Pattern 3: Bulk disabled-by-default sensors (SENS-04)

**What:** Build `ALL_CALC_DESCRIPTIONS` and `ALL_PARAM_DESCRIPTIONS` at module import time (from `INPUT_REGISTERS` and `HOLDING_REGISTERS` in register_definitions). Pass all with `entity_registry_enabled_default=False`.

**When to use:** Always — registered-but-disabled entities have no per-poll overhead in HA.

```python
# Import the register databases (already built at module load time)
from luxtronik2_modbus_proxy.register_definitions.calculations import (
    INPUT_REGISTERS,
    CALC_NAME_TO_INDEX,
)
from luxtronik2_modbus_proxy.register_definitions.parameters import (
    HOLDING_REGISTERS,
    NAME_TO_INDEX,
)

# Core sensor keys (to skip when building the "all" list)
_CORE_CALC_INDICES: frozenset[int] = frozenset({10, 11, 15, 17, 19, 20, 39, 44, 80, 257})

# Build disabled-by-default descriptions for all remaining calculations
_lux_calcs_lib = _lc.Calculations()

ALL_EXTRA_CALC_DESCRIPTIONS: list[LuxtronikSensorEntityDescription] = [
    LuxtronikSensorEntityDescription(
        key=f"calc_{idx}",
        name=f"Luxtronik {calc_def.luxtronik_id}",
        entity_registry_enabled_default=False,
        entity_category=EntityCategory.DIAGNOSTIC,
        data_source="calculations",
        lux_index=idx,
        value_fn=_lux_calcs_lib.calculations[idx].from_heatpump,
    )
    for idx, calc_def in INPUT_REGISTERS.items()
    if idx not in _CORE_CALC_INDICES
]
```

### Pattern 4: Entity class with device_info

```python
class LuxtronikSensorEntity(CoordinatorEntity[LuxtronikCoordinator], SensorEntity):
    """A single sensor entity backed by the Luxtronik coordinator."""

    entity_description: LuxtronikSensorEntityDescription

    def __init__(
        self,
        coordinator: LuxtronikCoordinator,
        entry: ConfigEntry,
        description: LuxtronikSensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        # D-07: Stable unique ID: config_entry_id + lux_index
        self._attr_unique_id = f"{entry.entry_id}_{description.lux_index}"

    @property
    def device_info(self) -> DeviceInfo:
        """D-14: Single device per config entry."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.config_entry.entry_id)},
            name="Luxtronik 2.0",
            manufacturer=MANUFACTURER,
            model=MODEL,
        )

    @property
    def native_value(self) -> Any:
        """Read raw int from coordinator.data and convert via from_heatpump()."""
        desc = self.entity_description
        raw: dict[int, int] = self.coordinator.data.get(desc.data_source, {})
        raw_val = raw.get(desc.lux_index)
        if raw_val is None:
            return None
        if desc.value_fn is not None:
            return desc.value_fn(raw_val)
        return raw_val
```

### Anti-Patterns to Avoid

- **Importing luxtronik at entity update time:** The datatype objects should be created once at module load (or sensor description build time), not inside `native_value`. `from_heatpump()` is stateless — pre-capture the callable.
- **Storing converted values in coordinator:** The coordinator stores raw ints (D-12/D-13). Conversion belongs in the entity layer.
- **Creating entities inside coordinator:** Coordinator is data-only; entity setup belongs in `async_setup_entry`.
- **Using `entity_registry_enabled_default=True` for all 1,377 sensors:** Only core sensors (9-10 entities) should be enabled by default. The rest must be explicitly `False`.
- **Making power sensor mandatory:** Always guard index 257 with `if 257 in coordinator.data["calculations"]` — some controllers omit it.
- **Using `to_heatpump()` in native_value:** The coordinator already stored `to_heatpump()` output. In `native_value`, call `from_heatpump()` to get the display value — not `to_heatpump()` again.

---

## Core Sensor Index Map (Claude's Discretion — RESOLVED)

All indices verified against `luxtronik==0.3.14` installed library. [VERIFIED: direct Python introspection]

| Sensor Name | data_source | Index | luxtronik_id | Type | from_heatpump example |
|-------------|-------------|-------|--------------|------|----------------------|
| outside_temperature | calculations | 15 | ID_WEB_Temperatur_TA | Celsius | 200 → 20.0 |
| flow_temperature | calculations | 10 | ID_WEB_Temperatur_TVL | Celsius | 200 → 20.0 |
| return_temperature | calculations | 11 | ID_WEB_Temperatur_TRL | Celsius | 200 → 20.0 |
| hot_water_temperature | calculations | 17 | ID_WEB_Temperatur_TBW | Celsius | 200 → 20.0 |
| source_in_temperature | calculations | 19 | ID_WEB_Temperatur_TWE | Celsius | 200 → 20.0 |
| source_out_temperature | calculations | 20 | ID_WEB_Temperatur_TWA | Celsius | 200 → 20.0 |
| operating_mode | calculations | 80 | ID_WEB_WP_BZ_akt | OperationMode | 0 → "heating", 4 → "defrost" |
| compressor_running | calculations | 44 | ID_WEB_VD1out | Bool | 0 → False, 1 → True |
| circulation_pump_running | calculations | 39 | ID_WEB_HUPout | Bool | 0 → False, 1 → True |
| heat_pump_power | calculations | 257 | Heat_Output | Power | 5000 → 5000 (unit: W) |

**Key facts:**
- Celsius type: `from_heatpump(int)` returns `float` (divide by 10 internally)
- OperationMode type: `from_heatpump(int)` returns lowercase string; values 0-7 defined, 8+ return None
- Bool type: `from_heatpump(int)` returns Python `bool`
- Power type: `from_heatpump(int)` returns `int` in Watts (no scaling, `measurement_type = "W"`)

**OperationMode string values (from library):**
```
0: "heating"
1: "hot water"
2: "swimming pool/solar"
3: "evu"
4: "defrost"
5: "no request"
6: "heating external source"
7: "cooling"
8+: None
```

**Icon recommendations (Claude's Discretion):**

| Sensor | mdi icon |
|--------|----------|
| outside_temperature | mdi:thermometer |
| flow_temperature | mdi:thermometer-chevron-up |
| return_temperature | mdi:thermometer-chevron-down |
| hot_water_temperature | mdi:water-thermometer |
| source_in_temperature | mdi:thermometer-water |
| source_out_temperature | mdi:thermometer-water |
| operating_mode | mdi:heat-pump |
| compressor_running | mdi:engine |
| circulation_pump_running | mdi:pump |
| heat_pump_power | mdi:lightning-bolt |

**suggested_display_precision recommendation:** Use `suggested_display_precision=1` for all temperature sensors. HA will then display "20.0 °C" rather than "20.000000 °C". [ASSUMED: HA 2024.1+ supports this field on SensorEntityDescription]

**Entity category for non-core sensors:** Use `EntityCategory.DIAGNOSTIC` for all disabled-by-default sensors. This groups them under the "Diagnostic" section in the device page, making the UI cleaner. [ASSUMED: standard HA convention]

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Data polling and retry | Custom asyncio polling loop | DataUpdateCoordinator (Phase 5 — already done) | HA handles retry, error propagation, entity unavailability automatically |
| Value conversion | Custom temperature scaling (raw / 10) | `luxtronik` datatype `from_heatpump()` | Handles edge cases, None values, enum mapping |
| Entity registration | Manual entity registry manipulation | `entity_registry_enabled_default=False` on description | Standard HA mechanism — toggling works in UI without code |
| Device grouping | Manual device registry lookup | `DeviceInfo` returned from `device_info` property | HA groups entities automatically |
| Coordinator entity lifecycle | Manual state_changed listeners | `CoordinatorEntity` base class | Handles subscribe/unsubscribe, availability, update propagation |

---

## Common Pitfalls

### Pitfall 1: coordinator.data has raw ints, not display values
**What goes wrong:** Entity reads `coordinator.data["calculations"][15]` expecting `20.0` but gets `200`.
**Why it happens:** `coordinator._sync_read()` calls `to_heatpump()` to convert float→int before storing. This is correct (matches wire format and what the Modbus proxy layer expects), but entity platforms must reverse it.
**How to avoid:** Always call `from_heatpump(raw_int)` in `native_value`. Pre-capture the callable in the entity description's `value_fn` field.
**Warning signs:** Temperature readings 10x too high (e.g., "200 °C" instead of "20 °C").

### Pitfall 2: Power sensor index 257 absent on some controllers
**What goes wrong:** `coordinator.data["calculations"].get(257)` returns `None` → `native_value` returns `None` but entity is still registered and visible.
**Why it happens:** Not all Alpha Innotec / Novelan controllers implement the power calculation. Index 257 (`Heat_Output`) is present only on controllers that compute it.
**How to avoid:** In `async_setup_entry`, only create the power sensor entity if `257 in coordinator.data.get("calculations", {})`. If the first poll returns no data (coordinator error), skip power sensor and log a warning.
**Warning signs:** Power sensor always shows "unavailable" even after coordinator recovers.

### Pitfall 3: OperationMode values are lowercase strings, not the enum names in D-02
**What goes wrong:** `from_heatpump(0)` returns `"heating"` (lowercase), not `"Heating"` (title case as shown in CONTEXT D-02).
**Why it happens:** The luxtronik library returns lowercase strings directly.
**How to avoid:** Either title-case the string in `value_fn` (`lambda raw: op.from_heatpump(raw).title() if op.from_heatpump(raw) else None`) or document that HA will display the raw string. The D-02 decision says "human-readable string (e.g., 'Heating')" — planner should implement `.title()` or `.replace("_", " ").title()` transform.
**Warning signs:** Entity state shows "heating" instead of "Heating" in UI.

### Pitfall 4: Bool sensors as string "Running"/"Stopped" vs Python bool
**What goes wrong:** D-03 says display as "Running"/"Stopped" but `from_heatpump()` returns Python `bool`. Using `native_value = True` with no device class means HA displays "True" not "Running".
**Why it happens:** With no `SensorDeviceClass`, HA renders `native_value` as string — so `True` becomes "True".
**How to avoid:** Wrap Bool conversions: `value_fn=lambda raw: "Running" if bool_calc.from_heatpump(raw) else "Stopped"`. Or use `SensorDeviceClass.ENUM` with options=["Running", "Stopped"]. The simplest approach is the lambda.
**Warning signs:** Entity shows "True"/"False" instead of "Running"/"Stopped".

### Pitfall 5: Import path conflict between proxy's register_definitions and HA integration
**What goes wrong:** `sensor.py` imports `from luxtronik2_modbus_proxy.register_definitions.calculations import INPUT_REGISTERS` — this is the proxy package path, not a relative import. In the HA integration context, the proxy package must be installed (via manifest.json requirements → PyPI).
**Why it happens:** The integration is in `custom_components/luxtronik2_modbus_proxy/` but it depends on `src/luxtronik2_modbus_proxy/` which is a separate package with a matching name.
**How to avoid:** The CONTEXT.md and STATE.md confirm: manifest.json `requirements: ["luxtronik==0.3.14"]`. The proxy package (`luxtronik2-modbus-proxy`) provides the register definitions. During dev, editable install (`pip install -e .`) makes it available. For SENS-04, importing from the proxy package is correct.
**Warning signs:** ImportError at HA startup for `luxtronik2_modbus_proxy.register_definitions`.

### Pitfall 6: All 1,377 sensor descriptions built at module import time
**What goes wrong:** Building the full descriptions list (251 + 1,126 entities) at import time takes measurable time and adds memory overhead.
**Why it happens:** Each description object references a `value_fn` closure. Instantiating 1,377 luxtronik datatype objects at import consumes memory.
**How to avoid:** The luxtronik library instantiates `_lc.Calculations()` and `_lp.Parameters()` as a single object — use it once and capture `calc_obj.from_heatpump` as the callable. This is already the pattern in `calculations.py` and `parameters.py` (they instantiate the library once at module load). Cost is acceptable — luxtronik is pure Python with no I/O.
**Warning signs:** Slow HA startup time after adding sensor platform.

---

## Code Examples

### async_setup_entry pattern

```python
# Source: HA developer docs (ASSUMED pattern, standard for 2024.x)
async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor entities from a config entry."""
    coordinator: LuxtronikCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[LuxtronikSensorEntity] = []

    # Core sensors: always enabled
    for desc in CORE_SENSOR_DESCRIPTIONS:
        # Power sensor: conditional
        if desc.lux_index == 257 and 257 not in coordinator.data.get("calculations", {}):
            continue
        entities.append(LuxtronikSensorEntity(coordinator, entry, desc))

    # All remaining calculations: disabled by default
    entities.extend(
        LuxtronikSensorEntity(coordinator, entry, desc)
        for desc in ALL_EXTRA_CALC_DESCRIPTIONS
    )

    # All parameters: disabled by default
    entities.extend(
        LuxtronikSensorEntity(coordinator, entry, desc)
        for desc in ALL_PARAM_DESCRIPTIONS
    )

    async_add_entities(entities)
```

### Unique ID pattern (D-07)

```python
# Unique ID must be stable across restarts.
# Using entry.entry_id ensures it's tied to this config entry instance.
# Using lux_index ensures uniqueness within the entry.
self._attr_unique_id = f"{entry.entry_id}_{description.data_source}_{description.lux_index}"
```

Note: Include `data_source` in unique ID because calculations and parameters share index namespace (both start at 0). A calculation at index 15 and a parameter at index 15 are different entities.

### Device info pattern (D-14)

```python
from homeassistant.helpers.entity import DeviceInfo

@property
def device_info(self) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, self.coordinator.config_entry.entry_id)},
        name=MODEL,
        manufacturer=MANUFACTURER,
        model=MODEL,
    )
```

### PLATFORMS list update (__init__.py, D-19)

```python
# In __init__.py — change from:
PLATFORMS: list[str] = []
# To:
PLATFORMS: list[str] = ["sensor"]
```

---

## Conversion Chain Reference

This is the single most important fact for implementing `native_value`:

```
Controller wire format (int) → luxtronik library stores as Python value
→ coordinator._sync_read() calls to_heatpump() → stores raw int
→ coordinator.data["calculations"][idx] = raw_int
→ entity native_value: calls from_heatpump(raw_int) → display value
```

| Data type | raw_int example | from_heatpump returns | HA display |
|-----------|-----------------|----------------------|------------|
| Celsius | 200 | 20.0 (float) | "20.0 °C" |
| OperationMode | 0 | "heating" (str) | "heating" (or .title() → "Heating") |
| Bool | 1 | True (bool) | must convert to "Running"/"Stopped" |
| Power | 5000 | 5000 (int) | "5000 W" |

---

## Environment Availability

Step 2.6: SKIPPED — this phase adds Python source files to an existing HA custom integration. No new external dependencies. All runtime requirements are already satisfied by Phase 5 (luxtronik==0.3.14 installed, HA environment active).

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | HA import path `homeassistant.components.sensor.SensorEntityDescription` supports `suggested_display_precision` field in HA 2024.1+ | Architecture Patterns | AttributeError at startup; workaround: set it via `_attr_suggested_display_precision` instead |
| A2 | `homeassistant.helpers.entity.EntityCategory` is the correct import for `EntityCategory.DIAGNOSTIC` in HA 2024.1+ | Architecture Patterns | ImportError; check for `homeassistant.const.EntityCategory` as fallback |
| A3 | `CoordinatorEntity[LuxtronikCoordinator]` generic syntax works in HA 2024.1+ Python 3.12 | Code Examples | TypeError at class definition; use `CoordinatorEntity` without generic if needed |
| A4 | `DeviceInfo` is importable from `homeassistant.helpers.entity` in HA 2024.1+ | Code Examples | ImportError; may have moved to `homeassistant.helpers.device_registry` |
| A5 | `AddEntitiesCallback` import path is `homeassistant.helpers.entity_platform` | Code Examples | ImportError; may differ between HA versions |

**All assumptions are low-risk** — they concern HA import paths which are stable across 2024.x. Verify the exact import paths against the installed HA version when writing sensor.py.

---

## Open Questions

1. **Unique ID collision between calculations and parameters**
   - What we know: Both index spaces start at 0. Calculation 15 and parameter 15 are different entities.
   - What's unclear: The D-07 decision says `{config_entry_id}_{calculation_or_parameter_index}` — this would collide.
   - Recommendation: Use `{entry_id}_calc_{index}` and `{entry_id}_param_{index}` to guarantee uniqueness. Planner should confirm this interpretation of D-07.

2. **Bool sensor display as string vs. native bool with labels**
   - What we know: `from_heatpump()` returns Python bool; D-03 says "Running"/"Stopped".
   - What's unclear: Should we use `SensorDeviceClass.ENUM` with `options=["Running", "Stopped"]` or just convert in `value_fn`?
   - Recommendation: Use `value_fn=lambda raw: "Running" if bool_calc.from_heatpump(raw) else "Stopped"` — simpler and avoids enum device class complexity.

3. **OperationMode display: lowercase vs title case**
   - What we know: Library returns lowercase ("heating", "hot water").
   - What's unclear: D-02 implies title case ("Heating", "Hot Water").
   - Recommendation: Apply `.title()` transform in `value_fn` for the operating_mode sensor. "Hot Water" from "hot water".title() is correct. Edge case: "no request".title() → "No Request" which is fine.

---

## Sources

### Primary (HIGH confidence)
- Direct Python introspection of `luxtronik==0.3.14` installed library — all calculation indices, types, and from_heatpump() return values verified by running code
- `custom_components/luxtronik2_modbus_proxy/coordinator.py` — confirmed coordinator.data structure (D-05: dict[int,int])
- `custom_components/luxtronik2_modbus_proxy/const.py` — DOMAIN, MANUFACTURER, MODEL values
- `src/luxtronik2_modbus_proxy/register_definitions/calculations.py` — INPUT_REGISTERS structure, CALC_NAME_TO_INDEX
- `src/luxtronik2_modbus_proxy/register_definitions/parameters.py` — HOLDING_REGISTERS structure, NAME_TO_INDEX

### Secondary (MEDIUM confidence)
- HA developer docs pattern for CoordinatorEntity + SensorEntity (ASSUMED: standard pattern unchanged since HA 2023.x)
- hacs.json minimum HA version: 2024.1.0

### Tertiary (LOW confidence)
- Import paths for SensorEntityDescription fields (suggested_display_precision, EntityCategory) — not verified against installed HA package

---

## Metadata

**Confidence breakdown:**
- Core sensor indices: HIGH — verified by direct luxtronik library introspection
- from_heatpump() conversion behavior: HIGH — verified by running actual conversions
- HA SensorEntity pattern: MEDIUM — standard stable pattern, import paths assumed
- Entity count (1,377): HIGH — verified by counting library objects
- Power sensor conditionality: HIGH — index 257 confirmed present in library but may be absent in coordinator.data for controllers that don't compute it

**Research date:** 2026-04-09
**Valid until:** 2026-07-09 (stable domain — luxtronik library rarely changes)

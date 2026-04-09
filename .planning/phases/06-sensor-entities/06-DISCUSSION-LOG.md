# Phase 6: Sensor Entities - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-09
**Phase:** 06-sensor-entities
**Mode:** auto
**Areas discussed:** Core sensor set, Entity naming, Additional sensor discovery, Device info, State class mapping

---

## Core Sensor Set

| Option | Description | Selected |
|--------|-------------|----------|
| Temperatures + mode + compressor + power | SENS-01/02/03 core set enabled by default | ✓ |
| Temperatures only | Minimal set, mode/status as additional | |

**User's choice:** Full core set (auto-selected recommended default)

---

## Entity Naming

| Option | Description | Selected |
|--------|-------------|----------|
| DOMAIN prefix pattern | sensor.luxtronik2_modbus_proxy_{name} | ✓ |
| Short prefix | sensor.luxtronik_{name} | |

**User's choice:** DOMAIN prefix (auto-selected — HA convention)

---

## Additional Sensor Discovery

| Option | Description | Selected |
|--------|-------------|----------|
| Disabled-by-default entities | All 1,377 entities registered, user enables via registry | ✓ |
| Config flow selection | Multi-select in config flow for additional sensors | |
| YAML configuration | sensors.yaml file listing enabled sensors | |

**User's choice:** Disabled-by-default entities (auto-selected — standard HA pattern, per SENS-04)

---

## Device Info

| Option | Description | Selected |
|--------|-------------|----------|
| Single device per entry | One device with MANUFACTURER/MODEL from const.py | ✓ |
| No device info | Sensors without device grouping | |

**User's choice:** Single device (auto-selected — standard HA pattern)

---

## State Class Mapping

| Option | Description | Selected |
|--------|-------------|----------|
| luxtronik from_heatpump conversion | Use library's built-in value conversion | ✓ |
| Custom conversion layer | Build own mapping table | |

**User's choice:** Library conversion (auto-selected — reuses proven code)

## Claude's Discretion

- Exact calculation/parameter indices for core sensors
- Icon selection, display precision
- Entity category for non-core sensors
- Startup strategy for 1,377 entities

## Deferred Ideas

- Control entities (Phase 7)
- Translations (Phase 7)

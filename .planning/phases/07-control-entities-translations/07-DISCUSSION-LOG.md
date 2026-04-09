# Phase 7: Control Entities & Translations - Discussion Log (Assumptions Mode)

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions captured in CONTEXT.md — this log preserves the analysis.

**Date:** 2026-04-09
**Phase:** 07-control-entities-translations
**Mode:** assumptions (auto)
**Areas analyzed:** Write Method, Rate Limiting, Select Entities, Number Entities, Entity Platform Structure, Translations

## Assumptions Presented

### Write Method in Coordinator
| Assumption | Confidence | Evidence |
|------------|-----------|----------|
| Add async_write_parameter() acquiring self._lock, write via executor, refresh after | Confident | coordinator.py line 75 comment, luxtronik_client.py lines 107-147 |

### Write Rate Limiting
| Assumption | Confidence | Evidence |
|------------|-----------|----------|
| Coordinator-level rate limiting with per-parameter timestamp dict, 60s default window | Likely | polling_engine.py lines 79-82, 236-256; ROADMAP success criterion #4 |

### Temperature Setpoint Parameters
| Assumption | Confidence | Evidence |
|------------|-----------|----------|
| Hot water: parameter 105 (ID_Soll_BWS_akt), range 30.0-65.0°C | Confident | parameters.py lines 107-116 |
| Flow/heating: parameter 1 (ID_Einst_WK_akt) — heating curve offset | Unclear | Multiple writable Celsius params exist |

### Entity Platform Structure
| Assumption | Confidence | Evidence |
|------------|-----------|----------|
| select.py + number.py following sensor.py pattern, added to PLATFORMS | Confident | sensor.py entity pattern, __init__.py line 29 comment |

### Translation Scope
| Assumption | Confidence | Evidence |
|------------|-----------|----------|
| Extend strings.json with entity.select state entries, create translations/de.json | Likely | strings.json lines 1-23, HA translation framework |

## Corrections Made

No corrections — all assumptions auto-confirmed.

## Auto-Resolved

- Flow temperature setpoint parameter: auto-selected Parameter 1 (ID_Einst_WK_akt) as recommended default. Flagged for research confirmation.
- Rate limiting location: auto-selected coordinator-level (Alternative A). Matches proxy pattern.
- Translation approach: auto-selected standard HA pattern (Alternative A). Standard and recommended.

## External Research Flagged

- HA SelectEntity translation pattern: exact strings.json structure for entity.select state options
- HA NumberEntity: native_min_value/native_max_value in display vs raw units
- Flow temperature setpoint: which parameter is the correct heating setpoint for Alpha Innotec installations

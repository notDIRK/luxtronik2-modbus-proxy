---
phase: 02-integration-ready-register-map
plan: "03"
subsystem: sg-ready
tags: [sg-ready, modbus, evcc, luxtronik, heat-pump, pymodbus, pydantic, docs]

requires:
  - phase: 02-01
    provides: Full 1126-parameter register map with HOLDING_BLOCK_SIZE=5001
  - phase: 02-02
    provides: User-selectable extra registers, RegistersConfig, config.py patterns

provides:
  - SG-ready virtual register at Modbus holding address 5000
  - translate_sg_ready_mode() function mapping modes 0-3 to Luxtronik parameter writes
  - SgReadyWrite dataclass for type-safe queue items
  - sg_ready_mode_map config override for custom hardware mappings
  - SG-ready write interception in ProxyHoldingDataBlock (async_setValues)
  - D-13 compliance: register 5000 reflects last successfully applied mode
  - evcc integration guide with ready-to-paste YAML snippet
  - HA coexistence guide with single-connection model and write conflict guidance

affects: [evcc-integration, ha-integration, polling-engine, register-cache, documentation]

tech-stack:
  added: []
  patterns:
    - "Virtual register interception: sg_ready wire address checked in async_setValues before normal write path"
    - "SG-ready queue items are typed (SgReadyWrite dataclass) not raw tuples for type-safety"
    - "D-13 pattern: async_setValues enqueues without updating datablock; polling engine updates after successful upstream write"
    - "Rate limiting applies to underlying param addresses (3,4) not to virtual address 5000"

key-files:
  created:
    - src/luxtronik2_modbus_proxy/sg_ready.py
    - tests/unit/test_sg_ready.py
    - docs/en/evcc-integration.md
    - docs/en/ha-coexistence.md
  modified:
    - src/luxtronik2_modbus_proxy/register_map.py
    - src/luxtronik2_modbus_proxy/register_cache.py
    - src/luxtronik2_modbus_proxy/polling_engine.py
    - src/luxtronik2_modbus_proxy/config.py
    - tests/unit/test_register_cache.py

key-decisions:
  - "D-13 compliance via deferred datablock update: async_setValues enqueues SgReadyWrite without touching the datablock; polling_engine updates register 5000 only after successful Luxtronik write — register reflects last successfully applied mode, not last attempted"
  - "SgReadyWrite is a typed dataclass not a raw (address, values) tuple — enables isinstance checks in polling_engine without address magic numbers"
  - "Rate limiting in _drain_and_write applies to the underlying Luxtronik parameter addresses (3, 4) not to the virtual register 5000 — per T-02-09"
  - "SG-ready register initialized to mode 1 (Normal) at RegisterCache startup so reads before any write return a sensible default"
  - "sg_ready_mode_map config field added to ProxyConfig (not RegistersConfig) as it is a top-level proxy behavior setting"

patterns-established:
  - "Virtual register pattern: register in RegisterMap with allowed_values, intercept by wire_address in async_setValues, enqueue typed write object"
  - "Deferred cache update pattern (D-13): queue write, update cache only after confirmed upstream success"

requirements-completed: [REG-05, INTEG-01, INTEG-02]

duration: 5min
completed: "2026-04-05"
---

# Phase 02 Plan 03: SG-ready Virtual Register and Integration Docs Summary

**SG-ready virtual Modbus register at address 5000 translates evcc mode writes (0-3) to Luxtronik HeatingMode + HotWaterMode parameter combinations, with evcc YAML snippet and HA coexistence documentation**

## Performance

- **Duration:** 5 min
- **Started:** 2026-04-05T20:24:09Z
- **Completed:** 2026-04-05T20:30:00Z
- **Tasks:** 2
- **Files modified:** 9 (4 created, 5 modified)

## Accomplishments

- SG-ready virtual register at address 5000 accepts writes of 0-3 and translates to Luxtronik HeatingMode + HotWaterMode parameter writes; reading returns last successfully applied mode (D-13 compliant)
- ProxyHoldingDataBlock intercepts writes to wire address 5000, enqueues typed SgReadyWrite; polling engine processes and updates datablock only after confirmed Luxtronik write
- evcc integration guide with ready-to-paste YAML snippet (heatsources, setmode/getmode at register 5000), SG-ready mode table, temperature registers, and troubleshooting section
- HA coexistence guide explaining single-connection model, recommended poll_interval settings, and write conflict ownership guidance

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): SG-ready failing tests** - `eeb97ef` (test)
2. **Task 1 (GREEN): SG-ready virtual register implementation** - `8fbd366` (feat)
3. **Task 2: evcc and HA coexistence documentation** - `5b6e3d7` (docs)

## Files Created/Modified

- `src/luxtronik2_modbus_proxy/sg_ready.py` - SG_READY_MODE_MAP, SgReadyWrite dataclass, translate_sg_ready_mode(), validate_sg_ready_mode()
- `src/luxtronik2_modbus_proxy/register_map.py` - SG-ready virtual register entry (SGReadyMode, allowed_values=[0,1,2,3])
- `src/luxtronik2_modbus_proxy/register_cache.py` - SG-ready interception in async_setValues; init register to mode 1
- `src/luxtronik2_modbus_proxy/polling_engine.py` - SgReadyWrite handling in _drain_and_write; deferred cache update
- `src/luxtronik2_modbus_proxy/config.py` - sg_ready_mode_map field (optional custom override)
- `tests/unit/test_sg_ready.py` - 19 tests for SG-ready module (mode map, translate, validate, SgReadyWrite)
- `tests/unit/test_register_cache.py` - 5 additional tests (SG-ready interception, invalid mode, writes disabled)
- `docs/en/evcc-integration.md` - evcc YAML, mode table, register reference, troubleshooting
- `docs/en/ha-coexistence.md` - single-connection model, poll_interval config, write conflict guidance, architecture diagram

## Decisions Made

- D-13 compliance via deferred datablock update: async_setValues enqueues SgReadyWrite without touching the holding register; polling_engine updates register 5000 only after successful upstream Luxtronik write. This ensures reads always reflect the last confirmed state, not an optimistic/failed write.
- SgReadyWrite is a typed dataclass (not a raw tuple) so _drain_and_write can use isinstance() to distinguish SG-ready items from normal (wire_address, values) writes.
- Rate limiting in _drain_and_write applies to underlying parameter addresses 3 and 4, not to virtual address 5000 — per T-02-09 in the threat model.

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required. Documentation guides are self-contained.

## Next Phase Readiness

- Phase 2 complete: full register map (Plan 01), user-selectable params + CLI (Plan 02), SG-ready virtual register + docs (Plan 03)
- SG-ready mode mapping is marked [ASSUMED] — requires hardware validation on Alpha Innotec MSW 14 before production use
- evcc integration guide is ready for user testing; upstream PR to evcc repo deferred until proxy is validated in production

## Self-Check: PASSED

All files verified present, all commits verified in git log, all acceptance criteria verified.

---
*Phase: 02-integration-ready-register-map*
*Completed: 2026-04-05*

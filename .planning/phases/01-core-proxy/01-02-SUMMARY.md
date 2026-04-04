---
phase: 01-core-proxy
plan: 02
subsystem: infra
tags: [pymodbus, modbus, register-cache, luxtronik, async, write-validation, ExcCodes]

# Dependency graph
requires:
  - phase: 01-core-proxy
    plan: 01
    provides: "RegisterMap with address lookup, validate_write_value, block sizes; ProxyConfig"
provides:
  - ProxyHoldingDataBlock subclass with async_setValues write validation and write queue
  - RegisterCache wrapping both datablocks with wire-address update methods and stale/fresh state
  - LuxtronikClient with async read/write using connect-per-call pattern via run_in_executor
  - 10 unit tests for cache and datablock behavior, all passing
affects: [01-03, 01-04]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "ProxyHoldingDataBlock overrides async_setValues to validate writes before accepting"
    - "wire_address = datablock_address - 1 (ModbusDeviceContext adds +1 on incoming writes)"
    - "LuxtronikClient creates new Luxtronik instance per call (connect-per-call PROTO-05)"
    - "run_in_executor(None, lux.read/write) pattern for async-safe blocking I/O"
    - "Luxtronik instance constructed via __new__ + manual attribute init to avoid auto-read in __init__"
    - "parameter.to_heatpump(parameter.value) to recover raw integer for Modbus storage"

key-files:
  created:
    - src/luxtronik2_modbus_proxy/register_cache.py
    - src/luxtronik2_modbus_proxy/luxtronik_client.py
    - tests/unit/test_register_cache.py
  modified: []

key-decisions:
  - "Luxtronik instance created via __new__ + manual attribute init to avoid auto-read on construction"
  - "Raw heatpump integer value stored in Modbus registers via to_heatpump(); converted values (floats) would not fit in 16-bit registers"
  - "wire_address = datablock_address - 1 pattern locked: ModbusDeviceContext always adds +1 before reaching datablock"
  - "enable_writes=False gate implemented in ProxyHoldingDataBlock (T-02-02) — all writes rejected unless explicitly enabled"

patterns-established:
  - "Pattern: ProxyHoldingDataBlock validates writes in 3 gates: enable_writes -> is_writable -> validate_write_value"
  - "Pattern: RegisterCache.update_holding_values / update_input_values converts wire_address to datablock_address (+1)"
  - "Pattern: LuxtronikClient.__new__ avoids auto-read in luxtronik.Luxtronik.__init__ by bypassing constructor"
  - "Pattern: async_write populates parameters.queue BEFORE dispatching write() to executor"

requirements-completed: [PROTO-02, PROTO-04, PROTO-05, WRITE-01, WRITE-02]

# Metrics
duration: 15min
completed: 2026-04-04
---

# Phase 01 Plan 02: Register Cache and Luxtronik Client Summary

**ProxyHoldingDataBlock validates Modbus writes against RegisterMap (enable_writes gate, writability, value range), queues valid writes; LuxtronikClient wraps blocking luxtronik library with async run_in_executor and connect-per-call pattern; 10 cache unit tests pass.**

## Performance

- **Duration:** ~15 minutes
- **Started:** 2026-04-04T18:47:00Z
- **Completed:** 2026-04-04T18:56:56Z
- **Tasks:** 2 of 2
- **Files modified:** 3 created, 0 modified

## Accomplishments

### Task 1: Register cache with write-through validation (TDD)

- `ProxyHoldingDataBlock(ModbusSequentialDataBlock)` overrides `async_setValues`:
  - Gate 1: `enable_writes` guard (T-02-02) — rejects all writes when disabled
  - Gate 2: `is_writable(wire_address)` — rejects non-writable and unmapped addresses
  - Gate 3: `validate_write_value(wire_address, value)` — rejects out-of-range values (T-02-01)
  - On success: updates datablock and enqueues `(wire_address, values)` for polling engine
- `RegisterCache` wraps both datablocks:
  - `update_holding_values(wire_address, values)` converts wire to datablock address (+1)
  - `update_input_values(wire_address, values)` same for input registers
  - `mark_stale()` / `mark_fresh()` manage cache validity state and `last_successful_read`
- 10 unit tests, all passing

### Task 2: Luxtronik client wrapper

- `LuxtronikClient` provides async read/write with connect-per-call enforcement:
  - `async_read()`: creates fresh `Luxtronik` instance via `__new__`, calls `lux.read()` in `run_in_executor`
  - `async_write(param_writes)`: creates fresh instance, populates `parameters.queue` before `run_in_executor(lux.write)`
  - `update_cache_from_read(lux, cache)`: extracts raw heatpump integers via `to_heatpump()` for each mapped address, updates cache
- Module docstring explains connect-per-call rationale and why new instances are created per call

## Test Results

```
29 passed in 0.07s
```

All 29 unit tests pass (6 config + 10 register cache + 13 register map).

## Task Commits

Each task was committed atomically:

1. **Task 1: Register cache tests (RED)** - `366ff46` (test)
2. **Task 1: Register cache implementation (GREEN)** - `f0fff3d` (feat)
3. **Task 2: LuxtronikClient implementation** - `912e8bb` (feat)

_Note: TDD tasks produce separate test and implementation commits._

## Files Created/Modified

- `src/luxtronik2_modbus_proxy/register_cache.py` - ProxyHoldingDataBlock + RegisterCache
- `src/luxtronik2_modbus_proxy/luxtronik_client.py` - LuxtronikClient async wrapper
- `tests/unit/test_register_cache.py` - 10 unit tests for cache and datablock

## Decisions Made

1. **Luxtronik instance created via `__new__` + manual init** — The `luxtronik.Luxtronik.__init__` calls `self.read()` automatically, which would make a live network connection during test or when we want to control timing. Using `__new__` + manual attribute assignment bypasses the auto-read and gives explicit control over when the network call happens.

2. **Raw heatpump integer for Modbus storage** — The `.value` attribute stores the human-readable converted value (e.g., `20.0` for Celsius, `"Party"` for HeatingMode). The raw wire-format integer (e.g., `200` for 20.0°C, `2` for "Party") is recovered via `to_heatpump(value)`. This integer is what Modbus clients expect in 16-bit registers.

3. **Wire address = datablock address - 1** — Locked pattern: `ModbusDeviceContext.setValues` unconditionally does `address += 1` before passing to the datablock (verified from pymodbus 3.12.1 source). All update methods add +1 when storing, subtract -1 when receiving from the server.

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

**Environment: pytest not installed in .venv** — The `.venv` (Python 3.14 via uv) was created during Plan 01 but pytest was installed in a different environment. Required `uv pip install --python .venv/bin/python3.14 pytest pytest-asyncio` to install in the correct environment. Tests then ran correctly with `.venv/bin/python3.14 -m pytest`.

This is an environment setup issue, not a code issue. All tests pass after correcting the invocation.

## Known Stubs

None. Both modules are fully implemented with real logic. `LuxtronikClient` will connect to the actual hardware when called; it is not tested with mocks in this plan (mock tests are Plan 04 scope per the plan spec).

## Threat Flags

None. No new network endpoints, auth paths, file access patterns, or schema changes introduced beyond what the threat model defined.

- T-02-01 (write value validation): Implemented in `ProxyHoldingDataBlock.async_setValues` gates 2 and 3
- T-02-02 (enable_writes=False default): Implemented as gate 1 in `async_setValues`
- T-02-04 (connect-per-call): Enforced in `LuxtronikClient` — new instance per read/write call

## Next Phase Readiness

- `RegisterCache` and `LuxtronikClient` are ready for Plan 03 (polling engine)
- Plan 03 will wire `LuxtronikClient.async_read` → `update_cache_from_read` → `cache.mark_fresh()` in a polling loop
- Plan 03 will also drain the write queue and call `LuxtronikClient.async_write`
- Blocker from STATE.md remains: SG-ready parameter ID combinations need hardware validation (Phase 2 scope, not blocking Phase 1)

## Self-Check: PASSED

All key files exist and all commits are in git history.

**Files verified:** register_cache.py, luxtronik_client.py, tests/unit/test_register_cache.py

**Commits verified:** 366ff46 (RED tests), f0fff3d (feat: register cache), 912e8bb (feat: luxtronik client)

---
*Phase: 01-core-proxy*
*Completed: 2026-04-04*

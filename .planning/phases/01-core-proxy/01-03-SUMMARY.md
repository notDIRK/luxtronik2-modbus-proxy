---
phase: 01-core-proxy
plan: 03
subsystem: infra
tags: [pymodbus, modbus, polling-engine, async, rate-limiting, sigterm, main, entrypoint]

# Dependency graph
requires:
  - phase: 01-core-proxy
    plan: 01
    provides: "ProxyConfig, RegisterMap, configure_logging"
  - phase: 01-core-proxy
    plan: 02
    provides: "RegisterCache with holding/input datablocks, LuxtronikClient with async read/write"
provides:
  - build_modbus_server() creating pymodbus ModbusTcpServer with ModbusDeviceContext (FC3/FC4/FC6/FC16)
  - PollingEngine with asyncio.Lock-serialized Luxtronik access, write queue draining, per-register rate limiting
  - main() async entry point wiring all components with SIGTERM graceful shutdown
  - cli() console entry point with --config argument
  - luxtronik2-modbus-proxy console script in pyproject.toml
affects: [01-04]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "build_modbus_server() pattern: ModbusDeviceContext(hr=, ir=) + ModbusServerContext(devices=, single=True)"
    - "PollingEngine uses asyncio.Lock to serialize all Luxtronik TCP access (prevents concurrent socket corruption)"
    - "Poll cycle order: drain writes first -> read -> update cache -> mark fresh (writes visible in same cycle)"
    - "Per-register write rate limiting via _write_timestamps dict[int, float] + time.time()"
    - "main.py SIGTERM handler: asyncio.create_task(shutdown()) inside loop.add_signal_handler()"
    - "serve_forever(background=False) as create_task for concurrent server + polling"

key-files:
  created:
    - src/luxtronik2_modbus_proxy/modbus_server.py
    - src/luxtronik2_modbus_proxy/polling_engine.py
    - src/luxtronik2_modbus_proxy/main.py
  modified:
    - pyproject.toml (added [project.scripts] console entry point)

key-decisions:
  - "ModbusDeviceContext (not ModbusSlaveContext) and devices= (not slaves=): pymodbus 3.x API — enforced in modbus_server.py"
  - "Poll cycle: sleep first, then poll — allows Modbus server to start serving clients before first Luxtronik connection"
  - "Write rate limiting uses time.time() float timestamps per register address, not a global counter"
  - "SIGTERM handler wraps shutdown() in asyncio.create_task() to schedule coroutine from sync signal handler"
  - "FC16 multi-register writes: only first value used for rate-limited upstream forwarding (single register write pattern)"

patterns-established:
  - "Pattern: build_modbus_server() single-function builder returning unconfigured ModbusTcpServer"
  - "Pattern: PollingEngine._drain_and_write() collects all queue items first, then applies rate limiting batch"
  - "Pattern: shutdown() cancels polling task, awaits server.shutdown(), then cancels server task (ordering matters)"
  - "Pattern: main.py component wiring order: register_map -> write_queue -> cache -> client -> engine -> server"

requirements-completed: [PROTO-01, PROTO-03, WRITE-03, OBS-02]

# Metrics
duration: 2min
completed: 2026-04-04
---

# Phase 01 Plan 03: Modbus Server, Polling Engine, and Main Entry Point Summary

**pymodbus ModbusTcpServer with ModbusDeviceContext (FC3/FC4/FC6/FC16), asyncio polling loop with per-register write rate limiting (T-03-01), and main.py entry point wiring all components with SIGTERM graceful shutdown — proxy is now a complete runnable application.**

## Performance

- **Duration:** ~2 minutes
- **Started:** 2026-04-04T19:00:44Z
- **Completed:** 2026-04-04T19:02:44Z
- **Tasks:** 2 of 2
- **Files modified:** 3 created, 1 modified

## Accomplishments

### Task 1: Modbus TCP server builder

- `build_modbus_server(cache, config) -> ModbusTcpServer`:
  - `ModbusDeviceContext(hr=cache.holding_datablock, ir=cache.input_datablock)` wires FC3/FC6/FC16 to holding registers and FC4 to input registers
  - `ModbusServerContext(devices=device_context, single=True)` — uses pymodbus 3.x API (`devices=` not `slaves=`, `ModbusDeviceContext` not `ModbusSlaveContext`)
  - Logs server configuration at INFO level with bind address and port
  - All docstrings explain the FC code routing and API change rationale

### Task 2: Polling engine and main.py entry point

- `PollingEngine`:
  - `asyncio.Lock()` serializes all Luxtronik TCP access (prevents concurrent read/write socket corruption)
  - `run_forever()`: sleep first → `_poll_cycle()` with try/except that catches transient errors and continues (T-03-02)
  - `_poll_cycle()`: drain writes → `async_read()` → `update_cache_from_read()` → `mark_fresh()` → on exception: `mark_stale()` + re-raise
  - `_drain_and_write()`: non-blocking queue drain → deduplicate by address → rate limit check per register → batch `async_write()` → update `_write_timestamps`
  - Write rate limiting: `time.time() - last_write < write_rate_limit` → log WARNING `write_rate_limited` with seconds remaining and skip

- `main()`:
  - Loads config, configures logging, creates all components in dependency order
  - Warns if `poll_interval < 15s` about HA BenPru contention
  - SIGTERM handler via `loop.add_signal_handler()` + `asyncio.create_task(shutdown())`
  - `asyncio.gather(polling_task, server_task)` runs both tasks concurrently

- `cli()`:
  - argparse with `--config` (default `/app/config.yaml` for Docker)
  - `asyncio.run(main())` with `KeyboardInterrupt` → `sys.exit(0)` (clean CTRL+C)

- `pyproject.toml`: added `[project.scripts]` with `luxtronik2-modbus-proxy = "luxtronik2_modbus_proxy.main:cli"`

## Test Results

```
29 passed in 0.08s
```

All 29 existing unit tests pass (6 config + 10 register cache + 13 register map). No new unit tests added in this plan (Plan 04 scope: integration tests with mock Luxtronik server).

## Task Commits

Each task was committed atomically:

1. **Task 1: Modbus TCP server builder** - `dad93a7` (feat)
2. **Task 2: Polling engine, main.py, and console script** - `8281bbe` (feat)

## Files Created/Modified

- `src/luxtronik2_modbus_proxy/modbus_server.py` - `build_modbus_server()` creating pymodbus async TCP server
- `src/luxtronik2_modbus_proxy/polling_engine.py` - `PollingEngine` with rate-limited write queue draining
- `src/luxtronik2_modbus_proxy/main.py` - Entry point wiring all components with SIGTERM shutdown
- `pyproject.toml` - Added `[project.scripts]` console entry point

## Decisions Made

1. **Poll cycle: sleep first, then poll** — The proxy starts serving Modbus clients immediately from cached values without blocking on an initial Luxtronik connection. This makes startup faster and avoids failing clients that connect before the first Luxtronik read.

2. **FC16 multi-register writes: use first value only** — The polling engine's write forwarding takes `values[0]` from queued writes. FC16 writes to a single Luxtronik parameter always use a single 16-bit value. Multi-value FC16 writes to non-contiguous registers are rejected at the datablock level.

3. **SIGTERM handler: `asyncio.create_task()` in sync callback** — `loop.add_signal_handler()` receives a synchronous callback. To call `await server.shutdown()`, we schedule `shutdown()` as a task. This is the correct pattern for triggering async shutdown from a sync signal handler.

4. **`ModbusDeviceContext` (not `ModbusSlaveContext`)** — The pymodbus 3.x API change was enforced in both the implementation and in docstrings explaining the pitfall, to avoid future regressions.

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None — all imports verified, all existing tests pass.

## Known Stubs

None. All three modules contain complete operational logic. The polling engine will make live network connections when `run_forever()` is called with a real `LuxtronikClient`.

## Threat Flags

None. No new network endpoints beyond the Modbus TCP server (already in the threat model). The SIGTERM handler does not introduce a new attack surface.

Threat mitigations implemented as required by the plan's threat model:
- T-03-01 (DoS via write flooding): per-register rate limiting in `PollingEngine._drain_and_write()`
- T-03-02 (DoS via upstream errors): try/except in `run_forever()` prevents proxy crash on transient Luxtronik failures
- T-03-03 (tampering via write queue): writes already validated by `ProxyHoldingDataBlock.async_setValues` in Plan 02; polling engine trusts queue contents

## Next Phase Readiness

- Proxy is a complete, runnable application: `luxtronik2-modbus-proxy --config config.yaml`
- All 4 components are wired: register map → cache → client → engine + server
- Plan 04 (integration tests + Docker) can now write mock-Luxtronik integration tests and containerize
- STATE.md blocker from earlier phases remains: SG-ready parameter ID combinations need hardware validation (Phase 2 scope)

## Self-Check: PASSED

All key files exist and all commits are present in git history.

**Files verified:** modbus_server.py, polling_engine.py, main.py, pyproject.toml

**Commits verified:** dad93a7 (modbus_server), 8281bbe (polling_engine + main)

---
*Phase: 01-core-proxy*
*Completed: 2026-04-04*

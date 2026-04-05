---
phase: 01-core-proxy
plan: 04
subsystem: infra
tags: [docker, integration-test, pymodbus, mock, deployment, config]

# Dependency graph
requires:
  - phase: 01-core-proxy
    plan: 03
    provides: "build_modbus_server, PollingEngine, main.py, all 5 proxy components wired"
provides:
  - config.example.yaml with all config options, placeholder IP, inline comments
  - Dockerfile: multi-stage python:3.12-slim build with tini and non-root proxy user (UID 1000)
  - docker-compose.yml: mounts config.yaml read-only, exposes 502:502, restart unless-stopped
  - ProxyDeviceContext(ModbusDeviceContext) routing FC6/FC16 writes through async validation
  - MockLuxtronikClient fixture for in-process integration testing
  - 4 integration tests covering FC3 read, FC4 read, FC6 valid write, FC6 invalid write rejection
  - All 33 tests passing (29 unit + 4 integration)
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "ProxyDeviceContext overrides async_setValues to route FC6/FC16 through ProxyHoldingDataBlock.async_setValues"
    - "MockLuxtronikClient overrides update_cache_from_read to populate cache directly without luxtronik library"
    - "proxy_stack fixture: runs one manual poll cycle before server start, no sleep needed for test isolation"
    - "Integration tests use port 15502 to avoid requiring root (>1024)"
    - "Docker multi-stage: builder copies src+pyproject.toml, runtime stage copies /install from builder"

key-files:
  created:
    - config.example.yaml
    - Dockerfile
    - docker-compose.yml
    - tests/integration/__init__.py
    - tests/integration/test_proxy_mock.py
  modified:
    - src/luxtronik2_modbus_proxy/register_cache.py (added ProxyDeviceContext)
    - src/luxtronik2_modbus_proxy/modbus_server.py (use ProxyDeviceContext)

key-decisions:
  - "ProxyDeviceContext at context layer (not datablock layer) is the correct intercept point for async writes in pymodbus 3.x"
  - "MockLuxtronikClient.update_cache_from_read populates cache directly — no need to mock luxtronik.Luxtronik internals"
  - "Dockerfile uses tini as PID 1 for SIGTERM forwarding (T-04-03); matches pitfall 8 guidance"
  - "config.example.yaml uses 192.168.x.x placeholder — pre-commit hook enforces no real IPs"

patterns-established:
  - "Pattern: ProxyDeviceContext.async_setValues checks func_code in _HOLDING_FC frozenset then delegates to hr block"
  - "Pattern: MockLuxtronikClient for integration tests — override async_read + update_cache_from_read + async_write"
  - "Pattern: proxy_stack fixture with asyncio.sleep(0.1) to allow server socket to bind before test clients connect"

requirements-completed: [DEPLOY-01, DEPLOY-03, PROTO-05]

# Metrics
duration: 5min
completed: 2026-04-04
---

# Phase 01 Plan 04: Docker Deployment, Config Example, and Integration Tests Summary

**Docker multi-stage build (python:3.12-slim, tini, non-root user), config.example.yaml with placeholder 192.168.x.x, and 4 integration tests proving the full proxy stack read/write flow with a mock Luxtronik client — including a critical auto-fix for write validation bypass.**

## Performance

- **Duration:** ~5 minutes
- **Started:** 2026-04-04T19:06:46Z
- **Completed:** 2026-04-04T19:11:55Z
- **Tasks:** 2 of 3 (Task 3 is human-verify checkpoint)
- **Files modified:** 5 created, 2 modified

## Accomplishments

### Task 1: Docker deployment and config.example.yaml

- `config.example.yaml`: all 8 config fields documented with inline comments; `luxtronik_host: "192.168.x.x"` placeholder only; `enable_writes: false` safety default; `write_rate_limit: 60` NAND flash protection
- `Dockerfile`: multi-stage build; builder stage installs to `/install` prefix; runtime stage installs `tini` for SIGTERM forwarding (T-04-03), creates `proxy` user (UID 1000) for T-04-02, copies `/install` from builder, `EXPOSE 502`
- `docker-compose.yml`: mounts `./config.yaml:/app/config.yaml:ro`, `502:502`, `restart: unless-stopped`
- Verified: no real IPs in committed files; config.example.yaml parses correctly with expected values

### Task 2: Integration test with mock Luxtronik server (TDD)

Built full proxy stack in-process on test port 15502 with `MockLuxtronikClient`:

- `test_read_holding_register`: FC3 read of HeatingMode at address 3 returns mock value 2
- `test_read_input_register`: FC4 read of flow temperature at address 10 returns mock value 215
- `test_write_valid_value`: FC6 write of value 2 to address 3 succeeds; write appears in queue
- `test_write_invalid_value`: FC6 write of value 99 to address 3 returns Modbus exception (ILLEGAL_VALUE)

All 33 tests pass (29 unit + 4 integration).

## Test Results

```
33 passed in 0.98s
```

## Task Commits

1. **Task 1: Docker deployment artifacts** - `f535e0e` (feat)
2. **Task 2: Integration tests RED** - `7227d24` (test)
3. **Task 2: Write validation fix GREEN** - `e047263` (fix)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Write validation was silently bypassed: ProxyHoldingDataBlock.async_setValues never called**

- **Found during:** Task 2 integration test run (test_write_valid_value and test_write_invalid_value both failed)
- **Issue:** pymodbus 3.12.1 calls `context.async_setValues` on the `ModbusServerContext`. `ModbusServerContext.async_setValues` delegates to `ModbusDeviceContext.async_setValues`, which is inherited from `ModbusBaseDeviceContext` — this base method simply calls the synchronous `self.setValues`. `ModbusDeviceContext.setValues` then calls `self.store['h'].setValues(address+1, values)`, which goes to `ModbusSequentialDataBlock.setValues` (the base class sync method) — completely bypassing `ProxyHoldingDataBlock.async_setValues`. The 3 validation gates (enable_writes, is_writable, validate_write_value) and the write queue never ran. Any Modbus client could write any value to any address regardless of configuration.
- **Fix:** Added `ProxyDeviceContext(ModbusDeviceContext)` in `register_cache.py` that overrides `async_setValues` to check if `func_code in _HOLDING_FC` and, if so, calls `await self.store['h'].async_setValues(address + 1, values)` directly. Updated `modbus_server.py` to use `ProxyDeviceContext` instead of `ModbusDeviceContext`.
- **Security impact:** High — write validation is a security boundary (T-02-01, T-02-02). All writes to the Luxtronik controller were unvalidated before this fix.
- **Files modified:** `src/luxtronik2_modbus_proxy/register_cache.py`, `src/luxtronik2_modbus_proxy/modbus_server.py`
- **Commit:** `e047263`

## Known Stubs

None. The integration tests use real pymodbus server and client code. The only mock is the Luxtronik protocol client, which is correctly replaced by `MockLuxtronikClient` for testing without hardware.

## Threat Flags

None beyond what was already in the threat model. The `ProxyDeviceContext` fix resolves T-02-01 and T-02-02 which were previously not functioning correctly.

Threat mitigations confirmed working by integration tests:
- T-04-01 (config.example.yaml placeholder): `192.168.x.x` confirmed in config.example.yaml
- T-04-02 (non-root user): `USER proxy` in Dockerfile
- T-04-03 (tini PID 1): `ENTRYPOINT ["tini", "--"]` in Dockerfile
- T-02-01/T-02-02 (write validation): now correctly enforced via ProxyDeviceContext

## Self-Check: PASSED

All key files exist and all commits are present in git history.

**Files verified:** config.example.yaml, Dockerfile, docker-compose.yml, tests/integration/__init__.py, tests/integration/test_proxy_mock.py, src/luxtronik2_modbus_proxy/register_cache.py (ProxyDeviceContext), src/luxtronik2_modbus_proxy/modbus_server.py (ProxyDeviceContext)

**Commits verified:** f535e0e (feat: Docker artifacts), 7227d24 (test: integration tests RED), e047263 (fix: ProxyDeviceContext write validation)

---
*Phase: 01-core-proxy*
*Completed: 2026-04-04*

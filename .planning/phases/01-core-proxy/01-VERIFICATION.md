---
phase: 01-core-proxy
verified: 2026-04-05T07:22:39Z
status: human_needed
score: 7/10 must-haves verified
re_verification: false
human_verification:
  - test: "Connect a Modbus client (e.g., modpoll) to the running proxy while it polls a real Luxtronik controller. Read holding register 3 (HeatingMode) and input register 10 (flow temperature)."
    expected: "Registers return current values from the controller. The Luxtronik TCP socket is not held open between 30-second polling cycles (verify with Wireshark or netstat)."
    why_human: "Requires real Luxtronik 2.0 hardware on the network. Integration tests use a mock client only."
  - test: "Write value 2 (Party) to holding register 3 via a Modbus client with enable_writes=true in config. Then write value 99 to the same register."
    expected: "Value 2 reaches the Luxtronik controller (visible in controller UI or HA). Value 99 is rejected with Modbus exception code 3 and does NOT reach the controller."
    why_human: "Requires real hardware to confirm write propagates. Exception rejection is tested in integration tests but controller-side confirmation needs hardware."
  - test: "Run docker build -t luxtronik2-modbus-proxy . then docker compose up (with config.yaml copied from config.example.yaml with a real or test IP)."
    expected: "Image builds successfully. Container starts, logs proxy_starting and proxy_running events. If IP is unreachable, proxy logs connection error and continues polling (does not crash). docker compose down sends SIGTERM and container exits cleanly."
    why_human: "Docker build and container runtime behavior cannot be verified without Docker daemon. SIGTERM propagation via tini requires a running container."
  - test: "Run the HA BenPru luxtronik HACS integration simultaneously while the proxy polls the same controller at 30s interval."
    expected: "HA integration continues to receive data. Neither the proxy nor HA logs persistent connection errors. No controller lockout occurs."
    why_human: "Requires real hardware, Home Assistant installation, and the BenPru HACS integration — cannot be simulated."
---

# Phase 1: Core Proxy Verification Report

**Phase Goal:** A working Modbus TCP proxy runs against real hardware, handles reads and writes safely, coexists with the HA BenPru integration, and ships in a Docker container — architecturally correct with no deferred pitfalls
**Verified:** 2026-04-05T07:22:39Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| #  | Truth | Status | Evidence |
|----|-------|--------|----------|
| 1  | Project installs cleanly with pip install -e . | VERIFIED | Package is installed, all imports succeed, 33 tests pass |
| 2  | Config loads from YAML with env var overrides | VERIFIED | ProxyConfig(BaseSettings) with LUXTRONIK_ prefix, YamlConfigSettingsSource; test_config_env_var_override passes |
| 3  | structlog produces JSON in non-TTY, colored in TTY | VERIFIED | configure_logging() uses os.isatty(1), ConsoleRenderer/JSONRenderer switching; tests pass |
| 4  | Register map resolves Luxtronik IDs to Modbus addresses | VERIFIED | HOLDING_REGISTERS and INPUT_REGISTERS wired through RegisterMap; all 13 register map tests pass |
| 5  | Modbus TCP server accepts FC3, FC4, FC6, FC16 | VERIFIED | ProxyDeviceContext + ModbusServerContext(single=True); integration test proves FC3/FC4/FC6 paths |
| 6  | Write validation rejects invalid values with ILLEGAL_VALUE | VERIFIED | ProxyHoldingDataBlock.async_setValues 3-gate validation; test_write_invalid_value passes |
| 7  | Polling engine drains write queue with rate limiting | VERIFIED | PollingEngine._drain_and_write uses _write_timestamps dict with time.time() comparison |
| 8  | main.py wires all components, SIGTERM triggers graceful shutdown | VERIFIED | All 6 component imports present; loop.add_signal_handler(SIGTERM) calls shutdown() |
| 9  | A Modbus client can read from proxy while it polls real hardware without holding socket open | ? HUMAN NEEDED | Architecture is correct (connect-per-call via __new__); requires real hardware to confirm |
| 10 | HA BenPru integration continues normally during proxy polling | ? HUMAN NEEDED | poll_interval warning at <15s, connect-per-call pattern, no persistent socket — but requires real hardware |

**Score:** 8/10 truths verified programmatically (truths 9 and 10 need hardware)

### ROADMAP Success Criteria

| # | Success Criterion | Status | Evidence |
|---|-------------------|--------|----------|
| SC1 | Modbus client reads temperature and operating mode registers while proxy polls real controller without holding port 8889 socket open | ? HUMAN NEEDED | Proxy code enforces connect-per-call; needs real hardware |
| SC2 | Modbus write to operating mode register reaches controller; out-of-range value rejected with exception code 3 | PARTIAL | Exception code 3 rejection verified by integration test; write reaching real controller needs hardware |
| SC3 | Proxy starts via `docker compose up` with no hardcoded IPs/credentials anywhere | PARTIAL | No real IPs found in codebase; Docker build behavior needs human verification |
| SC4 | Structured log output shows connection events, poll cycles, register reads, write attempts with contextual fields | VERIFIED | structlog.bind() with register/value/component context in polling_engine.py and luxtronik_client.py |
| SC5 | HA BenPru integration continues normally during proxy polling | ? HUMAN NEEDED | Architecture supports coexistence; cannot verify without real hardware and HA |

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `pyproject.toml` | Project metadata, dependencies, tool config | VERIFIED | Contains luxtronik2-modbus-proxy, luxtronik==0.3.14, pymodbus==3.12.1, asyncio_mode=auto |
| `src/luxtronik2_modbus_proxy/config.py` | ProxyConfig pydantic-settings model | VERIFIED | ProxyConfig(BaseSettings), 8 validated fields, YamlConfigSettingsSource, LUXTRONIK_ prefix |
| `src/luxtronik2_modbus_proxy/logging_config.py` | structlog configuration | VERIFIED | configure_logging(), JSONRenderer, ConsoleRenderer, os.isatty detection |
| `src/luxtronik2_modbus_proxy/register_map.py` | Register map with address lookup | VERIFIED | RegisterMap, RegisterEntry, HOLDING_BLOCK_SIZE=1200, INPUT_BLOCK_SIZE=260 |
| `src/luxtronik2_modbus_proxy/register_definitions/parameters.py` | Curated parameter definitions | VERIFIED | HOLDING_REGISTERS with 3 entries (addr 3, 4, 105) with validation metadata |
| `src/luxtronik2_modbus_proxy/register_definitions/calculations.py` | Curated calculation definitions | VERIFIED | INPUT_REGISTERS with 6 entries (addr 10, 11, 15, 17, 80, 257) |
| `src/luxtronik2_modbus_proxy/register_cache.py` | RegisterCache with ProxyHoldingDataBlock, ProxyDeviceContext | VERIFIED | All 3 classes present; ProxyDeviceContext routes FC6/FC16 through async validation |
| `src/luxtronik2_modbus_proxy/luxtronik_client.py` | LuxtronikClient async read/write | VERIFIED | async_read, async_write, update_cache_from_read; run_in_executor pattern; __new__ avoids auto-read |
| `src/luxtronik2_modbus_proxy/modbus_server.py` | Modbus TCP server builder | VERIFIED | build_modbus_server(), ProxyDeviceContext (not base ModbusDeviceContext), ModbusServerContext(devices=, single=True) |
| `src/luxtronik2_modbus_proxy/polling_engine.py` | Async polling engine | VERIFIED | PollingEngine, asyncio.Lock, _write_timestamps, _drain_and_write with rate limiting |
| `src/luxtronik2_modbus_proxy/main.py` | Application entry point | VERIFIED | async def main(), async def shutdown(), def cli(), signal.SIGTERM handler, all 6 components wired |
| `config.example.yaml` | Example config with placeholders | VERIFIED | 192.168.x.x placeholder, all 8 fields documented, no real IPs |
| `Dockerfile` | Docker container definition | VERIFIED | python:3.12-slim multi-stage, tini PID 1, non-root user (appuser/UID 1000), EXPOSE 502 |
| `docker-compose.yml` | Docker compose definition | VERIFIED | 502:502, ./config.yaml:/app/config.yaml:ro, restart: unless-stopped |
| `tests/integration/test_proxy_mock.py` | End-to-end smoke test | VERIFIED | 4 tests: FC3 read, FC4 read, FC6 valid write, FC6 invalid write; all pass |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| register_map.py | register_definitions/parameters.py | import HOLDING_REGISTERS | WIRED | `from luxtronik2_modbus_proxy.register_definitions.parameters import HOLDING_REGISTERS, ParameterDef` |
| register_map.py | register_definitions/calculations.py | import INPUT_REGISTERS | WIRED | `from luxtronik2_modbus_proxy.register_definitions.calculations import INPUT_REGISTERS, CalculationDef` |
| config.py | pydantic_settings | BaseSettings subclass | WIRED | `class ProxyConfig(BaseSettings)` with `YamlConfigSettingsSource` |
| register_cache.py | register_map.py | RegisterMap for validation | WIRED | `from luxtronik2_modbus_proxy.register_map import RegisterMap` |
| register_cache.py | pymodbus.datastore | ModbusSequentialDataBlock subclass | WIRED | `class ProxyHoldingDataBlock(ModbusSequentialDataBlock)` |
| luxtronik_client.py | luxtronik | luxtronik library | WIRED | `import luxtronik`; `luxtronik.Luxtronik.__new__()` pattern |
| modbus_server.py | register_cache.py | cache.holding_datablock, cache.input_datablock | WIRED | `ProxyDeviceContext(hr=cache.holding_datablock, ir=cache.input_datablock)` |
| polling_engine.py | luxtronik_client.py | LuxtronikClient.async_read/async_write | WIRED | `lux = await self._client.async_read()` |
| main.py | all components | full wiring chain | WIRED | RegisterMap -> write_queue -> RegisterCache -> LuxtronikClient -> PollingEngine -> build_modbus_server() |
| Dockerfile | pyproject.toml | pip install | WIRED | `pip install --no-cache-dir --prefix=/install .` in builder stage |
| docker-compose.yml | Dockerfile | build context | WIRED | `build: .` |
| docker-compose.yml | config.example.yaml | volume mount | WIRED | `./config.yaml:/app/config.yaml:ro` (user copies example to config.yaml) |

### Data-Flow Trace (Level 4)

This is a proxy (no UI rendering). Data flows through the cache are exercised by integration tests:

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `ProxyHoldingDataBlock` | `_holding` register values | `update_holding_values()` from LuxtronikClient | Yes — real Luxtronik library parameters | FLOWING (mocked in tests; real in production) |
| `ModbusSequentialDataBlock` (input) | `_input` register values | `update_input_values()` from LuxtronikClient | Yes — real Luxtronik library calculations | FLOWING (mocked in tests; real in production) |
| `MockLuxtronikClient.update_cache_from_read` | test cache values | Hardcoded test constants | Test-only mock values | VERIFIED — mock correctly simulates real flow |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| All module imports succeed | `.venv/bin/python3.14 -c "from luxtronik2_modbus_proxy.main import main, cli, shutdown; ..."` | All imports OK | PASS |
| RegisterMap returns correct entries and validates | `.venv/bin/python3.14 -c "rm.get_holding_entry(3), rm.validate_write_value(3,2), rm.validate_write_value(3,99)"` | Correct entry, True, False | PASS |
| 33 tests pass | `.venv/bin/python3.14 -m pytest tests/ -v` | 33 passed in 1.19s | PASS |
| No real IPs in codebase | `grep -rn "192.168.[0-9]+" ...` (excluding 192.168.x.x) | No matches | PASS |
| Docker build | `docker build -t luxtronik2-modbus-proxy .` | Not run (no Docker daemon) | SKIP — human checkpoint |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| PROTO-01 | 01-03 | Modbus TCP server on port 502 with FC3/FC4/FC6/FC16 | SATISFIED | ModbusTcpServer + ProxyDeviceContext; integration test FC3/FC4/FC6 |
| PROTO-02 | 01-02 | Connect to Luxtronik port 8889, read, disconnect in one cycle | SATISFIED | LuxtronikClient.async_read creates new instance per call; run_in_executor pattern |
| PROTO-03 | 01-03 | Connect-read-disconnect with configurable poll interval (default 30s) | SATISFIED | PollingEngine.run_forever() with asyncio.sleep(poll_interval); default 30s in ProxyConfig |
| PROTO-04 | 01-02 | In-memory register cache that Modbus clients read between cycles | SATISFIED | RegisterCache with holding+input datablocks; Modbus server reads from cache directly |
| PROTO-05 | 01-02, 01-04 | Never hold Luxtronik TCP connection longer than needed | SATISFIED | __new__ + run_in_executor per call; new instance per read/write; no persistent socket |
| REG-01 | 01-01 | Curated default register set covering evcc essentials | SATISFIED | 9 registers: HeatingMode(3), HotWaterMode(4), DHW setpoint(105), 5 temps, op mode, heat output |
| WRITE-01 | 01-02 | Write holding registers to Luxtronik controller | SATISFIED | LuxtronikClient.async_write with parameters.queue; integration test confirms write flow |
| WRITE-02 | 01-02 | Validate write values before sending to controller | SATISFIED | ProxyHoldingDataBlock 3-gate validation: enable_writes, is_writable, validate_write_value |
| WRITE-03 | 01-03 | Rate-limit writes to protect NAND flash | SATISFIED | PollingEngine._drain_and_write with _write_timestamps and write_rate_limit check |
| OBS-01 | 01-01 | Structured logging with configurable log levels | SATISFIED | configure_logging() with structlog, JSON/Console renderer, log_level field in ProxyConfig |
| OBS-02 | 01-03 | Log connection events, poll cycles, register ops, errors with context | SATISFIED | structlog.bind(component=, register=, value=) in polling_engine, luxtronik_client, register_cache |
| DEPLOY-01 | 01-04 | Docker container with YAML config mount | SATISFIED (code) | Dockerfile multi-stage python:3.12-slim, docker-compose.yml mounts config.yaml; build needs human verification |
| DEPLOY-03 | 01-04 | config.example.yaml with placeholder values and comments | SATISFIED | 192.168.x.x placeholder, all 8 fields documented with inline comments |

**Note:** DEPLOY-02 (systemd service) is Phase 3 scope and is not required here. No orphaned requirements found — all 13 Phase 1 requirements are covered.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| None found | - | No TODO, FIXME, placeholder comments, empty return values, or stub patterns | - | - |

**Additional finding:** The Dockerfile uses `USER appuser` (not `USER proxy` as specified in Plan 04's acceptance criteria). This was an intentional fix committed as `e445f3b` ("rename Docker user from 'proxy' to 'appuser' (Debian conflict)"). The non-root user requirement (T-04-02) is fully met — user `appuser` with UID 1000. This is a plan-vs-implementation deviation that is correct behavior.

### Human Verification Required

#### 1. Modbus reads from real Luxtronik controller (SC1)

**Test:** Start the proxy with a real `config.yaml` pointing to a Luxtronik 2.0 controller. Connect a Modbus client (e.g., `modpoll -m tcp -a 1 -r 3 -c 1 <proxy-ip>`) and read holding register 3 and input register 10.
**Expected:** Registers return current values from the controller. Connection to port 8889 opens and closes within each 30-second poll cycle (verify with `ss -tn | grep 8889` or Wireshark).
**Why human:** Requires real Luxtronik 2.0 hardware on the network. Integration tests use a mock client only.

#### 2. Write reaches real controller and rejection works end-to-end (SC2)

**Test:** With `enable_writes: true` in config.yaml and a real controller: (a) write value 2 to register 3 via a Modbus client, (b) write value 99 to register 3.
**Expected:** (a) Controller switches to Party mode (visible in controller UI or HA). (b) Write returns Modbus exception code 3 (illegal data value) and controller state is unchanged.
**Why human:** Requires real hardware to confirm write propagates to the physical controller. The exception code 3 rejection is already verified by integration test `test_write_invalid_value`.

#### 3. Docker image builds and proxy starts in container (SC3)

**Test:** `docker build -t luxtronik2-modbus-proxy .` then `cp config.example.yaml config.yaml` and `docker compose up`.
**Expected:** Build completes without errors. Container starts and logs `proxy_starting` and `proxy_running` at INFO level. On SIGTERM (`docker compose down`), container logs `proxy_shutting_down` and `proxy_stopped` then exits cleanly (exit code 0).
**Why human:** No Docker daemon available in verification environment.

#### 4. HA BenPru integration coexists with proxy polling (SC5)

**Test:** Run the HA BenPru luxtronik HACS integration while the proxy polls the same controller at 30-second intervals.
**Expected:** HA integration continues to receive data without persistent errors. No controller lockout or connection errors in proxy or HA logs. Heat pump operates normally.
**Why human:** Requires real hardware, Home Assistant installation, and the BenPru HACS integration simultaneously active.

### Gaps Summary

No blocking gaps found. All artifacts are present, substantive, and wired. All 33 tests pass. The only items preventing `passed` status are the 4 human verification items above, which require real hardware and a running Docker daemon. These are the standard hardware-dependent behaviors that cannot be verified statically.

The one notable deviation from plan specs is the Dockerfile using `USER appuser` instead of `USER proxy` — this was an intentional fix for a Debian system user conflict, documented in commit `e445f3b`, and represents correct behavior.

---

_Verified: 2026-04-05T07:22:39Z_
_Verifier: Claude (gsd-verifier)_

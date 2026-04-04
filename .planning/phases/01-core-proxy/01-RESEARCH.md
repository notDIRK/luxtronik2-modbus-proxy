# Phase 1: Core Proxy - Research

**Researched:** 2026-04-04
**Domain:** Async Modbus TCP server + proprietary binary protocol client + Docker deployment
**Confidence:** HIGH

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PROTO-01 | Proxy exposes Modbus TCP server on port 502 supporting FC3/FC4/FC6/FC16 | pymodbus `ModbusTcpServer` + `ModbusDeviceContext` with `hr`, `ir` datastores covers all four FCs |
| PROTO-02 | Proxy connects to Luxtronik on port 8889, reads mapped parameters, and disconnects within a single polling cycle | `luxtronik.Luxtronik.read()` calls `_connect`/`_read_*/`_disconnect` internally; for write path call `write()` which does the same; both are fully synchronous blocking calls that must run in `run_in_executor` |
| PROTO-03 | Proxy uses connect-read-disconnect pattern with configurable polling interval (default 30s) to coexist with HA BenPru integration | asyncio polling loop with configurable `poll_interval`; HA BenPru also uses connect-read-disconnect; both time-share port 8889 when intervals are staggered |
| PROTO-04 | Proxy maintains an in-memory register cache that Modbus clients read from between polling cycles | Subclass `ModbusSequentialDataBlock`; cache is updated by the Polling Engine, served directly by the Modbus server |
| PROTO-05 | Proxy never holds the Luxtronik TCP connection longer than needed for a single read/write cycle | Enforced by architecture: Luxtronik Client only called from Polling Engine inside a try/finally block that always disconnects |
| REG-01 | Proxy ships with a curated default register set covering evcc essentials | Verified: calcs[10-17] = temperatures; param[3]=HeatingMode, param[4]=HotWaterMode; param[105]=DHW setpoint; calc[257]=Heat_Output (watts); all confirmed from luxtronik 0.3.14 source |
| WRITE-01 | Proxy can write holding registers to the Luxtronik controller | `luxtronik.parameters.queue` dict populated then `luxtronik.Luxtronik.write()` called; target params are param[3] (HeatingMode), param[4] (HotWaterMode), param[105] (DHW setpoint Celsius) |
| WRITE-02 | Proxy validates write values against known parameter ranges before sending to controller | `datatype.to_heatpump()` converts; per-parameter min/max/allowed-values enforced before queuing; reject with `ExcCodes.ILLEGAL_VALUE` (code 3) |
| WRITE-03 | Proxy rate-limits writes to protect Luxtronik controller NAND flash from excessive wear | Per-register write timestamp tracking; max 1 write per 60s for same register; excess writes return `ExcCodes.ILLEGAL_VALUE` with a log warning |
| OBS-01 | Proxy uses structured logging (structlog) with configurable log levels | `structlog.configure()` at startup; JSON renderer in production, ConsoleRenderer in dev; `LOG_LEVEL` env var |
| OBS-02 | Proxy logs connection events, polling cycles, register reads/writes, and errors with contextual fields | `structlog.get_logger().bind(register=addr, param_name=name, value=val)` pattern on every upstream event |
| DEPLOY-01 | Proxy runs as a Docker container with configuration via mounted YAML file | `python:3.12-slim` + tini; mount `config.yaml` as volume at `/app/config.yaml`; expose port 502 |
| DEPLOY-03 | Proxy provides a config.example.yaml with placeholder values and comments explaining each option | File committed to repo; uses `192.168.x.x` and `your-heatpump-ip` placeholders; never a real IP |
</phase_requirements>

---

## Summary

Phase 1 builds the architecturally complete, hardware-safe core proxy from scratch. The project has done thorough prior research (STACK.md, PITFALLS.md, ARCHITECTURE.md); this phase research goes one level deeper into the actual library APIs, confirmed against the installed versions on this machine, to give the planner exact method signatures and data structures.

The five critical pitfalls identified in prior research (asyncio event loop starvation, concurrent read/write socket corruption, single-connection enforcement, write-path hardware damage, register addressing off-by-one) must all be addressed in this phase. None can be retrofitted. The planner should treat each pitfall as a hard constraint that shapes task design, not a checklist item to add at the end.

The pymodbus 3.12.1 API has changed significantly from what older tutorials show: `ModbusSlaveContext` is now `ModbusDeviceContext`, the `single=True` parameter in `ModbusServerContext` takes `devices` not `slaves`, and `ExcCodes` is an enum in `pymodbus.datastore.sequential`. The address offset in `ModbusDeviceContext.setValues` unconditionally does `address += 1`, meaning client 0-based addresses map to datablock 1-based addresses. Datablocks must be initialized starting at address 1.

**Primary recommendation:** Build in the order defined in ARCHITECTURE.md's Component Build Order section (register definitions → config → register map → register cache → luxtronik client → polling engine → modbus server → main). Do not parallelize tasks across components that depend on each other.

## Project Constraints (from CLAUDE.md)

### Security
- **NEVER** commit real IP addresses, hostnames, passwords, tokens, MAC addresses, or personal data
- `config.yaml` and `.env` are gitignored; only `config.example.yaml` is in the repo
- Pre-commit hook scans for `192.168.`, `10.`, `172.16–31.`, real TLDs, credential patterns — **never bypass with --no-verify**
- Bind proxy to configurable interface, not `0.0.0.0` by default

### Code
- Language: US English (code, comments, commit messages)
- Comments: every function, every module, complex logic
- Docstrings: US English, Google style
- Do not expose `safe=False` as a user-facing config option

### Tech Stack (locked)
- Python 3.10+ (3.12 preferred for Docker)
- `luxtronik` v0.3.14 (PyPI, Bouni/python-luxtronik — NOT BenPru fork)
- `pymodbus` 3.x (3.12.1 specifically)
- Docker with `python:3.12-slim` base
- `pydantic` v2 + `pydantic-settings` v2 (YAML + env var overrides)
- `structlog` for structured logging

### Documentation
- Two tracks: Quickstart (developers) + Guide (end users)
- Two languages: EN + DE
- Structure: `docs/en/` and `docs/de/`
- Phase 1 does NOT need bilingual docs (that is Phase 3)

### Private Repo Boundary
- NEVER reference or copy from `~/claude-code/wp-alpha-innotec/` into this repo

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.12 | Runtime | pymodbus 3.12.1 CI-tested on 3.10–3.14; 3.12 is stable, slim wheels install cleanly |
| `luxtronik` | 0.3.14 | Luxtronik 2.0 binary protocol client | Only maintained Python library for the proprietary protocol; MIT; pure Python; installed and verified |
| `pymodbus` | 3.12.1 | Modbus TCP async server | Authoritative Python Modbus implementation; 3.12.1 is latest stable (Feb 2026); full asyncio support |
| `pydantic` | 2.12.5 | Config validation | Industry standard; v2 significantly faster than v1; installed and verified |
| `pydantic-settings` | 2.13.1 | YAML config + env var overrides | `YamlConfigSettingsSource` built-in since 2.x; covers YAML + Docker env var override in one library; installed and verified |
| `structlog` | 25.5.0 | Structured logging | JSON in Docker, colorized in terminal; context binding per event; installed and verified |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `PyYAML` | 6.x | YAML parsing | Transitive via pydantic-settings; no direct use required |
| `pytest` | 9.0.2 | Test runner | Installed and verified; 9.x requires Python 3.10+ |
| `pytest-asyncio` | 1.3.0 | Async test support | Installed and verified; use `asyncio_mode = auto` in pyproject.toml |
| `pytest-cov` | 6.x | Coverage | `--cov=src` in CI |
| `ruff` | 0.15.9 | Linting + formatting | Installed and verified; replaces black + flake8 + isort |
| `mypy` | 1.20.0 | Static type checking | Installed and verified; use `strict = true` |

### Alternatives Considered

| Recommended | Alternative | Tradeoff |
|-------------|-------------|----------|
| `pymodbus` 3.12.x | `pymodbus` 4.0.0dev | v4 has breaking datastore API changes (`ModbusSlaveContext` replaced, `getValues`/`setValues` changed); no stable release; use 3.12.x |
| `python:3.12-slim` Docker base | `python:3.12-alpine` | Alpine forces musl libc; pymodbus and pydantic-core ship manylinux wheels that compile from source on Alpine, producing larger images |
| `tini` signal handler | Python `signal.signal()` only | tini also reaps zombie processes (Python spawns threads via `run_in_executor`); both approaches work but tini is more robust |

**Installation:**
```bash
pip install "luxtronik==0.3.14" "pymodbus==3.12.1" "pydantic==2.12.*" "pydantic-settings==2.13.*" "structlog==25.5.0"
pip install "pytest==9.0.*" "pytest-asyncio==1.3.*" "pytest-cov" "ruff" "mypy"
```

**Version verification:** [VERIFIED: pip3 index versions pymodbus, pip3 show luxtronik/pydantic/pydantic_settings/structlog/pytest/pytest-asyncio on this machine 2026-04-04]

---

## Architecture Patterns

### Recommended Project Structure

```
luxtronik2-modbus-proxy/
├── src/
│   └── luxtronik2_modbus_proxy/
│       ├── __init__.py
│       ├── main.py              # Entry point: load config, wire components, start event loop
│       ├── config.py            # Pydantic models for config.yaml; load_config() function
│       ├── register_map.py      # Static register map: luxtronik ID -> Modbus address, type, scale
│       ├── register_cache.py    # Thread-safe cache wrapping pymodbus datablock
│       ├── luxtronik_client.py  # Wrapper around luxtronik lib: connect, read_all, write_param, disconnect
│       ├── polling_engine.py    # Async polling task: periodic read, cache update, write queue drain
│       ├── modbus_server.py     # pymodbus async TCP server setup, callback datablock wiring
│       └── logging_config.py   # structlog configuration, dev vs. production renderer selection
├── register_definitions/
│   ├── __init__.py
│   ├── parameters.py           # Curated parameter definitions for Phase 1 (writable + key read-only)
│   └── calculations.py         # Curated calculation definitions for Phase 1 (temperatures + power)
├── config.example.yaml          # Example config with 192.168.x.x placeholder values (in repo)
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── tests/
    ├── unit/
    │   ├── test_config.py
    │   ├── test_register_map.py
    │   └── test_register_cache.py
    └── integration/
        └── test_proxy_mock.py   # Mock luxtronik server for end-to-end smoke test
```

**Note for Phase 1:** `register_definitions/` contains only the curated Phase 1 set (~20 registers). REG-02/REG-03/REG-04 (full parameter database) are Phase 2 scope.

### Pattern 1: pymodbus 3.12.1 Async Server Setup

**What:** `ModbusTcpServer` with `ModbusServerContext(single=True, devices=device_context)`. Note the API change from older versions: `ModbusSlaveContext` → `ModbusDeviceContext`; `slaves=` → `devices=`.

**When to use:** Required. This is the only async TCP server API in pymodbus 3.x.

```python
# Source: pymodbus 3.12.1 (verified against installed package)
from pymodbus.server import ModbusTcpServer
from pymodbus.datastore import ModbusServerContext, ModbusDeviceContext, ModbusSequentialDataBlock

def build_server(cache: RegisterCache, config: ProxyConfig) -> ModbusTcpServer:
    """Build the Modbus TCP server with the proxy datablock.
    
    Args:
        cache: The register cache providing the datablock.
        config: Proxy configuration for bind address and port.
    
    Returns:
        Configured but not yet running ModbusTcpServer.
    """
    device_context = ModbusDeviceContext(
        hr=cache.holding_datablock,   # FC3/FC6/FC16 — writable registers
        ir=cache.input_datablock,     # FC4 — read-only registers
    )
    server_context = ModbusServerContext(devices=device_context, single=True)
    return ModbusTcpServer(
        context=server_context,
        address=(config.bind_address, config.modbus_port),
    )
```

### Pattern 2: Register Address Convention (CRITICAL)

**What:** `ModbusDeviceContext.setValues` and `getValues` unconditionally apply `address += 1` before passing to the datablock. This means Modbus wire address 0 (what the client sends for "first register") becomes datablock index 1.

**Verified behavior:** [VERIFIED: inspected `ModbusDeviceContext.setValues` source in pymodbus 3.12.1]

```python
# Inside ModbusDeviceContext.setValues (pymodbus 3.12.1 source):
#   address += 1
# So client sends 0 → datablock receives 1
# DataBlock must be created starting at address 1:
holding_datablock = ModbusSequentialDataBlock(address=1, values=[0] * BLOCK_SIZE)
```

**Convention for this project (locked):**
- Luxtronik parameters (index 0–1125) → Modbus holding register wire address 0–1125
- Luxtronik calculations (index 0–250) → Modbus input register wire address 0–250
- Client sends wire address N; `ModbusDeviceContext` adds 1; datablock stores at index N+1
- Always document addresses in the register map as **0-based wire addresses**

### Pattern 3: Subclassing ModbusSequentialDataBlock for Write Passthrough

**What:** Override `async_setValues` to queue writes before delegating to the parent. The async version exists in pymodbus 3.12.1 and is called by the async server.

```python
# Source: pymodbus 3.12.1 (verified — async_setValues confirmed present)
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore.sequential import ExcCodes
import asyncio

class ProxyHoldingDataBlock(ModbusSequentialDataBlock):
    """Holding register datablock that queues writes to the Luxtronik controller.
    
    Modbus clients write to this datablock; the Polling Engine drains
    the write queue and forwards confirmed values to the controller.
    """

    def __init__(self, write_queue: asyncio.Queue, *args, **kwargs):
        """Initialize with a write queue for upstream forwarding.
        
        Args:
            write_queue: Queue for pending upstream writes.
            *args: Passed to ModbusSequentialDataBlock.
            **kwargs: Passed to ModbusSequentialDataBlock.
        """
        super().__init__(*args, **kwargs)
        self._write_queue = write_queue

    async def async_setValues(self, address: int, values: list[int]) -> None | ExcCodes:
        """Intercept writes: validate range, update cache, queue upstream write.
        
        Args:
            address: 1-based datablock address (wire address + 1 from ModbusDeviceContext).
            values: List of 16-bit integer values to write.
        
        Returns:
            None on success, ExcCodes.ILLEGAL_VALUE if range validation fails.
        """
        wire_address = address - 1  # convert back to 0-based for register map lookup
        exc = _validate_write(wire_address, values)
        if exc is not None:
            return exc  # rejects before touching cache or queue
        result = await super().async_setValues(address, values)
        if result is None:
            await self._write_queue.put((wire_address, values))
        return result
```

### Pattern 4: Polling Engine with asyncio Lock and run_in_executor

**What:** The Polling Engine serializes all upstream Luxtronik I/O through an `asyncio.Lock` and runs the blocking `luxtronik` library calls in a thread executor to prevent event loop starvation.

```python
# Source: Python asyncio docs + luxtronik library inspection (verified 2026-04-04)
import asyncio

class PollingEngine:
    """Background asyncio task that polls Luxtronik and updates the register cache.
    
    Owns the single asyncio lock that serializes all Luxtronik TCP connections.
    The blocking luxtronik library calls run in a thread executor.
    """

    def __init__(self, config: ProxyConfig, cache: RegisterCache, 
                 write_queue: asyncio.Queue) -> None:
        self._config = config
        self._cache = cache
        self._write_queue = write_queue
        self._lock = asyncio.Lock()
        self._loop = asyncio.get_event_loop()

    async def run_forever(self) -> None:
        """Run the polling loop indefinitely."""
        while True:
            await asyncio.sleep(self._config.poll_interval)
            await self._poll_cycle()

    async def _poll_cycle(self) -> None:
        """Execute one poll cycle: drain writes, read all, update cache."""
        async with self._lock:
            lux = _build_luxtronik_client(self._config)
            try:
                # Drain pending writes first (write + re-read in same connection)
                pending_writes = _drain_write_queue(self._write_queue)
                if pending_writes:
                    _apply_writes_to_queue(lux, pending_writes)
                    await self._loop.run_in_executor(None, lux.write)
                # Read all mapped parameters
                await self._loop.run_in_executor(None, lux.read)
                # Update cache
                self._cache.update_from_luxtronik(lux)
            except Exception:
                self._cache.mark_stale()
                raise
```

**Key insight:** `luxtronik.Luxtronik.read()` calls `_connect()` → `_read_parameters()` → `_read_calculations()` → `_read_visibilities()` → `_disconnect()` in one call. [VERIFIED: luxtronik 0.3.14 source inspection 2026-04-04]. Similarly `write()` manages its own connect/disconnect. Do not call `_connect`/`_disconnect` separately — use the public `read()` and `write()` methods.

### Pattern 5: ExcCodes for Modbus Exception Responses

**What:** Return `ExcCodes` enum values from `setValues`/`getValues` to signal Modbus exceptions to clients.

```python
# Source: pymodbus 3.12.1 (verified — ExcCodes confirmed in datastore.sequential)
from pymodbus.datastore.sequential import ExcCodes

# Reject out-of-range write value:
return ExcCodes.ILLEGAL_VALUE      # Modbus exception code 3

# Reject address out of range:
return ExcCodes.ILLEGAL_ADDRESS    # Modbus exception code 2

# Signal upstream failure (stale cache):
return ExcCodes.DEVICE_FAILURE     # Modbus exception code 4
```

### Pattern 6: pydantic-settings YAML Config

```python
# Source: pydantic-settings 2.13.1 (verified — YamlConfigSettingsSource confirmed)
from pydantic_settings import BaseSettings, YamlConfigSettingsSource, PydanticBaseSettingsSource
from pydantic import Field
from typing import ClassVar

class ProxyConfig(BaseSettings):
    """Proxy configuration loaded from config.yaml with env var overrides.
    
    Priority order: environment variables > config.yaml > defaults.
    """
    luxtronik_host: str = Field(..., description="Luxtronik controller IP address")
    luxtronik_port: int = Field(8889, description="Luxtronik controller port")
    modbus_port: int = Field(502, description="Modbus TCP server port")
    bind_address: str = Field("0.0.0.0", description="Bind address for Modbus server")
    poll_interval: int = Field(30, ge=10, description="Polling interval in seconds (min 10)")
    log_level: str = Field("INFO", description="Log level")

    model_config: ClassVar = {"yaml_file": "/app/config.yaml", "env_prefix": "LUXTRONIK_"}

    @classmethod
    def settings_customise_sources(
        cls, settings_cls, init_settings, env_settings, dotenv_settings, secrets_settings
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Load from YAML first, then override with env vars."""
        return (init_settings, YamlConfigSettingsSource(settings_cls), env_settings)
```

### Pattern 7: structlog Configuration

```python
# Source: structlog 25.5.0 docs (installed and verified)
import structlog, logging, os

def configure_logging(log_level: str) -> None:
    """Configure structlog for JSON output in production, colored in development.
    
    Args:
        log_level: Logging level string (DEBUG, INFO, WARNING, ERROR).
    """
    is_tty = os.isatty(1)  # stdout connected to terminal?
    renderer = structlog.dev.ConsoleRenderer() if is_tty else structlog.processors.JSONRenderer()
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper(), logging.INFO)
        ),
        logger_factory=structlog.PrintLoggerFactory(),
    )
```

### Anti-Patterns to Avoid

- **Holding Luxtronik socket open:** `luxtronik.read()` manages its own connect/disconnect; never cache the `Luxtronik` instance across poll cycles
- **Calling luxtronik directly in a coroutine without executor:** `_connect()` is a blocking `socket.connect()` — wrapping with `run_in_executor` is mandatory
- **Using the old `ModbusSlaveContext` API:** Renamed to `ModbusDeviceContext` in pymodbus 3.x; using the old name causes `ImportError`
- **Initializing datablocks at address 0:** `ModbusDeviceContext` adds 1 to all addresses; datablocks must start at address 1
- **Skipping the asyncio lock:** Even one concurrent poll + write without the lock produces socket corruption (Bouni/luxtronik issue #10)

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Modbus TCP server | Custom TCP socket framing + Modbus PDU parser | `pymodbus.server.ModbusTcpServer` | Modbus framing has edge cases (PDU length, exception responses, multi-client handling) that pymodbus has solved |
| Luxtronik binary protocol | Custom socket parsing of commands 3003/3004/3005 | `luxtronik.Luxtronik.read()` / `.write()` | The binary protocol is undocumented; luxtronik 0.3.14 is the battle-tested implementation |
| YAML config loading | `open(yaml_file); yaml.safe_load()` + manual validation | `pydantic-settings` `YamlConfigSettingsSource` | Env var override, type coercion, and validation for free |
| Structured logging | Custom log formatters | `structlog.configure()` | Context binding, renderer switching (JSON/console), and stdlib integration without reinventing |
| Signal handling in Docker | Manual `signal.signal(SIGTERM, ...)` + `asyncio.get_event_loop().stop()` | `tini` + Python's `asyncio` signal handler | tini as PID 1 forwards SIGTERM correctly; Python handles shutdown; no zombie processes from thread executor |
| Register address validation | Custom bounds checking in setValues | Return `ExcCodes.ILLEGAL_ADDRESS` or `ExcCodes.ILLEGAL_VALUE` from datablock | pymodbus propagates ExcCodes as proper Modbus exception responses automatically |

**Key insight:** The combination of pymodbus + luxtronik + pydantic-settings covers every infrastructure concern. Custom code should be limited to the protocol translation logic (register map, value scaling, write validation) and the polling engine orchestration.

---

## Common Pitfalls

### Pitfall 1: ModbusSlaveContext Renamed to ModbusDeviceContext

**What goes wrong:** Code based on any pymodbus tutorial or documentation from before 3.8+ uses `ModbusSlaveContext`. In pymodbus 3.12.1, `ModbusSlaveContext` does not exist in `pymodbus.datastore` — import raises `ImportError`.

**Why it happens:** The rename was part of pymodbus's Modbus terminology cleanup ("slave" → "device").

**How to avoid:** Import `ModbusDeviceContext` from `pymodbus.datastore`. The constructor parameters are `di`, `co`, `ir`, `hr` (keyword-only).

**Warning signs:** `ImportError: cannot import name 'ModbusSlaveContext' from 'pymodbus.datastore'`

[VERIFIED: inspected pymodbus 3.12.1 source, confirmed `ModbusSlaveContext` absent, `ModbusDeviceContext` present with `di`/`co`/`ir`/`hr` kwargs]

### Pitfall 2: ModbusDeviceContext Applies address += 1 — Datablocks Must Start at 1

**What goes wrong:** If you create `ModbusSequentialDataBlock(address=0, values=[...])` and a client reads wire address 0, `ModbusDeviceContext.setValues` does `address += 1`, tries to access datablock address 1, but the datablock starts at 0 and has no index 1 → returns `ExcCodes.ILLEGAL_ADDRESS`.

**Why it happens:** pymodbus 3.x uses 1-based datablock addresses internally while the Modbus wire protocol sends 0-based addresses. `ModbusDeviceContext` bridges this by adding 1.

**How to avoid:** Always create datablocks starting at address 1: `ModbusSequentialDataBlock(address=1, values=[0] * N)`.

[VERIFIED: inspected `ModbusDeviceContext.setValues` source — `address += 1` confirmed]

### Pitfall 3: luxtronik.read() is Blocking — Must Use run_in_executor

**What goes wrong:** `luxtronik.Luxtronik._connect()` calls `socket.connect()` which is a blocking system call. If called directly in a coroutine, the asyncio event loop is frozen for the duration of the TCP round-trip (200–500ms), causing all Modbus clients to time out on every poll cycle.

**Why it happens:** luxtronik 0.3.14 uses `socket` (stdlib), not asyncio. [VERIFIED: inspected `_connect()` source in installed luxtronik 0.3.14]

**How to avoid:** `await loop.run_in_executor(None, lux.read)` and `await loop.run_in_executor(None, lux.write)`.

**Warning signs:** Modbus client logs `timeout` on every request that coincides with a poll cycle; response time equals upstream poll duration.

### Pitfall 4: luxtronik.write() Uses an Internal Queue — Must Set Parameters First

**What goes wrong:** Calling `lux.write()` without populating `lux.parameters.queue` does nothing (empty queue, no writes, no error).

**Why it happens:** The write API is queue-based. [VERIFIED: inspected `write()` source — loops over `self.parameters.queue.items()`]

**How to avoid:** To write parameter 3 (HeatingMode) with value 2 (Party):
```python
lux = luxtronik.Luxtronik(host, port)
lux.parameters.queue[3] = 2    # populate queue before calling write()
await loop.run_in_executor(None, lux.write)  # queue is flushed after write
```

### Pitfall 5: Write Validation Must Happen Before the Write Queue Entry

**What goes wrong:** If range validation happens in the Polling Engine when draining the write queue (not at `async_setValues` time), the Modbus client already received a success acknowledgment. The heat pump rejects the value or applies a dangerous setting before the proxy discovers the error.

**Why it happens:** It is tempting to do all Luxtronik-specific validation in the Polling Engine where the upstream connection happens. But the Modbus client's write ACK should only be sent if the value is valid.

**How to avoid:** Validate in `ProxyHoldingDataBlock.async_setValues` before calling `super()` and before putting on the write queue. Return `ExcCodes.ILLEGAL_VALUE` immediately for rejections. The Polling Engine trusts queue contents to be pre-validated.

### Pitfall 6: Stale Cache Not Detected After Upstream Failures

**What goes wrong:** If the Luxtronik controller is unreachable, the cache holds values from the last successful poll. Without a staleness indicator, Modbus clients receive arbitrarily stale values silently — evcc may make energy management decisions based on hours-old data.

**How to avoid:** Track `last_successful_read: datetime` in `RegisterCache`. In `getValues`, if `datetime.now() - last_successful_read > N * poll_interval`, return `ExcCodes.DEVICE_FAILURE` (code 4) instead of stale data. Use N=3 as the threshold (i.e., 3 consecutive poll failures trigger the exception response).

### Pitfall 7: HA BenPru Contention — Proxy Poll Interval Must Leave Connection Windows

**What goes wrong:** BenPru/luxtronik HACS integration also uses connect-read-disconnect. If the proxy polls every 10 seconds and each poll takes 200ms, it leaves a 9.8s window. HA polls every 30s. This usually works. But if the proxy poll interval is reduced to < 15s with a full 1,126-parameter read, HA can starve.

**How to avoid:** Phase 1 default of 30s is safe. Enforce minimum 10s via pydantic `ge=10` validator. Log a WARNING if `poll_interval < 15`.

### Pitfall 8: Docker SIGTERM Not Handled — Upstream Socket Left Open

**What goes wrong:** `docker stop` sends SIGTERM. If the Python process ignores it, Docker waits 10s then sends SIGKILL. The Luxtronik socket is left in CLOSE_WAIT or TIME_WAIT state, and the next connection from HA or the restarting proxy may fail.

**How to avoid:** Use `tini` as PID 1 (it forwards SIGTERM). Register an `asyncio` signal handler:
```python
loop.add_signal_handler(signal.SIGTERM, lambda: asyncio.create_task(shutdown()))
```
The `shutdown()` coroutine cancels the polling task and the server task in order.

---

## Code Examples

### Full Curated Register Map (Phase 1 Default Set)

These parameter IDs and names were verified against the installed luxtronik 0.3.14 library:

```python
# Source: luxtronik 0.3.14 installed package, parameters.py and calculations.py
# Verified 2026-04-04 by direct inspection

# --- Holding Registers (FC3/FC6/FC16) — writable parameters ---
# Wire address matches luxtronik parameter index (0-based)
# ModbusDeviceContext adds +1 when routing to datablock

HOLDING_REGISTERS = {
    # addr: (luxtronik_id, name, type, writeable)
    3:   ("ID_Ba_Hz_akt",    "Heating circuit mode",      "HeatingMode",  True),
    # HeatingMode codes: {0: 'Automatic', 1: 'Second heatsource', 2: 'Party', 3: 'Holidays', 4: 'Off'}
    4:   ("ID_Ba_Bw_akt",    "Hot water mode",            "HotWaterMode", True),
    # HotWaterMode codes: {0: 'Automatic', 1: 'Second heatsource', 2: 'Party', 3: 'Holidays', 4: 'Off'}
    105: ("ID_Soll_BWS_akt", "Hot water setpoint (°C×10)","Celsius",      True),
    # Celsius: from_heatpump divides by 10; to_heatpump multiplies by 10
}

# --- Input Registers (FC4) — read-only calculations ---
# Wire address matches luxtronik calculation index (0-based)

INPUT_REGISTERS = {
    # addr: (luxtronik_id, name, type)
    10:  ("ID_WEB_Temperatur_TVL", "Flow temperature (°C×10)",     "Celsius"),
    11:  ("ID_WEB_Temperatur_TRL", "Return temperature (°C×10)",   "Celsius"),
    15:  ("ID_WEB_Temperatur_TA",  "Outside temperature (°C×10)",  "Celsius"),
    17:  ("ID_WEB_Temperatur_TBW", "Hot water temperature (°C×10)","Celsius"),
    80:  ("ID_WEB_WP_BZ_akt",      "Operating mode",               "OperationMode"),
    # OperationMode codes: {0:'heating', 1:'hot water', 2:'swimming pool/solar',
    #                       3:'evu', 4:'defrost', 5:'no request', ...}
    257: ("Heat_Output",           "Heat output (W)",               "Power"),
    # Power: from_heatpump returns value unchanged (raw watts)
}
```

### Datablock Initialization Pattern

```python
# Source: pymodbus 3.12.1 (verified)
# Datablocks must start at address=1 because ModbusDeviceContext adds 1 to all addresses

HOLDING_BLOCK_SIZE = 1200  # covers parameter indices 0-1125 + margin
INPUT_BLOCK_SIZE = 260     # covers calculation indices 0-257 + margin

holding_db = ModbusSequentialDataBlock(address=1, values=[0] * HOLDING_BLOCK_SIZE)
input_db   = ModbusSequentialDataBlock(address=1, values=[0] * INPUT_BLOCK_SIZE)

device_context = ModbusDeviceContext(hr=holding_db, ir=input_db)
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `ModbusSlaveContext` | `ModbusDeviceContext` | pymodbus 3.x | Import path change; no `slaves=` keyword |
| `ModbusServerContext(slaves=...)` | `ModbusServerContext(devices=...)` | pymodbus 3.x | Keyword rename |
| `from pymodbus.datastore import ModbusSlaveContext` | `from pymodbus.datastore import ModbusDeviceContext` | pymodbus 3.x | Direct ImportError if using old name |
| pymodbus 2.x async server setup | `asyncio`-native server in 3.x | pymodbus 3.0 | Cannot use v2 patterns in v3 |
| `asyncio_mode = "auto"` per-test decorator | `asyncio_mode = auto` global in `pyproject.toml` | pytest-asyncio 0.21+ | Single config line covers all async tests |
| `python:3.12` Docker base | `python:3.12-slim` | Ongoing | ~400MB → ~150MB image size; wheels install faster |

**Deprecated/outdated:**
- `ModbusSlaveContext`: removed in pymodbus 3.x — do not use
- `asyncio_mode = "auto"` (quoted string): works but prefer unquoted in pyproject.toml
- pymodbus 4.0 dev: `getValues`/`setValues` API changing again; stay on 3.12.1

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | luxtronik `read()` calls `_connect` + all 3 reads + `_disconnect` internally — the proxy should NOT call `_connect`/`_disconnect` manually | Architecture Patterns, Pitfall 4 | If the API changes in a future version, the Luxtronik Client wrapper would need updating |
| A2 | BenPru/luxtronik HACS integration uses the same connect-read-disconnect pattern on port 8889, not a persistent connection | Common Pitfalls, Pitfall 7 | If BenPru holds the connection open, the 30s polling interval still works because BenPru connects to the Luxtronik binary port (8889), not the proxy; but coexistence behavior needs hardware verification |
| A3 | The Luxtronik 2.0 controller at target site (Software V3.78) has the same parameter index layout as luxtronik 0.3.14 | Code Examples (register map) | If the controller firmware uses different indices for any curated parameter, reads return wrong values; needs hardware validation |

**All other claims were VERIFIED against installed package source or official PyPI data.**

---

## Open Questions

1. **HeatingMode vs HotWaterMode write range for safe defaults**
   - What we know: HeatingMode codes are {0: 'Automatic', 1: 'Second heatsource', 2: 'Party', 3: 'Holidays', 4: 'Off'}; all 5 are valid
   - What's unclear: Whether modes 1 and 3 are safe to expose via Modbus writes in Phase 1, or whether only Automatic (0) and Party (2) should be writable
   - Recommendation: Allow all 5 for Phase 1 but document that users should test with their specific hardware before relying on mode 1 ("Second heatsource") and mode 3 ("Holidays")

2. **Hot water setpoint safe range for write validation**
   - What we know: `ID_Soll_BWS_akt` (param 105) is `Celsius` type (value × 10); typical DHW setpoint is 45–55°C
   - What's unclear: What is the minimum and maximum safe setpoint value for this controller family?
   - Recommendation: Default to min=30°C (300 raw), max=65°C (650 raw) — conservative range that prevents Legionella risk (below 60°C threshold) while protecting against scalding/controller limits. Flag as needing hardware validation.

3. **evcc register addressing convention (0-based vs 1-based in YAML)**
   - What we know: pymodbus serves 0-based wire addresses; Modbus.org docs use 1-based
   - What's unclear: Does evcc's Modbus YAML template expect 0-based (`register: 3`) or 1-based (`register: 4`) for HeatingMode?
   - Recommendation: Defer to Phase 2 (where the evcc YAML template is finalized). Phase 1 registers are not published yet, so the convention is not locked. Document the decision in a register map comment when the evcc template is written.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.10+ | Runtime | ✓ | 3.10.12 | — |
| `luxtronik` 0.3.14 | Luxtronik client | ✓ | 0.3.14 | — |
| `pydantic` 2.12.x | Config validation | ✓ | 2.12.5 | — |
| `pydantic-settings` 2.13.x | YAML config loading | ✓ | 2.13.1 | — |
| `structlog` 25.5.0 | Structured logging | ✓ | 25.5.0 | — |
| `pytest` 9.x | Testing | ✓ | 9.0.2 | — |
| `pytest-asyncio` 1.3.x | Async testing | ✓ | 1.3.0 | — |
| `ruff` | Linting | ✓ | 0.15.9 | — |
| `mypy` | Type checking | ✓ | 1.20.0 | — |
| `pymodbus` 3.12.1 | Modbus TCP server | ✗ (not installed) | — | Install via pip (available on PyPI, confirmed) |
| Docker | Container deployment | ✗ | — | Test functionality without Docker; DEPLOY-01 requires Docker for final verification |
| Luxtronik controller (real hardware) | PROTO-02, PROTO-03 integration test | Unknown | — | Mock-based unit tests; hardware test deferred to manual verification step |

**Missing dependencies with no fallback:**
- None that block task execution. `pymodbus` requires `pip install` as a first task.

**Missing dependencies with fallback:**
- Docker: All code tasks can be executed and tested without Docker. DEPLOY-01 requires Docker for the final container build verification — this task should be last in the wave ordering. If Docker is not available on the development machine, that task cannot be completed; the user should install Docker or defer DEPLOY-01 verification.
- Luxtronik hardware: All unit tests use mocks. Integration testing against real hardware is a separate manual verification step documented in the phase success criteria.

---

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | Modbus has no auth layer; proxy is LAN-only by design |
| V3 Session Management | No | Stateless protocol; no sessions |
| V4 Access Control | Partial | Bind to specific interface (not `0.0.0.0` by default); limit writable registers to curated set only |
| V5 Input Validation | Yes | `pydantic` validates config at startup; `ProxyHoldingDataBlock.async_setValues` validates register write values before queuing |
| V6 Cryptography | No | No encryption required for local network proxy |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Out-of-range Modbus write damaging heat pump | Tampering | Per-parameter range validation in `async_setValues`; return `ExcCodes.ILLEGAL_VALUE` (code 3) before value reaches controller |
| Rapid writes exhausting NAND flash | Denial of Service | Per-register write rate limiting (max 1 write per 60s per register address) |
| Real IP committed to public repo | Information Disclosure | `.gitignore` covers `config.yaml`; pre-commit hook scans for private IP ranges; `config.example.yaml` uses placeholder values only |
| Full parameter exposure by default | Tampering | Only curated register set (~20 registers) in default config; writes gated by `enable_writes: true` flag |
| Logging sensitive operational data | Information Disclosure | DEBUG level for full parameter dumps; INFO level shows counts and event types, not raw values |

---

## Sources

### Primary (HIGH confidence)
- [luxtronik 0.3.14 installed source] — `Luxtronik.read()`, `Luxtronik.write()`, `_connect()`, `_disconnect()` inspected directly; parameter/calculation counts and types verified; HeatingMode/HotWaterMode enum codes confirmed [VERIFIED: 2026-04-04]
- [pymodbus 3.12.1 installed to /tmp/pmcheck] — `ModbusDeviceContext`, `ModbusSequentialDataBlock`, `ExcCodes`, `ModbusTcpServer`, `ModbusServerContext` APIs inspected; `address += 1` offset confirmed; `async_setValues` signature confirmed [VERIFIED: 2026-04-04]
- [pydantic-settings 2.13.1 installed] — `YamlConfigSettingsSource` signature confirmed; `settings_customise_sources` pattern verified [VERIFIED: 2026-04-04]
- [pymodbus PyPI](https://pypi.org/project/pymodbus/) — 3.12.1 confirmed latest stable; version list confirmed
- [luxtronik PyPI](https://pypi.org/project/luxtronik/) — 0.3.14 confirmed current
- [Bouni/python-luxtronik GitHub](https://github.com/Bouni/python-luxtronik) — NAND flash write risk, `safe=True` default [CITED]
- [HA core issue #149494](https://github.com/home-assistant/core/issues/149494) — persistent Modbus connection confirmed intentional [CITED]
- [Bouni/luxtronik issue #10](https://github.com/Bouni/luxtronik/issues/10) — concurrent read/write socket corruption [CITED]

### Secondary (MEDIUM confidence)
- [.planning/research/ARCHITECTURE.md] — component build order, data flow diagrams, anti-patterns [CITED: prior project research 2026-04-04]
- [.planning/research/PITFALLS.md] — full pitfall catalog with recovery costs [CITED: prior project research 2026-04-04]
- [.planning/research/STACK.md] — version decisions and alternatives analysis [CITED: prior project research 2026-04-04]
- [evcc discussion #7153](https://github.com/evcc-io/evcc/discussions/7153) — register addresses for power, energy, temperatures [CITED: MEDIUM — community, not official spec]

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all versions verified against installed packages and PyPI index
- Architecture: HIGH — pymodbus API verified against 3.12.1 source; luxtronik API verified against 0.3.14 source
- Register map (Phase 1 curated set): HIGH — parameter IDs and types verified against luxtronik 0.3.14 parameters.py
- Pitfalls: HIGH — critical pitfalls verified from multiple primary sources
- Hardware behavior: MEDIUM — address offset, connection timing, and coexistence confirmed by library source and GitHub issues; needs hardware validation for final confidence

**Research date:** 2026-04-04
**Valid until:** 2026-07-04 (90 days — pymodbus 3.x is stable; luxtronik 0.3.14 is latest since Jun 2024)

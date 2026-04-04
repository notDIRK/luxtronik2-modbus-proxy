# Architecture Research

**Domain:** Protocol translation proxy — binary TCP to Modbus TCP (heat pump controller)
**Researched:** 2026-04-04
**Confidence:** HIGH (pymodbus, luxtronik library), MEDIUM (proxy patterns, register mapping design)

## Standard Architecture

### System Overview

```
External Modbus Clients                Luxtronik 2.0 Controller
(evcc, Home Assistant, etc.)           (Alpha Innotec MSW 14)
         |                                        |
         | Modbus TCP (port 502)                  | Binary TCP (port 8889)
         |                                        |
+--------v----------------------------------------v--------+
|                  luxtronik2-modbus-proxy                  |
|                                                           |
|  +-------------------+     +---------------------------+  |
|  |  Modbus TCP Server|     |  Luxtronik Client         |  |
|  |  (pymodbus async) |     |  (luxtronik lib v0.3.14)  |  |
|  |  port 502         |     |  connect/read/write/disc  |  |
|  +--------+----------+     +-------------+-------------+  |
|           |                              |                 |
|  +--------v------------------------------v-----------+    |
|  |               Register Cache                       |    |
|  |  (in-memory datablock, thread-safe, TTL-based)     |    |
|  +--------------------+-------------------------------+    |
|                       |                                    |
|  +--------------------v-------------------------------+    |
|  |               Register Map                          |    |
|  |  (luxtronik param/calc/visibility → Modbus addr)   |    |
|  +-----------------------------------------------------+    |
|                       |                                    |
|  +--------------------v-------------------------------+    |
|  |               Polling Engine                        |    |
|  |  (asyncio task, configurable interval, mutex lock)  |    |
|  +-----------------------------------------------------+    |
|                       |                                    |
|  +--------------------v-------------------------------+    |
|  |               Config Loader                         |    |
|  |  (config.yaml → pydantic, validated on startup)     |    |
|  +-----------------------------------------------------+    |
+-----------------------------------------------------------+
              |                          |
       Docker Container            Structured Logs
       (Python 3.10+)              (structlog → stderr)
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|---------------|------------------------|
| Modbus TCP Server | Accept inbound Modbus TCP connections; serve register reads/writes from cache; route writes to Polling Engine | `pymodbus.server.async_io.StartAsyncTcpServer` with custom `CallbackDataBlock` |
| Register Cache | Thread-safe in-memory store of all mapped register values; updated by Polling Engine; read by Modbus Server | `ModbusSequentialDataBlock` or custom dict protected by `asyncio.Lock` |
| Register Map | Static definition: luxtronik param/calc/visibility ID → Modbus register address, data type, scaling, read/write flag | Python module with typed dataclass definitions; YAML-loadable user overrides |
| Polling Engine | Periodic asyncio task; connects to Luxtronik, reads all mapped parameters, updates Register Cache, disconnects | `asyncio.create_task` loop with configurable sleep interval and `asyncio.Lock` guarding Luxtronik connection |
| Luxtronik Client | Thin wrapper around `luxtronik` library; encapsulates connect/read/write/disconnect lifecycle; exposes typed interface | Class holding `Luxtronik` instance, using `read()` / `write()` methods |
| Config Loader | Parse `config.yaml`, validate with pydantic, produce typed config object used by all components at startup | `pydantic.BaseModel` + `pyyaml`; fail-fast on bad config |
| Write Handler | On Modbus write to a writable register, translate to luxtronik parameter write; queue write for next poll cycle | Callback on `CallbackDataBlock.setValues`; write immediately then re-read |
| Structured Logger | Emit machine-readable logs for polling events, connect/disconnect, write operations, errors | `structlog` configured for JSON output in production, pretty-print in dev |

## Recommended Project Structure

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
│   ├── parameters.py           # All 1,126 parameter definitions (ID, name, type, writable, scale)
│   ├── calculations.py         # All 251 calculation definitions (ID, name, type, read-only, scale)
│   └── visibilities.py         # All 355 visibility definitions (ID, name)
├── config.example.yaml          # Example config with placeholder values (in repo)
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── tests/
    ├── unit/
    │   ├── test_config.py
    │   ├── test_register_map.py
    │   └── test_register_cache.py
    └── integration/
        └── test_proxy_mock.py   # Uses a mock luxtronik server for end-to-end testing
```

### Structure Rationale

- **`register_definitions/`:** Separate from `src/` because they are data, not logic. Generated once from luxtronik source files; rarely edited. Keeping them out of the main package makes the boundary explicit.
- **`register_map.py`:** Combines definitions with addressing decisions (which luxtronik IDs get which Modbus addresses). The mapping is the intellectual core of the proxy — it deserves its own module.
- **`polling_engine.py`:** Owns the only place that touches the Luxtronik connection. Centralizing this prevents the accidental multi-connection bug.
- **`modbus_server.py`:** Owns everything pymodbus. If pymodbus is ever replaced, only this file and `register_cache.py` change.

## Architectural Patterns

### Pattern 1: Async Server + Background Polling Task

**What:** The pymodbus async TCP server and the Luxtronik polling loop run as concurrent asyncio tasks in the same event loop. The server never calls the Luxtronik controller directly — it only reads from the in-memory cache.

**When to use:** Required. The Luxtronik controller accepts only one TCP connection. Separating the server (always listening) from the poller (connects briefly, then releases) is the fundamental architecture choice.

**Trade-offs:** The cache introduces a maximum staleness of one polling interval. For energy management use cases (evcc, HA automations) this is acceptable at 30-60s intervals. Write latency is bounded by the poll interval.

**Example structure:**
```python
async def main():
    config = load_config("config.yaml")
    cache = RegisterCache(register_map)
    poller = PollingEngine(config, cache)
    server = ModbusServer(config, cache)

    await asyncio.gather(
        server.serve_forever(),
        poller.run_forever(),
    )

asyncio.run(main())
```

### Pattern 2: CallbackDataBlock for Write Passthrough

**What:** Subclass pymodbus `ModbusSequentialDataBlock`, override `setValues` (and `async_setValues` for async server). On write, immediately queue the (register address, value) pair for the Polling Engine to translate and forward to the Luxtronik controller.

**When to use:** Required for write support. The Modbus server cannot call the Luxtronik client directly (single connection constraint). The callback queues the write; the Polling Engine drains the queue during its next connection window.

**Trade-offs:** Writes are not instantaneous — they execute on the next poll cycle (bounded by polling interval). For SG-ready mode switching this is acceptable. Acknowledge-before-confirm: the server writes to the cache immediately so the Modbus client sees the "new" value before the heat pump confirms it. Flag stale writes if confirmed value differs.

**Example structure:**
```python
class ProxyDataBlock(ModbusSequentialDataBlock):
    def __init__(self, write_queue: asyncio.Queue, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._write_queue = write_queue

    async def async_setValues(self, address, values):
        await super().async_setValues(address, values)
        await self._write_queue.put((address, values))
```

### Pattern 3: Mutex-Protected Single Connection

**What:** The Polling Engine holds an `asyncio.Lock` that it acquires before each connect-read/write-disconnect cycle. Any component needing a Luxtronik connection must acquire this lock. In practice only the Polling Engine ever acquires it — the lock acts as a safeguard against future refactoring accidents.

**When to use:** Required given the single-connection constraint of Luxtronik 2.0.

**Trade-offs:** Straightforward with asyncio. If a poll cycle is slow (network timeout), the lock delay is bounded by the timeout setting, not indefinite. Set `lock_timeout` in the luxtronik library call (default 30s).

### Pattern 4: Sparse Register Map with Address Range Partitioning

**What:** Luxtronik parameters (0–1125), calculations (0–250), and visibilities (0–354) are indexed independently. Map them to non-overlapping Modbus holding register address ranges:

```
Address Range      Luxtronik Source        Access
0    – 1125        Parameters (index)      Read + Write
2000 – 2250        Calculations (index)    Read only
3000 – 3354        Visibilities (index)    Read only
```

The address offset encodes the type, making the mapping trivially reversible without a lookup table. Use `ModbusSparseDataBlock` (or a sequential block covering only used addresses) so memory is not wasted on the sparse gaps.

**When to use:** Recommended for this project. The alternative (arbitrary Modbus addresses defined in YAML) requires users to look up IDs and is error-prone.

**Trade-offs:** Requires documenting the address scheme. Clients must know which range corresponds to which data type. This is the trade-off between user-facing simplicity and implementation simplicity — choose the offset scheme and document it clearly.

## Data Flow

### Read Flow (Modbus client reads a register)

```
Modbus client (evcc or HA)
    | Modbus TCP FC 03 (Read Holding Registers)
    v
Modbus TCP Server (pymodbus)
    | address → ProxyDataBlock.getValues(address, count)
    v
Register Cache (in-memory datablock)
    | returns cached value (stale by at most polling_interval seconds)
    v
Modbus TCP Server
    | encodes response
    v
Modbus client
```

### Write Flow (Modbus client writes a register)

```
Modbus client (evcc or HA)
    | Modbus TCP FC 06 / FC 16 (Write Register(s))
    v
Modbus TCP Server (pymodbus)
    | address → ProxyDataBlock.async_setValues(address, values)
    v
Register Cache (update optimistically)
    + write_queue.put((address, values))
    v
Polling Engine (next cycle)
    | acquire Luxtronik lock
    | translate address → luxtronik parameter ID + value
    | LuxtronikClient.write_param(id, value)
    | LuxtronikClient.read_all()   ← re-read to confirm
    | update Register Cache with confirmed values
    | release lock
```

### Polling Flow (background, repeating)

```
Polling Engine asyncio task
    | asyncio.sleep(polling_interval)
    | acquire Luxtronik lock
    v
LuxtronikClient.connect()       ← opens TCP to port 8889
    v
LuxtronikClient.read_all()      ← cmd 3003 (params), 3004 (calcs), 3005 (vis)
    v
RegisterMap.translate(raw_data) ← apply scaling, type conversion
    v
RegisterCache.bulk_update(values)
    v
LuxtronikClient.disconnect()    ← releases connection for HA/other tools
    | release Luxtronik lock
    | log timing + any changed values
```

## Component Build Order

Build order follows data flow dependencies from the inside out:

1. **Register Definitions** (`register_definitions/`) — Pure data, no dependencies. Define all 1,126 parameters, 251 calculations, 355 visibilities with their types, scaling factors, and read/write flags. This is the foundation everything else references.

2. **Config Loader** (`config.py`) — Pydantic models for `config.yaml`. Depends on: nothing. All other components receive a typed config object.

3. **Register Map** (`register_map.py`) — Defines luxtronik ID → Modbus address assignments using the address offset scheme. Depends on: register definitions. This is the contract between luxtronik and Modbus worlds.

4. **Register Cache** (`register_cache.py`) — In-memory datablock initialized from the register map. Depends on: register map, pymodbus datastore. Wraps pymodbus datablock with a typed interface.

5. **Luxtronik Client** (`luxtronik_client.py`) — Thin wrapper around `luxtronik` library. Depends on: config (host, port, timeout). Exposes `connect()`, `read_all() → RawData`, `write_param(id, value)`, `disconnect()`. Unit-testable by mocking the luxtronik library.

6. **Polling Engine** (`polling_engine.py`) — Depends on: Luxtronik Client, Register Cache, Register Map, config (interval). Contains the asyncio lock and write queue. Core loop: sleep → lock → connect → read/write → update cache → disconnect → release.

7. **Modbus Server** (`modbus_server.py`) — Depends on: Register Cache (for `ProxyDataBlock`), config (bind address, port), Polling Engine (to inject write queue). Sets up pymodbus async TCP server.

8. **Main Entry Point** (`main.py`) — Wires all components together. Depends on everything. Calls `asyncio.gather(server.serve_forever(), poller.run_forever())`.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Luxtronik 2.0 controller (port 8889) | Short-lived TCP connection; connect → read/write → disconnect per poll cycle | Single connection enforced by controller; must release before HA reconnects |
| Home Assistant BenPru/luxtronik HACS | Shares the heat pump connection by time-sharing via polling interval gaps | Proxy polls every N seconds; HA polls independently; gaps allow HA to connect |
| evcc (Modbus TCP client) | Connects to proxy port 502 as a standard Modbus TCP client | No special handling needed; evcc sees the proxy as a regular Modbus device |
| Docker runtime | Single process container; health check via TCP connect attempt to port 502 | No HTTP health endpoint needed; Modbus port is the health indicator |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| Polling Engine ↔ Modbus Server | `asyncio.Queue` for pending writes; shared `RegisterCache` reference | Queue is the only cross-boundary state mutation path |
| Polling Engine ↔ Luxtronik Client | Direct method calls (both in same async context) | Luxtronik Client is not an independent async task; called by Polling Engine |
| Modbus Server ↔ Register Cache | `ProxyDataBlock` holds a reference to the cache; reads/writes go through cache interface | pymodbus calls `getValues`/`setValues` on the datablock directly |
| Config ↔ All components | Config object passed at construction time | No global config singleton; inject via constructor for testability |

## Docker Container Structure

```
FROM python:3.10-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY src/ src/
COPY register_definitions/ register_definitions/
COPY config.example.yaml .

# Runtime: user mounts config.yaml at /app/config.yaml
VOLUME ["/app/config"]

# Modbus TCP port
EXPOSE 502

# Use tini for signal forwarding and zombie reaping
RUN apt-get install -y tini
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python", "-m", "luxtronik2_modbus_proxy"]
```

**Health check:** `HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import socket; s=socket.create_connection(('localhost', 502), 3)"` — a Modbus TCP connect attempt verifies the server is alive.

**Graceful shutdown:** The Python process handles `SIGTERM` via `asyncio` signal handlers; it completes the current poll cycle, disconnects from the Luxtronik controller, then exits.

## Anti-Patterns

### Anti-Pattern 1: Holding the Luxtronik Connection Open

**What people do:** Open a persistent connection to the Luxtronik controller for low-latency reads, similar to a database connection pool.

**Why it's wrong:** The Luxtronik 2.0 controller allows exactly one TCP connection. A persistent connection blocks Home Assistant's BenPru integration from connecting, breaking coexistence. The controller also does not send push notifications — a persistent connection buys nothing.

**Do this instead:** Use the connect-read/write-disconnect pattern per poll cycle. Keep poll intervals at 30–120 seconds. The connection open time is typically under 500ms.

### Anti-Pattern 2: Calling Luxtronik from the Modbus Request Handler

**What people do:** On a Modbus read request, synchronously call `luxtronik.read()` to get a fresh value before responding.

**Why it's wrong:** This makes every Modbus read depend on the Luxtronik connection being available and fast. If the connection is slow or the controller is busy, Modbus clients time out. It also breaks the single-connection constraint if multiple Modbus clients connect simultaneously.

**Do this instead:** Serve all reads from the Register Cache. The cache is always available and fast. Accept that data is bounded-stale by the polling interval.

### Anti-Pattern 3: One Modbus Address per Write, Separate from Read

**What people do:** Assign separate Modbus addresses for read vs. write of the same parameter (e.g., read temperature at register 100, write setpoint at register 200).

**Why it's wrong:** Standard Modbus practice is to read and write the same holding register (FC 03 reads it, FC 06/16 writes it). Split addressing confuses clients and requires custom evcc/HA configuration.

**Do this instead:** Use holding registers (FC 03/06/16) for writable parameters. Read-only data uses input registers (FC 04) or read-only holding registers.

### Anti-Pattern 4: Putting All 1,126 Parameters in the Default Config

**What people do:** Export every Luxtronik parameter as a Modbus register so "users can choose what they want."

**Why it's wrong:** Polling 1,126 parameters increases connection time significantly. Most users need fewer than 20 registers for evcc and 50 for HA. Exposing all parameters also increases the risk of accidental writes to production-critical controller parameters.

**Do this instead:** Ship a curated default set of ~30 essential registers (operating mode, flow/return temperatures, SG-ready, hot water setpoint, compressor status). Document the full mapping as an opt-in extension. Gate writes on an explicit `enable_writes: true` config flag.

### Anti-Pattern 5: Flat Register Numbering Without Namespace

**What people do:** Assign sequential Modbus addresses 0, 1, 2, ... to selected parameters without a clear scheme.

**Why it's wrong:** When users add registers to the config, address allocation becomes manual and error-prone. Documentation becomes a required artifact rather than something derivable from the address.

**Do this instead:** Use the partition scheme (parameters 0–1125, calculations 2000–2250, visibilities 3000–3354). The address is self-documenting — the range tells you the type, the offset tells you the luxtronik index.

## Scaling Considerations

This is a single-instance, local-network proxy. Scaling in the traditional sense does not apply. The relevant capacity questions are:

| Concern | Behavior | Limit |
|---------|----------|-------|
| Concurrent Modbus clients | pymodbus async server handles multiple concurrent TCP connections | Practical limit: dozens; no single heat pump needs more |
| Polling interval | Shorter intervals increase Luxtronik connection frequency and HA conflict risk | Minimum practical: 30s; recommended: 60s |
| Register count | More registers = longer read time per poll cycle | Full set (1,126 params + 251 calcs) reads in ~200ms; safe |
| Write throughput | Writes queue until next poll cycle | Not a concern for energy management use cases (1–2 writes per hour) |

## Sources

- pymodbus architecture overview: [DeepWiki — pymodbus overview](https://deepwiki.com/pymodbus-dev/pymodbus/1-overview)
- pymodbus server patterns: [DeepWiki — server examples](https://deepwiki.com/pymodbus-dev/pymodbus/5.2-server-examples)
- pymodbus callback server: [PyModbus 3.0.1 docs — callback server](https://pymodbus.readthedocs.io/en/v3.0.1/source/example/callback_server.html)
- pymodbus datastore: [PyModbus 3.8.3 docs — datastore](https://pymodbus.readthedocs.io/en/v3.8.3/source/library/datastore.html)
- luxtronik binary protocol: [Bouni/Luxtronik-2 documentation.md](https://github.com/Bouni/Luxtronik-2/blob/master/documentation.md)
- luxtronik Python library: [Bouni/python-luxtronik GitHub](https://github.com/Bouni/python-luxtronik)
- luxtronik lock_timeout: [luxtronik PyPI](https://pypi.org/project/luxtronik/)
- evcc modbus proxy pattern: [evcc modbusproxy docs](https://docs.evcc.io/en/docs/reference/configuration/modbusproxy)
- Luxtronik SHI Modbus registers (2.1 reference): [raibisch/mylibs — Modbusregister.md](https://github.com/raibisch/mylibs/blob/main/LuxModbusSHI/Modbusregister.md)
- structlog async: [structlog performance docs](https://www.structlog.org/en/stable/performance.html)
- pydantic-yaml: [pydantic-yaml PyPI](https://pypi.org/project/pydantic-yaml/)
- Docker graceful shutdown Python: [Medium — Gracefully Stopping Python in Docker](https://medium.com/@khaerulumam42/gracefully-stopping-python-processes-inside-a-docker-container-0692bb5f860f)

---
*Architecture research for: Modbus TCP proxy for Luxtronik 2.0 heat pump controllers*
*Researched: 2026-04-04*

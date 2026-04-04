# Project Research Summary

**Project:** luxtronik2-modbus-proxy
**Domain:** Protocol translation proxy — proprietary binary TCP to Modbus TCP (heat pump controller)
**Researched:** 2026-04-04
**Confidence:** HIGH

## Executive Summary

This project is a protocol translation proxy, not a transparent TCP relay. Experts in this space build a two-sided async architecture: a pymodbus TCP server on port 502 serves Modbus clients (evcc, Home Assistant) from an in-memory register cache, while a background polling engine briefly connects to the Luxtronik 2.0 controller on port 8889, reads all mapped parameters, updates the cache, and disconnects. The connect-read-disconnect pattern per poll cycle is not a performance trade-off — it is the fundamental correctness requirement imposed by the Luxtronik controller's single-connection enforcement and the need to coexist with Home Assistant's BenPru/luxtronik HACS integration.

The recommended stack is Python 3.12, pymodbus 3.12.x (async TCP server), luxtronik 0.3.14 (upstream binary protocol client), pydantic-settings 2.x (YAML config with env var overrides), and structlog 25.x (structured logging). The entire stack is well-understood with high source confidence. The architecture has five primary components — Modbus Server, Register Cache, Register Map, Polling Engine, and Luxtronik Client — with strict component boundaries enforced by an asyncio queue and lock. Build order follows data dependencies: register definitions first, then config, register map, cache, client, poller, server, and finally the main entry point wiring everything together.

The dominant risks are all architectural and must be addressed in Phase 1 before any feature work: the asyncio event loop starvation from blocking luxtronik socket calls (fix: run_in_executor), socket corruption from concurrent read/write (fix: asyncio lock), register addressing off-by-one (fix: document and test the convention before any mapping entries are written), and write-path safety (fix: per-parameter range validation rejecting out-of-range writes with Modbus exception code 3 before values reach the controller). A pre-project security concern — no real IP addresses or credentials in any committed file — must be handled before the first code commit.

## Key Findings

### Recommended Stack

The stack is effectively pre-decided by the domain: luxtronik 0.3.14 is the only maintained Python library for the proprietary Luxtronik 2.0 binary protocol, and pymodbus 3.12.x is the authoritative async Python Modbus TCP server. pydantic-settings provides YAML config with env var overrides in a single library, which matters for Docker deployments. structlog adds structured context (register address, parameter name, poll cycle) to every log event without replacing stdlib logging. Stay on pymodbus 3.12.x — pymodbus 4.0 is in development with breaking datastore API changes. Use python:3.12-slim as the Docker base; Alpine forces musl libc compilation and produces larger, slower images for pymodbus and pydantic-core.

**Core technologies:**
- Python 3.12: runtime — stable, slim Docker wheels install cleanly, pymodbus CI-tested
- `luxtronik` 0.3.14: Luxtronik binary protocol client — only maintained library, MIT, pure Python
- `pymodbus` 3.12.1: Modbus TCP async server — authoritative, actively maintained, full asyncio support
- `pydantic` 2.12.x + `pydantic-settings` 2.13.x: config validation and YAML loading — single library covers YAML + env var override
- `structlog` 25.5.0: structured logging — JSON in Docker, colorized in terminal, context binding per event
- `ruff`: linting + formatting — replaces black + flake8 + isort with one fast tool
- `pytest` 9.x + `pytest-asyncio` 1.3.x: testing — required for async polling loop tests

### Expected Features

The MVP centers on a working protocol bridge for evcc integration, with Home Assistant coexistence documented and verified. Features not in this list belong in v1.x or v2+.

**Must have (table stakes):**
- Modbus TCP server on port 502 (FC03/FC04/FC06/FC16) — without this, nothing works
- Connect-poll-disconnect cycle with configurable interval (default 30 s) — required for single-connection safety and HA HACS coexistence
- Curated default register set (~20 registers): flow/return/outside/hot-water temps, operating modes, DHW setpoint, electrical power — zero-config starting point
- Operating mode read + write (heating circuit + DHW circuit) — evcc requires this for SG-ready control
- SG-ready virtual register (0–3 int maps to Luxtronik mode combinations) — primary evcc integration mechanism
- YAML configuration file (host, port, poll_interval, optional extra registers) — no hardcoded values
- Docker container + docker-compose.yml — standard deployment target
- Structured logging (connection events, register reads/writes, errors) — essential for first-deployment debugging
- EN + DE user documentation with evcc YAML snippet — primary audience is German-speaking

**Should have (competitive differentiators):**
- Full parameter database (all 1,126 parameters accessible by name in config, not by raw ID) — power users; add post-validation
- Human-readable register names in logs — reduces support burden when users debug
- systemd service unit — Raspberry Pi users without Docker
- Health endpoint or diagnostic register — Docker healthcheck and monitoring hooks
- evcc upstream PR (device template) — community visibility, submit after register map is validated

**Defer (v2+):**
- Web UI register browser — CLI + docs cover the need with less complexity and attack surface
- Multi-device support — edge case; multiple proxy instances solve this
- Alerting / push notifications — belongs in HA/evcc, not the proxy

### Architecture Approach

The architecture is a read-through cache proxy with a background async poller. Two asyncio tasks run concurrently in the same event loop: the pymodbus async TCP server (always listening, serves reads from cache, queues writes) and the Polling Engine (periodic connect-read-write-disconnect cycle protected by an asyncio lock). All upstream Luxtronik I/O is serialized through the Polling Engine — the Modbus Server never touches the upstream connection directly. All blocking luxtronik library calls must run in a thread executor to prevent event loop starvation.

**Major components:**
1. Modbus TCP Server (`modbus_server.py`) — accepts inbound Modbus connections; serves reads from cache; queues writes via `ProxyDataBlock.async_setValues`
2. Register Cache (`register_cache.py`) — thread-safe in-memory pymodbus datablock; updated by poller, read by server; tracks `last_successful_read` for staleness detection
3. Register Map (`register_map.py`) — static mapping: luxtronik param/calc/visibility index to Modbus address using offset partitioning (params 0–1125, calcs 2000–2250, vis 3000–3354)
4. Polling Engine (`polling_engine.py`) — asyncio task; owns the asyncio lock; drains write queue; calls LuxtronikClient in executor; updates cache
5. Luxtronik Client (`luxtronik_client.py`) — thin wrapper around `luxtronik` lib; exposes typed connect/read_all/write_param/disconnect interface; unit-testable by mocking the library

### Critical Pitfalls

1. **HA persistent Modbus connection blocks coexistence** — Home Assistant's built-in Modbus integration holds the TCP socket open indefinitely (confirmed intentional by HA maintainer). The proxy must own the upstream connection using connect-poll-disconnect; never hold the port 8889 socket open between cycles. Must be the foundational design decision in Phase 1.

2. **Blocking luxtronik calls starvate asyncio event loop** — luxtronik 0.3.14 uses synchronous blocking socket calls. Called directly in a coroutine, every poll cycle freezes the event loop for 200–500 ms, causing all concurrent Modbus clients to time out. Wrap all upstream calls in `run_in_executor`. Cannot be retrofitted easily; must be in the initial async architecture.

3. **Concurrent read+write causes socket corruption** — If a Modbus write arrives while the polling loop is mid-read, both operations attempt to use the same socket, producing `struct.error` and `Bad file descriptor` (documented in Bouni/luxtronik issue #10). An asyncio lock serializing all upstream operations must be part of the first prototype.

4. **Write path without range validation damages hardware** — Luxtronik 2.0 applies any value sent to it with no server-side validation. Out-of-range writes can trigger safety lockouts requiring manual panel reset. The proxy must validate every write against per-parameter min/max/allowed-values metadata and return Modbus exception code 3 for rejections before any value reaches the upstream connection.

5. **Register addressing off-by-one** — Modbus protocol transmits 0-based wire addresses; Modbus.org documentation uses 1-based register numbers; pymodbus `ModbusSlaveContext` defaults to 1-based. A single wrong convention choice shifts every register by one. Document the convention explicitly, set `zero_mode` explicitly, and verify with an independent Modbus test tool before publishing the evcc template.

## Implications for Roadmap

Based on research, the critical architectural constraints drive a clear phase sequence. All five critical pitfalls must be addressed in Phase 1. Features that depend on the core working proxy come in Phase 2. Documentation and community-facing artifacts come last once the register map is validated.

### Phase 1: Core Proxy Foundation

**Rationale:** All critical pitfalls are architectural and must be resolved before any feature is built on top of them. The event loop starvation, socket corruption, and single-connection constraints are foundational — retrofitting any of them later requires rewriting the connection layer. Project security hygiene (gitignore, pre-commit hook, config.example.yaml) must come before the first code commit.

**Delivers:** A working protocol proxy that translates Luxtronik binary reads to Modbus TCP holding registers, handles writes safely, coexists with BenPru/luxtronik HACS, and runs in Docker. Not feature-complete, but architecturally correct and safe to expose to real hardware.

**Addresses:**
- Project initialization: `.gitignore`, pre-commit hook, `config.example.yaml` with placeholder values
- Async architecture: pymodbus async server + background polling task via `asyncio.gather`
- Blocking upstream calls in executor: `run_in_executor` wrapping all luxtronik library calls
- Single-connection safety: asyncio lock in Polling Engine; connect-read/write-disconnect per cycle
- Register map with documented convention: offset partitioning, `zero_mode` set explicitly, verified with Modbus test tool
- Write path with range validation: per-parameter min/max/allowed-values enforcement; Modbus exception 3 on rejection
- Stale cache detection: `last_successful_read` timestamp; exception code 4 after N missed polls
- Curated default register set: ~20 essential registers for evcc
- YAML config (host, port, poll_interval) with pydantic-settings validation
- Docker container with tini, SIGTERM handler, and TCP healthcheck
- Structured logging with structlog

**Avoids:**
- HA persistent connection blocking coexistence (Pitfall 1)
- asyncio event loop starvation (Pitfall 5)
- Concurrent read/write socket corruption (Pitfall 2)
- Write-path hardware damage (Pitfall 4)
- Register addressing off-by-one (Pitfall 3)
- Sensitive data in public repo (Pitfall 7)

### Phase 2: Integration-Ready Register Map and SG-Ready

**Rationale:** Once the proxy core is architecturally sound, the register map can be expanded and the SG-ready virtual register implemented. These depend on Phase 1's write path being validated. The evcc template cannot be published until the register addresses are confirmed stable.

**Delivers:** Complete curated register set covering all evcc and HA essentials; SG-ready virtual register (0–3 maps to mode combinations); validated evcc YAML snippet ready for documentation.

**Addresses:**
- SG-ready virtual register — requires working operating mode write from Phase 1
- Hot water boost via single register write — maps to SG-ready mode 2
- Extended default register set: compressor status, energy meters, fault state
- Operating mode enumeration validation (per-parameter allowed-values from register map metadata)

**Uses:** Register definitions module (`register_definitions/`) as the authoritative source for parameter IDs, types, scaling, and write constraints.

**Avoids:**
- Exposing all 1,126 parameters by default (Anti-Pattern 4)
- Flat register numbering without namespace (Anti-Pattern 5)

### Phase 3: User-Facing Polish and Documentation

**Rationale:** Documentation and community artifacts require a stable register map and validated evcc template. Bilingual documentation is a project requirement (CLAUDE.md mandate), not optional. This phase delivers the user-facing artifacts that make the project usable by the target audience (German-speaking home automation community).

**Delivers:** EN + DE user guide (install, configure, evcc YAML snippet); developer quickstart; systemd service unit; human-readable register names in logs; README.md and README.de.md.

**Addresses:**
- EN + DE documentation (required by CLAUDE.md)
- evcc YAML snippet (tested against running evcc instance, not just syntax-checked)
- Bilingual coexistence guide (HA BenPru + evcc + proxy timing recommendations)
- Human-readable register names in log messages (Modbus register + Luxtronik parameter name)
- systemd service unit for non-Docker deployments

### Phase 4: Extended Parameter Access and v1.x Enhancements

**Rationale:** The full parameter database (all 1,126 parameters accessible by name in config) is a differentiator but not required for the primary evcc use case. Add after Phase 1 is validated in real deployments. Health endpoint and evcc upstream PR belong here once the register map is proven stable.

**Delivers:** Full parameter database as user-configurable name lookup; health endpoint or diagnostic register; evcc upstream PR submitted.

**Addresses:**
- Full 1,126-parameter database (user adds parameters by name, not raw index)
- Health endpoint (`/health` HTTP or `0xFFFF` diagnostic register) for Docker healthcheck and monitoring
- evcc upstream device template PR (submit after register map validated in community)

### Phase Ordering Rationale

- Phase 1 must come first because all five critical pitfalls are architectural; no phase builds on a broken foundation.
- Phase 2 cannot start until the write path is validated (SG-ready requires trusted operating mode writes).
- Phase 3 cannot ship the evcc snippet until the register addresses are confirmed stable in Phase 2.
- Phase 4 adds power-user features after the core use case is proven in the community.
- The security setup (gitignore, pre-commit hook) precedes everything else — even the first Python file.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 2 (SG-ready mapping):** The exact Luxtronik parameter ID combinations for each SG-ready mode (0=Off, 1=Normal, 2=Boost, 3=Reduced) need validation against a real device; sources are community documentation rather than official specs.
- **Phase 2 (register address convention):** The evcc Modbus template convention (0-based vs. 1-based in YAML) should be confirmed against a running evcc instance before Phase 2 register addresses are locked.
- **Phase 4 (evcc upstream PR):** evcc has previously closed Luxtronik support as "not planned" (issue #19993, April 2025); the upstream PR approach needs a community engagement strategy, not just a code submission.

Phases with standard patterns (skip research-phase):
- **Phase 1 (async architecture):** pymodbus async server + background task + executor for blocking I/O is a well-documented pattern; implementation details are in ARCHITECTURE.md.
- **Phase 1 (Docker):** python:3.12-slim + tini + SIGTERM handler is standard; no research needed.
- **Phase 3 (bilingual docs):** Content creation, not technology research; structure is defined in CLAUDE.md.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Core stack pre-decided in PROJECT.md; versions verified against PyPI/official docs; pymodbus 3.12.1 and luxtronik 0.3.14 confirmed current |
| Features | MEDIUM-HIGH | Core proxy features HIGH (evcc/HA requirements confirmed from GitHub issues and community discussions); SG-ready mode mappings MEDIUM (community-documented, not official spec) |
| Architecture | HIGH | pymodbus async patterns documented in official docs and DeepWiki; luxtronik single-connection constraint confirmed by library docs and community reports; asyncio executor pattern is standard Python |
| Pitfalls | HIGH | Critical pitfalls verified from multiple sources: HA maintainer confirmation (issue #149494), luxtronik library issue #10, pymodbus official docs; recovery costs assessed |

**Overall confidence:** HIGH

### Gaps to Address

- **SG-ready mode combinations:** The mapping of SG-ready int (0–3) to specific Luxtronik parameter ID + value combinations needs hardware validation. Community sources agree on the concept but differ on exact parameter values for "Boost" mode.
- **evcc register convention (0-based vs. 1-based):** evcc Modbus YAML templates use a specific addressing convention that must be verified against a running instance before the register map is locked and the evcc template is published.
- **BenPru/luxtronik HACS poll interval:** The exact timing relationship between the proxy poll interval and the BenPru HACS poll interval for reliable coexistence needs testing. The 30 s default is recommended by the community but not formally documented as a safe threshold.
- **pymodbus 4.0 migration path:** pymodbus 4.0 is in development with breaking datastore API changes. The register cache design should remain abstracted behind a typed interface so migration requires changing only one module.

## Sources

### Primary (HIGH confidence)
- [pymodbus PyPI / GitHub](https://github.com/pymodbus-dev/pymodbus) — version 3.12.1, async architecture, datastore patterns, breaking changes in 4.0 dev
- [python-luxtronik GitHub](https://github.com/Bouni/python-luxtronik) — v0.3.14, writable parameter IDs, `safe=True` default, connection behavior
- [pydantic-settings PyPI](https://pypi.org/project/pydantic-settings/) — 2.13.1, `YamlConfigSettingsSource` built-in
- [structlog docs](https://www.structlog.org/) — 25.5.0, async performance, stdlib integration
- [HA core issue #149494](https://github.com/home-assistant/core/issues/149494) — persistent Modbus connection confirmed intentional by HA maintainer
- [Bouni/luxtronik issue #10](https://github.com/Bouni/luxtronik/issues/10) — concurrent read/write socket corruption documented with exact error messages
- [pymodbus docs — blocking code warning](https://pymodbus.readthedocs.io/) — event loop starvation explicitly documented
- [Bouni/python-luxtronik PyPI](https://pypi.org/project/luxtronik/) — `safe=True` default, NAND flash write risk
- [Continental Control Systems — Modbus misconceptions](https://www.ccontrolsys.com/) — register addressing convention as #1 source of exception codes

### Secondary (MEDIUM confidence)
- [evcc issue #19993](https://github.com/evcc-io/evcc/issues/19993) — required Luxtronik parameters for evcc; closed "not planned" April 2025
- [evcc discussion #7153](https://github.com/evcc-io/evcc/discussions/7153) — concrete register addresses for power (70–71), energy (68), hot water temp (11), setpoint (125)
- [evcc discussion #17257](https://github.com/evcc-io/evcc/discussions/17257) — HA/evcc coexistence problem statement; 30 s minimum polling interval recommendation
- [openHAB LuxtronikHeatpump binding](https://www.openhab.org/addons/bindings/luxtronikheatpump/) — full channel inventory for temperatures, operating modes, energy meters, SG-ready hooks
- [BenPru/luxtronik GitHub](https://github.com/BenPru/luxtronik) — writable parameters (~18), HA entity model
- [raibisch/mylibs — Luxtronik SHI Modbus registers](https://github.com/raibisch/mylibs/blob/main/LuxModbusSHI/Modbusregister.md) — 2.1 reference register layout (MEDIUM: for Luxtronik 2.1, not 2.0)
- [pythonspeed.com Docker base image guide](https://pythonspeed.com/) — slim vs. Alpine for wheel-dependent packages

### Tertiary (LOW confidence)
- Community forum posts (haustechnikdialog.de, evcc forum) — SG-ready mode combination values need hardware validation

---
*Research completed: 2026-04-04*
*Ready for roadmap: yes*

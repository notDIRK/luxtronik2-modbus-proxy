# PUBLIC-luxtronik2-modbus-proxy

## What This Is
Open-source Modbus TCP proxy for Luxtronik 2.0 heat pump controllers.
Translates the proprietary Luxtronik binary protocol (port 8889) to standard Modbus TCP (port 502),
enabling evcc, Home Assistant, and other Modbus-capable tools to control older heat pumps
that lack native Modbus support.

## SECURITY — READ FIRST

**This is a PUBLIC repository. Every file may end up on GitHub.**

### NEVER put these in any file:
- Real IP addresses (use `192.168.x.x` or `your-heatpump-ip`)
- Real hostnames or domain names (use `heatpump.example.local`)
- Passwords, PINs, tokens, API keys
- Personal names, email addresses
- Internal network topology

### Pre-commit hook
A pre-commit hook scans every commit for sensitive patterns and BLOCKS if found.
**Do not bypass with --no-verify.**

### Config files
- `config.example.yaml` — IN the repo (placeholder values only)
- `config.yaml` — NEVER in the repo (.gitignore'd)
- `.env` — NEVER in the repo (.gitignore'd)

## Code Standards
- **Language:** US English for all code, comments, variable names, commit messages
- **Comments:** Every function, every module, complex logic explained
- **Docstrings:** US English, Google style

## Documentation Standards
- **Two tracks:** Quickstart (developers) + Guide (end users / non-technical)
- **Two languages:** US English + German
- Structure: `docs/en/` and `docs/de/`
- `README.md` (EN) + `README.de.md` (DE)

## Tech Stack
- Python 3.10+
- `luxtronik` library (v0.3.14, MIT license) for binary protocol
- `pymodbus` for Modbus TCP server
- Docker for deployment
- Home Assistant integration via HACS

## Related Private Project
Private data, backups, and HA configs live in `~/claude-code/wp-alpha-innotec/` — NEVER reference or copy from there into this repo.

## GSD Workflow
Use `/gsd:progress` to check current state and next steps.

<!-- GSD:project-start source:PROJECT.md -->
## Project

**luxtronik2-modbus-proxy**

A Modbus TCP proxy for Luxtronik 2.0 heat pump controllers. Translates the proprietary Luxtronik binary protocol (port 8889) to standard Modbus TCP (port 502), enabling evcc, Home Assistant, and other Modbus-capable tools to control older heat pumps that lack native Modbus support. Targets thousands of heat pumps from Alpha Innotec, Novelan, Buderus, Nibe, Roth, Elco, and Wolf that have no firmware upgrade path.

**Core Value:** Owners of Luxtronik 2.0 heat pumps can integrate them into evcc and modern energy management systems via standard Modbus TCP, without needing to understand the proprietary protocol or Modbus register numbers.

### Constraints

- **Single connection**: Luxtronik 2.0 allows only one TCP connection — proxy must connect briefly and release
- **No Modbus on controller**: Port 502 is closed on the heat pump; the proxy provides it
- **No firmware upgrade**: Hardware limitation, cannot move to Luxtronik 2.1
- **Public repository**: No private data (IPs, hostnames, credentials) — ever
- **Language**: Code in US English, docs bilingual EN+DE
- **License**: MIT (matching luxtronik library ecosystem)
- **Tech stack**: Python 3.10+, `luxtronik` v0.3.14, `pymodbus`, Docker
<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->
## Technology Stack

## Recommended Stack
### Core Technologies
| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.10–3.12 | Runtime | pymodbus 3.12.1 tests against 3.10–3.14; 3.12 is stable, well-supported on Docker slim; avoid 3.13+ until ecosystem catches up |
| `luxtronik` | 0.3.14 | Luxtronik binary protocol client (port 8889) | Only maintained Python library for the proprietary Luxtronik 2.0 binary TCP protocol; MIT license, no dependencies; latest stable release Jun 2024; pre-decided in PROJECT.md |
| `pymodbus` | 3.12.1 | Modbus TCP server (port 502) | The authoritative Python Modbus implementation, actively maintained; 3.12.1 released Feb 2026; full async support via asyncio; `ModbusTcpServer` + custom `ModbusSequentialDataBlock` subclass is the correct pattern for a translating proxy; stay on 3.x — v4.0 is still dev with breaking datastore API changes |
| `pydantic` | 2.12.x | Config validation and type-safe data models | Industry standard for Python config schemas; v2 is significantly faster than v1; validates register map config at startup before any connection attempt |
| `pydantic-settings` | 2.13.x | YAML config file loading via `YamlConfigSettingsSource` | Ships `YamlConfigSettingsSource` as of 2.x — no extra library needed; supports env var overrides on top of YAML, which matters for Docker deployments |
| `structlog` | 25.5.0 | Structured logging | Production-grade structured logging with JSON output in Docker and colorized output in terminal; best choice for a network proxy where log context (register address, value, poll cycle) enriches every event |
### Supporting Libraries
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `PyYAML` | 6.x | YAML file parsing (pulled in by pydantic-settings) | Transitive dependency via pydantic-settings; no direct use required |
| `pytest` | 9.0.x | Unit and integration testing | Standard Python test runner; 9.x requires Python 3.10+, matching this project |
| `pytest-asyncio` | 1.3.x | Async test support | Required for testing async pymodbus server startup and the polling loop; use `asyncio_mode = auto` in pyproject.toml to avoid per-test decorator clutter |
| `pytest-cov` | 6.x | Coverage reporting | Integrates cleanly with pytest; use `--cov=src` in CI |
### Development Tools
| Tool | Purpose | Notes |
|------|---------|-------|
| `ruff` | Linting + formatting (replaces flake8 + black + isort) | Single fast tool; configure in `pyproject.toml`; enforces Google docstring style via `pydocstyle` rules |
| `mypy` | Static type checking | Catches protocol translation errors at dev time rather than runtime; use `strict = true` with pyproject.toml config |
| Docker `python:3.12-slim` | Container base image | `slim` beats Alpine for this project: pymodbus and pydantic-core ship as compiled wheels; Alpine's musl libc forces source compilation and produces larger, slower images |
| `docker-compose` | Local development stack | Single-file definition for proxy + any test fixture |
## Installation
# Core runtime
# Dev dependencies
## Alternatives Considered
| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| `pymodbus` 3.12.x | `pyModbusTCP` 0.3.x | pyModbusTCP is client-only; cannot serve Modbus TCP — not viable here |
| `pymodbus` 3.12.x | `pymodbus` 4.0.0dev | v4 is not yet stable; datastore API is changing; `getValues`/`setValues` removed in favor of `server.async_get/setValues`; wait for stable release |
| `structlog` | stdlib `logging` | stdlib logging works, but lacks structured context binding; structlog wraps stdlib so you can migrate later if needed |
| `pydantic-settings` with YAML | `dynaconf`, `python-dotenv` | dynaconf adds complexity for no gain; dotenv is env-var-only, no YAML; pydantic-settings covers both in one library |
| `python:3.12-slim` Docker base | `python:3.12-alpine` | Alpine forces musl libc; pymodbus and pydantic-core ship manylinux wheels that install instantly on slim but require source compilation on Alpine — larger images, longer builds |
| `ruff` | `black` + `flake8` + `isort` | ruff replaces all three with a single Rust-based tool; no reason to run three tools when one is faster and covers everything |
## What NOT to Use
| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `pymodbus` 2.x | Deprecated; no asyncio support; import paths changed completely in 3.0 | `pymodbus` 3.12.x |
| `pymodbus` 4.0.0dev | Pre-release; breaking API changes to datastore (your proxy's core component); no stable release date confirmed | `pymodbus` 3.12.x until 4.0 stable |
| `minimalmodbus` | Serial-only (RS-485); no TCP server capability | `pymodbus` |
| `umodbus` | Client-only; no server mode | `pymodbus` |
| `modbus-proxy` (PyPI) | TCP-to-TCP proxy only; cannot translate Luxtronik binary protocol — wrong abstraction level | Custom proxy using `pymodbus` server + `luxtronik` client |
| `luxtronik` v0.3.x from BenPru fork | BenPru/luxtronik is the HA integration repo, not the pypi library; different codebase, not a drop-in replacement | `luxtronik` 0.3.14 from Bouni/python-luxtronik via PyPI |
| `asyncio.sleep`-based polling without connect/disconnect | Luxtronik 2.0 allows exactly one TCP connection; holding the socket open blocks HA's BenPru integration | Connect → read/write → disconnect per poll cycle |
## Stack Patterns by Variant
- Use asyncio with a configurable `poll_interval` (default: 30s)
- Pattern: `await asyncio.sleep(poll_interval)` → connect luxtronik → read all mapped params → update pymodbus datastore → disconnect
- Write path: Modbus client writes register → pymodbus fires `setValues` callback → proxy connects luxtronik → writes param → disconnects
- Because: Luxtronik 2.0 enforces one connection; connect/disconnect per cycle is the only safe model
- Use `pydantic-settings` `BaseSettings` with `YamlConfigSettingsSource`
- User provides `config.yaml`; env vars (`LUXTRONIK_HOST`, `POLL_INTERVAL`) override YAML for Docker deployments
- Validate at startup: invalid register mappings fail fast before any network activity
- Use `python:3.12-slim` as base
- Multi-stage build: install dependencies in builder stage, copy only dist-packages to final stage
- Run as non-root user (UID 1000)
- Expose port 502 (or configurable `MODBUS_PORT`)
- Mount `config.yaml` as a volume at `/app/config.yaml`
- Subclass `ModbusSequentialDataBlock` to override `setValues` for write-through to Luxtronik
- Override `getValues` (or use async polling to keep datablock current) for reads
- Use `ModbusSlaveContext` with holding registers (FC3/FC6/FC16) as the primary register space
- Use `ModbusServerContext(single=True)` — single slave context covers all evcc/HA client requests
## Version Compatibility
| Package | Compatible With | Notes |
|---------|-----------------|-------|
| `pymodbus==3.12.1` | Python 3.10–3.14 | Tested by CI on all minor versions |
| `luxtronik==0.3.14` | Python 3.x (no stated floor) | No compiled extensions; pure Python; works on 3.10+ |
| `pydantic==2.12.x` | Python 3.8+ | v2 is not compatible with v1 API; use v2 from the start |
| `pydantic-settings==2.13.x` | `pydantic>=2.7.0` | `YamlConfigSettingsSource` available since pydantic-settings 2.3+ |
| `structlog==25.5.0` | Python 3.8+ | No compatibility issues with any stack component |
| `pytest-asyncio==1.3.x` | `pytest>=9.0` | v1.x is a major revision; `asyncio_mode = auto` is the recommended config |
## Sources
- [pymodbus PyPI](https://pypi.org/project/pymodbus/) — version 3.12.1, released Feb 19 2026; Python 3.10+ requirement confirmed
- [pymodbus GitHub](https://github.com/pymodbus-dev/pymodbus) — async architecture, datastore patterns confirmed
- [pymodbus API changes (4.0 dev)](https://pymodbus.readthedocs.io/en/latest/source/api_changes.html) — breaking datastore changes confirmed; reason to stay on 3.x
- [python-luxtronik GitHub Releases](https://github.com/Bouni/python-luxtronik/releases) — v0.3.14 released Jun 7 2024; latest stable
- [luxtronik PyPI](https://pypi.org/project/luxtronik/) — version 0.3.14 current; no dependencies
- [structlog PyPI / docs](https://www.structlog.org/) — version 25.5.0, Python 3.8+ support confirmed
- [pydantic PyPI](https://pypi.org/project/pydantic/) — version 2.12.5 stable
- [pydantic-settings PyPI](https://pypi.org/project/pydantic-settings/) — version 2.13.1; `YamlConfigSettingsSource` confirmed built-in
- [pytest PyPI](https://pypi.org/project/pytest/) — version 9.0.2, Python 3.10+ required
- [pytest-asyncio PyPI](https://pypi.org/project/pytest-asyncio/) — version 1.3.0
- [pythonspeed.com Docker base image guide (Feb 2026)](https://pythonspeed.com/articles/base-image-python-docker-images/) — slim vs Alpine recommendation for wheel-dependent packages (MEDIUM confidence — third-party but authoritative author)
- [evcc heat pump Modbus discussion](https://github.com/evcc-io/evcc/discussions/7153) — Modbus register patterns for heat pump integration confirmed (MEDIUM confidence)
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, or `.github/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->

---
phase: 01-core-proxy
plan: 01
subsystem: infra
tags: [pydantic-settings, structlog, modbus, register-map, config, logging]

# Dependency graph
requires: []
provides:
  - Installable Python package (luxtronik2-modbus-proxy 0.1.0)
  - ProxyConfig with YAML load, env var overrides, and startup validation
  - configure_logging with JSON/Console renderer switching
  - RegisterMap with address lookup, writability checks, and write value validation
  - Curated holding registers: HeatingMode (addr 3), HotWaterMode (addr 4), DHW setpoint (addr 105)
  - Curated input registers: temperatures (10,11,15,17), operating mode (80), heat output (257)
affects: [01-02, 01-03, 01-04]

# Tech tracking
tech-stack:
  added:
    - luxtronik==0.3.14
    - pymodbus==3.12.1
    - pydantic>=2.12,<3
    - pydantic-settings[yaml]>=2.13,<3
    - structlog>=25.0
    - PyYAML>=6.0
    - pytest>=9.0, pytest-asyncio>=1.3, pytest-cov, ruff, mypy
  patterns:
    - "ProxyConfig subclass pattern for yaml_file override in load_config()"
    - "env vars take priority over YAML (init > env > yaml > defaults)"
    - "ParameterDef + CalculationDef dataclasses with validation metadata"
    - "RegisterMap builds from dicts at init; exposes typed lookup methods"

key-files:
  created:
    - pyproject.toml
    - setup.py (shim for older pip editable install support)
    - .gitignore
    - src/luxtronik2_modbus_proxy/__init__.py
    - src/luxtronik2_modbus_proxy/config.py
    - src/luxtronik2_modbus_proxy/logging_config.py
    - src/luxtronik2_modbus_proxy/register_definitions/__init__.py
    - src/luxtronik2_modbus_proxy/register_definitions/parameters.py
    - src/luxtronik2_modbus_proxy/register_definitions/calculations.py
    - src/luxtronik2_modbus_proxy/register_map.py
    - tests/__init__.py
    - tests/unit/__init__.py
    - tests/unit/test_config.py
    - tests/unit/test_register_map.py
  modified: []

key-decisions:
  - "env vars take priority over YAML (not YAML over env); required for Docker deployments to override config"
  - "PyYAML added as explicit dependency; pydantic-settings[yaml] does not install it transitively on all environments"
  - "setup.py shim added for editable install on pip 22.x (system pip on Ubuntu 22.04)"
  - "load_config() creates a dynamic subclass to override yaml_file at class level (pydantic-settings constraint)"
  - "uv used as install tool in this environment; pyproject.toml build system uses setuptools.build_meta"

patterns-established:
  - "Pattern: ProxyConfig dynamic subclass in load_config() to override yaml_file path per-call"
  - "Pattern: RegisterMap wraps HOLDING_REGISTERS/INPUT_REGISTERS dicts into RegisterEntry dataclasses at init"
  - "Pattern: validate_write_value() checks allowed_values first, then min/max range"

requirements-completed: [REG-01, OBS-01]

# Metrics
duration: 6min
completed: 2026-04-04
---

# Phase 01 Plan 01: Project Scaffold and Data Layer Summary

**Installable Python package with pydantic-settings YAML config, structlog JSON/console logging, and a curated RegisterMap covering all 9 Phase 1 registers with write validation.**

## Performance

- **Duration:** 6 minutes
- **Started:** 2026-04-04T18:40:46Z
- **Completed:** 2026-04-04T18:46:46Z
- **Tasks:** 2 of 2
- **Files modified:** 14 created, 0 modified

## Accomplishments

### Task 1: Project scaffold, config, and logging

Created the complete project scaffold:

- `pyproject.toml` with all runtime dependencies (luxtronik, pymodbus, pydantic-settings[yaml], structlog) and dev dependencies (pytest, pytest-asyncio, ruff, mypy)
- `ProxyConfig(BaseSettings)` with 8 validated fields including `poll_interval` (ge=10), `enable_writes` (safety default False), `write_rate_limit` (ge=10)
- `load_config(yaml_path)` convenience function using dynamic subclass pattern to override yaml_file path
- `configure_logging(log_level)` with TTY detection, ConsoleRenderer for dev, JSONRenderer for production
- 6 unit tests for config loading, defaults, validation, env var override, and logging calls — all pass

### Task 2: Register definitions and register map

Created the curated register layer:

- `ParameterDef` and `CalculationDef` dataclasses with validation metadata (allowed_values, min/max)
- `HOLDING_REGISTERS`: 3 writable parameters (HeatingMode addr 3, HotWaterMode addr 4, DHW setpoint addr 105)
- `INPUT_REGISTERS`: 6 read-only calculations (temps at 10/11/15/17, op mode at 80, heat output at 257)
- `RegisterEntry` dataclass combining Modbus address with Luxtronik metadata
- `RegisterMap` class with address lookup, writability checks, write value validation, and block size constants (HOLDING=1200, INPUT=260)
- 13 unit tests covering all lookup, writability, and validation scenarios — all pass

## Test Results

```
19 passed in 0.07s
```

All 19 unit tests pass (6 config + 13 register map).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Dependency] Added PyYAML as explicit dependency**
- **Found during:** Task 1 verification
- **Issue:** `pydantic-settings[yaml]` requires PyYAML but does not install it transitively in all environments; `YamlConfigSettingsSource` raised `ImportError` at runtime
- **Fix:** Added `"PyYAML>=6.0"` to `[project.dependencies]` in pyproject.toml; updated install spec to `pydantic-settings[yaml]`
- **Files modified:** pyproject.toml

**2. [Rule 3 - Blocking] setup.py shim for editable install**
- **Found during:** Task 1 setup
- **Issue:** System pip 22.0.2 (Ubuntu 22.04) lacks PEP 660 support; `pip install -e .` failed with "missing build_editable hook"
- **Fix:** Added `setup.py` shim (7 lines) that calls `setup()` and defers all metadata to pyproject.toml; switched to `uv` for fast dependency installation in the virtualenv
- **Files modified:** setup.py (created)

**3. [Rule 1 - Bug] Fixed env var / YAML priority order**
- **Found during:** Task 1 test run (test_config_env_var_override failed)
- **Issue:** `settings_customise_sources` returned `(init, yaml, env_settings)` — YAML took priority over env vars, breaking Docker override behavior
- **Fix:** Reordered to `(init, env_settings, yaml)` — env vars now correctly override YAML values
- **Files modified:** src/luxtronik2_modbus_proxy/config.py

**4. [Rule 2 - Missing] Added .gitignore**
- **Found during:** Post-task cleanup (git status showed build artifacts untracked)
- **Issue:** No `.gitignore` existed; `__pycache__/`, `*.egg-info/`, `.venv/` were untracked
- **Fix:** Created `.gitignore` covering Python build artifacts, virtual environments, pytest cache, and the security-critical `config.yaml` / `.env` exclusions
- **Files modified:** .gitignore (created)

## Known Stubs

None. All register definitions are wired to real Luxtronik parameter IDs confirmed from luxtronik 0.3.14 source.

## Threat Flags

None. This plan only introduces config loading and static in-memory data structures — no network endpoints, no file access beyond the config file read at startup, no schema changes.

## Self-Check: PASSED

All key files exist and all commits are present in git history.

**Files verified:** pyproject.toml, src/luxtronik2_modbus_proxy/__init__.py, config.py, logging_config.py, register_definitions/parameters.py, register_definitions/calculations.py, register_map.py, tests/unit/test_config.py, tests/unit/test_register_map.py

**Commits verified:** d565931 (RED tests config), 17ea0a3 (feat: scaffold+config+logging), a61a051 (RED tests register_map), 023f19a (feat: register definitions+map), b30442e (chore: .gitignore)

---
phase: 02-integration-ready-register-map
plan: 02
subsystem: config-and-cli
tags: [config, register-map, cli, pydantic, argparse, difflib]
dependency_graph:
  requires: ["02-01"]
  provides: ["RegistersConfig", "resolve_parameter_names", "list-params CLI"]
  affects: ["config.py", "register_map.py", "main.py", "config.example.yaml"]
tech_stack:
  added: ["difflib (stdlib)", "argparse subparsers"]
  patterns: ["pydantic BaseModel nested config", "fuzzy name validation", "subcommand CLI pattern"]
key_files:
  created: []
  modified:
    - src/luxtronik2_modbus_proxy/config.py
    - src/luxtronik2_modbus_proxy/register_map.py
    - src/luxtronik2_modbus_proxy/main.py
    - config.example.yaml
    - tests/unit/test_config.py
    - tests/unit/test_register_map.py
decisions:
  - "Curated defaults (addresses 3, 4, 105) always present regardless of user config — extra params skip duplicates silently"
  - "difflib.get_close_matches with cutoff=0.6 provides useful Did-you-mean suggestions for typos"
  - "list-params --type selector supports all three register spaces (parameters, calculations, visibilities)"
metrics:
  duration: "~10 minutes"
  completed: "2026-04-05T20:22:00Z"
  tasks_completed: 2
  files_modified: 6
---

# Phase 02 Plan 02: User-Selectable Parameters and list-params CLI Summary

**One-liner:** RegistersConfig YAML section + fuzzy name validation in RegisterMap + list-params subcommand for parameter discovery across all 1,126 Luxtronik parameters.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add RegistersConfig to ProxyConfig and dynamic parameter loading to RegisterMap | `0e01424` | config.py, register_map.py, main.py, test_config.py, test_register_map.py |
| 2 | Add list-params CLI subcommand and update config.example.yaml | `d392554` | main.py, config.example.yaml |

## What Was Built

### RegistersConfig (config.py)

Added `RegistersConfig(BaseModel)` with a `parameters: list[str]` field (default empty list). Added `registers: RegistersConfig` field to `ProxyConfig`. Users can now write:

```yaml
registers:
  parameters:
    - ID_Einst_WK_akt
    - ID_Ba_Hz_MK3_akt
```

### Dynamic Parameter Loading (register_map.py)

Added `resolve_parameter_names(names: list[str]) -> dict[int, ParameterDef]`:
- Validates each name against `NAME_TO_INDEX` (1,126-entry reverse lookup)
- Uses `difflib.get_close_matches(cutoff=0.6)` for typo suggestions
- Raises `ValueError("Unknown parameter name '{name}'. Did you mean: {suggestions}?")` on failure

Updated `RegisterMap.__init__` to accept `extra_param_names: list[str] | None = None`:
- Resolves names via `resolve_parameter_names` at startup (fail-fast before network)
- Merges extra params into `self._holding`, skipping addresses already present (curated defaults take precedence)

Wired `config.registers.parameters` to `RegisterMap` in `main.py`.

### list-params CLI Subcommand (main.py)

Converted `cli()` from single-arg to subcommand-based argparse:
- `luxtronik2-modbus-proxy` (no subcommand): runs proxy as before
- `luxtronik2-modbus-proxy list-params`: prints tabular parameter database (1,126 entries)
- `luxtronik2-modbus-proxy list-params --search <term>`: case-insensitive substring filter
- `luxtronik2-modbus-proxy list-params --type calculations|visibilities`: switch register space

### config.example.yaml

Added commented-out `registers:` section with discovery instructions referencing the `list-params` command.

## Verification Results

```
35 passed in 0.14s   (pytest test_config.py + test_register_map.py)
1126 parameters      (list-params total count)
1                    (grep count for ID_Ba_Hz_akt in filtered search)
2                    (grep count for "Unknown parameter name" on bogus input — error message appears on both stderr lines)
```

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None. All functionality is fully wired: RegistersConfig loads from YAML, names are resolved at startup, list-params outputs live data from the parameter database.

## Threat Surface Scan

No new network endpoints, auth paths, or file access patterns introduced. The `resolve_parameter_names` function implements T-02-04 mitigation as specified: all user-supplied names validated against `NAME_TO_INDEX` at startup before any network activity.

## Self-Check: PASSED

- `src/luxtronik2_modbus_proxy/config.py` — FOUND (RegistersConfig class, registers field)
- `src/luxtronik2_modbus_proxy/register_map.py` — FOUND (resolve_parameter_names, extra_param_names)
- `src/luxtronik2_modbus_proxy/main.py` — FOUND (list-params subcommand, _list_params function)
- `config.example.yaml` — FOUND (registers: section commented out)
- Commit `0e01424` — FOUND
- Commit `d392554` — FOUND

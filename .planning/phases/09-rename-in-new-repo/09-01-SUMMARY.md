---
phase: 09-rename-in-new-repo
plan: 01
subsystem: rebrand
tags: [rename, hacs, ha-integration, phase-9]
wave: 1
requires: []
provides:
  - custom_components/luxtronik2_hass (HA integration at new name)
  - manifest.json with domain luxtronik2_hass and "Luxtronik 2.0 (Home Assistant)" name
  - pyproject.toml distribution name luxtronik2-hass
affects:
  - /home/dwolbeck/claude-code/luxtronik2-hass (working copy only; source repo unchanged)
tech-stack:
  added: []
  patterns:
    - git mv for folder rename preserves file history
key-files:
  created: []
  modified:
    - /home/dwolbeck/claude-code/luxtronik2-hass/custom_components/luxtronik2_hass/manifest.json
    - /home/dwolbeck/claude-code/luxtronik2-hass/custom_components/luxtronik2_hass/const.py
    - /home/dwolbeck/claude-code/luxtronik2-hass/custom_components/luxtronik2_hass/__init__.py
    - /home/dwolbeck/claude-code/luxtronik2-hass/custom_components/luxtronik2_hass/config_flow.py
    - /home/dwolbeck/claude-code/luxtronik2-hass/custom_components/luxtronik2_hass/coordinator.py
    - /home/dwolbeck/claude-code/luxtronik2-hass/custom_components/luxtronik2_hass/sensor.py
    - /home/dwolbeck/claude-code/luxtronik2-hass/custom_components/luxtronik2_hass/select.py
    - /home/dwolbeck/claude-code/luxtronik2-hass/custom_components/luxtronik2_hass/number.py
    - /home/dwolbeck/claude-code/luxtronik2-hass/custom_components/luxtronik2_hass/button.py
    - /home/dwolbeck/claude-code/luxtronik2-hass/tests/unit/test_select.py
    - /home/dwolbeck/claude-code/luxtronik2-hass/tests/unit/test_number.py
    - /home/dwolbeck/claude-code/luxtronik2-hass/tests/unit/__init__.py
    - /home/dwolbeck/claude-code/luxtronik2-hass/tests/__init__.py
    - /home/dwolbeck/claude-code/luxtronik2-hass/pyproject.toml
    - /home/dwolbeck/claude-code/luxtronik2-hass/hacs.json
    - /home/dwolbeck/claude-code/luxtronik2-hass/README.md
    - /home/dwolbeck/claude-code/luxtronik2-hass/README.de.md
  renamed:
    - custom_components/luxtronik2_modbus_proxy -> custom_components/luxtronik2_hass (via git mv)
decisions:
  - Folder renamed via `git mv` to preserve git blame/history for all 19 files (18 tracked as pure renames, manifest.json shown as delete+create because content similarity dropped below git's rename threshold)
  - `BACKUP_DIR = "luxtronik2_backups"` in const.py preserved (D-10 lock — user-facing HA path)
  - "Luxtronik 2.0" product name literals in translations/strings.json left untouched (heat pump brand, not a rename target)
  - `_SG_READY_PATH` in test_select.py rewritten to point at `src/luxtronik2_hass/sg_ready.py` per strict mapping table; the path will never exist in this HA-only repo so the cross-validation test continues to skip as intended
  - Comment in test_select.py referencing the archived standalone proxy repo rephrased to avoid the banned literal while preserving meaning
metrics:
  duration: ~6 min
  completed: 2026-04-10
  tasks: 3
  files_touched: 19 (incl. renamed folder contents)
  tests_passed: 36
  tests_skipped: 1
---

# Phase 9 Plan 01: Rename luxtronik2_modbus_proxy -> luxtronik2_hass Summary

**One-liner:** HACS integration extract rebranded from `luxtronik2_modbus_proxy` to `luxtronik2_hass` across folder, HA domain, Python imports, package metadata, docstrings, URLs, and placeholder READMEs with pytest still green.

## What Was Done

### Task 1 — Core identity (manifest + const + folder)

- `git mv custom_components/luxtronik2_modbus_proxy custom_components/luxtronik2_hass` (preserves file history)
- `custom_components/luxtronik2_hass/manifest.json` overwritten with the locked target JSON:
  - `domain`: `luxtronik2_hass`
  - `name`: `"Luxtronik 2.0 (Home Assistant)"`
  - `documentation`: `https://github.com/notDIRK/luxtronik2-hass`
  - `issue_tracker`: `https://github.com/notDIRK/luxtronik2-hass/issues`
  - `version`: `1.1.2` (unchanged per locked decision)
- `custom_components/luxtronik2_hass/const.py`:
  - Module docstring updated to `"""Constants for the Luxtronik 2.0 (Home Assistant) integration."""`
  - `DOMAIN = "luxtronik2_hass"`
  - **`BACKUP_DIR = "luxtronik2_backups"` preserved** (D-10 — user-facing HA path)

### Task 2 — Tests, pyproject, READMEs, hacs.json, and platform docstrings

- `tests/unit/test_select.py`: path constants `_SELECT_PATH`, `_STRINGS_PATH`, `_SG_READY_PATH` rewritten to `luxtronik2_hass`; stale comment referring to the archived standalone proxy repo rephrased
- `tests/unit/test_number.py`: `_NUMBER_PATH`, `_STRINGS_PATH` rewritten to `luxtronik2_hass`
- `tests/__init__.py` and `tests/unit/__init__.py`: package comments rewritten
- `pyproject.toml`: `name = "luxtronik2-hass"` (hyphen form, PyPI convention)
- `hacs.json`: `name` field updated to `"Luxtronik 2.0 (Home Assistant)"`
- `README.md` (placeholder): title and description updated to new name
- `README.de.md` (Phase 8 placeholder content): title, HACS custom-repo URL, integration name, and ASCII diagram label updated
- Docstrings in `__init__.py`, `config_flow.py` (3 hits), `coordinator.py`, `sensor.py`, `select.py`, `number.py`, `button.py` — all legacy "Luxtronik 2 Modbus Proxy" references replaced with "Luxtronik 2.0 (Home Assistant)"

### Task 3 — Verification

All checks passed from `/home/dwolbeck/claude-code/luxtronik2-hass`:

1. Structural: `custom_components/luxtronik2_hass/` exists; `custom_components/luxtronik2_modbus_proxy/` does not.
2. Manifest + const content checks: all six required grep assertions green.
3. Full rename sweep: `grep -rn 'luxtronik2_modbus_proxy\|luxtronik2-modbus-proxy\|Luxtronik 2 Modbus Proxy' . --exclude-dir=.git` exits 1 (no matches).
4. `pytest tests/unit/test_select.py tests/unit/test_number.py -q` -> `36 passed, 1 skipped in 0.23s`
5. `pytest -q` (full suite) -> `36 passed, 1 skipped in 0.15s`
6. Import smoke test: `importlib.util.find_spec('luxtronik2_hass')` -> `IMPORT OK`

The 1 skipped test is the `sg_ready` cross-validation in `test_select.py` (gracefully absent `src/luxtronik2_hass/sg_ready.py` in this HA-only repo — expected Phase 8+ behavior).

## git log (new working copy)

```
a4d4deb refactor(09): rename luxtronik2_modbus_proxy to luxtronik2_hass
49b7b90 fix(08): skip SG_READY cross-validation when proxy src/ absent
6910326 chore(08): trim pyproject, add placeholder README, drop proxy-coupled tests
0319f9c docs: rewrite README (EN+DE) — highlight standalone HA integration
220c7b1 chore: bump version to 1.1.2
```

The rename commit `a4d4deb` shows 27 files changed, 44 insertions(+), 45 deletions(-), with 18 files recorded as pure git renames (similarity 80%–100%) and manifest.json recorded as delete+create because content similarity dropped below git's rename threshold.

## Requirements Satisfied

- **RENAME-01** `manifest.json` — domain, name, documentation URL, issue_tracker URL all updated
- **RENAME-02** folder renamed via `git mv` preserving history
- **RENAME-03** `const.py` DOMAIN + all Python imports/paths (custom_components + tests) updated
- **RENAME-04** `pyproject.toml` distribution name updated to `luxtronik2-hass`
- **RENAME-05** internal strings, docstrings, URLs in READMEs and hacs.json updated

All four Phase 9 Success Criteria verified green in Task 3.

## Deviations from Plan

Only minor, all documented in decisions above:

1. **[Rule 2 — completeness] hacs.json rename.** The plan's task list did not enumerate `hacs.json`, but the pre-edit sweep flagged `"name": "Luxtronik 2 Modbus Proxy"` inside it. Updated to `"Luxtronik 2.0 (Home Assistant)"` — required to satisfy the plan's `grep -r ... = exit 1` success criterion.
2. **[Rule 2 — completeness] README.de.md rename.** README.de.md contains full Phase-8 README content (not just the short Phase-8 placeholder shown in README.md). Updated three specific substrings (title, HACS URL, integration name) and the ASCII-diagram label, without expanding or rewriting the README — that remains Phase 10's responsibility.
3. **[Rule 2 — completeness] Platform docstrings in 7 custom_components files.** The plan's Task 1 grep only matched underscore-form `luxtronik2_modbus_proxy`, but the banned literal `"Luxtronik 2 Modbus Proxy"` also appeared in module docstrings in `__init__.py`, `config_flow.py`, `coordinator.py`, `sensor.py`, `select.py`, `number.py`, `button.py`. All updated to `"Luxtronik 2.0 (Home Assistant)"`.
4. **[Rule 2 — completeness] Stale comment in test_select.py.** Lines 160-163 referenced the archived standalone proxy repo by the banned literal `luxtronik2-modbus-proxy`. Rephrased to "the archived standalone proxy repository" to preserve factual historical context without violating the sweep rule.

None of these required user decisions — all were direct consequences of the locked rename mapping table and the zero-hit grep success criterion.

## Preservation Check

- ✅ `BACKUP_DIR = "luxtronik2_backups"` still present in const.py (user-facing HA path per D-10)
- ✅ "Luxtronik 2.0" product-name strings in `translations/*.json` and `strings.json` untouched (heat pump brand, not a rename target)
- ✅ `version: "1.1.2"` unchanged
- ✅ git history preserved for all tracked files via `git mv`

## Self-Check: PASSED

Structural checks:
- `custom_components/luxtronik2_hass/` exists — FOUND
- `custom_components/luxtronik2_modbus_proxy/` removed — CONFIRMED
- Commit `a4d4deb` in new working copy log — FOUND
- Full sweep `grep -rn 'luxtronik2_modbus_proxy\|luxtronik2-modbus-proxy\|Luxtronik 2 Modbus Proxy' . --exclude-dir=.git` — exit 1 (no matches)
- pytest (full) — 36 passed, 1 skipped
- Import smoke test — IMPORT OK

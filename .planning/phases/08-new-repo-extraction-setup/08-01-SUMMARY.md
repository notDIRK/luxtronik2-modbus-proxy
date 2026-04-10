---
phase: 08-new-repo-extraction-setup
plan: 01
subsystem: repo-split
tags: [filter-repo, history-rewrite, hacs, repo-split, v1.2]
dependency_graph:
  requires: []
  provides:
    - /home/dwolbeck/claude-code/luxtronik2-hass (clean local working copy)
    - rewritten git history preserving Phase 4-7 HACS commits
    - trimmed pyproject.toml (dev-only, no proxy entry points)
    - placeholder README.md (Phase 10 will rewrite)
  affects:
    - none (Phase 8 is strictly local; no push, no remote)
tech_stack:
  added: []
  patterns:
    - git clone --no-local + two-pass git filter-repo
    - whitelist path filter, then --invert-paths drop pass
key_files:
  created:
    - /home/dwolbeck/claude-code/luxtronik2-hass/.git/
    - /home/dwolbeck/claude-code/luxtronik2-hass/pyproject.toml (trimmed)
    - /home/dwolbeck/claude-code/luxtronik2-hass/README.md (placeholder)
  modified:
    - /home/dwolbeck/claude-code/luxtronik2-hass/tests/unit/test_select.py (skip SG_READY proxy cross-check)
  deleted:
    - /home/dwolbeck/claude-code/luxtronik2-hass/tests/unit/test_sensor.py
    - /home/dwolbeck/claude-code/luxtronik2-hass/tests/unit/test_register_map.py
    - /home/dwolbeck/claude-code/luxtronik2-hass/tests/unit/test_register_definitions.py
    - /home/dwolbeck/claude-code/luxtronik2-hass/tests/unit/test_register_cache.py
    - /home/dwolbeck/claude-code/luxtronik2-hass/tests/unit/test_config.py
    - /home/dwolbeck/claude-code/luxtronik2-hass/tests/unit/test_sg_ready.py
    - /home/dwolbeck/claude-code/luxtronik2-hass/tests/integration/test_proxy_mock.py
    - /home/dwolbeck/claude-code/luxtronik2-hass/tests/integration/ (empty dir removed)
decisions:
  - "SHAs rewritten by filter-repo as expected; SPLIT-02 verified via commit messages/dates + git blame graph walk, not byte-identical SHAs"
  - "Dropped proxy-specific .github workflows (publish.yml, docs.yml) in filter-repo pass 2"
  - "Kept README.de.md in extraction (Phase 10 will rewrite both EN+DE READMEs)"
metrics:
  duration_minutes: ~5
  completed_date: "2026-04-10"
  tasks_completed: 4
  files_created: 2
  files_modified: 1
  files_deleted: 8
requirements:
  - SPLIT-02
  - SPLIT-03
---

# Phase 8 Plan 01: New Repo Extraction Summary

**One-liner:** Clean local working copy of `luxtronik2-hass` created via two-pass `git filter-repo` extraction from `PUBLIC-luxtronik2-modbus-proxy`, history preserved for HACS integration, proxy-coupled tests pruned, pytest green.

## Target

**Path:** `/home/dwolbeck/claude-code/luxtronik2-hass`
**Created:** 2026-04-10
**Source:** `/home/dwolbeck/claude-code/PUBLIC-luxtronik2-modbus-proxy` (unmodified)
**Remote:** none (Phase 8 is local-only; Phase 11 pushes to `notDIRK/luxtronik2-hass`)

## Extraction Method

Two-pass `git filter-repo`:

**Pass 1 — whitelist keep paths:**
```
git filter-repo --force \
  --path custom_components/ \
  --path tests/ \
  --path .github/ \
  --path hacs.json \
  --path pyproject.toml \
  --path README.md \
  --path README.de.md
```

**Pass 2 — drop proxy-specific workflows:**
```
git filter-repo --force --invert-paths \
  --path .github/workflows/publish.yml \
  --path .github/workflows/docs.yml
```

`--force` was required on both passes: pass 1 because `git remote remove origin` ran first (filter-repo then considers the repo "not fresh"), pass 2 because pass 1 already rewrote history. See deviation note below.

## History Preservation Proof (SPLIT-02)

| File | Commits in new repo | Sample messages |
|------|---------------------|-----------------|
| `custom_components/luxtronik2_modbus_proxy/coordinator.py` | 3 | `feat(05-01): add LuxtronikCoordinator with connect-per-call polling`; `feat(07-01): add write methods and rate limiting to LuxtronikCoordinator`; `fix(coordinator): use dict.items() for luxtronik parameter/calculation extraction` |
| `custom_components/luxtronik2_modbus_proxy/config_flow.py` | 3 | `feat(05-02): add config flow with connection test and BenPru conflict detection`; `feat(260409-l1l): add LuxtronikOptionsFlow to config_flow.py`; `fix(config_flow): remove manual config_entry init from OptionsFlow` |

`git blame` on both files resolves to real SHAs (no `00000000` lines). SHAs are rewritten versus the source repo (expected — filter-repo rewrites any commit that touched dropped paths) and documented in `.git/filter-repo/commit-map` (171 mappings).

## Preserved Commit Messages (sample, Phase 4-7)

```
7e275c6 test(07-03): add unit tests for select and number entity logic
cdbc2b7 feat(07-02): add number entity platform for temperature setpoints
76d3847 feat(07-03): add EN+DE translations for select and number entities
bb7400d feat(07-02): add select entity platform for HeatingMode, HotWaterMode, SG-Ready
8695e24 feat(07-01): register select and number platforms in __init__.py
cf43bc8 feat(07-01): add write methods and rate limiting to LuxtronikCoordinator
762834c feat(06-01): create sensor platform with core entity descriptions
cd32ffc feat(05-02): wire __init__.py to coordinator and enable config_flow in manifest
3e1849e feat(05-02): add config flow with connection test and BenPru conflict detection
a7962ae feat(05-01): add LuxtronikCoordinator with connect-per-call polling
```

## Forbidden-File Absence Proof (SPLIT-03)

| Path | Exists? |
|------|---------|
| `src/` | no |
| `Dockerfile` | no |
| `docker-compose.yml` | no |
| `config.example.yaml` | no |
| `mkdocs.yml` | no |
| `contrib/` | no |
| `docs/` | no |
| `luxtronik2-modbus-proxy.service` (systemd unit) | no |
| `.github/workflows/publish.yml` | no |
| `.github/workflows/docs.yml` | no |

## Tree Listing (tracked files only)

```
custom_components/luxtronik2_modbus_proxy/brand/icon.png
custom_components/luxtronik2_modbus_proxy/brand/icon@2x.png
custom_components/luxtronik2_modbus_proxy/brand/logo.png
custom_components/luxtronik2_modbus_proxy/button.py
custom_components/luxtronik2_modbus_proxy/config_flow.py
custom_components/luxtronik2_modbus_proxy/const.py
custom_components/luxtronik2_modbus_proxy/coordinator.py
custom_components/luxtronik2_modbus_proxy/__init__.py
custom_components/luxtronik2_modbus_proxy/icon.png
custom_components/luxtronik2_modbus_proxy/icon@2x.png
custom_components/luxtronik2_modbus_proxy/logo.png
custom_components/luxtronik2_modbus_proxy/manifest.json
custom_components/luxtronik2_modbus_proxy/number.py
custom_components/luxtronik2_modbus_proxy/select.py
custom_components/luxtronik2_modbus_proxy/sensor.py
custom_components/luxtronik2_modbus_proxy/strings.json
custom_components/luxtronik2_modbus_proxy/translations/de.json
custom_components/luxtronik2_modbus_proxy/translations/en.json
.github/workflows/validate.yml
hacs.json
pyproject.toml
README.de.md
README.md
tests/__init__.py
tests/unit/__init__.py
tests/unit/test_number.py
tests/unit/test_select.py
```

`.pytest_cache/` and `__pycache__/` directories exist in the working tree from running pytest but are git-ignored.

## pytest Result

```
36 passed, 1 skipped in 0.25s
```

Surviving tests: `tests/unit/test_select.py`, `tests/unit/test_number.py` (both pure `ast.literal_eval` parsing of the HA component sources, no HA runtime required). Skipped: `test_sg_ready_mode_map_matches_proxy` — see deviation below.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `git filter-repo` pass 1 required `--force`**

- **Found during:** Task 1, Step 4.
- **Issue:** The plan ran `git remote remove origin` in Step 3, which causes filter-repo to refuse pass 1 with "this does not look like a fresh clone (expected one remote, origin)".
- **Fix:** Added `--force` to pass 1. The clone was genuinely fresh (content-wise) and the remote removal was defensive per the plan itself; `--force` is safe here and matches the documented pattern for the "remove remote first" variant.
- **Files modified:** none (command-line only)
- **Commit:** n/a (filter-repo operation)

**2. [Rule 3 - Blocking] `test_select.py` depended on the deleted `src/luxtronik2_modbus_proxy/sg_ready.py`**

- **Found during:** Task 4 pytest run.
- **Issue:** The research document claimed `test_select.py` was pure `ast`-based and self-contained, but it actually performs a cross-validation: it reads `src/luxtronik2_modbus_proxy/sg_ready.py` (the proxy source) and asserts `SG_READY_MODE_MAP` in the HA `select.py` matches the proxy's map. After filter-repo, `src/` is gone, so test collection fails with `FileNotFoundError`.
- **Fix:** Gated `_SG_READY_PATH.read_text()` on `_SG_READY_PATH.exists()`; when absent, `PROXY_SG_READY_MODE_MAP` is set to `None` and the single cross-validation test calls `pytest.skip(...)` with a descriptive message. The other 36 assertions in the file continue to run. This preserves the cross-validation capability for anyone running the tests against a checkout that still has the proxy alongside, while unblocking the HA-only repo.
- **Files modified:** `tests/unit/test_select.py`
- **Commit:** `49b7b90 fix(08): skip SG_READY cross-validation when proxy src/ absent`

### Deferred Items

None.

## Commits Made (in the new working copy)

```
49b7b90 fix(08): skip SG_READY cross-validation when proxy src/ absent
6910326 chore(08): trim pyproject, add placeholder README, drop proxy-coupled tests
0319f9c docs: rewrite README (EN+DE) — highlight standalone HA integration   <-- filtered HEAD
```

(Plus 47 filtered ancestor commits preserved from Phase 1-7 history for the kept paths.)

## Source Repo Unchanged

The source repo `/home/dwolbeck/claude-code/PUBLIC-luxtronik2-modbus-proxy` was only read from (via `git clone --no-local`). No commits, no working-tree modifications, no ref changes. This SUMMARY file is the first write in the source repo for Phase 8.

## Self-Check: PASSED

- `/home/dwolbeck/claude-code/luxtronik2-hass/.git` FOUND
- `custom_components/luxtronik2_modbus_proxy/coordinator.py` FOUND (3 commits)
- `custom_components/luxtronik2_modbus_proxy/config_flow.py` FOUND (3 commits)
- `hacs.json`, `pyproject.toml` (trimmed), `README.md` (placeholder) all FOUND
- No remote origin in new working copy (VERIFIED)
- pytest: 36 passed, 1 skipped, 0 failed (VERIFIED)
- No forbidden files (`src/`, `Dockerfile`, `mkdocs.yml`, etc.) present (VERIFIED)
- Commits `49b7b90`, `6910326` FOUND in new working copy log

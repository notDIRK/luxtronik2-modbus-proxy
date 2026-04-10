---
phase: 08-new-repo-extraction-setup
verified: 2026-04-10T00:00:00Z
status: passed
score: 4/4 success criteria verified
---

# Phase 8: New Repo Extraction & Setup — Verification Report

**Phase Goal:** A clean local working copy of the future `luxtronik2-hass` repo exists with preserved HACS integration history and no proxy artifacts — ready for rename in Phase 9.

**Verified:** 2026-04-10
**Status:** PASSED
**Re-verification:** No — initial verification

## Goal Achievement

### Success Criteria

| #   | Criterion                                                                                                                       | Status     | Evidence                                                                                                  |
| --- | ------------------------------------------------------------------------------------------------------------------------------- | ---------- | --------------------------------------------------------------------------------------------------------- |
| 1   | `/home/dwolbeck/claude-code/luxtronik2-hass/` exists, produced via `git filter-repo`, no remote origin                          | VERIFIED   | Path exists; `git remote` returns empty (0 lines); `.git/filter-repo/commit-map` has 171 mappings         |
| 2   | `git log -- custom_components/` shows Phase 4-7 commits; `git blame` resolves on coordinator.py and config_flow.py              | VERIFIED   | coordinator.py: 3 commits (a7962ae 05-01, cf43bc8 07-01, 1b2bddf fix); config_flow.py: 3 commits (3e1849e 05-02, 5ebbbbd 260409-l1l, 3bc8198 fix); blame shows real SHAs (no `00000000`); phase-prefixed commits 04/05/06/07 found |
| 3   | No `src/`, `Dockerfile`, `config.example.yaml`, `mkdocs.yml`, `docs/en/proxy*`, systemd unit                                    | VERIFIED   | All 7 forbidden paths absent; `find` for `*.service` and `proxy*` returned nothing                        |
| 4   | Trimmed `pyproject.toml` (dev deps only, no proxy entry points) + `README.md` placeholder; pytest passes on surviving HA tests  | VERIFIED   | `[project.scripts]` and `main:cli` absent from pyproject; README contains "HACS integration extract" placeholder text; pytest: **36 passed, 1 skipped, 0 failed in 0.27s** |

**Score:** 4/4 success criteria verified

### Verification Commands & Output

**SC-1: No remote origin**
```
$ cd /home/dwolbeck/claude-code/luxtronik2-hass && git remote
(empty)
$ git remote | wc -l
0
```

**SC-2: History preserved**
```
$ git log --oneline -- custom_components/luxtronik2_modbus_proxy/coordinator.py
1b2bddf fix(coordinator): use dict.items() for luxtronik parameter/calculation extraction
cf43bc8 feat(07-01): add write methods and rate limiting to LuxtronikCoordinator
a7962ae feat(05-01): add LuxtronikCoordinator with connect-per-call polling

$ git log --oneline -- custom_components/luxtronik2_modbus_proxy/config_flow.py
3bc8198 fix(config_flow): remove manual config_entry init from OptionsFlow
5ebbbbd feat(260409-l1l): add LuxtronikOptionsFlow to config_flow.py
3e1849e feat(05-02): add config flow with connection test and BenPru conflict detection

$ git blame coordinator.py | head -1
a7962ae5 (Ubuntu 2026-04-09 06:54:40 +0000   1) """Coordinator for the Luxtronik 2 Modbus Proxy ..."""
```

Phase-prefixed commits across `custom_components/`: includes `feat(05-01)`, `feat(05-02)`, `feat(06-01)`, `feat(07-01)`, `feat(07-02)`, `feat(07-03)`, `test(07-03)`. SHAs are rewritten by filter-repo (171 commit-map entries) — expected per plan and SPLIT-02 contract.

**SC-3: Forbidden files absent**
```
OK: src absent
OK: Dockerfile absent
OK: docker-compose.yml absent
OK: config.example.yaml absent
OK: mkdocs.yml absent
OK: contrib absent
OK: docs absent
$ find . -name 'luxtronik2-modbus-proxy.service' -not -path './.git/*'
(empty)
$ find . -name 'proxy*' -not -path './.git/*'
(empty)
```

**SC-4: Trimmed pyproject + placeholder README + pytest green**
```
$ grep -E 'project.scripts|main:cli' pyproject.toml
(no match — entry points removed)

$ head README.md
# luxtronik2-modbus-proxy (HACS integration extract)
Local working copy created via `git filter-repo` ...

$ python3 -m pytest tests/unit/test_select.py tests/unit/test_number.py -q
........s............................                                    [100%]
36 passed, 1 skipped in 0.27s
```

The trimmed `pyproject.toml` contains only the `[project]` metadata, `[project.optional-dependencies]` dev block (pytest, pytest-asyncio, pytest-cov, ruff, mypy), and tool configs (pytest, ruff, mypy). No runtime deps, no `[project.scripts]`, no `src/` pythonpath. The 1 skipped test is the SG_READY cross-validation that requires `src/sg_ready.py` (gated and skipped cleanly per the auto-fix documented in the SUMMARY).

### Tracked File Tree (27 files)

```
.github/workflows/validate.yml
README.de.md
README.md
custom_components/luxtronik2_modbus_proxy/__init__.py
custom_components/luxtronik2_modbus_proxy/brand/{icon,icon@2x,logo}.png
custom_components/luxtronik2_modbus_proxy/button.py
custom_components/luxtronik2_modbus_proxy/config_flow.py
custom_components/luxtronik2_modbus_proxy/const.py
custom_components/luxtronik2_modbus_proxy/coordinator.py
custom_components/luxtronik2_modbus_proxy/{icon,icon@2x,logo}.png
custom_components/luxtronik2_modbus_proxy/manifest.json
custom_components/luxtronik2_modbus_proxy/number.py
custom_components/luxtronik2_modbus_proxy/select.py
custom_components/luxtronik2_modbus_proxy/sensor.py
custom_components/luxtronik2_modbus_proxy/strings.json
custom_components/luxtronik2_modbus_proxy/translations/{de,en}.json
hacs.json
pyproject.toml
tests/__init__.py
tests/unit/__init__.py
tests/unit/test_number.py
tests/unit/test_select.py
```

### Anti-Patterns Found

None. No TODO/FIXME/placeholder leakage in `pyproject.toml` or `README.md` (the README placeholder text is intentional and labeled as "intermediate working state" with explicit forward references to Phase 9/10/11 — this is documented intent, not a stub). No real IPs, hostnames, or credentials in either file (CLAUDE.md security rule satisfied).

### Requirements Coverage

| Requirement | Source Plan | Description                                              | Status    | Evidence                                                                                  |
| ----------- | ----------- | -------------------------------------------------------- | --------- | ----------------------------------------------------------------------------------------- |
| SPLIT-02    | 08-01-PLAN  | Git history preserved across the split                   | SATISFIED | git log shows 3 commits each on coordinator.py and config_flow.py with original messages/authors/dates; git blame resolves to real SHAs |
| SPLIT-03    | 08-01-PLAN  | New repo contains only HA-relevant files                 | SATISFIED | 27 tracked files, all under custom_components/, tests/unit/, .github/workflows/validate.yml, plus root metadata; all forbidden paths absent |

### Human Verification Required

None. All 4 success criteria are programmatically verifiable and pass.

### Gaps Summary

No gaps. The phase achieved its goal: a clean local working copy at `/home/dwolbeck/claude-code/luxtronik2-hass` exists with rewritten-but-equivalent HACS integration history, no remote origin, no proxy artifacts, a trimmed pyproject.toml, a placeholder README, and a green pytest run on the surviving HA tests. Ready for Phase 9 (rename).

---

_Verified: 2026-04-10_
_Verifier: Claude (gsd-verifier)_

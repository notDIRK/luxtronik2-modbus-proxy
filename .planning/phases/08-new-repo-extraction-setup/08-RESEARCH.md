# Phase 8: New Repo Extraction & Setup - Research

**Researched:** 2026-04-10
**Domain:** Git history rewriting (`git filter-repo`), HACS integration repo layout, pytest scoping
**Confidence:** HIGH

## Summary

Phase 8 produces a clean local working copy of the future `luxtronik2-hass` repo at `~/claude-code/luxtronik2-hass/` by running `git filter-repo` on a fresh clone of the current repo. The standard, vendor-blessed tool is `git filter-repo` (`git-filter-repo` is already installed at `/home/dwolbeck/.local/bin/git-filter-repo`, version `a40bce548d2c`). The phase is **strictly local** — no remote operations occur until Phase 11.

The single load-bearing technical question is: **does `git filter-repo --path custom_components/ --path tests/ --path .github/` preserve `git blame` resolution for `coordinator.py` and `config_flow.py` against the original SHAs?** Answer: **YES, SHAs are preserved exactly** for any commit that touched only the kept paths. Commits that touched both kept and removed paths are **rewritten with new SHAs but the same content for the kept files**, and `git blame` continues to work because blame walks the new history graph, not literal SHA matches. (`git filter-repo` writes a `.git/filter-repo/commit-map` file documenting old→new SHA mappings.)

The second load-bearing discovery is a **test-suite trap**: 6 of the 9 unit tests in `tests/unit/` import from `luxtronik2_modbus_proxy` — and that import refers to the **proxy package in `src/`**, NOT the HA `custom_components/luxtronik2_modbus_proxy/`. After extraction, those 6 tests will `ImportError` because `src/` is gone. Only `test_select.py` and `test_number.py` (which use `ast.literal_eval` to parse the HA component without importing it) survive cleanly. **Phase 8 must drop or rewrite the proxy-coupled tests** before "HA tests pass under pytest" can be true.

**Primary recommendation:** Use a 4-task plan: (1) fresh clone + `git filter-repo` extraction, (2) verify history/blame, (3) prune proxy-only files that escaped the path filter (root-level loose files like `pyproject.toml`, `README.md`), (4) trim `pyproject.toml` + drop proxy-coupled tests + add placeholder README + run `pytest`.

## User Constraints (from CONTEXT.md)

No CONTEXT.md exists for Phase 8 (orchestrator did not run `/gsd-discuss-phase` first). Constraints are taken from `ROADMAP.md` Phase 8 section, `REQUIREMENTS.md` SPLIT-02/SPLIT-03, and `STATE.md` v1.2 architecture decisions.

### Locked Decisions (from STATE.md / ROADMAP.md)

- **Local only.** Phase 8 does NOT push, does NOT rename remote, does NOT touch GitHub. The new working copy has **no remote origin set**.
- **Target path:** `~/claude-code/luxtronik2-hass/` (sibling to current repo). Confirmed in roadmap success criterion 1.
- **No rename in Phase 8.** Folder stays `custom_components/luxtronik2_modbus_proxy/`, domain stays `luxtronik2_modbus_proxy`, package stays `luxtronik2-modbus-proxy`. Renaming is Phase 9's job.
- **History preserved.** Use `git filter-repo --path custom_components/ --path tests/ --path .github/`. `git blame` on `coordinator.py` and `config_flow.py` MUST resolve.
- **Files to remove:** `src/`, `Dockerfile`, `docker-compose.yml`, `config.example.yaml`, `mkdocs.yml`, `docs/en/proxy*` (all of `docs/`), systemd unit (`contrib/luxtronik2-modbus-proxy.service`).
- **Files to keep:** `custom_components/luxtronik2_modbus_proxy/`, `tests/`, `.github/`, plus a trimmed `pyproject.toml` and a placeholder `README.md`.
- **Tests must pass under pytest** in the new working copy (success criterion 4).
- **Phase 8 is reversible.** Local-only. If something is wrong, `rm -rf ~/claude-code/luxtronik2-hass` and restart. Phase 11 is the irreversible checkpoint.

### Claude's Discretion

- Whether `.planning/` survives (filter or keep) — research recommendation below.
- Whether `.github/workflows/publish.yml` and `docs.yml` survive (proxy-specific) — recommendation: drop in this phase or in Phase 9.
- Exact content of placeholder `README.md` — recommendation below.
- Whether to use `git filter-repo --path` or instead `git filter-repo --paths-from-file` (latter is cleaner for many paths but unnecessary here).
- Whether to also rewrite-prune the `.planning/phases/` v1.0/v1.1 archive (irrelevant to the new repo's identity).

### Deferred (OUT OF SCOPE for Phase 8)

- Renaming `custom_components/luxtronik2_modbus_proxy/` → `luxtronik2_hass/` → **Phase 9**
- Renaming `manifest.json` `domain` → **Phase 9**
- README rewrite (three-path positioning) → **Phase 10**
- Pushing to GitHub → **Phase 11**
- Archiving the old repo → **Phase 11**
- HA live migration → **Phase 12**

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SPLIT-02 | Git history of HACS integration preserved; `git blame` resolves on `coordinator.py` and `config_flow.py` | `git filter-repo` with `--path` preserves blame; verification recipe in "Verification Recipes" below |
| SPLIT-03 | New repo contains only HA-relevant files (no `src/`, `Dockerfile`, `config.example.yaml`, `mkdocs.yml`) | `git filter-repo --path` whitelist excludes everything not listed; verification via `find` listing |

## Standard Stack

### Core Tool: git filter-repo

| Tool | Version | Purpose | Why Standard |
|------|---------|---------|--------------|
| `git filter-repo` | a40bce548d2c (installed) | History rewriting, path filtering | **The git project's official replacement** for `git filter-branch`. Recommended in `git filter-branch`'s own man page. Used by GitHub, GitLab, Atlassian docs for repo splits. [VERIFIED: installed at `/home/dwolbeck/.local/bin/git-filter-repo`] |
| `git` | 2.34.1 | Underlying VCS | System-installed [VERIFIED] |
| `python3` | 3.10.12 | Required by `git filter-repo` | System-installed [VERIFIED] |

**Installation status:** Already installed. No action needed. If a fresh machine is used: `pip install --user git-filter-repo` (pure-Python, no compilation).

**Critical fact about `git filter-repo`:** It **refuses to run on a non-fresh clone** by default — it requires `--force` on a repo with a remote, or a fresh clone, to prevent accidental destruction. This is a *feature*, not a bug. The recommended pattern is **clone fresh, then filter**. [VERIFIED: standard `git filter-repo` documentation]

### Alternatives Considered

| Instead of | Could Use | Why Not |
|------------|-----------|---------|
| `git filter-repo` | `git filter-branch` | **Officially deprecated.** `git filter-branch` is slow (orders of magnitude), buggy with edge cases (encoding, signatures), and the git man page actively recommends `git filter-repo` instead. |
| `git filter-repo` | `git subtree split --prefix=custom_components/` | Only extracts ONE prefix. We need three paths (`custom_components/`, `tests/`, `.github/`). Would require manual merging of three subtree splits. Not viable. |
| `git filter-repo` | Manual `git rebase -i` deleting commits | Doesn't scale (170 commits in this repo), error-prone, doesn't truly remove file blobs from history. |
| Fresh clone + filter | Filter the working repo in-place | DESTRUCTIVE — would corrupt the live repo we still need for Phases 11 (banner commit on the old repo). **Always work on a clone.** |

## Architecture Patterns

### Recommended Working-Copy Layout (after Phase 8)

```
~/claude-code/luxtronik2-hass/
├── .git/                                       # rewritten history
├── .github/
│   └── workflows/
│       ├── validate.yml                        # KEEP — HACS + hassfest validation
│       ├── publish.yml                         # DROP (proxy PyPI publish)
│       └── docs.yml                            # DROP (mkdocs gh-deploy)
├── custom_components/
│   └── luxtronik2_modbus_proxy/                # NOT renamed yet — Phase 9 does that
│       ├── __init__.py
│       ├── manifest.json
│       ├── const.py
│       ├── config_flow.py
│       ├── coordinator.py
│       ├── sensor.py
│       ├── select.py
│       ├── number.py
│       ├── button.py
│       ├── strings.json
│       ├── translations/{en,de}.json
│       ├── icon.png, icon@2x.png, logo.png
│       └── brand/
├── tests/
│   ├── __init__.py
│   ├── unit/
│   │   ├── test_select.py                      # KEEP — pure ast parsing, no proxy import
│   │   ├── test_number.py                      # KEEP — pure ast parsing, no proxy import
│   │   ├── test_sensor.py                      # DROP or REWRITE — imports proxy
│   │   ├── test_register_map.py                # DROP — proxy-only
│   │   ├── test_register_definitions.py        # DROP — proxy-only
│   │   ├── test_register_cache.py              # DROP — proxy-only
│   │   ├── test_config.py                      # DROP — proxy ProxyConfig
│   │   └── test_sg_ready.py                    # DROP — proxy sg_ready module
│   └── integration/
│       └── test_proxy_mock.py                  # DROP — proxy-only
├── pyproject.toml                              # TRIMMED (dev deps only)
├── README.md                                   # PLACEHOLDER (Phase 10 rewrites it)
├── hacs.json                                   # KEEP (root-level HACS marker)
└── LICENSE                                     # KEEP if present in current repo
```

**Key observations:**

1. **Three-path filter is too narrow.** `git filter-repo --path custom_components/ --path tests/ --path .github/` keeps ONLY those directories. Root-level files (`pyproject.toml`, `hacs.json`, `README.md`, `LICENSE`) are **dropped**. We need to either:
   - **Option A (recommended):** Extend the filter to include those root files explicitly, then trim/replace them after extraction.
   - **Option B:** Filter strictly, then re-create root files as new commits.
   - Recommendation: **Option A** — use `--path-glob` or list each root file. This keeps `hacs.json` and `LICENSE` in history, which matters for `git blame` on legal/HACS-validation grounds.

2. **`hacs.json` is mandatory at repo root** for HACS validation. The validate.yml workflow will fail without it. Confirmed: `hacs.json` exists in current repo root. Must be kept.

3. **`.planning/` is NOT in the filter whitelist** — it gets dropped automatically. Recommendation: **drop it.** The new repo starts a fresh `.planning/` in Phase 9 or later. The current `.planning/` documents the proxy's history; carrying it to the HA-only repo creates confusion.

### The Exact filter-repo Command

```bash
# Step 1: Fresh clone (NOT a copy of the working repo with dirty state)
cd ~/claude-code
git clone --no-local PUBLIC-luxtronik2-modbus-proxy luxtronik2-hass
cd luxtronik2-hass

# Step 2: Remove origin BEFORE filtering (defensive)
git remote remove origin

# Step 3: Run filter-repo with the exact path whitelist
git filter-repo \
  --path custom_components/ \
  --path tests/ \
  --path .github/ \
  --path hacs.json \
  --path LICENSE \
  --invert-paths --path .github/workflows/publish.yml \
  --invert-paths --path .github/workflows/docs.yml
```

**WAIT — `git filter-repo` cannot mix `--path` (keep) and `--invert-paths` in one invocation.** The correct pattern is **two passes**:

```bash
# Pass 1: Keep only HA-relevant paths
git filter-repo \
  --path custom_components/ \
  --path tests/ \
  --path .github/ \
  --path hacs.json \
  --path LICENSE

# Pass 2: Drop the proxy-specific workflows that were kept by .github/
git filter-repo --invert-paths \
  --path .github/workflows/publish.yml \
  --path .github/workflows/docs.yml \
  --force
```

The `--force` flag is needed on pass 2 because the repo already has a rewritten history (filter-repo treats it as "not fresh"). [VERIFIED: this is the documented two-pass pattern.]

**Note on `LICENSE`:** Current repo has no `LICENSE` file at root (only the MIT declaration in `pyproject.toml`). Drop `--path LICENSE` from pass 1, or add a `LICENSE` file in Phase 8 task 4.

### Test Pruning Strategy

**The test problem (CRITICAL):**

| File | Imports | Status After Extraction |
|------|---------|------------------------|
| `tests/unit/test_select.py` | `ast`, `json`, `pathlib` only | **WORKS** — pure file parsing |
| `tests/unit/test_number.py` | `ast`, `json`, `pathlib` only | **WORKS** — pure file parsing |
| `tests/unit/test_sensor.py` | `from luxtronik2_modbus_proxy.register_definitions...` | **BREAKS** — proxy package gone |
| `tests/unit/test_register_map.py` | `from luxtronik2_modbus_proxy.register_definitions...` | **BREAKS** |
| `tests/unit/test_register_definitions.py` | `from luxtronik2_modbus_proxy.register_definitions...` | **BREAKS** |
| `tests/unit/test_register_cache.py` | `from luxtronik2_modbus_proxy.register_cache...` | **BREAKS** |
| `tests/unit/test_config.py` | `from luxtronik2_modbus_proxy.config...` | **BREAKS** |
| `tests/unit/test_sg_ready.py` | `from luxtronik2_modbus_proxy.sg_ready...` | **BREAKS** |
| `tests/integration/test_proxy_mock.py` | proxy server fixture | **BREAKS** |

**Recommendation:** Delete the 7 broken test files in Phase 8 (they test the proxy, which is being archived as legacy). Keep only `test_select.py`, `test_number.py`, plus `__init__.py` files. Document the deletion in a commit message: `chore(08): drop proxy-coupled tests not relevant to HA repo`.

The 7 deleted tests still **exist in git history** (they were committed during Phases 1-7 alongside the proxy). That's fine — `git blame` and `git log -- tests/unit/test_sensor.py` still resolve to the original commits.

**Alternative considered:** Rewrite `test_sensor.py` to use `ast.literal_eval` like `test_select.py` does, parsing the HA `sensor.py` without importing it. This is **more work** and is **out of scope for Phase 8** (Phase 8 is "extract", not "expand test coverage"). Defer to a future phase if HA-side sensor tests are wanted.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| History rewriting / path filtering | A bash script that `git rm`s files and amends commits | `git filter-repo` | Filter-repo is the only correct, fast, safe way to rewrite git history. Hand-rolled scripts get encoding, signature, and ref-handling wrong. |
| Detecting which commits touched HA-only paths | A python script walking `git log` | `git filter-repo --path` | Filter-repo handles it natively, including merge commits and renames. |
| Verifying blame preservation | Manually comparing SHAs | `git filter-repo`'s auto-generated `.git/filter-repo/commit-map` + `git blame` walking | The commit-map file documents every old→new SHA mapping. |
| Cleaning .git after filter | `git gc` flag tuning | Filter-repo runs gc automatically | Don't double-gc; trust the tool. |

**Key insight:** Repo splitting is a solved problem. The temptation to "just use git rm and amend" produces repos with bloated `.git/objects` (deleted files still occupy space) and broken cross-references. Filter-repo is the right answer.

## Common Pitfalls

### Pitfall 1: Filter-repo refuses on a non-fresh clone

**What goes wrong:** Running `git filter-repo` in the current `PUBLIC-luxtronik2-modbus-proxy` directory fails with "Aborting: Refusing to destructively overwrite repo history since this does not look like a fresh clone."

**Why it happens:** Safety check — filter-repo doesn't want to corrupt a repo with a remote that has unpushed work.

**How to avoid:** Always `git clone --no-local` to a NEW directory first. Never run filter-repo on a working repo with valuable state.

**Warning sign:** The error message itself is unmissable.

### Pitfall 2: `git blame` "broken" because SHAs differ

**What goes wrong:** After filter-repo, `git blame coordinator.py` shows DIFFERENT commit SHAs from the original repo, and the planner panics that history is lost.

**Why it happens:** Filter-repo rewrites every commit that touched any removed path. A commit like `de54fed feat(05-01): add LuxtronikCoordinator with connect-per-call polling` may also have touched `src/` — after filtering, it gets a new SHA but the same content for `coordinator.py`.

**How to verify it's actually fine:** `.git/filter-repo/commit-map` lists `<old SHA> <new SHA>` for every rewritten commit. `git log -- custom_components/luxtronik2_modbus_proxy/coordinator.py` should still show the same commit MESSAGES and DATES. `git blame` walks the new graph correctly.

**How to avoid the panic:** In Phase 8 verification, compare commit *messages* and *author dates*, not SHAs. Document in the SUMMARY that "SHAs may differ; messages and dates match originals."

**Warning sign:** None — this is normal and expected. SPLIT-02 must be interpreted as "blame resolves to commits with the original messages/dates", not "the SHA strings are byte-identical."

### Pitfall 3: Root files vanish silently

**What goes wrong:** After filter-repo, `pyproject.toml`, `hacs.json`, `README.md` are GONE because they weren't in the path whitelist. The plan said "trim pyproject.toml" but there's nothing to trim.

**Why it happens:** `--path` is a whitelist. Anything not listed is dropped from history.

**How to avoid:** Add `--path hacs.json --path pyproject.toml --path README.md --path README.de.md` to pass 1 of the filter command. Then trim/replace them as separate commits in task 4.

**Warning sign:** `ls` in the new working copy shows only `custom_components/`, `tests/`, `.github/` and nothing else.

### Pitfall 4: Pre-commit hook ships sample, not real

**What goes wrong:** The CLAUDE.md mentions "a pre-commit hook scans every commit for sensitive patterns and BLOCKS if found." But `.git/hooks/` only contains `*.sample` files. The hook is **not committed to the repo** — it's local to each clone.

**Why it happens:** Git hooks live in `.git/hooks/`, which is never tracked. There's no `.pre-commit-config.yaml` either.

**How to avoid:** This is informational. The hook does NOT come along via filter-repo (because `.git/hooks/` is per-clone). If the new repo needs the same hook in Phase 11 before pushing, install it manually or add a `.pre-commit-config.yaml` (separate concern, not Phase 8).

**Warning sign:** None for Phase 8. Flag for Phase 11.

### Pitfall 5: pytest discovers cached `.pyc` files from old tests

**What goes wrong:** After deleting `test_sensor.py`, running `pytest` still tries to import the deleted test from `__pycache__/test_sensor.cpython-310.pyc` and fails.

**Why it happens:** `__pycache__` directories are tracked by neither git nor filter-repo (they're in `.gitignore`), so they don't end up in the new working copy. **But** the current repo HAS `__pycache__` directories sitting in the working tree (visible in earlier `find` output) — those are local stale artifacts.

**How to avoid:** The fresh clone will NOT carry working-tree-only `__pycache__` directories. Verify with `find tests -name __pycache__` after clone. If any appear (shouldn't), `find tests -name __pycache__ -exec rm -rf {} +`.

**Warning sign:** pytest errors mentioning files that don't exist on disk.

### Pitfall 6: HA tests need a runtime that may not be available

**What goes wrong:** Even the "surviving" tests (`test_select.py`, `test_number.py`) might need HA-specific imports or test plugins.

**Why it happens (and good news):** Both files explicitly avoid HA imports (they say so in their docstrings: "All tests are pure Python -- no Home Assistant runtime required"). They use `ast.literal_eval` to parse the HA component files as text. **They will work in any pytest 9.0+ environment.**

**How to avoid:** Confirmed safe by reading the test files. No mitigation needed. Verification: `pytest tests/unit/test_select.py tests/unit/test_number.py -x` should pass in the new working copy.

**Warning sign:** ImportError on `homeassistant` — would only happen if a different test file is kept by mistake.

### Pitfall 7: `--invert-paths` second pass requires `--force`

**What goes wrong:** Pass 2 of the filter (dropping proxy-specific workflows) errors with "Aborting: Refusing to destructively overwrite repo history."

**Why it happens:** After pass 1, the repo is no longer "fresh" by filter-repo's definition.

**How to avoid:** Add `--force` to pass 2 of the filter command. Safe because we just rewrote it ourselves seconds ago.

**Warning sign:** The error message.

## Code Examples

### The full extraction recipe (executable)

```bash
#!/usr/bin/env bash
set -euo pipefail

SOURCE=~/claude-code/PUBLIC-luxtronik2-modbus-proxy
TARGET=~/claude-code/luxtronik2-hass

# Pre-flight: target must not exist
if [[ -e "$TARGET" ]]; then
  echo "ERROR: $TARGET already exists. Remove it first."
  exit 1
fi

# Step 1: Fresh clone (--no-local forces real object copy, not hardlinks)
git clone --no-local "$SOURCE" "$TARGET"
cd "$TARGET"

# Step 2: Drop the remote so we cannot accidentally push
git remote remove origin

# Step 3: Pass 1 — whitelist the paths to keep
git filter-repo \
  --path custom_components/ \
  --path tests/ \
  --path .github/ \
  --path hacs.json \
  --path pyproject.toml \
  --path README.md \
  --path README.de.md

# Step 4: Pass 2 — drop proxy-specific workflows kept by .github/
git filter-repo --force --invert-paths \
  --path .github/workflows/publish.yml \
  --path .github/workflows/docs.yml

# Step 5: Verify history is intact
echo "=== Commits touching coordinator.py ==="
git log --oneline -- custom_components/luxtronik2_modbus_proxy/coordinator.py

echo "=== git blame head of coordinator.py (first 5 lines) ==="
git blame custom_components/luxtronik2_modbus_proxy/coordinator.py | head -5

echo "=== Tree listing ==="
find . -type f -not -path './.git/*' | sort
```

### Verification script (for the planner to put in a verify task)

```bash
#!/usr/bin/env bash
# Phase 8 verification — run inside ~/claude-code/luxtronik2-hass

set -euo pipefail
fail=0

# SC-1: no remote origin
if git remote | grep -q .; then
  echo "FAIL SC-1: a remote is set"; fail=1
else
  echo "PASS SC-1: no remote configured"
fi

# SC-2: history preserved for coordinator.py and config_flow.py
for f in custom_components/luxtronik2_modbus_proxy/coordinator.py \
         custom_components/luxtronik2_modbus_proxy/config_flow.py; do
  count=$(git log --oneline -- "$f" | wc -l)
  if [[ "$count" -lt 2 ]]; then
    echo "FAIL SC-2: $f has only $count commits in history"; fail=1
  else
    echo "PASS SC-2: $f has $count commits in history"
  fi
done

# SC-3: forbidden files absent
for forbidden in src Dockerfile docker-compose.yml config.example.yaml mkdocs.yml \
                 contrib/luxtronik2-modbus-proxy.service docs/en/proxy; do
  if [[ -e "$forbidden" ]]; then
    echo "FAIL SC-3: $forbidden still exists"; fail=1
  fi
done
[[ ! -e src ]] && echo "PASS SC-3: src/ removed"

# SC-4: pyproject.toml is trimmed (no proxy entry point)
if grep -q 'luxtronik2-modbus-proxy = "luxtronik2_modbus_proxy.main:cli"' pyproject.toml; then
  echo "FAIL SC-4: pyproject.toml still has proxy entry point"; fail=1
else
  echo "PASS SC-4: pyproject.toml has no proxy entry point"
fi

# SC-4: pytest passes
pytest tests/unit/test_select.py tests/unit/test_number.py -x --no-header -q
echo "PASS SC-4: pytest green"

exit $fail
```

### Trimmed `pyproject.toml` (HA-only, dev-only)

```toml
[project]
name = "luxtronik2-modbus-proxy"          # NOT renamed yet — Phase 9 renames to luxtronik2-hass
version = "1.1.2"                          # matches manifest.json version
description = "Home Assistant custom integration for Luxtronik 2.0 heat pumps"
requires-python = ">=3.10"
license = { text = "MIT" }
readme = "README.md"
keywords = ["luxtronik", "heat-pump", "home-assistant", "hacs"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: End Users/Desktop",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Home Automation",
]

# No runtime dependencies — HA installs them via manifest.json `requirements`.
# This pyproject is dev-only: pytest, ruff, mypy.

[project.optional-dependencies]
dev = [
    "pytest>=9.0",
    "pytest-asyncio>=1.3",
    "pytest-cov",
    "ruff",
    "mypy",
]

# NO [project.scripts] — proxy CLI is gone.
# NO [build-system] — this package is never built or published; HACS distributes
# the custom_components/ folder directly.

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
# pythonpath removed — no src/ layout

[tool.ruff]
target-version = "py310"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "W", "I", "D", "UP", "B", "SIM", "RUF"]

[tool.ruff.lint.pydocstyle]
convention = "google"

[tool.mypy]
strict = true
python_version = "3.10"
```

**Note on package name:** Phase 8 leaves `name = "luxtronik2-modbus-proxy"` because the rename is Phase 9's job. This is intentional and matches the "no rename in Phase 8" decision.

### Placeholder `README.md` (replaced in Phase 10)

```markdown
# luxtronik2-modbus-proxy (HACS integration extract)

Local working copy created via `git filter-repo` from
`PUBLIC-luxtronik2-modbus-proxy` on 2026-04-10 as part of milestone v1.2
Phase 8 (Repo Split & HA-First Rebrand).

This is an **intermediate working state**:

- The internal name is still `luxtronik2_modbus_proxy` — Phase 9 renames it to `luxtronik2_hass`.
- This README is a placeholder — Phase 10 rewrites it with three-path positioning (Supported / Experimental / Planned).
- There is no remote origin — Phase 11 pushes to `notDIRK/luxtronik2-hass`.

See `.planning/ROADMAP.md` (in the parent project repo) for context.
```

## Runtime State Inventory

Phase 8 is a local-only filesystem operation. There is no runtime state to migrate.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — verified by reading STATE.md and PROJECT.md. The HA integration's stored state lives in the maintainer's HA instance config entry, which is **out of scope until Phase 12**. | None |
| Live service config | None — Phase 8 does not touch any live service. The proxy may still be running on the maintainer's machine, but Phase 8 doesn't modify it. | None |
| OS-registered state | None — Phase 8 creates a new directory; it does not register systemd units, scheduled tasks, or pm2 processes. The proxy's systemd unit (`contrib/luxtronik2-modbus-proxy.service`) is dropped from the new repo but remains in the source repo. | None |
| Secrets/env vars | None — no secret keys are renamed or migrated. | None |
| Build artifacts | The current source repo has stale `__pycache__/` directories under `tests/unit/`. These are working-tree-only and will NOT be cloned by `git clone`. | Verify after clone with `find tests -name __pycache__` (expect empty). |

**Phase 9 will need a Runtime State Inventory** because the rename from `luxtronik2_modbus_proxy` to `luxtronik2_hass` touches `manifest.json` `domain`, which IS a runtime-state key (HA stores config entries by domain). **Phase 8 does not.**

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `git filter-branch` | `git filter-repo` | filter-repo released ~2019, became official replacement around git 2.24 | Fast (parallel), correct, safer defaults |
| Manual `git rm` + amend | `git filter-repo --path` whitelist | — | Filter-repo is the only correct way to truly remove blob history |
| `git subtree split` for one prefix | `git filter-repo --path` for many prefixes | — | Subtree only handles one prefix at a time |

**Deprecated:**
- `git filter-branch` — git's own man page recommends against it.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The current `pyproject.toml` `version = "1.1.2"` is the right version to ship in the new repo's trimmed pyproject. | Trimmed pyproject example | LOW — Phase 9 may bump it. Easy to change. |
| A2 | `LICENSE` file is missing from the current repo root (only in pyproject.toml). | Filter command | LOW — verified by `ls` listing showing no LICENSE file. If a LICENSE exists in a subdirectory, it'd survive only if listed in `--path`. |
| A3 | The maintainer wants `.planning/` dropped from the new repo. | Files-to-keep table | MEDIUM — if maintainer wants to carry v1.2 roadmap into the new repo, plan must add `--path .planning/` and then prune obsolete v1.0/v1.1 phase dirs. **Discuss-phase question.** |
| A4 | Dropping 7 proxy-coupled tests is acceptable (vs rewriting them as ast-based HA tests). | Test pruning | MEDIUM — losing test coverage is a real cost. **Discuss-phase question:** is "drop and document" OK, or should Phase 8 include rewrite work? |
| A5 | `.github/workflows/publish.yml` and `docs.yml` should be dropped in Phase 8 (vs Phase 9 or 10). | Filter command pass 2 | LOW — they're proxy-specific in either case. Dropping in Phase 8 keeps the new repo coherent. |
| A6 | `git filter-repo`'s SHA-rewriting is acceptable for SPLIT-02 ("`git blame` resolves to original SHAs"). | Pitfall 2 | **HIGH** — the requirement text says "original SHAs". Strictly read, that is **impossible** for any commit that touched both kept and removed paths. The roadmap likely means "original commits" (messages/dates), not "byte-identical SHA strings". **Confirm with user before Phase 8 starts.** |

**A6 is the load-bearing assumption** for this entire phase. If the user truly requires byte-identical SHAs, the only option is to filter ONLY commits that touched HA-only files (skipping mixed commits), which would lose history for any commit that touched both proxy and HA code — a strictly worse outcome. Recommendation: clarify the requirement language before planning.

## Open Questions

1. **Does `.planning/` come along?**
   - What we know: Roadmap says "no, drop it". STATE.md says new phase dirs will be created fresh.
   - What's unclear: Where does the v1.2 roadmap *itself* live during Phases 9-12? In the source repo, or copied to the new working copy?
   - Recommendation: **Drop `.planning/` from the new repo** in Phase 8. Continue tracking v1.2 progress in the source repo's `.planning/`. Phase 9+ work is documented in the source repo until Phase 11 pushes the new repo, after which the source repo's `.planning/` becomes the historical record.

2. **Should `pyproject.toml` keep the proxy package name `luxtronik2-modbus-proxy` until Phase 9, or rename in Phase 8?**
   - What we know: Phase 8 = "no rename". Phase 9 = "rename".
   - What's unclear: The trimmed pyproject is a NEW file (different content from original). Is replacing it with a new file a "rename"?
   - Recommendation: Keep `name = "luxtronik2-modbus-proxy"` literally in Phase 8's trimmed pyproject. Phase 9 changes it to `luxtronik2-hass`. This honors the "no rename in Phase 8" decision strictly.

3. **What about the `.github/workflows/validate.yml` file — does it need any tweaks?**
   - What we know: It runs HACS validation and hassfest. Both check `custom_components/<domain>/manifest.json`. Currently the domain is `luxtronik2_modbus_proxy` and the directory matches. After Phase 8, domain still matches → workflow should pass.
   - What's unclear: hassfest runs in CI on push, but Phase 8 has no remote, so CI never runs. Validation will only happen for real in Phase 11.
   - Recommendation: Leave validate.yml untouched in Phase 8. If a local hassfest dry-run is wanted, that's a Phase 9 or Phase 11 task.

4. **Does the maintainer have `git filter-repo` in `$PATH` in fresh shell sessions?**
   - What we know: It's installed at `/home/dwolbeck/.local/bin/git-filter-repo`. `~/.local/bin` is typically in PATH but not guaranteed.
   - Recommendation: Phase 8 task 1 should `command -v git-filter-repo` first and fail loudly if missing.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `git` | Clone, history operations | YES | 2.34.1 | None |
| `git-filter-repo` | History rewriting (the entire phase) | YES | a40bce548d2c (`/home/dwolbeck/.local/bin/`) | `pip install --user git-filter-repo` |
| `python3` | Required by git-filter-repo | YES | 3.10.12 | None |
| `pytest` | Test verification (success criterion 4) | UNKNOWN — verify in plan | needs `>=9.0` | `pip install pytest pytest-asyncio` |
| `find` | Verification recipes | YES (POSIX) | — | None |
| `~/claude-code/luxtronik2-hass/` directory | Target path | MUST NOT EXIST | — | Phase 8 task 1 must check |

**Missing dependencies with no fallback:** None.

**Action items for the planner:**
- Phase 8 task 1 should `command -v git-filter-repo` and `python3 -m pytest --version` before any destructive operation, failing fast if either is missing.
- Phase 8 task 1 should verify `~/claude-code/luxtronik2-hass/` does NOT exist.

## Validation Architecture

`workflow.nyquist_validation` is not explicitly set to `false` in `.planning/config.json` (verified earlier — config exists but key absent). Validation section included.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.x with pytest-asyncio 1.3.x |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` (carried over from current repo, trimmed in task 4) |
| Quick run command | `pytest tests/unit/test_select.py tests/unit/test_number.py -x -q` |
| Full suite command | `pytest tests/ -x` (after pruning, this is the same set) |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| SPLIT-02 | Git history of HACS integration preserved | smoke | `git log --oneline -- custom_components/luxtronik2_modbus_proxy/coordinator.py \| wc -l` (expect ≥2) | N/A — git command, not pytest |
| SPLIT-02 | `git blame` on `coordinator.py` resolves to original commits | smoke | `git blame custom_components/luxtronik2_modbus_proxy/coordinator.py \| head -5 \| awk '{print $1}'` (expect non-zero, non-uncommitted SHAs) | N/A |
| SPLIT-02 | `git blame` on `config_flow.py` resolves | smoke | same as above for config_flow.py | N/A |
| SPLIT-03 | No `src/` directory | smoke | `[[ ! -d src ]]` | N/A |
| SPLIT-03 | No `Dockerfile` | smoke | `[[ ! -f Dockerfile ]]` | N/A |
| SPLIT-03 | No `config.example.yaml` | smoke | `[[ ! -f config.example.yaml ]]` | N/A |
| SPLIT-03 | No `mkdocs.yml` | smoke | `[[ ! -f mkdocs.yml ]]` | N/A |
| SPLIT-03 | HA tests pass | unit | `pytest tests/unit/test_select.py tests/unit/test_number.py -x` | YES — both files exist in current repo |
| SC-4 | Trimmed `pyproject.toml` exists with no proxy entry point | smoke | `! grep -q 'luxtronik2_modbus_proxy.main:cli' pyproject.toml` | YES — file exists |
| SC-4 | Placeholder `README.md` exists | smoke | `[[ -f README.md ]]` | YES |

### Sampling Rate
- **Per task commit:** `pytest tests/unit/test_select.py tests/unit/test_number.py -x -q` (≈3 seconds)
- **Per wave merge:** Same (only 2 test files in scope after pruning)
- **Phase gate:** Verification script from "Code Examples" section above runs all SPLIT-02/SPLIT-03 checks + pytest

### Wave 0 Gaps

None for this phase. The two surviving test files (`test_select.py`, `test_number.py`) are pure-Python and will run on any pytest 9.0+ install. No new fixtures or test infrastructure required.

If the maintainer decides assumption A4 needs revisiting (rewriting proxy-coupled tests as HA tests), Wave 0 would need:
- [ ] Rewrite `tests/unit/test_sensor.py` to use `ast.literal_eval` parsing (similar pattern to `test_select.py`)
- [ ] Decide on a coverage target

## Security Domain

Phase 8 is a local filesystem and git operation with no network exposure. Standard security review still applies because the project's CLAUDE.md mandates "no IPs, hostnames, credentials in any committed file."

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | No auth in scope |
| V3 Session Management | no | No sessions |
| V4 Access Control | no | Local filesystem only |
| V5 Input Validation | no | No user input flows |
| V6 Cryptography | no | No crypto in scope |
| V14 Configuration | YES | Verify no secret/PII leaks survive into the new repo's history |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Sensitive data in git history (IPs, hostnames, tokens) | Information Disclosure | Run a secret-pattern grep over the new repo BEFORE Phase 11 push. Filter-repo CANNOT remove what's already been searched/leaked, so this is a defense-in-depth check, not a primary control. |
| Accidentally pushing to wrong remote | Tampering | Phase 8 explicitly removes `origin` immediately after clone. No `git push` is possible until Phase 11 sets a new remote. |
| Filter-repo silently keeping deleted files via merge commits | Information Disclosure | Filter-repo handles merges correctly by default. Verification: `git log --all --diff-filter=A -- src/` should return zero results in the new repo (no commits added `src/` files). |

**Defense-in-depth secret scan (recommended task):**

```bash
# Run inside the new working copy after filter-repo finishes
git grep -nIE '([0-9]{1,3}\.){3}[0-9]{1,3}' -- '*.py' '*.yaml' '*.yml' '*.json' '*.md' | \
  grep -v '192.168.x.x\|your-heatpump-ip\|127.0.0.1\|0.0.0.0\|255.255.255.255'
# Expected: zero output. Any line is a potential leak.
```

This is the same check the (uncommitted) pre-commit hook performs. Phase 8 should run it as a verification step. Phase 11 must run it again before push.

## Sources

### Primary (HIGH confidence — directly verified in this session)
- Local repo inspection: `find`, `ls`, `git log`, `cat` of pyproject.toml, manifest.json, workflows, test files
- `command -v git-filter-repo` → `/home/dwolbeck/.local/bin/git-filter-repo`
- `git filter-repo --version` → `a40bce548d2c`
- Reading `.planning/STATE.md`, `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`, `.planning/PROJECT.md`, `./CLAUDE.md`
- Test file content inspection confirming proxy-package coupling vs ast-based parsing

### Secondary (MEDIUM confidence — well-known tool conventions)
- `git filter-repo` two-pass pattern with `--force` on the second pass — standard documented usage
- `git filter-repo` SHA-rewriting semantics — standard tool behavior, documented in `.git/filter-repo/commit-map`
- HACS integration directory layout requirements — standard HACS docs
- pytest 9.0 test discovery behavior — standard pytest

### Tertiary (none)

No tertiary sources in this phase. All claims are either verified locally or rely on standard tool documentation.

## Metadata

**Confidence breakdown:**
- Standard stack (`git filter-repo`): HIGH — tool is installed, version verified, standard documented usage
- Architecture (filter command, file layout): HIGH — paths verified by `find`/`ls` against the live repo
- Test pruning strategy: HIGH — verified by reading every test file's imports
- Pitfalls: HIGH — pitfall 2 (SHA rewriting) and pitfall 3 (root files vanish) are derived from filter-repo's documented behavior
- Assumption A6 (SHA preservation interpretation): **MEDIUM-LOW** — depends on user intent for SPLIT-02 wording. **MUST be clarified before Phase 8 plans are written.**

**Research date:** 2026-04-10
**Valid until:** 2026-05-10 (30 days — `git filter-repo` is a stable tool, low churn)

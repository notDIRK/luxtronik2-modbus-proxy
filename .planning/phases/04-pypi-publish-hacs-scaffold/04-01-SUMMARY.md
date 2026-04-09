---
phase: 04-pypi-publish-hacs-scaffold
plan: 01
subsystem: packaging
tags: [pypi, packaging, github-actions, oidc, version-bump]
dependency_graph:
  requires: []
  provides: [pypi-package-metadata, trusted-publishing-workflow]
  affects: [pyproject.toml, src/luxtronik2_modbus_proxy/__init__.py, .github/workflows/publish.yml]
tech_stack:
  added: [pypa/gh-action-pypi-publish, python -m build]
  patterns: [OIDC trusted publishing, two-job build+publish workflow]
key_files:
  created:
    - .github/workflows/publish.yml
  modified:
    - pyproject.toml
    - src/luxtronik2_modbus_proxy/__init__.py
decisions:
  - "Use OWNER placeholder in project.urls since no git remote is configured — must be updated before first v* tag push"
  - "id-token: write scoped to publish job only (not workflow-level) per T-04-01 minimal privilege"
  - "Trigger on v* tags only — no branch push trigger per T-04-03"
metrics:
  duration: "~2 minutes"
  completed: "2026-04-09"
  tasks_completed: 2
  files_modified: 3
requirements:
  - HACS-04
---

# Phase 04 Plan 01: PyPI Publish Preparation Summary

**One-liner:** Version bumped to 1.1.0 with PyPI classifiers/URLs and OIDC trusted publishing workflow via `pypa/gh-action-pypi-publish@release/v1` on `v*` tags.

## What Was Built

The proxy package is now ready for PyPI publication. Two tasks were executed:

1. **Version bump + metadata** (`pyproject.toml`, `__init__.py`): version bumped from 0.1.0 to 1.1.0; classifiers added (Development Status, License, Python 3.10/3.11/3.12, Home Automation, Networking); `[project.urls]` section added with Homepage, Repository, Documentation, and Bug Tracker keys using `OWNER` placeholder (no git remote configured).

2. **Publish workflow** (`.github/workflows/publish.yml`): Two-job OIDC trusted publishing workflow — `build` job compiles wheel+sdist and uploads artifact; `publish` job downloads artifact and publishes to PyPI. Triggers only on `v*` tags. `id-token: write` permission scoped to publish job only.

## Verification Results

All 6 plan verification checks passed:
- `version = "1.1.0"` in pyproject.toml
- `__version__ = "1.1.0"` in `__init__.py`
- `[project.urls]` section present in pyproject.toml
- `.github/workflows/publish.yml` exists
- Uses `pypa/gh-action-pypi-publish@release/v1`
- `UNKNOWN.egg-info` does not exist (was already absent)

Build verified: `python3 -m build` produced `luxtronik2_modbus_proxy-1.1.0.tar.gz` and `luxtronik2_modbus_proxy-1.1.0-py3-none-any.whl` successfully. Artifacts cleaned after verification.

## Commits

| Task | Commit | Message |
|------|--------|---------|
| Task 1 | `3676612` | feat(04-01): bump version to 1.1.0 and add PyPI metadata |
| Task 2 | `5ab827e` | feat(04-01): add PyPI trusted publishing workflow |

## Deviations from Plan

None — plan executed exactly as written.

Note: `UNKNOWN.egg-info/` directory was already absent from the worktree; no cleanup was needed.

## Known Stubs

**project.urls OWNER placeholder** — `pyproject.toml` lines contain `OWNER` in all four project URLs. No git remote is configured in this repo, so the actual GitHub username cannot be determined automatically. These URLs must be updated to the real GitHub username before publishing. The PyPI package name `luxtronik2-modbus-proxy` is correct.

## User Setup Required

Before pushing a `v*` tag to trigger the publish workflow, the user must:

1. Replace `OWNER` in `pyproject.toml` `[project.urls]` with the actual GitHub username
2. Create a pending trusted publisher on pypi.org:
   - Package name: `luxtronik2-modbus-proxy`
   - Owner: `<your-github-username>`
   - Repository: `luxtronik2-modbus-proxy` (or `PUBLIC-luxtronik2-modbus-proxy`)
   - Workflow name: `publish.yml`
   - Environment name: `pypi`

## Threat Surface Scan

No new threat surface beyond what was documented in the plan's threat model (T-04-01 through T-04-04). All mitigations were implemented:
- T-04-01: `environment: pypi` with `id-token: write` on publish job only
- T-04-02: Two-job pattern with upload-artifact/download-artifact
- T-04-03: Trigger on `v*` tags only, no branch push trigger
- T-04-04: Accepted (public URLs by design)

## Self-Check: PASSED

All files confirmed present:
- FOUND: pyproject.toml
- FOUND: src/luxtronik2_modbus_proxy/__init__.py
- FOUND: .github/workflows/publish.yml
- FOUND: .planning/phases/04-pypi-publish-hacs-scaffold/04-01-SUMMARY.md

All commits confirmed:
- FOUND commit: 3676612 (feat(04-01): bump version to 1.1.0 and add PyPI metadata)
- FOUND commit: 5ab827e (feat(04-01): add PyPI trusted publishing workflow)

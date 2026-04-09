---
phase: 04-pypi-publish-hacs-scaffold
verified: 2026-04-09T00:00:00Z
status: gaps_found
score: 7/9 must-haves verified
gaps:
  - truth: "pip install luxtronik2-modbus-proxy==1.1.0 succeeds from PyPI"
    status: failed
    reason: "Package is not published on PyPI. No git remote is configured, no v1.1.0 tag was pushed. The publish.yml workflow infrastructure exists but has never been triggered. PyPI API returns 404 for luxtronik2-modbus-proxy."
    artifacts:
      - path: ".github/workflows/publish.yml"
        issue: "Workflow exists and is structurally correct, but has never run — no remote configured, no v* tag pushed"
    missing:
      - "Configure git remote pointing to the real GitHub repository"
      - "Replace OWNER placeholder in pyproject.toml [project.urls] with actual GitHub username"
      - "Register pending trusted publisher on pypi.org (package name: luxtronik2-modbus-proxy, workflow: publish.yml, environment: pypi)"
      - "Push a v1.1.0 tag to trigger the publish workflow"

  - truth: "HACS can add the repository as a custom integration without validation errors"
    status: partial
    reason: "The scaffold structure is complete and schema-valid. However, @OWNER placeholder in manifest.json codeowners and documentation URL fields will cause hacs/action validation to fail on the first real CI run. This is a known stub documented in SUMMARY, but means HACS-01 is not fully met until the placeholder is replaced."
    artifacts:
      - path: "custom_components/luxtronik2_modbus_proxy/manifest.json"
        issue: "codeowners: ['@OWNER'] and documentation/issue_tracker URLs contain OWNER placeholder — hacs/action will reject this as an invalid GitHub username"
    missing:
      - "Replace @OWNER in codeowners with actual GitHub username"
      - "Replace OWNER in documentation and issue_tracker URLs with actual GitHub username"
---

# Phase 4: PyPI Publish & HACS Scaffold Verification Report

**Phase Goal:** The proxy package is on PyPI and the repo has a valid, HACS-discoverable integration skeleton
**Verified:** 2026-04-09
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | pyproject.toml declares version 1.1.0 with classifiers and project.urls | VERIFIED | version = "1.1.0", classifiers list with 8 entries, [project.urls] with 4 keys |
| 2 | src/__init__.py declares __version__ = "1.1.0" | VERIFIED | Line 8: `__version__ = "1.1.0"` |
| 3 | publish.yml triggers on v* tags and uses OIDC trusted publishing | VERIFIED | on.push.tags: v*, id-token: write on publish job, pypa/gh-action-pypi-publish@release/v1 |
| 4 | hacs.json exists at repo root with correct name, homeassistant, render_readme | VERIFIED | name: "Luxtronik 2 Modbus Proxy", homeassistant: "2024.1.0", render_readme: true |
| 5 | manifest.json has all required fields | VERIFIED | All 9 required fields present: domain, name, version, integration_type, iot_class, requirements, codeowners, documentation, config_flow |
| 6 | const.py defines DOMAIN, DEFAULT_PORT, DEFAULT_POLL_INTERVAL, MANUFACTURER, MODEL | VERIFIED | All 5 constants present with correct values |
| 7 | __init__.py is a minimal stub (no integration logic) | VERIFIED | 1 line (docstring only), no imports, no async_setup_entry |
| 8 | pip install luxtronik2-modbus-proxy==1.1.0 succeeds from PyPI (SC1) | FAILED | PyPI API returns 404 for luxtronik2-modbus-proxy. No git remote configured, no v1.1.0 tag pushed. Workflow infrastructure exists but was never triggered. |
| 9 | HACS can add the repository as a custom integration without validation errors (SC2) | PARTIAL | Scaffold is structurally complete, but @OWNER placeholder in manifest.json codeowners/documentation will cause hacs/action to reject the manifest. Known stub, documented in SUMMARY. |

**Score:** 7/9 truths verified

### Roadmap Success Criteria Coverage

The ROADMAP defines 4 success criteria for Phase 4:

| SC | Criterion | Status | Evidence |
|----|-----------|--------|----------|
| 1 | `pip install luxtronik2-modbus-proxy==1.1.0` succeeds from PyPI | FAILED | PyPI API 404. No remote, no v1.1.0 tag. |
| 2 | HACS can add the repository as a custom integration without validation errors | PARTIAL | @OWNER placeholder blocks validation |
| 3 | GitHub Actions validate.yml runs the HACS action on every push and reports pass/fail | VERIFIED (structural) | validate.yml exists with hacs/action@main on push to main and pull_request |
| 4 | hacs.json, manifest.json, const.py, and brand icon exist and are schema-valid | VERIFIED | All 4 exist; icon is 256x256 RGBA PNG; JSON schemas are valid |

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `pyproject.toml` | Version 1.1.0, classifiers, project.urls | VERIFIED | version = "1.1.0"; 8 classifiers; 4 project.urls with OWNER placeholder |
| `src/luxtronik2_modbus_proxy/__init__.py` | __version__ = "1.1.0" | VERIFIED | Line 8 confirmed |
| `.github/workflows/publish.yml` | PyPI trusted publishing on v* tags | VERIFIED | Two-job pattern (build + publish), OIDC id-token: write on publish job only |
| `hacs.json` | HACS repository metadata | VERIFIED | render_readme: true, homeassistant: 2024.1.0 |
| `custom_components/luxtronik2_modbus_proxy/manifest.json` | All required HA fields | VERIFIED (with stub) | All 9 required fields present; OWNER placeholder in codeowners/documentation |
| `custom_components/luxtronik2_modbus_proxy/const.py` | DOMAIN and 4 constants | VERIFIED | DOMAIN = "luxtronik2_modbus_proxy", all 5 constants correct |
| `custom_components/luxtronik2_modbus_proxy/__init__.py` | Minimal stub | VERIFIED | 1-line docstring, no imports |
| `custom_components/luxtronik2_modbus_proxy/brand/icon.png` | Valid 256x256 PNG | VERIFIED | 256x256 RGBA PNG confirmed via Pillow |
| `.github/workflows/validate.yml` | HACS + hassfest CI | VERIFIED | Two independent jobs; hacs/action@main (no checkout); hassfest@master (with checkout) |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `.github/workflows/publish.yml` | `pyproject.toml` | python -m build reads pyproject.toml | VERIFIED | `python -m build` step present in build job |
| `pyproject.toml` | `src/luxtronik2_modbus_proxy/__init__.py` | Both declare version 1.1.0 | VERIFIED | Both files confirmed at 1.1.0 |
| `.github/workflows/validate.yml` | `hacs.json` | hacs/action validates hacs.json schema | VERIFIED (structural) | hacs/action@main with category: "integration" present |
| `.github/workflows/validate.yml` | `custom_components/.../manifest.json` | hassfest validates manifest.json | VERIFIED (structural) | hassfest@master present with explicit checkout |
| `custom_components/.../manifest.json` | `custom_components/.../const.py` | Both define domain luxtronik2_modbus_proxy | VERIFIED | manifest domain: "luxtronik2_modbus_proxy" matches DOMAIN constant |

### Anti-Patterns Found

| File | Content | Severity | Impact |
|------|---------|----------|--------|
| `pyproject.toml` lines 42-45 | OWNER placeholder in all 4 project.urls | Warning | PyPI metadata will show broken URLs on package page; must fix before v* tag push |
| `custom_components/.../manifest.json` lines 8-10 | @OWNER in codeowners, OWNER in documentation/issue_tracker URLs | Blocker | hacs/action validation CI will fail on first real run; blocks HACS-01 and SC2 |
| `UNKNOWN.egg-info/` (repo root) | Stale egg-info directory still present on disk | Info | Gitignored (.gitignore has `UNKNOWN.egg-info/`), not committed; no effect on published package; plan task said to remove it but it was already absent from commits |

Note on UNKNOWN.egg-info: The directory exists on the local filesystem but is gitignored and not tracked. It will not be included in PyPI distributions or affect the build. The plan truth "Stale UNKNOWN.egg-info is removed from worktree" is technically unmet on this worktree's filesystem, but the SUMMARY notes it was "already absent" — this is likely a worktree-specific regeneration. Classified as Info, not Blocker.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| HACS-04 | 04-01-PLAN.md | Proxy package published to PyPI for manifest.json requirements | FAILED | Package not on PyPI (404). Workflow exists but never triggered. |
| HACS-01 | 04-02-PLAN.md | Repository has valid hacs.json, manifest.json, and brand icon | PARTIAL | All files exist and are structurally valid; @OWNER placeholder in manifest.json will block HACS validation |
| HACS-03 | 04-02-PLAN.md | GitHub Actions validate HACS compliance on every push | VERIFIED (structural) | validate.yml exists with correct triggers; will fail on first run due to @OWNER placeholder |

No orphaned requirements: REQUIREMENTS.md traceability table maps exactly HACS-04, HACS-01, HACS-03 to Phase 4. All three are accounted for.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| PyPI package availability | curl pypi.org/pypi/luxtronik2-modbus-proxy/json | HTTP 404 — Not Found | FAIL |
| hacs.json is valid JSON | python3 -c "import json; json.load(open('hacs.json'))" | Parsed successfully | PASS |
| manifest.json domain matches const.py DOMAIN | grep comparison | Both: "luxtronik2_modbus_proxy" | PASS |
| brand/icon.png is 256x256 PNG | python3 PIL check | Size: (256, 256), Mode: RGBA, Format: PNG | PASS |
| publish.yml uses OIDC (not token) | grep id-token | id-token: write found in publish job | PASS |
| validate.yml triggers on push+PR | grep pull_request | pull_request and push to main both present | PASS |

### Gaps Summary

**Gap 1 — PyPI publication not completed (HACS-04, SC1):** The publish workflow (`publish.yml`) is structurally correct and ready for use. However, the package is not on PyPI because no git remote is configured in this worktree and no `v1.1.0` tag has been pushed. The PyPI API returns 404. The goal's first success criterion — that `pip install luxtronik2-modbus-proxy==1.1.0` succeeds — is not met. This is the primary blocker. Resolution requires: configuring the git remote, replacing the OWNER placeholder in `pyproject.toml` URLs, registering a pending trusted publisher on pypi.org, and pushing a `v1.1.0` tag.

**Gap 2 — @OWNER placeholder blocks HACS validation (HACS-01, HACS-03, SC2):** The manifest.json `codeowners` field contains `@OWNER` and the `documentation`/`issue_tracker` URLs contain `OWNER`. The HACS action validates that codeowners references real GitHub usernames. On first CI run, the validate-hacs job will fail. The scaffold structure is otherwise complete and schema-correct. This is a known stub documented in both SUMMARY files, requiring human substitution before the first tag push.

These two gaps share a root cause: the GitHub username (OWNER) was not determined at execution time because no git remote is configured in this repository. Resolving both gaps requires the same prerequisite action — configuring the real GitHub remote — after which OWNER can be substituted throughout.

---

_Verified: 2026-04-09_
_Verifier: Claude (gsd-verifier)_

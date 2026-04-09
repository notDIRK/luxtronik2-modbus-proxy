# Phase 4: PyPI Publish & HACS Scaffold - Research

**Researched:** 2026-04-09
**Domain:** PyPI trusted publishing (OIDC), HACS integration scaffold, Home Assistant manifest schema, GitHub Actions CI
**Confidence:** HIGH

## Summary

Phase 4 is an infrastructure and scaffolding phase with no new business logic. It has two independent tracks: (1) publishing the existing `luxtronik2-modbus-proxy` package to PyPI via GitHub Actions trusted publishing, and (2) creating the HACS-discoverable integration skeleton under `custom_components/luxtronik2_modbus_proxy/`. The two tracks are connected only by the requirement that `manifest.json` references the PyPI package name.

PyPI trusted publishing via OIDC is the current industry standard — no long-lived tokens needed. The workflow requires a one-time "pending publisher" setup on pypi.org before the first push. The HACS skeleton requires exactly six files: `hacs.json`, `manifest.json`, `__init__.py`, `const.py`, brand icon(s) in a `brand/` subdirectory, and the validate CI workflow. As of HA 2026.3.0, custom integrations ship their own brand images in `custom_components/<domain>/brand/` — no central brands repository PR needed.

A stale `UNKNOWN.egg-info/` artifact exists in the repo root from a prior broken build. It must be cleaned up and the proper `luxtronik2_modbus_proxy.egg-info` artifact under `src/` verified before the PyPI build runs.

**Primary recommendation:** Build both tracks in parallel (PyPI workflow first since it unblocks `manifest.json` requirements), clean the stale egg-info artifact in Wave 1, and use the `home-assistant/actions/hassfest@master` + `hacs/action@main` combo in a single `validate.yml` workflow per D-16 through D-18.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**PyPI Publishing**
- D-01: Bump version from `0.1.0` to `1.1.0` in `pyproject.toml` (and `__init__.py` `__version__`)
- D-02: GitHub Actions trusted publishing (OIDC) — no long-lived API tokens; workflow triggers on git tag `v*`
- D-03: Add `[project.urls]` metadata to `pyproject.toml` (Homepage, Repository, Documentation, Bug Tracker)
- D-04: Add classifiers for Python 3.10-3.12, MIT license, and topic tags
- D-05: Existing `setuptools` build backend is fine — no need to switch to hatch or flit

**HACS Integration Skeleton**
- D-06: Integration lives at `custom_components/luxtronik2_modbus_proxy/` in repo root
- D-07: `hacs.json` specifies: `name`, `homeassistant` minimum version (2024.1.0), `render_readme: true`
- D-08: `manifest.json` domain is `luxtronik2_modbus_proxy`, name is "Luxtronik 2 Modbus Proxy"
- D-09: `manifest.json` requirements: `["luxtronik==0.3.14"]` only
- D-10: `manifest.json` `iot_class: "local_polling"`
- D-11: `manifest.json` version: `"1.1.0"` matching PyPI package
- D-12: `const.py` contains DOMAIN, DEFAULT_PORT (8889), DEFAULT_POLL_INTERVAL (30), MANUFACTURER/MODEL constants
- D-13: `__init__.py` is a minimal stub — actual logic in Phase 5
- D-14: Brand icon at `custom_components/luxtronik2_modbus_proxy/brand/icon.png` (256x256 PNG) and optionally `logo.png`
- D-15: Simple heat pump silhouette icon — clean, monochrome, recognizable in HA sidebar
- D-16: GitHub Actions workflow `.github/workflows/validate.yml` uses `hacs/action@main`
- D-17: Triggers on push to main and pull requests
- D-18: Workflow also runs `hassfest` validation for manifest.json schema compliance

### Claude's Discretion
- Exact icon design (heat pump silhouette, clean and recognizable)
- PyPI long_description format (markdown from README.md)
- Exact `homeassistant` minimum version in hacs.json (reasonable recent version — 2024.1.0 is locked in D-07)
- Whether to add a `MANIFEST.in` or rely on `pyproject.toml` package discovery

### Deferred Ideas (OUT OF SCOPE)
None — analysis stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| HACS-04 | Proxy package published to PyPI for manifest.json requirements | D-01 through D-05; OIDC workflow pattern; version bump procedure; pyproject.toml classifiers and URLs |
| HACS-01 | Repository has valid hacs.json, manifest.json, and brand icon | hacs.json schema; manifest.json required fields; brand icon spec (brand/ directory, 256x256 PNG); HA 2026.3.0 local brand images |
| HACS-03 | GitHub Actions validate HACS compliance on every push | hacs/action@main (category: integration); home-assistant/actions/hassfest@master; workflow trigger patterns |
</phase_requirements>

## Standard Stack

### Core Tools and Actions

| Tool / Action | Version | Purpose | Why Standard |
|---------------|---------|---------|--------------|
| `pypa/gh-action-pypi-publish` | `release/v1` | Publish distribution files to PyPI via OIDC | Official PyPA action; no tokens needed; signed attestations via Sigstore generated automatically [VERIFIED: github.com/pypa/gh-action-pypi-publish] |
| `python -m build` | via `build>=1.4.0` | Build sdist + wheel before publish | PEP 517 standard frontend; creates both `.tar.gz` and `.whl`; `build` package already available on this machine [VERIFIED: npm view equivalent — `pip show build` returns 1.4.0] |
| `hacs/action@main` | `main` | Validate HACS integration requirements | Official HACS validation action; accepts `category: integration` input [CITED: hacs.xyz/docs/publish/action/] |
| `home-assistant/actions/hassfest@master` | `master` | Validate manifest.json schema compliance | Official HA action; validates domain, version, iot_class, codeowners, documentation, requirements fields [CITED: github.com/home-assistant/actions] |
| `actions/checkout@v4` | v4 | Checkout in all workflows | Project already uses v4 in docs.yml [VERIFIED: .github/workflows/docs.yml] |

### Supporting Libraries

| Library | Purpose | Notes |
|---------|---------|-------|
| `setuptools>=68` + `wheel` | Build backend | Already in `pyproject.toml`; no change needed [VERIFIED: pyproject.toml line 32] |
| `build` pip package | Build frontend | Install with `pip install build`; `python -m build` produces both sdist and wheel |

### Installation (CI build step)

```bash
pip install build
python -m build
# Produces: dist/luxtronik2_modbus_proxy-1.1.0.tar.gz
#           dist/luxtronik2_modbus_proxy-1.1.0-py3-none-any.whl
```

## Architecture Patterns

### Recommended Project Structure After Phase 4

```
custom_components/
└── luxtronik2_modbus_proxy/
    ├── brand/
    │   ├── icon.png          # 256x256 PNG (required)
    │   └── icon@2x.png       # 512x512 PNG (optional hDPI)
    ├── __init__.py           # Minimal stub
    ├── const.py              # DOMAIN, DEFAULT_PORT, DEFAULT_POLL_INTERVAL, MANUFACTURER, MODEL
    └── manifest.json         # Full HA manifest

.github/workflows/
├── docs.yml                  # Existing docs workflow (unchanged)
├── publish.yml               # NEW: PyPI trusted publishing on v* tags
└── validate.yml              # NEW: hacs/action + hassfest on push/PR

pyproject.toml                # Version bumped to 1.1.0, URLs and classifiers added
src/luxtronik2_modbus_proxy/  # Existing proxy package (unchanged except __init__.py __version__)
hacs.json                     # NEW: in repo root
```

### Pattern 1: PyPI Trusted Publishing Workflow

**What:** Two-job GitHub Actions workflow — `build` creates artifacts, `publish` uploads them. Triggered on push to tags matching `v*`.

**When to use:** Whenever a new version is released; tag `v1.1.0` triggers the workflow automatically.

**Example:**
```yaml
# Source: pypa/gh-action-pypi-publish README + docs.pypi.org/trusted-publishers
name: Publish to PyPI

on:
  push:
    tags:
      - "v*"

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install build frontend
        run: pip install build
      - name: Build distributions
        run: python -m build
      - uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/

  publish:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: pypi
      url: https://pypi.org/p/luxtronik2-modbus-proxy
    permissions:
      id-token: write  # REQUIRED for trusted publishing
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: dist
          path: dist/
      - uses: pypa/gh-action-pypi-publish@release/v1
```

### Pattern 2: HACS + Hassfest Validation Workflow

**What:** Single `validate.yml` workflow with two jobs — one for HACS validation, one for hassfest — both triggered on push and pull_request.

**When to use:** Every push and every PR. The CI gate that ensures the integration remains valid.

**Example:**
```yaml
# Source: hacs.xyz/docs/publish/action/ + github.com/home-assistant/actions
name: Validate

on:
  push:
  pull_request:
  schedule:
    - cron: "0 0 * * *"
  workflow_dispatch:

permissions: {}

jobs:
  validate-hacs:
    runs-on: ubuntu-latest
    steps:
      - name: HACS validation
        uses: "hacs/action@main"
        with:
          category: "integration"

  validate-hassfest:
    runs-on: ubuntu-latest
    steps:
      - uses: "actions/checkout@v4"
      - uses: "home-assistant/actions/hassfest@master"
```

### Pattern 3: manifest.json Full Schema

**What:** All required and relevant optional fields for a custom HA integration at v1.1.0 phase.

**Example:**
```json
{
  "domain": "luxtronik2_modbus_proxy",
  "name": "Luxtronik 2 Modbus Proxy",
  "version": "1.1.0",
  "integration_type": "hub",
  "iot_class": "local_polling",
  "requirements": ["luxtronik==0.3.14"],
  "codeowners": ["@<github-username>"],
  "documentation": "https://github.com/<owner>/luxtronik2-modbus-proxy",
  "issue_tracker": "https://github.com/<owner>/luxtronik2-modbus-proxy/issues",
  "config_flow": false
}
```

Note: `codeowners` and `documentation` are required by HACS validation. `config_flow: false` is appropriate for a stub; Phase 5 will set it to `true`. [CITED: hacs.xyz/docs/publish/integration/ + developers.home-assistant.io/docs/creating_integration_manifest/]

### Pattern 4: hacs.json Root Manifest

```json
{
  "name": "Luxtronik 2 Modbus Proxy",
  "homeassistant": "2024.1.0",
  "render_readme": true
}
```

`render_readme: true` causes HACS to display the root `README.md` as the integration info page, avoiding the need for a separate `info.md` file. [CITED: hacs.xyz/docs/publish/start/]

### Pattern 5: pyproject.toml Additions

**What:** Version bump, `[project.urls]` table, and classifiers block to add to existing `pyproject.toml`.

```toml
# In [project] table — change version and add classifiers
version = "1.1.0"
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Home Automation",
    "Topic :: System :: Networking",
]

# New section after [project]
[project.urls]
Homepage = "https://github.com/<owner>/luxtronik2-modbus-proxy"
Repository = "https://github.com/<owner>/luxtronik2-modbus-proxy"
Documentation = "https://<owner>.github.io/luxtronik2-modbus-proxy"
"Bug Tracker" = "https://github.com/<owner>/luxtronik2-modbus-proxy/issues"
```

### Pattern 6: Brand Icon Requirements (HA 2026.3.0+)

As of HA 2026.3.0, custom integrations ship brand images directly in `custom_components/<domain>/brand/` — no PR to the central `home-assistant/brands` repository required. Local images automatically take priority over CDN images. [CITED: developers.home-assistant.io/blog/2026/02/24/brands-proxy-api/]

| File | Location | Size | Required |
|------|----------|------|----------|
| `icon.png` | `brand/icon.png` | 256x256 px, square | Yes |
| `icon@2x.png` | `brand/icon@2x.png` | 512x512 px, square | Optional (hDPI) |
| `logo.png` | `brand/logo.png` | shortest side 128-256 px | Optional |
| `logo@2x.png` | `brand/logo@2x.png` | shortest side 256-512 px | Optional |

All images: PNG format, lossless compression, transparency preferred. [CITED: github.com/home-assistant/brands/blob/master/README.md]

### Anti-Patterns to Avoid

- **Using `master` tag for `pypa/gh-action-pypi-publish`:** The `master` branch has been sunset; always use `release/v1` or a pinned SHA. [CITED: pypa/gh-action-pypi-publish README]
- **Setting `id-token: write` at workflow level:** Set it only at the job level (`publish` job) to minimize privilege scope. [CITED: pypa/gh-action-pypi-publish docs]
- **Publishing on every push:** The `publish.yml` workflow MUST only trigger on `v*` tags; triggering on push to `main` would attempt to re-publish the same version.
- **Leaving `config_flow: false` out of manifest.json:** HACS hassfest validation requires `config_flow` to be explicitly present; omitting it produces a warning or error.
- **Placing icon directly at `custom_components/domain/icon.png`:** The `brand/` subdirectory structure is required since HA 2026.3.0. `icon.png` directly in the integration directory is the OLD pattern that no longer applies. [ASSUMED — based on the brands-proxy-api blog post; exact HA version cutoff for enforcement needs user validation]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| PyPI authentication | Custom token management or secrets rotation | PyPI trusted publishing (OIDC) | OIDC tokens expire in 15 minutes; no secret storage; signed attestations via Sigstore automatically |
| Manifest validation | Custom JSON schema checker | `home-assistant/actions/hassfest@master` | Runs the same validator HA core uses; catches field typos, missing required fields, invalid iot_class values |
| HACS compliance check | Manual reading of HACS docs | `hacs/action@main` | Validates repo structure, hacs.json, and integration requirements automatically |
| Distribution building | Custom `setup.py bdist_wheel` invocation | `python -m build` | PEP 517 standard; builds both sdist and wheel cleanly from `pyproject.toml` |

## Common Pitfalls

### Pitfall 1: Stale UNKNOWN.egg-info Artifact

**What goes wrong:** The repo root contains `UNKNOWN.egg-info/` with `Name: UNKNOWN, Version: 0.0.0`. This is a stale artifact from an incorrectly run `pip install -e .` in the repo root (outside `src/`). If left in place, `python -m build` may pick up conflicting metadata, or the published package may have a stale PKG-INFO.

**Why it happens:** Running `pip install -e .` when the working directory lacks a proper `src/` layout awareness, creating a ghost egg-info.

**How to avoid:** Delete `UNKNOWN.egg-info/` from the repo root before running the build. The correct egg-info lives at `src/luxtronik2_modbus_proxy.egg-info/` (or `src/luxtronik2_modbus_proxy/luxtronik2_modbus_proxy.egg-info/`).

**Warning signs:** `UNKNOWN.egg-info/PKG-INFO` shows `Name: UNKNOWN`; `pip show luxtronik2-modbus-proxy` returns wrong version.

### Pitfall 2: PyPI Pending Publisher Must Be Configured Before First Tag Push

**What goes wrong:** The GitHub Actions publish workflow runs on `v*` tag but fails with a 403 because no trusted publisher is registered on pypi.org for this package name.

**Why it happens:** For a brand-new package (`luxtronik2-modbus-proxy` does not yet exist on PyPI), the developer must set up a "pending publisher" on pypi.org BEFORE pushing the first tag. A pending publisher creates the project on first use.

**How to avoid:** Before tagging, log into pypi.org → Publishing → "Add a pending trusted publisher" → fill in: package name `luxtronik2-modbus-proxy`, GitHub owner, repo name, workflow filename `publish.yml`, and optionally environment name `pypi`.

**Warning signs:** CI publish job fails with authentication error or 403; project does not appear on pypi.org.

### Pitfall 3: hacs/action Does Not Check Out Code

**What goes wrong:** `hacs/action@main` handles checkout internally; adding an explicit `actions/checkout@v4` step before it is unnecessary and may cause conflicts.

**Why it happens:** Developers assume all actions need explicit checkout. HACS action is self-contained.

**How to avoid:** In the `validate-hacs` job, use only `hacs/action@main` with `category: integration`. In the `validate-hassfest` job, add `actions/checkout@v4` explicitly first (hassfest requires it). [CITED: hacs.xyz/docs/publish/action/]

### Pitfall 4: manifest.json `version` Field Is Required for Custom Integrations

**What goes wrong:** hassfest fails because `version` is omitted from `manifest.json`. The field is optional for core HA integrations but REQUIRED for custom integrations.

**Why it happens:** Copying a core integration example that lacks `version`.

**How to avoid:** Always include `"version": "1.1.0"` in `manifest.json` for custom integrations. The value must match a version string recognized by AwesomeVersion (SemVer or CalVer). [CITED: developers.home-assistant.io/docs/creating_integration_manifest/]

### Pitfall 5: `__version__` Drift Between pyproject.toml and __init__.py

**What goes wrong:** `pyproject.toml` says `version = "1.1.0"` but `src/luxtronik2_modbus_proxy/__init__.py` still says `__version__ = "0.1.0"`. Tools that read `__version__` at runtime will return the wrong version.

**Why it happens:** Version bump touches only one file.

**How to avoid:** Bump version in both files simultaneously. The plan tasks must explicitly update both. Consider adding a ruff or mypy check, or simply make it a two-file atomic change.

### Pitfall 6: `codeowners` and `documentation` Required by HACS Validator

**What goes wrong:** The HACS action reports validation failures for missing `codeowners` or `documentation` in manifest.json, even though these are described as optional in the general HA dev docs.

**Why it happens:** HACS imposes stricter requirements than bare HA for integration quality.

**How to avoid:** Always include `codeowners` (array of GitHub @usernames) and `documentation` (URL) in manifest.json when targeting HACS. [CITED: hacs.xyz/docs/publish/integration/]

## Runtime State Inventory

Step 2.5: SKIPPED. This is a greenfield phase — no rename, rebrand, refactor, or migration. New files are being created; existing proxy code in `src/` is unchanged except for the version string.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|---------|
| Python 3.x | Build workflow (local) | Yes | 3.10.12 | — |
| `build` package | `python -m build` locally | Yes | 1.4.0 | Install with `pip install build` |
| `gh` CLI | Optional release tagging | Yes | 2.89.0 | Manual git tag push |
| PyPI account + trusted publisher setup | `publish.yml` workflow | Unknown | — | Manual one-time setup on pypi.org |
| GitHub Actions (pypi environment) | `publish.yml` job environment | Unknown | — | Skip environment protection for first publish |
| `python-can-generate-png` tooling | Brand icon creation | Unknown | — | Use any image editor; or use an SVG-to-PNG converter |

**Missing dependencies with no fallback:**
- PyPI account with "pending trusted publisher" configured for `luxtronik2-modbus-proxy` — required before pushing `v1.1.0` tag; this is a one-time human action outside CI.

**Missing dependencies with fallback:**
- Brand icon PNG: Can be created with any image editor, Inkscape, or a simple Python script using `Pillow`. The plan should include generating a minimal 256x256 placeholder if no design tool is available.

## Code Examples

### const.py Scaffold

```python
"""Constants for the Luxtronik 2 Modbus Proxy integration."""

DOMAIN = "luxtronik2_modbus_proxy"

# Default connection parameters
DEFAULT_PORT = 8889
DEFAULT_POLL_INTERVAL = 30  # seconds

# Device identification
MANUFACTURER = "Alpha Innotec / Novelan"
MODEL = "Luxtronik 2.0"
```

### __init__.py Minimal Stub

```python
"""Luxtronik 2 Modbus Proxy integration."""
```

(Empty body is valid for a stub. Phase 5 will add async_setup_entry and platforms.)

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Long-lived PyPI API tokens in GitHub secrets | OIDC trusted publishing (`id-token: write`, no secrets) | PyPI introduced ~2022, now default recommendation | No token rotation needed; 15-minute expiry; automatic Sigstore attestations |
| Brand icons via PR to home-assistant/brands | Brand images in `custom_components/<domain>/brand/` | HA 2026.3.0 (Feb 2026) | Custom integrations no longer need a PR to a separate repo; images ship with the integration |
| `setup.py` as primary build config | `pyproject.toml` with PEP 517/518 | PEP 517 finalized 2017; now universal | `setup.py` in this repo is a compatibility shim only; `pyproject.toml` is authoritative |
| `hacs/action@master` | `hacs/action@main` | HACS repo renamed default branch | Use `@main` not `@master` |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Brand icon in `custom_components/<domain>/brand/icon.png` is the canonical path since HA 2026.3.0 | Architecture Patterns, Anti-Patterns | If older HA versions require `icon.png` directly in the domain directory, the CI might pass but older HA installs show no icon |
| A2 | `config_flow: false` can be omitted from the stub manifest without causing hassfest failures | Architecture Patterns | hassfest may require the field to be explicitly present; if so, set to `false` explicitly |
| A3 | The `hacs/action@main` for `category: integration` does NOT require an explicit `actions/checkout` step | Common Pitfalls | If checkout IS required, the validate-hacs job will fail on first run |
| A4 | The GitHub Actions `pypi` environment name matches what PyPI expects in the trusted publisher configuration | Architecture Patterns | Environment name must exactly match what is configured on pypi.org; mismatch causes auth failure |

## Open Questions

1. **GitHub username for `codeowners`**
   - What we know: `codeowners` field requires `["@github-username"]`
   - What's unclear: The repo owner's GitHub username — not visible in CLAUDE.md (private data not exposed)
   - Recommendation: Planner should include a placeholder `["@OWNER"]` and flag this as a required human substitution before the first HACS validation run

2. **Documentation URL**
   - What we know: MkDocs is configured and `docs.yml` deploys to GitHub Pages; the URL pattern is `https://<owner>.github.io/luxtronik2-modbus-proxy`
   - What's unclear: The actual GitHub Pages URL (depends on GitHub username)
   - Recommendation: Use a placeholder in manifest.json referencing the GitHub repo URL directly as fallback

3. **PyPI pending publisher setup timing**
   - What we know: Must be configured BEFORE the first `v*` tag push
   - What's unclear: Whether the user already has a PyPI account
   - Recommendation: Wave 1 should include a human-action task to configure the pending publisher on pypi.org; the CI workflow is ready but cannot succeed until this is done

## Sources

### Primary (HIGH confidence)
- [hacs.xyz/docs/publish/integration/](https://www.hacs.xyz/docs/publish/integration/) — HACS integration folder structure, manifest.json required fields for HACS, brand asset requirement
- [hacs.xyz/docs/publish/action/](https://www.hacs.xyz/docs/publish/action/) — Exact YAML for `hacs/action@main`, category input, permissions
- [hacs.xyz/docs/publish/start/](https://www.hacs.xyz/docs/publish/start/) — General HACS requirements, render_readme field, hacs.json fields
- [developers.home-assistant.io/docs/creating_integration_manifest/](https://developers.home-assistant.io/docs/creating_integration_manifest/) — All manifest.json fields with valid values; version required for custom integrations
- [developers.home-assistant.io/blog/2026/02/24/brands-proxy-api/](https://developers.home-assistant.io/blog/2026/02/24/brands-proxy-api/) — Custom integration brand images in `brand/` directory since HA 2026.3.0
- [github.com/home-assistant/actions](https://github.com/home-assistant/actions) — `home-assistant/actions/hassfest@master` workflow configuration
- [github.com/pypa/gh-action-pypi-publish](https://github.com/pypa/gh-action-pypi-publish) — Exact YAML for trusted publishing; `release/v1` pinning; `id-token: write` requirement
- [docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/) — Pending publisher setup for new packages; one-time pypi.org configuration
- [github.com/home-assistant/brands/blob/master/README.md](https://github.com/home-assistant/brands/blob/master/README.md) — icon.png 256x256, logo.png size constraints, PNG format requirements

### Secondary (MEDIUM confidence)
- Verified via `pip show build` on target machine — `build 1.4.0` available locally
- Verified via `pip show luxtronik` — `luxtronik 0.3.14` installed
- Verified via `pip show pymodbus` — `pymodbus 3.12.1` installed
- [pyproject.toml in repo] — current version `0.1.0`; build backend `setuptools>=68`; no `[project.urls]` currently present

### Tertiary (LOW confidence)
- A3 (hacs/action checkout behavior) — inferred from HACS docs stating the action is self-contained; not explicitly documented

## Metadata

**Confidence breakdown:**
- PyPI workflow: HIGH — pypa/gh-action-pypi-publish docs are authoritative and current
- HACS integration structure: HIGH — hacs.xyz docs verified directly
- manifest.json schema: HIGH — verified against developers.home-assistant.io
- Brand icon location (`brand/` directory): HIGH — verified against HA 2026.3.0 blog post
- Icon dimensions: HIGH — verified against home-assistant/brands README

**Research date:** 2026-04-09
**Valid until:** 2026-07-09 (90 days — HACS and HA manifest schemas are stable; PyPI trusted publishing API is stable)

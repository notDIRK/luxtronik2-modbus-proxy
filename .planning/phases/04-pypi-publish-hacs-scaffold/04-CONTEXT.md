# Phase 4: PyPI Publish & HACS Scaffold - Context

**Gathered:** 2026-04-09 (auto mode)
**Status:** Ready for planning

<domain>
## Phase Boundary

The proxy package is published to PyPI as `luxtronik2-modbus-proxy==1.1.0` and the repository has a valid, HACS-discoverable integration skeleton with `hacs.json`, `manifest.json`, `const.py`, brand icon, and CI validation. This phase does NOT implement any HA integration logic (coordinator, config flow, entities) — only the scaffold that later phases build on.

</domain>

<decisions>
## Implementation Decisions

### PyPI Publishing
- **D-01:** Bump version from `0.1.0` to `1.1.0` in `pyproject.toml` to match v1.1 milestone
- **D-02:** Use GitHub Actions with trusted publishing (OIDC) — no long-lived API tokens; workflow triggers on git tag `v*`
- **D-03:** Add `[project.urls]` metadata to `pyproject.toml` (Homepage, Repository, Documentation, Bug Tracker) for PyPI display
- **D-04:** Add classifiers for Python 3.10-3.12, MIT license, and topic tags
- **D-05:** Existing `setuptools` build backend is fine — no need to switch to hatch or flit

### HACS Integration Skeleton
- **D-06:** Integration lives at `custom_components/luxtronik2_modbus_proxy/` in repo root (monorepo layout, decided in STATE.md)
- **D-07:** `hacs.json` specifies: `name`, `homeassistant` minimum version (2024.1.0), `render_readme: true`
- **D-08:** `manifest.json` domain is `luxtronik2_modbus_proxy`, name is "Luxtronik 2 Modbus Proxy"
- **D-09:** `manifest.json` requirements: `["luxtronik==0.3.14"]` only — HA integration bypasses pymodbus entirely and talks directly to Luxtronik via the luxtronik library (architecture decision from STATE.md)
- **D-10:** `manifest.json` `iot_class: "local_polling"` — integration connects locally and polls periodically
- **D-11:** `manifest.json` version: `"1.1.0"` matching PyPI package
- **D-12:** `const.py` contains DOMAIN, DEFAULT_PORT (8889), DEFAULT_POLL_INTERVAL (30), and MANUFACTURER/MODEL constants
- **D-13:** `__init__.py` is a minimal stub (empty or just `"""Luxtronik 2 Modbus Proxy integration."""`) — actual logic comes in Phase 5

### Brand Icon
- **D-14:** Custom SVG icon placed at `custom_components/luxtronik2_modbus_proxy/icon.png` (64x64 PNG) and optionally `logo.png` (256x256)
- **D-15:** Simple heat pump silhouette icon — clean, monochrome, recognizable in HA sidebar

### CI Validation
- **D-16:** GitHub Actions workflow `.github/workflows/validate.yml` uses `hacs/action@main`
- **D-17:** Triggers on push to main and on pull requests
- **D-18:** Workflow also runs `hassfest` validation for manifest.json schema compliance

### Claude's Discretion
- Exact icon design (as long as it's a heat pump silhouette, clean and recognizable)
- PyPI long_description format (markdown from README.md)
- Exact `homeassistant` minimum version in hacs.json (reasonable recent version)
- Whether to add a `MANIFEST.in` or rely on `pyproject.toml` package discovery

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project architecture
- `.planning/PROJECT.md` — Core value, constraints, monorepo decision
- `.planning/STATE.md` — v1.1 architecture decisions (monorepo, PyPI first, no proxy reuse in HA)
- `.planning/REQUIREMENTS.md` — HACS-01, HACS-03, HACS-04 acceptance criteria

### Existing package config
- `pyproject.toml` — Current build config, dependencies, version (0.1.0)
- `setup.py` — Legacy setup file (may need removal or coordination)

### GitHub Actions
- `.github/workflows/docs.yml` — Existing workflow pattern for reference

### External references (not in repo)
- HACS documentation: hacs.json schema, manifest.json requirements
- PyPI trusted publishing docs: OIDC setup for GitHub Actions
- HA developer docs: custom component structure, hassfest validation

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `pyproject.toml` — Already has package name, dependencies, build config; needs version bump and metadata additions
- `.github/workflows/docs.yml` — Existing GH Actions pattern (checkout, setup-python, cache) to reference for new workflows
- `src/luxtronik2_modbus_proxy/` — Existing package structure with `__init__.py`, all modules

### Established Patterns
- Package uses `setuptools` with `src/` layout — `[tool.setuptools.packages.find] where = ["src"]`
- Dependencies pinned with ranges (e.g., `pydantic>=2.12,<3`) — consistent strategy for manifest.json

### Integration Points
- `custom_components/luxtronik2_modbus_proxy/` is a NEW directory — no existing integration code
- `manifest.json` requirements list connects to PyPI package availability
- `hacs.json` connects to HACS discovery and validation
- `validate.yml` connects to existing `.github/workflows/` directory

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches. Follow HACS and PyPI best practices.

</specifics>

<deferred>
## Deferred Ideas

None — analysis stayed within phase scope.

</deferred>

---

*Phase: 04-pypi-publish-hacs-scaffold*
*Context gathered: 2026-04-09*

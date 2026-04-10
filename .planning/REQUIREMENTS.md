# Requirements: luxtronik2-hass (formerly luxtronik2-modbus-proxy)

**Defined:** 2026-04-10
**Core Value:** Owners of Luxtronik 2.0 heat pumps can integrate them into modern energy management systems — with Home Assistant as the primary, supported integration path.

## v1.2 Requirements

Requirements for the Repo Split & HA-First Rebrand milestone. Each maps to roadmap phases.

### Repo Split (SPLIT)

- [ ] **SPLIT-01**: New GitHub repository `notDIRK/luxtronik2-hass` exists, is public, MIT-licensed
- [ ] **SPLIT-02**: Git history of the HACS integration (Phases 4-7 commits + related quick tasks) is preserved in the new repo — `git blame` on `coordinator.py` and `config_flow.py` resolves to original commits
- [ ] **SPLIT-03**: New repo contains only HA-relevant files (`custom_components/`, HA tests, HA docs, `pyproject.toml` for dev deps) — no `src/` proxy leftovers, no `Dockerfile`, no `config.example.yaml`, no `mkdocs.yml`
- [ ] **SPLIT-04**: Old repo `luxtronik2-modbus-proxy` is archived on GitHub (read-only, visible "Archived" label in repo UI)
- [ ] **SPLIT-05**: Old repo README starts with a prominent "⚠️ Experimental — not actively maintained" banner and a forward link to the new repo

### Rename (RENAME)

- [ ] **RENAME-01**: `manifest.json` `domain` renamed from `luxtronik2_modbus_proxy` to `luxtronik2_hass`; `name` updated to reflect the HA-first identity
- [ ] **RENAME-02**: `custom_components/luxtronik2_modbus_proxy/` directory renamed to `custom_components/luxtronik2_hass/` in the new repo
- [ ] **RENAME-03**: `const.py` `DOMAIN` constant and all Python imports/references updated to `luxtronik2_hass`
- [ ] **RENAME-04**: `pyproject.toml` in the new repo uses package name `luxtronik2-hass` (dev-only, not published to PyPI)
- [ ] **RENAME-05**: All internal strings, logger names, HACS update URLs, documentation URLs, and badge URLs updated to point at the new repo and domain

### Documentation (DOCS)

- [ ] **DOCS-01**: `README.md` (EN) in the new repo uses three-path structure with honest status labels: Path 1 (HACS HA integration, ✅ Supported), Path 2 (Legacy Modbus Proxy, ⚠️ Experimental, linked to archived repo), Path 3 (HA Add-on, 📋 Planned v1.3)
- [ ] **DOCS-02**: `README.de.md` is a content-equivalent German mirror of `README.md`
- [ ] **DOCS-03**: Both READMEs make it clear within the first 3 sentences that the primary use case is Home Assistant; the Modbus proxy is a legacy byproduct and is not maintained
- [ ] **DOCS-04**: `MIGRATION.md` in the new repo documents the steps for v1.1 users to upgrade (remove old integration, install new, re-enter IP, confirm dashboard still works)
- [ ] **DOCS-05**: Old repo READMEs (EN + DE) begin with the experimental banner and a "→ Use [luxtronik2-hass](link) instead" forward link

### Maintainer Migration (MIGRATE)

- [ ] **MIGRATE-01**: Old integration `luxtronik2_modbus_proxy` is removed from the maintainer's HA instance (config entry deleted, no ghost entities left)
- [ ] **MIGRATE-02**: New integration `luxtronik2_hass` is installed via HACS custom repository, config flow completes successfully with the re-entered IP
- [ ] **MIGRATE-03**: All 31 previous entities are re-created under the stable `luxtronik_2_0_*` device slug, and `dashboard-waermepumpe.yaml` renders all values correctly

## v1.3 Requirements (Planned, not in this milestone)

### HA Add-on

- **ADDON-01**: Proxy is available as a Home Assistant Add-on for HA OS / Supervised installations
- **ADDON-02**: Add-on configuration exposes `luxtronik_host`, `modbus_port`, `enable_writes`, `write_rate_limit` through the HA UI
- **ADDON-03**: Add-on README documents evcc integration using the Supervisor-internal hostname

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| PyPI republish or rename | HA integration does not depend on the proxy's PyPI package (manifest requirements: `luxtronik==0.3.14`). Old package name was never published (trusted-publishing setup was pending). No PyPI work needed. |
| Docker image rename | Docker image belongs to the proxy, which is being archived. No new Docker releases. |
| HA Add-on (Path 3) | Deferred to v1.3 — v1.2 is rebrand-only |
| Code changes to the proxy | Proxy is frozen as legacy in the archived repo |
| Automated migration for external users | Sole existing user is the maintainer; any future users follow `MIGRATION.md` manually |
| HACS default store listing | Remains "Custom Repository" in v1.2; official listing is a separate track for later |
| Changes to entity IDs or device names | Deliberately stable — this is the core of the "painless migration" promise |
| Tests / CI infrastructure refactor | Existing CI carries over unchanged |
| New features in the HA integration | v1.2 is refactor-only; no behavior changes |
| Backporting the proxy to a Python package used by HA | Proxy is standalone; HA uses `luxtronik` library directly |
| Out-of-scope entries from v1.1 that are now resolved | Options Flow (CONF-10) shipped as a quick task; Diagnostics (CONF-11) still deferred |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| SPLIT-01 | Phase 11 | Pending |
| SPLIT-02 | Phase 8 | Pending |
| SPLIT-03 | Phase 8 | Pending |
| SPLIT-04 | Phase 11 | Pending |
| SPLIT-05 | Phase 11 | Pending |
| RENAME-01 | Phase 9 | Pending |
| RENAME-02 | Phase 9 | Pending |
| RENAME-03 | Phase 9 | Pending |
| RENAME-04 | Phase 9 | Pending |
| RENAME-05 | Phase 9 | Pending |
| DOCS-01 | Phase 10 | Pending |
| DOCS-02 | Phase 10 | Pending |
| DOCS-03 | Phase 10 | Pending |
| DOCS-04 | Phase 10 | Pending |
| DOCS-05 | Phase 11 | Pending |
| MIGRATE-01 | Phase 12 | Pending |
| MIGRATE-02 | Phase 12 | Pending |
| MIGRATE-03 | Phase 12 | Pending |

**Coverage:**
- v1.2 requirements: 18 total
- Mapped to phases: 18
- Unmapped: 0

## Archive — v1.1 Requirements (Shipped)

All 19 requirements from v1.1 (SETUP, SENS, CTRL, HACS, ARCH categories) shipped in Phases 4-7 on 2026-04-09. See `.planning/MILESTONES.md` for the v1.1 summary. Six HUMAN-UAT items from `06-VERIFICATION.md` remain pending human verification on a live HA instance.

---
*Requirements defined: 2026-04-10*
*Last updated: 2026-04-10 at start of milestone v1.2 — Repo Split & HA-First Rebrand*

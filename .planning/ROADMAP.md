# Roadmap: luxtronik2-hass (formerly luxtronik2-modbus-proxy)

## Milestones

- ✅ **v1.0 MVP** — Phases 1-3 (shipped 2026-04-08) — [Archive](milestones/v1.0-ROADMAP.md)
- ✅ **v1.1 HACS Integration** — Phases 4-7 (code-complete 2026-04-09)
- **v1.2 Repo Split & HA-First Rebrand** — Phases 8-12 (active)

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 1-3) — SHIPPED 2026-04-08</summary>

- [x] Phase 1: Core Proxy (4/4 plans) — Async protocol bridge with write safety, curated defaults, Docker, and logging
- [x] Phase 2: Integration-Ready Register Map (3/3 plans) — Full parameter database, SG-ready virtual register, and evcc/HA integration docs
- [x] Phase 3: Documentation and Release (4/4 plans) — Bilingual user and developer guides, systemd service, and GitHub Pages

</details>

<details>
<summary>✅ v1.1 HACS Integration (Phases 4-7) — CODE-COMPLETE 2026-04-09</summary>

- [x] Phase 4: PyPI Publish & HACS Scaffold — Proxy package on PyPI, repo skeleton with hacs.json + manifest.json + brand icon + CI validation action
- [x] Phase 5: Coordinator & Config Flow — DataUpdateCoordinator with connect-per-call, asyncio.Lock, config flow UI
- [x] Phase 6: Sensor Entities — Read-only temperature, mode, power, and status sensors; entity registry exposes full 1,126-parameter database
- [x] Phase 7: Control Entities & Translations — HeatingMode/HotWaterMode/SG-Ready select entities, setpoint numbers, write rate limiting, EN+DE translations

</details>

**v1.2 Repo Split & HA-First Rebrand**

- [ ] **Phase 8: New Repo Extraction & Setup** — Create local `luxtronik2-hass` working copy via `git filter-repo`, strip proxy-only files, verify history is intact. No push, no rename yet.
- [ ] **Phase 9: Rename in New Repo** — Rename HACS domain, Python package, `custom_components/` folder, const, imports, and all internal references in the extracted working copy.
- [ ] **Phase 10: Documentation Rewrite** — EN+DE README with three-path positioning (Supported / Experimental / Planned) plus `MIGRATION.md` in the new-repo working copy.
- [ ] **Phase 11: Publish & Archive Legacy** — Push new repo to GitHub, add experimental banner + forward link to old repo README (EN+DE), archive the old repo. Irreversible checkpoint.
- [ ] **Phase 12: Maintainer Migration Verification** — Live migration on the maintainer's HA instance: remove old integration, install new via HACS custom repository, verify all 31 entities + dashboard render correctly.

## Phase Details

### Phase 8: New Repo Extraction & Setup
**Goal**: A clean local working copy of the future `luxtronik2-hass` repo exists with preserved HACS integration history and no proxy artifacts — ready for rename work in Phase 9.
**Depends on**: Phase 7 (v1.1 code-complete)
**Requirements**: SPLIT-02, SPLIT-03
**Success Criteria** (what must be TRUE):
  1. A local clone-derived working directory (e.g. `~/claude-code/luxtronik2-hass/`) exists, produced via `git filter-repo --path custom_components/ --path tests/ --path .github/` (or equivalent), with no remote origin set.
  2. `git log -- custom_components/` in the new working copy shows all Phase 4-7 commits and the quick-task backup commits; `git blame` on `coordinator.py` and `config_flow.py` resolves to the original SHAs.
  3. The working copy contains no `src/`, no `Dockerfile`, no `config.example.yaml`, no `mkdocs.yml`, no `docs/en/proxy*`, no systemd unit file — verified by `find` listing.
  4. A trimmed `pyproject.toml` (dev deps only, no proxy entry points) and `README.md` placeholder exist so the tree is coherent; existing HA tests still pass under `pytest`.
**Plans**: TBD

### Phase 9: Rename in New Repo
**Goal**: The extracted working copy is fully rebranded as `luxtronik2_hass` internally — domain, folder, package, imports, strings — with HA integration tests still passing.
**Depends on**: Phase 8
**Requirements**: RENAME-01, RENAME-02, RENAME-03, RENAME-04, RENAME-05
**Success Criteria** (what must be TRUE):
  1. `custom_components/luxtronik2_hass/` exists; `custom_components/luxtronik2_modbus_proxy/` does not; `manifest.json` `domain` is `luxtronik2_hass` and `name` reflects the HA-first identity.
  2. `grep -r luxtronik2_modbus_proxy` in the working copy returns zero hits across Python sources, tests, translations, and pyproject.toml (historical commit messages in `git log` are allowed).
  3. `const.py` `DOMAIN` equals `luxtronik2_hass`; all imports, logger names, HACS update URLs, documentation URLs and badge URLs point at `notDIRK/luxtronik2-hass`.
  4. `pytest` passes on the renamed tree; the HA integration loads without domain/import errors when smoke-loaded.
**Plans**: TBD
**UI hint**: yes

### Phase 10: Documentation Rewrite
**Goal**: The new working copy has honest, HA-first documentation (EN+DE) with three-path positioning and a migration guide for v1.1 users.
**Depends on**: Phase 9
**Requirements**: DOCS-01, DOCS-02, DOCS-03, DOCS-04
**Success Criteria** (what must be TRUE):
  1. `README.md` (EN) opens with three-path structure and honest status labels: Path 1 HACS HA integration ✅ Supported, Path 2 Legacy Modbus Proxy ⚠️ Experimental (linked to archived repo), Path 3 HA Add-on 📋 Planned v1.3.
  2. `README.de.md` is a content-equivalent German mirror of `README.md` — same sections, same links, same labels.
  3. Both READMEs state within the first three sentences that Home Assistant is the primary supported use case and the Modbus proxy is an unmaintained legacy byproduct.
  4. `MIGRATION.md` documents the v1.1 → v1.2 upgrade path: remove old integration, add new via HACS custom repository, re-enter IP, verify dashboard renders — with a "one dashboard file, 31 entities, zero automations" blast-radius note matching the maintainer's live snapshot.
**Plans**: TBD
**UI hint**: yes

### Phase 11: Publish & Archive Legacy
**Goal**: `notDIRK/luxtronik2-hass` is public on GitHub and the old repo is archived behind an experimental banner with forward links — the rebrand is live and irreversible.
**Depends on**: Phase 10
**Requirements**: SPLIT-01, SPLIT-04, SPLIT-05, DOCS-05
**Success Criteria** (what must be TRUE):
  1. `gh repo view notDIRK/luxtronik2-hass` shows a public, MIT-licensed repository containing `custom_components/luxtronik2_hass/`; clicking through to `coordinator.py` shows the preserved Phase 4-7 commit history via `git blame`.
  2. The old repo `notDIRK/luxtronik2-modbus-proxy` displays the GitHub "Archived" label, is read-only, and both `README.md` and `README.de.md` begin with a "⚠️ Experimental — not actively maintained" banner and a "→ Use luxtronik2-hass instead" forward link to the new repo.
  3. Pre-commit secret scan passes on both repos before their respective final pushes; no IP/hostname/credential leak in the new repo or in the banner commit on the old one.
  4. The HACS custom repository URL for the new repo validates successfully in a trial HACS "Add custom repository" dialog (no manifest/hacs.json errors).
**Plans**: TBD

### Phase 12: Maintainer Migration Verification
**Goal**: The maintainer's live HA instance runs the new `luxtronik2_hass` integration end-to-end with all entities and the dashboard intact — proving the rebrand works in practice.
**Depends on**: Phase 11
**Requirements**: MIGRATE-01, MIGRATE-02, MIGRATE-03
**Success Criteria** (what must be TRUE):
  1. On the maintainer's HA 2026.4.1 instance, the old `luxtronik2_modbus_proxy` config entry is deleted and the HA entity registry shows zero entities referencing the old domain (no ghosts).
  2. The new `luxtronik2_hass` integration is installed via HACS "Add custom repository" pointing at `notDIRK/luxtronik2-hass`, and the config flow completes successfully after entering the heat pump IP.
  3. After the new integration loads, the HA entity registry shows all 31 previously expected entities under the stable `luxtronik_2_0_*` device slug, and `docs/examples/dashboard-waermepumpe.yaml` renders all 32 referenced values without "entity not found" errors.
**Plans**: TBD
**UI hint**: yes

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Core Proxy | v1.0 | 4/4 | Complete | 2026-04-05 |
| 2. Integration-Ready Register Map | v1.0 | 3/3 | Complete | 2026-04-06 |
| 3. Documentation and Release | v1.0 | 4/4 | Complete | 2026-04-06 |
| 4. PyPI Publish & HACS Scaffold | v1.1 | 2/2 | Complete | 2026-04-09 |
| 5. Coordinator & Config Flow | v1.1 | 2/2 | Complete | 2026-04-09 |
| 6. Sensor Entities | v1.1 | 2/2 | Complete | 2026-04-09 |
| 7. Control Entities & Translations | v1.1 | 3/3 | Complete | 2026-04-09 |
| 8. New Repo Extraction & Setup | v1.2 | 0/? | Ready to plan | - |
| 9. Rename in New Repo | v1.2 | 0/? | Not started | - |
| 10. Documentation Rewrite | v1.2 | 0/? | Not started | - |
| 11. Publish & Archive Legacy | v1.2 | 0/? | Not started | - |
| 12. Maintainer Migration Verification | v1.2 | 0/? | Not started | - |

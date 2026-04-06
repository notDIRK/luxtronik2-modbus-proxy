---
phase: 03-documentation-and-release
plan: 01
subsystem: documentation
tags: [mkdocs, material, i18n, github-actions, docs-infrastructure]
dependency_graph:
  requires: []
  provides: [mkdocs-site-scaffold, docs-en-homepage, docs-de-homepage, gh-pages-deploy-workflow]
  affects: [03-02, 03-03, 03-04]
tech_stack:
  added: [mkdocs-material==9.7.6, mkdocs-static-i18n==1.3.1]
  patterns: [mkdocs-folder-i18n, github-actions-gh-deploy, material-theme]
key_files:
  created:
    - mkdocs.yml
    - docs/en/index.md
    - docs/de/index.md
    - .github/workflows/docs.yml
  modified: []
decisions:
  - "MkDocs Material theme with mkdocs-static-i18n in folder mode (docs_structure: folder) — avoids navigation.instant incompatibility with language switcher"
  - "Pin mkdocs-material==9.7.6 and mkdocs-static-i18n==1.3.1 in CI — reproducible builds, no surprise breakage on dependency updates"
  - "OWNER placeholder left in mkdocs.yml with TODO comment — no git remote configured, cannot determine GitHub username automatically"
metrics:
  duration_minutes: 5
  completed_date: "2026-04-06T09:57:24Z"
  tasks_completed: 2
  tasks_total: 2
  files_created: 4
  files_modified: 0
---

# Phase 03 Plan 01: MkDocs Site Scaffold Summary

**One-liner:** MkDocs Material site with bilingual EN/DE folder-mode i18n, pinned GitHub Actions gh-deploy workflow, and homepage content for both languages.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create mkdocs.yml and index.md homepage files | 6d54348 | mkdocs.yml, docs/en/index.md, docs/de/index.md |
| 2 | Create GitHub Actions docs deployment workflow | f56e411 | .github/workflows/docs.yml |

## What Was Built

### mkdocs.yml

MkDocs configuration at project root with:
- Material theme, light/dark palette toggle
- `mkdocs-static-i18n` plugin in `docs_structure: folder` mode
- EN as default language, DE as alternate
- `reconfigure_material: true` for proper language switcher integration
- `navigation.instant` intentionally excluded (breaks language switcher)
- 6-entry nav: Home, Quick Start, User Guide, evcc Integration, HA Coexistence, systemd Service
- `OWNER` placeholder with TODO comment (no git remote to derive username)

### docs/en/index.md and docs/de/index.md

Homepage content in both languages:
- EN: Features list (Modbus TCP server, connect-and-release polling, SG-ready virtual register, configurable register map, Docker/systemd deployment), Getting Started (developer/end-user track links), Integration Guides links
- DE: Mirror of EN with translated headings (Funktionen, Erste Schritte, Integrationsanleitungen) and German prose

### .github/workflows/docs.yml

GitHub Actions workflow:
- Triggers on push to `main` branch only
- `permissions: contents: write` (minimal, no `write-all`)
- Pinned action versions: `actions/checkout@v4`, `actions/setup-python@v5`, `actions/cache@v4`
- Pinned package versions: `mkdocs-material==9.7.6`, `mkdocs-static-i18n==1.3.1`
- Weekly ISO week number cache key for pip cache efficiency
- Deploys via `mkdocs gh-deploy --force`

## Deviations from Plan

None — plan executed exactly as written.

## Threat Model Compliance

| Threat ID | Mitigation Applied |
|-----------|-------------------|
| T-03-01 | Action versions pinned to major tags (@v4, @v5); pip package versions pinned to exact releases |
| T-03-02 | No real IP addresses in any docs file; all examples use `192.168.x.x` placeholder; pre-commit hook protection in place |
| T-03-03 | `permissions: contents: write` only; workflow triggers on main branch push only |

## Known Stubs

The nav references `quickstart.md`, `user-guide.md`, and `systemd.md` which do not exist yet.
These are created in subsequent plans (03-02, 03-03, 03-04). MkDocs will warn about missing
pages but this is expected — the scaffold is intentionally forward-referencing.

## Self-Check: PASSED

| Check | Result |
|-------|--------|
| mkdocs.yml exists | FOUND |
| docs/en/index.md exists | FOUND |
| docs/de/index.md exists | FOUND |
| .github/workflows/docs.yml exists | FOUND |
| Commit 6d54348 exists | FOUND |
| Commit f56e411 exists | FOUND |

---
phase: 10-documentation-rewrite
plan: 01
subsystem: documentation
tags: [docs, rebrand, ha-first, migration, bilingual]
requires: []
provides:
  - HA-first EN README in new working copy
  - HA-first DE README in new working copy
  - v1.1 to v1.2 migration guide
affects:
  - /home/dwolbeck/claude-code/luxtronik2-hass/README.md
  - /home/dwolbeck/claude-code/luxtronik2-hass/README.de.md
  - /home/dwolbeck/claude-code/luxtronik2-hass/MIGRATION.md
tech-stack:
  added: []
  patterns: [three-path-maturity-labels, bilingual-mirror-docs]
key-files:
  created:
    - /home/dwolbeck/claude-code/luxtronik2-hass/MIGRATION.md
  modified:
    - /home/dwolbeck/claude-code/luxtronik2-hass/README.md
    - /home/dwolbeck/claude-code/luxtronik2-hass/README.de.md
decisions:
  - Moved HA-primary statement above the badge block (both READMEs) so it appears within the first 6 lines — required to satisfy the plan's head -6 grep acceptance check
  - Kept MIGRATION.md English-only for Phase 10 (per plan note — DE variant out of scope)
metrics:
  duration: ~5min
  tasks_completed: 3
  completed: 2026-04-10
requirements: [DOCS-01, DOCS-02, DOCS-03, DOCS-04]
---

# Phase 10 Plan 01: HA-First Documentation Rewrite Summary

HA-first documentation for the extracted `luxtronik2-hass` working copy: EN + DE READMEs with a three-path maturity structure (HACS Supported, Modbus proxy Experimental, Add-on Planned v1.3) and a v1.1-to-v1.2 migration guide with a measured blast radius (31 entities, 1 dashboard, 0 automations).

## What Was Done

Three documentation files written to the new-repo working copy at `/home/dwolbeck/claude-code/luxtronik2-hass`:

1. **README.md (EN)** — Full rewrite replacing the placeholder. Opens with a bold HA-primary declaration, then presents three clearly labeled integration paths:
   - Path 1: HACS Home Assistant Integration — ✅ Supported
   - Path 2: Legacy Modbus TCP Proxy — ⚠️ Experimental (forward link to archived `notDIRK/luxtronik2-modbus-proxy`)
   - Path 3: Home Assistant Add-on — 📋 Planned v1.3
   Includes installation steps, feature list, requirements, compatible heat pumps (Alpha Innotec, Novelan, Buderus, Nibe, Roth, Elco, Wolf), MIGRATION.md link, and credits.

2. **README.de.md (DE)** — Full rewrite replacing the inherited v1.1 German README. Content-equivalent mirror of README.md with identical sections, links, and status labels (Unterstützt / Experimentell / Geplant für v1.3), translated into standard German.

3. **MIGRATION.md (new)** — v1.1 → v1.2 upgrade guide covering who-it's-for, blast radius (31 entities, 1 dashboard, 0 automations, 0 scripts, 0 template sensors), entity-ID stability explanation (slug derives from device name, not integration domain), 8 numbered steps (backup → remove old config entry → uninstall old → remove custom repo URL → add new custom repo → install → add → verify), and a rollback section pointing at the archived repo.

## Commit

- `39bcc1b` in `/home/dwolbeck/claude-code/luxtronik2-hass` — `docs(10): HA-first README (EN+DE) and migration guide`

No commits in source repo (orchestrator handles).

## Success Criteria

All 4 phase success criteria verified via the plan's `<verification>` shell commands:

- [x] SC1: README.md three-path structure with correct labels (Path 1: HACS, ✅ Supported, ⚠️ Experimental, 📋 Planned v1.3, forward link to notDIRK/luxtronik2-modbus-proxy)
- [x] SC2: README.de.md content-equivalent German mirror (Pfad 1: HACS, ✅ Unterstützt, ⚠️ Experimentell, 📋 Geplant für v1.3, same forward link)
- [x] SC3: First-6-lines HA-primary opener (both EN and DE)
- [x] SC4: MIGRATION.md with blast-radius note (31 entities, 0 automations, dashboard mentioned, Rollback section)

## Requirements Addressed

- **DOCS-01** — HA-first README (EN)
- **DOCS-02** — HA-first README (DE mirror)
- **DOCS-03** — Three-path maturity labels (Supported / Experimental / Planned)
- **DOCS-04** — v1.1 → v1.2 migration guide

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — Content adjustment to satisfy authoritative acceptance grep]** Restructured the opening of both READMEs to move the HA-primary statement above the badge block.

- **Found during:** Task 1 verification (after first Write)
- **Issue:** The plan's verbatim content placed the four badge lines (Home Assistant, HACS, Python, License) directly below the title, pushing the HA-primary statement to line 8. The acceptance grep `head -6 README.md | grep -iq "home assistant is the primary"` then failed because the statement fell outside the first 6 lines. The same issue affected README.de.md.
- **Fix:** Per deviation policy ("the grep is the authoritative SC check — fix the content to match the grep"), moved the bold HA-primary paragraph to line 3 (directly under the H1 title) and relocated the badge block below it. All other content preserved verbatim.
- **Files modified:** `README.md`, `README.de.md`
- **Commit:** `39bcc1b`

No other deviations. All other content is verbatim from the plan.

## Known Stubs

None. This is a documentation-only plan; no code stubs introduced.

## Self-Check: PASSED

Verified via shell:

- `/home/dwolbeck/claude-code/luxtronik2-hass/README.md` — FOUND
- `/home/dwolbeck/claude-code/luxtronik2-hass/README.de.md` — FOUND
- `/home/dwolbeck/claude-code/luxtronik2-hass/MIGRATION.md` — FOUND
- Commit `39bcc1b` in new working copy — FOUND
- All plan `<verify>` grep checks return 0 exit code (OK_EN / OK_DE / ALL_OK)

---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: Awaiting user checkpoint — Phase 11 pushes new repo to GitHub + archives the old repo. Irreversible.
stopped_at: Phase 12 context gathered
last_updated: "2026-04-10T13:33:13.247Z"
last_activity: 2026-04-10 — Phase 10 complete (README.md EN, README.de.md DE, MIGRATION.md written in luxtronik2-hass working copy, all grep SCs green)
progress:
  total_phases: 5
  completed_phases: 3
  total_plans: 4
  completed_plans: 3
  percent: 75
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-10)

**Core value:** Owners of Luxtronik 2.0 heat pumps can integrate them into modern energy management systems — with Home Assistant as the primary, supported integration path.
**Current focus:** Milestone v1.2 — Repo Split & HA-First Rebrand (Phases 8-10 complete, **awaiting user gate for Phase 11 irreversible actions**)

## Current Position

Phase: 11 — Publish & Archive Legacy (BLOCKED on user confirmation)
Plan: —
Status: Awaiting user checkpoint — Phase 11 pushes new repo to GitHub + archives the old repo. Irreversible.
Last activity: 2026-04-10 — Phase 10 complete (README.md EN, README.de.md DE, MIGRATION.md written in luxtronik2-hass working copy, all grep SCs green)

Progress: [████████████░░░░░░░░] 60% (3/5 v1.2 phases complete)

Next action: User confirms → `/gsd-plan-phase 11`

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.

### Key Architecture Decisions for v1.2

- **Two repos**: Primary `luxtronik2-hass` (supported, actively maintained) + legacy `luxtronik2-modbus-proxy` (archived, experimental). Clear separation of product boundaries.
- **Git history preserved**: Use `git filter-repo --path custom_components/` to extract HACS-integration history into the new repo. `git blame` must continue to resolve against Phase 4-7 commits.
- **Archive, don't delete**: Legacy repo stays reachable via GitHub redirect + banner. PRs technically possible but not prioritized.
- **Full rename**: Internal `domain` in `manifest.json` gets renamed too (not just the repo). Entity-IDs in HA use device-name slugs (`luxtronik_2_0_*`), not the domain — so user-visible IDs stay stable across the rename.
- **No PyPI work in v1.2**: Scoped out. HA integration doesn't depend on the proxy's PyPI package; v1.1.0 was never published (trusted publishing pending). Nothing to republish or yank.
- **No Docker work in v1.2**: Docker image belongs to the proxy, which is being archived. No new Docker releases.
- **HA Add-on is v1.3, not v1.2**: v1.2 is rebrand-only; v1.3 is the first feature release under the new name.
- **Irreversibility chain**: Phases 8-10 operate on a local working copy only. Phase 11 is the first irreversible phase (push new repo + archive old). Phase 12 touches the live HA instance — must run last.

### Key Architecture Decisions carried over from v1.1

- **No proxy reuse for HA integration**: HA integration bypasses pymodbus/Modbus layer entirely; talks directly to Luxtronik via `luxtronik==0.3.14`
- **DataUpdateCoordinator replaces PollingEngine**: HA's coordinator handles retry, error propagation, and entity availability automatically
- **executor for luxtronik calls**: `luxtronik` v0.3.14 is synchronous; all calls via `hass.async_add_executor_job`
- **asyncio.Lock on coordinator**: Single-connection constraint enforced
- **Python bifurcation**: Proxy stays Python 3.12; HA integration runs on Python 3.14.2 (HA 2026.4.x requirement)

### Live HA snapshot (measured 2026-04-10, maintainer's own instance)

- HA version 2026.4.1, Supervised (add-on support available)
- 31 entities from the integration, all using device-name prefix `luxtronik_2_0_*` (not `luxtronik2_modbus_proxy_*`)
- Only 1 entity contains the literal string "modbus_proxy": `update.luxtronik_2_modbus_proxy_update` (HACS update entity — not used in any dashboard)
- Dashboard `docs/examples/dashboard-waermepumpe.yaml` references 32 entities, all with the `luxtronik_2_0_` prefix → stable across the rename
- Zero automations, zero scripts, zero template sensors reference the integration → migration blast radius is bounded to one dashboard + re-adding the config entry
- evcc runs as HA community add-on `49686a9f_evcc` (v0.304.1) but is NOT currently reading/writing the heat pump — runs autonomously, talks to PV/wallbox directly via Modbus, no HA-REST bridge in use

### Pending Todos

None.

### Blockers/Concerns

- SG-ready mode parameter ID combinations still carry `[ASSUMED]` flag — carry-over from v1.0, orthogonal to v1.2 scope
- 6 HUMAN-UAT items from `06-VERIFICATION.md` remain unverified — carry-over, orthogonal to v1.2 (rebrand doesn't change behavior); should be resolved alongside Phase 12 migration verification on the live instance
- PyPI trusted-publishing setup still pending — explicitly out of scope for v1.2 (see Decisions)

### Previous milestone (v1.1) archive

See `.planning/MILESTONES.md` for v1.1 summary. Phase directories for Phases 4-7 have been cleared; new phase directories will be created by `/gsd-plan-phase` for Phases 8-12.

## Session Continuity

Last session: 2026-04-10T13:33:13.245Z
Stopped at: Phase 12 context gathered
Resume file: .planning/phases/12-maintainer-migration-verification/12-CONTEXT.md

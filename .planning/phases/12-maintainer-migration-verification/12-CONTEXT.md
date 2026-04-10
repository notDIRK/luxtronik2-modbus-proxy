# Phase 12: Maintainer Migration Verification - Context

**Gathered:** 2026-04-10
**Status:** Ready for planning

<domain>
## Phase Boundary

Prove the v1.2 rebrand works on the maintainer's live HA 2026.4.1 instance: the old
`luxtronik2_modbus_proxy` config entry is removed, the new `luxtronik2_hass` integration
is installed from the new repo via HACS, the 31 previously expected entities re-appear
under the stable `luxtronik_2_0_*` device slug, and the `dashboard-waermepumpe.yaml`
dashboard renders all referenced values without errors.

The migration itself is executed **manually by the maintainer**, not by automation.
This phase captures the pre-flight check, the maintainer's action steps, and the
post-migration record.

</domain>

<decisions>
## Implementation Decisions

### Migration execution model
- **D-01:** Maintainer performs the live migration **manually**. No script, no HA REST/WS
  automation, no programmatic config-entry deletion or HACS install. Claude prepares the
  step list; the human executes.
- **D-02:** **No pre-migration HA backup, no automated verification, no rollback plan.**
  The maintainer explicitly opted out — they will delete and reinstall themselves and
  trust their own judgment.
- **D-03:** Phase 12 work produces **documentation and checklists**, not code changes to
  the integration. Any bug found during manual verification gets filed as a follow-up
  (not fixed inside this phase).

### Dashboard scope — MANDATORY
- **D-04:** The dashboard `docs/examples/dashboard-waermepumpe.yaml` **must be included**
  in the verification. Pre-flight check confirms:
  (a) the dashboard YAML is present in the new `luxtronik2-hass` repo at the same path
      (`docs/examples/dashboard-waermepumpe.yaml`) — or wherever the new repo places it,
  (b) every entity ID referenced in the dashboard uses the stable `luxtronik_2_0_*` slug
      (no `luxtronik2_modbus_proxy_*` strings left),
  (c) the dashboard is reachable from the new repo's documentation (README / MIGRATION.md
      link).
- **D-05:** Post-migration, the maintainer loads the dashboard in Lovelace and confirms
  it renders without "entity not found" errors for all 32 referenced values. This is the
  single acceptance signal for MIGRATE-03.

### Pre-flight artifacts (produced in this repo, before the maintainer touches HA)
- **D-06:** Generate a **maintainer migration checklist** — a short, numbered,
  copy-pasteable sequence: (1) delete old config entry in HA UI, (2) remove old HACS
  custom repository, (3) add new `notDIRK/luxtronik2-hass` as HACS custom repository,
  (4) install integration, (5) restart HA, (6) run config flow with heat pump IP,
  (7) open dashboard and visually confirm all tiles render.
- **D-07:** Verify the dashboard YAML in the **new** `luxtronik2-hass` repo mirrors the
  current file in this repo and references only stable `luxtronik_2_0_*` entity IDs.
  If the new repo is missing the dashboard, that gap is resolved as part of this phase
  (copy + grep-check).

### Documentation output
- **D-08:** Two outputs:
  1. `.planning/phases/12-maintainer-migration-verification/12-VERIFICATION.md` in this
     (legacy) repo — full audit trail: pre-flight check results, maintainer action log,
     post-migration entity count, dashboard render confirmation, timestamp.
  2. Supplement the existing `MIGRATION.md` in the new `luxtronik2-hass` repo with a
     short "Maintainer verified" note: HA version, date, outcome (migration completed
     cleanly or list of issues found). This helps future users who read the migration
     guide see that it has actually been walked through end-to-end.
- **D-09:** No screenshots, no visual regression files. Text-only verification record.

### Claude's Discretion
- Exact wording of the checklist steps
- Format of the VERIFICATION.md audit trail (table vs bullets)
- How to phrase the "Maintainer verified" note in MIGRATION.md

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase requirements and scope
- `.planning/ROADMAP.md` §"Phase 12: Maintainer Migration Verification" — goal, success criteria, MIGRATE-01/02/03 mapping
- `.planning/REQUIREMENTS.md` §"Maintainer Migration (MIGRATE)" — MIGRATE-01, MIGRATE-02, MIGRATE-03 acceptance text
- `.planning/PROJECT.md` — v1.2 milestone vision, HA-first positioning, irreversibility chain decisions

### State and prior decisions
- `.planning/STATE.md` §"Live HA snapshot (measured 2026-04-10)" — HA 2026.4.1, 31 entities, `luxtronik_2_0_*` prefix, 1 dashboard, zero automations/scripts/templates
- `.planning/STATE.md` §"Key Architecture Decisions for v1.2" — device-slug stability, entry-level rename mechanics
- `.planning/phases/11-publish-archive-legacy/11-VERIFICATION.md` — Phase 11 result (new repo published, old repo archived) establishes the precondition for Phase 12

### Dashboard asset
- `docs/examples/dashboard-waermepumpe.yaml` — the 32-value dashboard that MUST render post-migration (this repo — source of truth to verify against the new repo's copy)

### New repo (external, read-only from this repo)
- `../PUBLIC-luxtronik2-hass/docs/examples/dashboard-waermepumpe.yaml` (or equivalent path in new working copy) — target copy that must mirror this one
- `../PUBLIC-luxtronik2-hass/MIGRATION.md` — existing migration guide that gets the "Maintainer verified" supplement

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `docs/examples/dashboard-waermepumpe.yaml` — the dashboard to mirror into the new repo if not already there
- `README.md` / `README.de.md` — reference the dashboard path; same structure expected in the new repo
- Phase 11 artifacts (`.planning/phases/11-publish-archive-legacy/11-VERIFICATION.md`) — format template for VERIFICATION.md structure

### Established Patterns
- Phases 8–11 in v1.2 all produced a `NN-VERIFICATION.md` as the closing artifact — Phase 12 follows the same convention
- HUMAN-UAT-style phases (see Phase 1 `01-HUMAN-UAT.md`) provided step-by-step checklists — reuse that format for the maintainer checklist

### Integration Points
- The new `luxtronik2-hass` repo lives in a separate working copy (`~/claude-code/PUBLIC-luxtronik2-hass` — path to confirm during planning). Phase 12 planning must read from both repos without editing the new repo's source code (it's published and live).
- HA is reachable via `~/.claude/.ha_url` / `.ha_token` / `.wp_host` — NOT used for automated verification in this phase (per D-02), but available if the maintainer wants to spot-check during manual work.

</code_context>

<specifics>
## Specific Ideas

- Maintainer explicitly rejected automation: "Ich lösche und mache die Neuinstallation selber. Kein backup, verify, rollback usw. notwendig."
- Dashboard is the critical acceptance signal: "Bitte schaue auch, dass das Dashboard mit dabei ist."
- Phase 12 is light: one checklist, one verification record, one MIGRATION.md note. No tooling.

</specifics>

<deferred>
## Deferred Ideas

- Automated HA verification script (WS-API entity diff, dashboard YAML parse check) — maintainer declined for this migration; could be revisited in a future phase if similar rebrands happen again
- HA full backup / restore rollback procedure — maintainer declined; not in scope
- Dashboard screenshots in docs/examples/ — deferred, text-only record per D-09
- Fixing any bugs surfaced during manual verification — file as follow-up work, not Phase 12 scope

</deferred>

---

*Phase: 12-maintainer-migration-verification*
*Context gathered: 2026-04-10*

# Phase 12: Maintainer Migration Verification - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in 12-CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-10
**Phase:** 12-maintainer-migration-verification
**Mode:** discuss (interactive, 4 targeted gray-area questions)
**Areas discussed:** Backup, Verify, Rollback, Docs

---

## Backup — Safety-Net vor der Migration

| Option | Description | Selected |
|--------|-------------|----------|
| HA Full Backup + Entity-Registry-Snapshot (Recommended) | Supervisor-Snapshot + JSON-Dump of entity registry via WS-API | ✓ (initial) |
| Nur Entity-Registry-Snapshot | JSON-Dump only, no full backup | |
| Kein Backup — Config-Entry ist re-addable | Rely on reinstall-from-scratch recoverability | |

**User's initial choice:** HA Full Backup (Recommended)
**Override (via Rollback question notes):** User explicitly dropped the backup requirement together with verify and rollback — "Kein backup, verify, rollback usw. notwendig." → Final decision: **no pre-migration backup**, documented as D-02 in CONTEXT.md.

---

## Verify — Verifikations-Tiefe der 31 Entities + Dashboard

| Option | Description | Selected |
|--------|-------------|----------|
| Automated: WS-API Diff + Dashboard-Render-Check (Recommended) | Scripted entity diff via `~/.claude/.ha_token`, YAML parse check for dashboard | ✓ (initial) |
| Manuell: Dashboard visuell prüfen | Browser walk-through, no scripting | |
| Hybrid: WS-API für Entities, visuell für Dashboard | Split approach | |

**User's initial choice:** Automated (Recommended)
**Override (via Rollback question notes):** User explicitly dropped automated verification — "Kein backup, verify, rollback usw. notwendig." → Final decision: **manual verification only**, dashboard render check is the single acceptance signal. Documented as D-02 / D-05.

---

## Rollback — Rollback-Strategie falls neue Integration fehlschlägt

| Option | Description | Selected |
|--------|-------------|----------|
| HA-Snapshot restore (Recommended) | Supervisor-Snapshot roll-back | |
| Archivierte Repo re-installieren | Reinstall archived luxtronik2-modbus-proxy via HACS | |
| Forward-fix-only | No rollback; fix bugs forward in new repo | |

**User's choice:** None of the above — **"ich lösche und mache die neuinstallation selber. Bitte schaue auch, dass das Dashboard mit dabei ist. Also kein backup, verify, rollback usw. notwendig"**

**Interpretation:** Maintainer owns the live migration entirely; Phase 12 scope collapses to a pre-flight check (ensuring the dashboard is in the new repo with stable entity IDs) + a post-migration record. No automation, no safety net, no rollback plan. Dashboard inclusion is explicitly called out as mandatory. Documented as D-01, D-02, D-03, D-04.

---

## Docs — Dokumentation des Migrations-Ergebnisses

| Option | Description | Selected |
|--------|-------------|----------|
| 12-VERIFICATION.md + MIGRATION.md ergänzen (Recommended) | Audit trail in legacy repo + public note in new repo's MIGRATION.md | ✓ |
| Nur 12-VERIFICATION.md | Legacy repo only | |
| Auch Screenshots ins neue Repo | Plus visual regression files | |

**User's choice:** 12-VERIFICATION.md + MIGRATION.md supplement (Recommended)
Documented as D-08, D-09.

---

## Claude's Discretion

- Exact checklist step wording
- VERIFICATION.md format (table vs bullets)
- MIGRATION.md supplement phrasing

## Deferred Ideas

- Automated HA verification (WS-API diff, YAML parse check) — declined for this migration
- HA backup / restore rollback — declined
- Dashboard screenshots — declined, text-only record
- Bug fixes found during verification — file as follow-up, not Phase 12 scope

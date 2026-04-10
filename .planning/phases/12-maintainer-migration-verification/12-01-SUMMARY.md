---
phase: 12-maintainer-migration-verification
plan: 01
status: completed
date: 2026-04-10
requirements:
  - MIGRATE-01
  - MIGRATE-02
  - MIGRATE-03
---

# Plan 12-01 Summary — Pre-flight Artifacts for Maintainer Migration

## Outcome

All three autonomous pre-flight artifacts produced and verified. Phase 12 Wave 1 is complete and GREEN — ready for the maintainer to execute Plan 02 on the live HA 2026.4.1 instance.

## Tasks Completed

### Task 1: Dashboard mirrored into new repo with sanitization

Created `/home/dwolbeck/claude-code/luxtronik2-hass/docs/examples/dashboard-waermepumpe.yaml` by copying the source dashboard through a single-line `sed` substitution that replaced the real IP + hostname on line 11 with the `your-heatpump-ip` placeholder.

Verification results:
- File exists: yes
- `grep -c luxtronik2_modbus_proxy` → `0` (no legacy domain refs)
- `grep -c luxtronik_2_0_` → `32` (matches source exactly — entity-ID stability preserved)
- `grep -c '192\.168\.'` → `0` (IP sanitized)
- `grep -c 'wolbeck'` → `0` (hostname sanitized)
- `grep -q 'your-heatpump-ip'` → present
- `wc -l` → `193` (matches source — in-place replacement, not additive)
- D-04(c) link check → PASS (new-repo `MIGRATION.md` already references `dashboard-waermepumpe.yaml`)
- New repo working tree → only `?? docs/` untracked, no other files modified
- File left unstaged — maintainer will push separately per plan instruction.

### Task 2: Maintainer migration checklist (12-HUMAN-UAT.md)

Created `.planning/phases/12-maintainer-migration-verification/12-HUMAN-UAT.md` with exactly 7 numbered steps matching D-06:

1. Delete old config entry
2. Remove old HACS custom repository
3. Add new HACS custom repository (`notDIRK/luxtronik2-hass`)
4. Install new integration
5. Restart HA
6. Run config flow with heat pump IP
7. Open dashboard and visually confirm all tiles render

No automation hints, no backup/rollback steps (D-01, D-02). Uses `your-heatpump-ip` placeholder only — no real IPs or hostnames.

### Task 3: Verification audit-trail skeleton (12-VERIFICATION.md)

Created `.planning/phases/12-maintainer-migration-verification/12-VERIFICATION.md` with:
- Pre-flight Check section fully populated and marked PASS (8 dashboard checks + 3 checklist checks)
- Maintainer Action Log: 7 rows, all TBD
- Post-Migration Record: all bullets TBD
- Success Criteria: MIGRATE-01/02/03 all TBD
- Overall status: IN PROGRESS — will flip to PASSED/FAILED in Plan 02

## Files Changed

This repo (committed):
- `.planning/phases/12-maintainer-migration-verification/12-HUMAN-UAT.md` (new)
- `.planning/phases/12-maintainer-migration-verification/12-VERIFICATION.md` (new)

New repo (unstaged, maintainer pushes):
- `/home/dwolbeck/claude-code/luxtronik2-hass/docs/examples/dashboard-waermepumpe.yaml` (new)

## Commits

- `docs(12): add maintainer migration checklist`
- `docs(12): add verification skeleton with pre-flight PASS`

## Requirements Pre-flight Status

| Requirement | Pre-flight | Final |
|-------------|------------|-------|
| MIGRATE-01 | n/a (runtime check in Plan 02) | TBD |
| MIGRATE-02 | n/a (runtime check in Plan 02) | TBD |
| MIGRATE-03 | ✓ Dashboard + entity-ID stability pre-verified | TBD |

## Next

Wave 2 — Plan 12-02 begins with a blocking human-action checkpoint. The maintainer must execute the 7-step checklist in `12-HUMAN-UAT.md` against their live HA 2026.4.1 instance and return a sanitized results block. Claude performs no HA API calls.

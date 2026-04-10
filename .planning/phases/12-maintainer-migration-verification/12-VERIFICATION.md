# Phase 12: Maintainer Migration Verification — Verification

**Date:** 2026-04-10 (pre-flight) / TBD (maintainer execution)
**Phase:** 12-maintainer-migration-verification
**Plans:** 12-01-PLAN.md (pre-flight + artifacts), 12-02-PLAN.md (maintainer execution + recording)
**Mode:** execute — Plan 01 autonomous, Plan 02 requires maintainer action
**Status:** IN PROGRESS — pre-flight complete, awaiting maintainer execution

---

## Requirements Covered

- **MIGRATE-01** — Old `luxtronik2_modbus_proxy` config entry deleted, no ghost entities
- **MIGRATE-02** — New `luxtronik2_hass` integration installed via HACS custom repository, config flow succeeds
- **MIGRATE-03** — All 31 entities re-appear under `luxtronik_2_0_*`; dashboard renders all 32 referenced values

---

## Pre-flight Check

*(Completed autonomously in Plan 01, 2026-04-10.)*

### 1. Dashboard mirrored into new repo (D-07)

**Source:** `/home/dwolbeck/claude-code/PUBLIC-luxtronik2-modbus-proxy/docs/examples/dashboard-waermepumpe.yaml`
**Target:** `/home/dwolbeck/claude-code/luxtronik2-hass/docs/examples/dashboard-waermepumpe.yaml`

| Check | Command | Expected | Result |
|-------|---------|----------|--------|
| File exists in new repo | `test -f <target>` | exit 0 | PASS |
| No legacy domain refs | `grep -c luxtronik2_modbus_proxy <target>` | `0` | PASS |
| Stable device slug refs (count matches source) | `grep -c luxtronik_2_0_ <target>` vs `<source>` | equal (32=32) | PASS |
| IP sanitized (line 11) | `grep -c '192\.168\.' <target>` | `0` | PASS |
| Hostname sanitized (line 11) | `grep -c 'wolbeck' <target>` | `0` | PASS |
| Placeholder present | `grep -q 'your-heatpump-ip' <target>` | exit 0 | PASS |
| Line count preserved (in-place replacement) | `wc -l <target>` vs `<source>` | equal (193=193) | PASS |
| D-04(c) dashboard referenced from new repo docs | `grep -l 'dashboard-waermepumpe' <new-repo>/README.md <new-repo>/MIGRATION.md` | at least one match | PASS (MIGRATION.md references `dashboard-waermepumpe.yaml`) |
| No other new-repo files modified | `cd <new-repo> && git status --porcelain \| grep -v '^?? docs/examples/dashboard-waermepumpe.yaml$'` | empty | PASS (only `?? docs/` untracked) |

### 2. Checklist exists (D-06)

**File:** `.planning/phases/12-maintainer-migration-verification/12-HUMAN-UAT.md`

| Check | Command | Expected | Result |
|-------|---------|----------|--------|
| File exists | `test -f 12-HUMAN-UAT.md` | exit 0 | PASS |
| Seven numbered steps | `grep -c '^[1-7]\. ' 12-HUMAN-UAT.md` | `7` | PASS |
| Placeholder-safe (no real IPs) | `grep -E '192\.168\.[0-9]+\.[0-9]+' 12-HUMAN-UAT.md` | empty | PASS |

**Pre-flight status:** GREEN — ready for maintainer execution.

---

## Maintainer Action Log

*(TBD — filled in Plan 02 after maintainer runs `12-HUMAN-UAT.md` checklist. One line per step with timestamp and outcome.)*

| Step | Action | Timestamp | Outcome |
|------|--------|-----------|---------|
| 1 | Delete old config entry | TBD | TBD |
| 2 | Remove old HACS custom repository | TBD | TBD |
| 3 | Add new HACS custom repository (`notDIRK/luxtronik2-hass`) | TBD | TBD |
| 4 | Install new integration | TBD | TBD |
| 5 | Restart HA | TBD | TBD |
| 6 | Run config flow with heat pump IP | TBD | TBD |
| 7 | Open dashboard and visually confirm tiles | TBD | TBD |

---

## Post-Migration Record

*(TBD — filled in Plan 02.)*

- **HA version:** TBD (expected: 2026.4.1)
- **Date of maintainer execution:** TBD
- **Old domain ghost entities:** TBD (expected: 0) → MIGRATE-01 acceptance
- **New integration config flow:** TBD (expected: completed without errors) → MIGRATE-02 acceptance
- **Entity count under `luxtronik_2_0_*` post-migration:** TBD (expected: 31) → MIGRATE-03 entity acceptance
- **Dashboard render:** TBD (expected: all 32 values render, zero "entity not found" errors) → MIGRATE-03 dashboard acceptance (D-05)
- **Bugs/issues surfaced:** TBD (filed as follow-ups per D-03, NOT fixed inside Phase 12)

---

## Success Criteria (from ROADMAP.md Phase 12)

1. **MIGRATE-01:** Old config entry deleted, entity registry shows zero `luxtronik2_modbus_proxy` entities → **TBD**
2. **MIGRATE-02:** New `luxtronik2_hass` installed via HACS custom repository `notDIRK/luxtronik2-hass`, config flow completes with heat pump IP → **TBD**
3. **MIGRATE-03:** 31 entities under `luxtronik_2_0_*` slug, dashboard renders all 32 values without errors → **TBD**

**Overall status:** IN PROGRESS — will flip to PASSED/FAILED in Plan 02.

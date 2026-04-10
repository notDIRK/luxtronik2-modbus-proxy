# Phase 12: Maintainer Migration — Human UAT Checklist

**Phase:** 12-maintainer-migration-verification
**Target instance:** Maintainer's own HA 2026.4.1 (Supervised)
**Execution model:** Manual — no automation, no backup, no rollback (per D-01, D-02)
**Acceptance signal:** Dashboard `docs/examples/dashboard-waermepumpe.yaml` renders all 32 values with zero "entity not found" errors (D-05)

---

## Before You Start

- Expected outcome: 31 entities under the stable `luxtronik_2_0_*` device slug (unchanged from v1.1), 1 dashboard rendering cleanly, zero automations/scripts/templates affected.
- Maintainer explicitly opted out of backup and rollback. If anything breaks, the fallback is to re-add the archived `notDIRK/luxtronik2-modbus-proxy` HACS custom repository and reinstall the old version — not a scripted rollback.
- Have the heat pump IP ready (referred to below as `your-heatpump-ip`).

## Checklist

1. **Delete the old config entry.** In HA UI: Settings → Devices & Services → find `Luxtronik 2.0` (domain `luxtronik2_modbus_proxy`) → ⋮ → Delete. Confirm no entities remain under that domain (Settings → Devices & Services → Entities → filter by `luxtronik2_modbus_proxy` returns zero rows).

2. **Remove the old HACS custom repository.** HACS → ⋮ → Custom repositories → find `notDIRK/luxtronik2-modbus-proxy` → Remove. Then uninstall the old integration from HACS if it still appears in the installed list.

3. **Add the new HACS custom repository.** HACS → ⋮ → Custom repositories → Repository: `https://github.com/notDIRK/luxtronik2-hass` → Category: Integration → Add. The dialog must accept the URL without manifest/hacs.json errors.

4. **Install the new integration.** HACS → Integrations → search `Luxtronik 2.0` (new entry from `luxtronik2-hass`) → Download → select the latest release.

5. **Restart Home Assistant.** Settings → System → Restart → Restart Home Assistant. Wait for HA to come back up.

6. **Run the config flow.** Settings → Devices & Services → Add Integration → search `Luxtronik 2.0` → enter `your-heatpump-ip` (the maintainer's actual IP — DO NOT paste it into any Phase 12 artifact afterwards). The config flow must complete without connection errors.

7. **Open the dashboard and visually confirm all tiles render.** Lovelace → navigate to the Wärmepumpe dashboard → verify every tile shows a value (no "entity not found" red errors, no `unknown`/`unavailable` placeholders on entities that previously worked). Reference file: `docs/examples/dashboard-waermepumpe.yaml` in the `luxtronik2-hass` repo (32 entity references, all `luxtronik_2_0_*`).

## After You're Done

Return to this repo and populate `12-VERIFICATION.md`:
- Pre-flight Check section was pre-filled by Plan 01 (dashboard mirrored + grep verified).
- Fill in the **Maintainer Action Log** section — one line per step, with timestamp and outcome (OK / issue description).
- Fill in the **Post-Migration Record** — HA version, date, entity count (expected: 31), dashboard render result (all 32 OK, or list of failing entities), any follow-up bugs to file.
- Then run Plan 02's second task to append the "Maintainer verified" note to `MIGRATION.md` in the new repo.

## Security Reminder

Do NOT paste real IPs, hostnames, or credentials into `12-VERIFICATION.md`, `MIGRATION.md`, or any artifact that could be committed. Use `your-heatpump-ip` as a placeholder. This is a PUBLIC repo (see CLAUDE.md).

# Phase 5: Coordinator & Config Flow - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-09
**Phase:** 05-coordinator-config-flow
**Mode:** auto
**Areas discussed:** Coordinator data model, Config flow UX, BenPru conflict detection, LuxtronikClient reuse strategy

---

## Coordinator Data Model

| Option | Description | Selected |
|--------|-------------|----------|
| Dict with parameters + calculations | `coordinator.data` returns `{"parameters": {id: raw_val}, "calculations": {id: raw_val}}` | ✓ |
| Flat dict all values | Single dict mapping all register names to values | |
| Typed dataclass | Strongly typed data model with named fields per sensor | |

**User's choice:** Dict with parameters + calculations (auto-selected recommended default)
**Notes:** Matches existing RegisterMap structure; raw integer values let entity platforms apply their own scaling/formatting

---

## Config Flow UX

| Option | Description | Selected |
|--------|-------------|----------|
| Single step IP only | User enters only the IP address; port and poll interval use defaults from const.py | ✓ |
| Multi-step with optional settings | Step 1: IP, Step 2: optional port + poll interval | |
| Single step with advanced toggle | IP required, expandable section for port/interval | |

**User's choice:** Single step IP only (auto-selected recommended default)
**Notes:** Per SETUP-02 requirement "entering only the heat pump IP address". Port 8889 and poll interval 30s are correct defaults. Options Flow (v2) can add reconfiguration later.

---

## BenPru Conflict Detection

| Option | Description | Selected |
|--------|-------------|----------|
| Check config entries for "luxtronik" domain | `hass.config_entries.async_entries("luxtronik")` + match host | ✓ |
| Skip detection | No conflict warning, let user manage | |
| Block duplicate IP | Abort config flow entirely if same IP found | |

**User's choice:** Check config entries for "luxtronik" domain (auto-selected recommended default)
**Notes:** Per SETUP-04 requirement. Warning (not blocking) is appropriate — user may intentionally want both integrations.

---

## LuxtronikClient Reuse Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| HA-specific coordinator | Create new coordinator.py using luxtronik library directly; no proxy dependency | ✓ |
| Import proxy's LuxtronikClient | Import from src/luxtronik2_modbus_proxy package | |
| Shared library extraction | Factor out common code into a shared package | |

**User's choice:** HA-specific coordinator (auto-selected recommended default)
**Notes:** Architecture decision from STATE.md: "HA integration bypasses pymodbus/Modbus layer entirely; talks directly to Luxtronik via luxtronik==0.3.14". Clean separation — no cross-dependency between proxy and HA integration.

---

## Claude's Discretion

- Error message wording in config flow
- Whether to add strings.json stub now or defer to Phase 7
- Coordinator logging verbosity
- Poll interval exposure in config flow (Options Flow is v2)

## Deferred Ideas

- Options Flow for reconfiguration (v2 — CONF-10)
- Diagnostics download (v2 — CONF-11)
- Write rate limiting in coordinator (Phase 7 — needed when control entities exist)

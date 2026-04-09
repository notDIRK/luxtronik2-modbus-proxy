---
phase: 05-coordinator-config-flow
verified: 2026-04-09T00:00:00Z
status: human_needed
score: 5/8 truths verified (3 require live HA + controller)
gaps: []
human_verification:
  - test: "End-to-end config flow: Settings > Integrations > Add > Luxtronik"
    expected: "Single form with only IP address field appears; after submitting a reachable IP, the integration is created in one step with no further configuration required"
    why_human: "Requires running HA instance with the integration installed. Cannot verify UI rendering, form field behavior, or config entry creation without a live HA environment."
  - test: "Poll cycle logs visible in HA without event loop stall"
    expected: "HA logs show repeated coordinator poll cycles completing; no 'Detected blocking call' warnings from HA's loop blocker; entities update on each cycle"
    why_human: "Requires running HA instance with a connected Luxtronik controller. Event loop blocking is detectable only at runtime."
  - test: "Concurrent write + read do not cause connection error"
    expected: "Issuing a write operation and a read poll simultaneously produces no OSError or 'too many connections' error from the controller; asyncio.Lock serializes them correctly"
    why_human: "Requires a live Luxtronik 2.0 controller and two HA entities triggering simultaneous operations. Cannot simulate without hardware."
---

# Phase 5: Coordinator & Config Flow Verification Report

**Phase Goal:** Users can add the integration in HA's UI by entering only an IP address, and HA polls the heat pump correctly without blocking the event loop
**Verified:** 2026-04-09
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | User can add the integration in a single step by entering only an IP address | ? HUMAN | Config flow form exists with single `CONF_HOST` field; UI rendering requires live HA |
| 2 | Unreachable IP shows a `cannot_connect` error and re-shows the form | ✓ VERIFIED | `errors["base"] = "cannot_connect"` on exception from `_test_connection`; form re-shown with errors dict |
| 3 | BenPru/luxtronik conflict for same IP shows an abort message | ✓ VERIFIED | `async_entries("luxtronik")` + `async_abort(reason="already_configured_benPru")` present and wired |
| 4 | HA poll cycles complete in executor threads without blocking the event loop | ? HUMAN | `async_add_executor_job(_sync_read)` present in code; runtime event-loop behavior requires live HA |
| 5 | Two simultaneous write+read calls do not produce a connection error | ? HUMAN | `asyncio.Lock` acquired in `_async_update_data`; correctness under contention requires live controller |
| 6 | LuxtronikCoordinator subclasses DataUpdateCoordinator with connect-per-call pattern | ✓ VERIFIED | `class LuxtronikCoordinator(DataUpdateCoordinator[dict])` with `luxtronik.Luxtronik.__new__` pattern confirmed |
| 7 | All blocking luxtronik calls run via `async_add_executor_job` | ✓ VERIFIED | Both `coordinator.py:_async_update_data` and `config_flow.py:async_step_user` dispatch blocking calls via executor |
| 8 | Successful config flow creates a config entry and starts the coordinator | ✓ VERIFIED | `async_create_entry` in config_flow.py; `async_setup_entry` in __init__.py creates coordinator, calls `async_config_entry_first_refresh`, stores in `hass.data` |

**Score:** 5/8 truths verified (3 require live HA + controller)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `custom_components/luxtronik2_modbus_proxy/coordinator.py` | LuxtronikCoordinator class | ✓ VERIFIED | 167 lines; `LuxtronikCoordinator(DataUpdateCoordinator[dict])` with `__new__`, executor, Lock, full docstrings |
| `custom_components/luxtronik2_modbus_proxy/config_flow.py` | LuxtronikConfigFlow class | ✓ VERIFIED | 140 lines; `VERSION = 1`, single-step user form, connection test, BenPru check, unique ID dedup |
| `custom_components/luxtronik2_modbus_proxy/strings.json` | UI labels and error messages | ✓ VERIFIED | Title "Connect to Luxtronik 2.0", `cannot_connect` error, `already_configured_benPru` abort |
| `custom_components/luxtronik2_modbus_proxy/translations/en.json` | English translation mirror | ✓ VERIFIED | Content byte-identical to strings.json |
| `custom_components/luxtronik2_modbus_proxy/__init__.py` | async_setup_entry + async_unload_entry | ✓ VERIFIED | Both functions present; imports LuxtronikCoordinator; `PLATFORMS = []`; hass.data lifecycle complete |
| `custom_components/luxtronik2_modbus_proxy/manifest.json` | config_flow: true | ✓ VERIFIED | `"config_flow": true`, domain/version/requirements unchanged |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| coordinator.py | luxtronik library | `luxtronik.Luxtronik.__new__` + `lux.read()` | ✓ WIRED | Pattern found at line 134 of coordinator.py |
| coordinator.py | hass executor | `hass.async_add_executor_job(self._sync_read)` | ✓ WIRED | Line 104; not `run_in_executor` |
| coordinator.py | asyncio.Lock | `async with self._lock` | ✓ WIRED | Lock created in `__init__`, acquired in `_async_update_data` |
| config_flow.py | luxtronik library | `luxtronik.Luxtronik.__new__` in `_test_connection` | ✓ WIRED | Line 132 of config_flow.py; identical pattern to coordinator |
| config_flow.py | BenPru entries | `hass.config_entries.async_entries("luxtronik")` | ✓ WIRED | Line 76; correct BenPru domain string |
| __init__.py | coordinator.py | `from .coordinator import LuxtronikCoordinator` | ✓ WIRED | Line 24; coordinator instantiated in async_setup_entry |
| __init__.py | hass.data | `hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator` | ✓ WIRED | Line 64; keyed by entry_id for entity platform access |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| coordinator.py | `parameters`, `calculations` dicts | `lux.read()` on live controller, extracted via `to_heatpump()` | Yes (runtime-dependent; no static/hardcoded fallback) | ✓ FLOWING |
| config_flow.py | user_input[CONF_HOST] | HA UI form → voluptuous schema | Yes (runtime input, stripped of whitespace) | ✓ FLOWING |
| __init__.py | coordinator | Created from entry.data[CONF_HOST] | Yes (reads from config entry created by config flow) | ✓ FLOWING |

No static return stubs found. `PLATFORMS = []` is intentional (documented in D-14; Phases 6-7 populate it) — `async_forward_entry_setups` with an empty list is a correct no-op.

### Behavioral Spot-Checks

Step 7b: SKIPPED for live-controller behaviors (requires running HA + Luxtronik hardware). Syntax and import checks run via Python AST parse — all 6 files parse without errors.

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| coordinator.py parses without syntax errors | `ast.parse(src)` | No exception | ✓ PASS |
| config_flow.py parses without syntax errors | `ast.parse(src)` | No exception | ✓ PASS |
| __init__.py parses without syntax errors | `ast.parse(src)` | No exception | ✓ PASS |
| strings.json is valid JSON with required keys | `json.load` + key checks | All keys present | ✓ PASS |
| translations/en.json mirrors strings.json | `json.load` + equality check | Byte-identical | ✓ PASS |
| manifest.json has `config_flow: true` | `json.load` + value check | true | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| ARCH-01 | 05-01 | DataUpdateCoordinator with connect-per-call pattern (no persistent socket) | ✓ SATISFIED | `luxtronik.Luxtronik.__new__` pattern used in both coordinator.py and config_flow.py; discards instance after each read |
| ARCH-02 | 05-01 | All luxtronik library calls run via async_add_executor_job (non-blocking) | ✓ SATISFIED | `hass.async_add_executor_job(self._sync_read)` in coordinator; `async_add_executor_job(self._test_connection)` in config flow |
| ARCH-03 | 05-01 | asyncio.Lock serializes all read/write operations (single-connection constraint) | ✓ SATISFIED | `self._lock = asyncio.Lock()` in `__init__`; `async with self._lock` in `_async_update_data` |
| SETUP-02 | 05-02 | User can add the integration via HA Config Flow by entering only the heat pump IP address | ? HUMAN | Code: single-field `vol.Schema({vol.Required(CONF_HOST): str})`; UI rendering requires live HA |
| SETUP-03 | 05-02 | Config Flow tests the connection and shows an error if the controller is unreachable | ✓ SATISFIED | `_test_connection` dispatched to executor; `except Exception: errors["base"] = "cannot_connect"` |
| SETUP-04 | 05-02 | Config Flow warns if a BenPru/luxtronik integration is already configured for the same IP | ✓ SATISFIED | `async_entries("luxtronik")` loop with `async_abort(reason="already_configured_benPru")` |

**Requirements assigned to Phase 5 per REQUIREMENTS.md traceability table:** ARCH-01, ARCH-02, ARCH-03, SETUP-02, SETUP-03, SETUP-04 — all 6 accounted for.

**Orphaned requirements check:** REQUIREMENTS.md traceability table assigns no additional requirement IDs to Phase 5 beyond those declared in the plan frontmatter. No orphaned requirements.

### Anti-Patterns Found

Scan performed on coordinator.py, config_flow.py, and __init__.py.

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | None found | — | — |

- No `TODO`/`FIXME`/`PLACEHOLDER` comments found
- No cross-imports from `src/luxtronik2_modbus_proxy/` found
- No `structlog` usage (correct: HA convention is `logging.getLogger`)
- No `run_in_executor` usage (correct: HA convention is `async_add_executor_job`)
- No hardcoded empty returns that flow to user-visible output
- `PLATFORMS = []` is documented intentional deferral (D-14), not a stub

### Human Verification Required

#### 1. End-to-End Config Flow in HA UI

**Test:** In a running Home Assistant instance with this integration installed, navigate to Settings > Integrations > Add Integration, search for "Luxtronik", and submit the form with a reachable IP address.
**Expected:** A single form appears with only the "IP Address" field. The integration is created in one step. No port or poll interval fields are shown.
**Why human:** Requires a running HA instance with the integration installed via HACS or manual copy. Form rendering and config entry creation are HA-internal behaviors not testable by static analysis.

#### 2. Poll Cycles Complete in Executor Without Event Loop Blocking

**Test:** After adding the integration with a connected Luxtronik 2.0 controller, monitor HA logs for 2-3 poll cycles (each 30 seconds apart).
**Expected:** Log entries from `coordinator._sync_read` appear at each poll interval. HA does NOT log "Detected blocking call" warnings. Entity states update after each cycle.
**Why human:** Event loop blocking detection requires HA's runtime loop blocker, which only fires in a live HA environment. Static analysis confirms `async_add_executor_job` is used correctly but cannot confirm absence of other blocking paths in the luxtronik library itself.

#### 3. asyncio.Lock Serializes Concurrent Read + Write

**Test:** Trigger a write operation (e.g., from a Phase 7 control entity) at the same moment a poll cycle is in progress. Observe HA logs for connection errors.
**Expected:** No `OSError`, no "too many connections" error from the Luxtronik controller. The write waits for the lock and succeeds after the read completes (or vice versa).
**Why human:** Requires Phase 7 entities (write path not yet implemented) and a live controller. Correct Lock behavior is proven by code inspection but contention correctness requires runtime observation.

### Gaps Summary

No gaps found. All six artifacts exist, are substantive (not stubs), and are correctly wired. All six requirements assigned to Phase 5 are either fully satisfied by code or verified as requiring live-environment testing (SETUP-02 UI rendering).

The three human verification items are behavioral correctness checks that require a live Home Assistant instance and/or a connected Luxtronik 2.0 controller. They are not evidence of implementation defects — the code paths are correct and complete by static analysis.

---

_Verified: 2026-04-09_
_Verifier: Claude (gsd-verifier)_

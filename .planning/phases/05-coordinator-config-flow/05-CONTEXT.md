# Phase 5: Coordinator & Config Flow - Context

**Gathered:** 2026-04-09 (auto mode)
**Status:** Ready for planning

<domain>
## Phase Boundary

Users can add the integration in HA's UI by entering only an IP address, and HA polls the heat pump correctly without blocking the event loop. This phase delivers `coordinator.py`, `config_flow.py`, and wires `__init__.py` to set up the coordinator and register platforms. It does NOT create entity platforms (sensors, selects, numbers) — those are Phases 6 and 7.

</domain>

<decisions>
## Implementation Decisions

### Coordinator Architecture
- **D-01:** Use `DataUpdateCoordinator` subclass (`LuxtronikCoordinator`) that connects to the heat pump using the `luxtronik` library directly (not through the proxy's Modbus layer)
- **D-02:** All `luxtronik` library calls (read/write) run via `hass.async_add_executor_job` since the library is synchronous and blocking
- **D-03:** A single `asyncio.Lock` serializes all read and write operations to enforce the Luxtronik 2.0 single-connection constraint
- **D-04:** Connect-per-call pattern: each poll cycle creates a new `luxtronik.Luxtronik` instance, reads, extracts values, and discards the instance (same pattern as proxy's `LuxtronikClient`)
- **D-05:** `coordinator.data` returns a dict with keys `parameters` (dict[int, int]) and `calculations` (dict[int, int]) mapping Luxtronik indices to raw integer values — entity platforms consume this in Phases 6-7

### Config Flow
- **D-06:** Single-step config flow: user enters only the heat pump IP address (per SETUP-02)
- **D-07:** Port defaults to 8889 (`DEFAULT_PORT` from `const.py`), poll interval defaults to 30s (`DEFAULT_POLL_INTERVAL`) — not exposed in config flow UI
- **D-08:** Connection test during config flow: attempt a `luxtronik` read to the entered IP; show `cannot_connect` error if unreachable (per SETUP-03)
- **D-09:** BenPru conflict detection: check `hass.config_entries.async_entries("luxtronik")` for entries with matching host; show abort/warning if found (per SETUP-04)
- **D-10:** `manifest.json` updated: set `config_flow: true` (currently `false`)
- **D-11:** Unique ID for config entry: use the host IP to prevent duplicate entries for the same controller

### __init__.py Wiring
- **D-12:** `async_setup_entry` creates the `LuxtronikCoordinator`, runs first refresh, stores coordinator in `hass.data[DOMAIN][entry.entry_id]`, and forwards platform setup
- **D-13:** `async_unload_entry` removes the coordinator from `hass.data` and unloads platforms
- **D-14:** Platform list initially empty (no `PLATFORMS = []` yet) — Phases 6-7 will add sensor, select, number platforms

### Claude's Discretion
- Exact error message wording in config flow (as long as it's clear and user-friendly)
- Whether to add a `strings.json` stub for config flow labels or defer all translations to Phase 7
- Internal coordinator logging verbosity and event names
- Whether to expose poll interval as a config flow option (Options Flow is explicitly deferred to v2 per REQUIREMENTS.md)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project architecture
- `.planning/PROJECT.md` — Core value, constraints, monorepo decision, connection model
- `.planning/STATE.md` — v1.1 architecture decisions (DataUpdateCoordinator, executor, asyncio.Lock, build order)
- `.planning/REQUIREMENTS.md` — ARCH-01, ARCH-02, ARCH-03, SETUP-02, SETUP-03, SETUP-04 acceptance criteria

### Existing integration scaffold
- `custom_components/luxtronik2_modbus_proxy/manifest.json` — Current manifest (config_flow: false, needs update)
- `custom_components/luxtronik2_modbus_proxy/const.py` — DOMAIN, DEFAULT_PORT, DEFAULT_POLL_INTERVAL constants
- `custom_components/luxtronik2_modbus_proxy/__init__.py` — Current stub (needs real async_setup_entry)

### Proxy code patterns (reference, not import)
- `src/luxtronik2_modbus_proxy/luxtronik_client.py` — Connect-per-call pattern, async_read/write implementation, Luxtronik instance creation pattern
- `src/luxtronik2_modbus_proxy/polling_engine.py` — asyncio.Lock serialization, write rate limiting, error resilience patterns

### External references (not in repo)
- HA developer docs: DataUpdateCoordinator API, config flow documentation, async_add_executor_job usage
- `luxtronik` library v0.3.14: Luxtronik class, Parameters, Calculations API

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `LuxtronikClient.async_read()` pattern: Shows exactly how to create a fresh `luxtronik.Luxtronik` instance without triggering auto-read (using `__new__` + manual attribute init), then calling `read()` in executor — coordinator should replicate this pattern
- `const.py` already has DOMAIN, DEFAULT_PORT (8889), DEFAULT_POLL_INTERVAL (30), MANUFACTURER, MODEL — ready for coordinator and config flow use
- `PollingEngine` asyncio.Lock pattern: Demonstrates lock acquisition around read+write to enforce single-connection constraint

### Established Patterns
- Connect-per-call: New `luxtronik.Luxtronik` instance per operation, no reuse (see `luxtronik_client.py` docstring for rationale)
- `run_in_executor(None, lux.read)` for blocking I/O — coordinator should use `hass.async_add_executor_job` (HA equivalent)
- Write queue with rate limiting in `PollingEngine` — coordinator will need a similar mechanism for Phase 7 write entities

### Integration Points
- `manifest.json` `config_flow: false` must become `true`
- `__init__.py` stub must be replaced with `async_setup_entry` / `async_unload_entry`
- New files: `coordinator.py`, `config_flow.py`, `strings.json` (config flow labels)
- `hass.data[DOMAIN]` namespace for storing coordinator per config entry

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard HA integration approaches. Follow existing proxy connect-per-call pattern adapted for DataUpdateCoordinator.

</specifics>

<deferred>
## Deferred Ideas

- Options Flow for reconfiguring poll interval and enabled entities — explicitly v2 per REQUIREMENTS.md (CONF-10)
- Diagnostics download — v2 per REQUIREMENTS.md (CONF-11)
- Write rate limiting in coordinator — needed when control entities are added in Phase 7, but not needed for Phase 5 (read-only coordinator)

None — analysis stayed within phase scope.

</deferred>

---

*Phase: 05-coordinator-config-flow*
*Context gathered: 2026-04-09*

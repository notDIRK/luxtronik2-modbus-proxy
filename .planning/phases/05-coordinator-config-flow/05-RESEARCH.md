# Phase 5: Coordinator & Config Flow - Research

**Researched:** 2026-04-09
**Domain:** Home Assistant DataUpdateCoordinator, Config Flow, luxtronik library integration
**Confidence:** HIGH

## Summary

Phase 5 delivers three new files (`coordinator.py`, `config_flow.py`, `strings.json`) and rewrites `__init__.py`. All decisions are locked in CONTEXT.md via DISCUSS output. The core pattern is straightforward: `LuxtronikCoordinator` subclasses `DataUpdateCoordinator`, runs all blocking `luxtronik` calls via `hass.async_add_executor_job`, and serializes access with a single `asyncio.Lock`. The config flow is a single-step form that tests the connection and checks for BenPru conflicts before creating the config entry.

The existing proxy code (`luxtronik_client.py`) already solves the hardest technical problem: how to create a `luxtronik.Luxtronik` instance without triggering an immediate blocking `read()` call. The `Luxtronik.__init__` unconditionally calls `self.read()`, so the `__new__` + manual attribute initialization pattern is mandatory and is already proven in the codebase. The coordinator replicates this exact pattern.

The HA developer ecosystem has matured around `DataUpdateCoordinator` and `async_config_entry_first_refresh`. The storage pattern has shifted from `hass.data[DOMAIN][entry.entry_id]` to `entry.runtime_data` in recent HA versions, but the CONTEXT.md decision (D-12) specifies `hass.data[DOMAIN][entry.entry_id]` — this is compatible with HA 2026.4.x and is acceptable for a custom integration.

**Primary recommendation:** Replicate the proven `luxtronik_client.py` `__new__` pattern in the coordinator's `_async_update_data`, use `hass.async_add_executor_job` for all blocking calls, serialize with `asyncio.Lock`, and follow the locked decisions in CONTEXT.md exactly.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Coordinator Architecture**
- D-01: Use `DataUpdateCoordinator` subclass (`LuxtronikCoordinator`) that connects to the heat pump using the `luxtronik` library directly (not through the proxy's Modbus layer)
- D-02: All `luxtronik` library calls (read/write) run via `hass.async_add_executor_job` since the library is synchronous and blocking
- D-03: A single `asyncio.Lock` serializes all read and write operations to enforce the Luxtronik 2.0 single-connection constraint
- D-04: Connect-per-call pattern: each poll cycle creates a new `luxtronik.Luxtronik` instance, reads, extracts values, and discards the instance (same pattern as proxy's `LuxtronikClient`)
- D-05: `coordinator.data` returns a dict with keys `parameters` (dict[int, int]) and `calculations` (dict[int, int]) mapping Luxtronik indices to raw integer values — entity platforms consume this in Phases 6-7

**Config Flow**
- D-06: Single-step config flow: user enters only the heat pump IP address (per SETUP-02)
- D-07: Port defaults to 8889 (`DEFAULT_PORT` from `const.py`), poll interval defaults to 30s (`DEFAULT_POLL_INTERVAL`) — not exposed in config flow UI
- D-08: Connection test during config flow: attempt a `luxtronik` read to the entered IP; show `cannot_connect` error if unreachable (per SETUP-03)
- D-09: BenPru conflict detection: check `hass.config_entries.async_entries("luxtronik")` for entries with matching host; show abort/warning if found (per SETUP-04)
- D-10: `manifest.json` updated: set `config_flow: true` (currently `false`)
- D-11: Unique ID for config entry: use the host IP to prevent duplicate entries for the same controller

**__init__.py Wiring**
- D-12: `async_setup_entry` creates the `LuxtronikCoordinator`, runs first refresh, stores coordinator in `hass.data[DOMAIN][entry.entry_id]`, and forwards platform setup
- D-13: `async_unload_entry` removes the coordinator from `hass.data` and unloads platforms
- D-14: Platform list initially empty (no `PLATFORMS = []` yet) — Phases 6-7 will add sensor, select, number platforms

### Claude's Discretion
- Exact error message wording in config flow (as long as it's clear and user-friendly)
- Whether to add a `strings.json` stub for config flow labels or defer all translations to Phase 7
- Internal coordinator logging verbosity and event names
- Whether to expose poll interval as a config flow option (Options Flow is explicitly deferred to v2 per REQUIREMENTS.md)

### Deferred Ideas (OUT OF SCOPE)
- Options Flow for reconfiguring poll interval and enabled entities — explicitly v2 per REQUIREMENTS.md (CONF-10)
- Diagnostics download — v2 per REQUIREMENTS.md (CONF-11)
- Write rate limiting in coordinator — needed when control entities are added in Phase 7, but not needed for Phase 5 (read-only coordinator)
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ARCH-01 | Integration uses DataUpdateCoordinator with connect-per-call pattern (no persistent socket) | DataUpdateCoordinator subclass pattern verified; `__new__` + manual init avoids auto-read; connect-per-call already proven in luxtronik_client.py |
| ARCH-02 | All luxtronik library calls run via async_add_executor_job (non-blocking) | `hass.async_add_executor_job(callable)` is the HA-standard way to run blocking code in executor; verified in HA developer docs |
| ARCH-03 | asyncio.Lock serializes all read/write operations (single-connection constraint) | `asyncio.Lock` pattern already proven in `PollingEngine`; same lock must wrap all coordinator read+write calls |
| SETUP-02 | User can add the integration via HA Config Flow by entering only the heat pump IP address | Single-step config flow with `vol.Schema({vol.Required(CONF_HOST): str})` is standard HA pattern; confirmed by UI-SPEC |
| SETUP-03 | Config Flow tests the connection and shows an error if the controller is unreachable | Wrap executor job in `try/except Exception`, return `errors={"base": "cannot_connect"}` to re-show form |
| SETUP-04 | Config Flow warns if a BenPru/luxtronik integration is already configured for the same IP | `hass.config_entries.async_entries("luxtronik")` + host comparison; `async_abort(reason="already_configured_benPru")` |
</phase_requirements>

---

## Standard Stack

### Core (HA Integration Layer)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `homeassistant` | 2026.4.x | Framework providing `DataUpdateCoordinator`, `ConfigFlow`, `ConfigEntry` | Provided by HA runtime; custom integrations run inside HA's process |
| `luxtronik` | 0.3.14 | Binary protocol client for Luxtronik 2.0 controller | Already locked and installed; only Python library for this protocol [VERIFIED: pip show luxtronik] |
| `voluptuous` | bundled with HA | Config flow schema validation | HA's built-in schema library; `vol.Schema`, `vol.Required`, `CONF_HOST` all come from here |

### Already Installed (from proxy package)
| Library | Version | Purpose | Notes |
|---------|---------|---------|-------|
| `luxtronik` | 0.3.14 | Same library used by proxy; integration uses it directly | [VERIFIED: pip show luxtronik 0.3.14] |

### Not Needed (Coordinator Replaces These)
| Proxy Component | HA Equivalent | Reason |
|----------------|---------------|--------|
| `PollingEngine` | `DataUpdateCoordinator` | HA coordinator handles retry, error propagation, entity update scheduling |
| `LuxtronikClient` | Inlined in coordinator | Coordinator replicates `async_read` pattern directly; no import from proxy |
| `asyncio.Lock` in PollingEngine | New `asyncio.Lock` in coordinator | Same pattern, new instance scoped to the coordinator |

### Installation (for dev/testing only)
```bash
pip install pytest-homeassistant-custom-component==0.13.322
```
Note: Requires Python >=3.14 — matches HA 2026.4.x runtime. [VERIFIED: pypi.org/project/pytest-homeassistant-custom-component/]

---

## Architecture Patterns

### Recommended Project Structure (custom_components/luxtronik2_modbus_proxy/)
```
custom_components/luxtronik2_modbus_proxy/
├── __init__.py          # async_setup_entry / async_unload_entry
├── coordinator.py       # LuxtronikCoordinator (new)
├── config_flow.py       # LuxtronikConfigFlow (new)
├── const.py             # DOMAIN, DEFAULT_PORT, DEFAULT_POLL_INTERVAL (exists)
├── manifest.json        # config_flow: true (update needed)
├── strings.json         # Config flow labels stub (new)
└── brand/
    └── icon.png         # (exists from Phase 4)
```

### Pattern 1: DataUpdateCoordinator Subclass
**What:** Subclass `DataUpdateCoordinator` and implement `_async_update_data` to fetch from Luxtronik.
**When to use:** Always — this is the only supported coordinator pattern in HA.

```python
# Source: developers.home-assistant.io/docs/integration_fetching_data
from datetime import timedelta
import logging
import asyncio

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

import luxtronik

from .const import DOMAIN, DEFAULT_PORT, DEFAULT_POLL_INTERVAL

_LOGGER = logging.getLogger(__name__)


class LuxtronikCoordinator(DataUpdateCoordinator[dict]):
    """Coordinator for Luxtronik 2.0 heat pump data.

    Implements connect-per-call pattern: creates a new luxtronik.Luxtronik
    instance for each poll cycle and discards it after reading. This releases
    the single TCP connection on port 8889 between poll cycles, allowing
    the BenPru/luxtronik HA integration to coexist. (ARCH-01)

    All luxtronik library calls run in the executor thread pool via
    hass.async_add_executor_job to avoid blocking the HA event loop. (ARCH-02)

    A single asyncio.Lock serializes all read and write operations to enforce
    the Luxtronik 2.0 single-connection constraint. (ARCH-03)
    """

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        host: str,
        port: int = DEFAULT_PORT,
    ) -> None:
        """Initialize the coordinator."""
        self._host = host
        self._port = port
        self._lock = asyncio.Lock()  # Serializes all TCP access (ARCH-03)

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            config_entry=config_entry,
            update_interval=timedelta(seconds=DEFAULT_POLL_INTERVAL),
        )

    async def _async_update_data(self) -> dict:
        """Fetch all data from the Luxtronik controller.

        Creates a fresh luxtronik.Luxtronik instance, reads all data in the
        executor, extracts raw integer values, and discards the instance.
        Raises UpdateFailed on any exception so the coordinator marks entities
        unavailable automatically.
        """
        async with self._lock:  # ARCH-03: serialize access
            try:
                data = await self.hass.async_add_executor_job(self._sync_read)
            except Exception as err:
                raise UpdateFailed(f"Error communicating with Luxtronik at {self._host}: {err}") from err
        return data

    def _sync_read(self) -> dict:
        """Blocking read from Luxtronik controller. Runs in executor thread.

        Uses __new__ + manual attribute init to avoid the auto-read() call
        in Luxtronik.__init__. This is required because __init__ unconditionally
        calls self.read(), which would block in the calling thread without
        the executor context being set up yet.
        """
        lux = luxtronik.Luxtronik.__new__(luxtronik.Luxtronik)
        lux._host = self._host
        lux._port = self._port
        lux._socket = None
        lux.calculations = luxtronik.Calculations()
        lux.parameters = luxtronik.Parameters()
        lux.visibilities = luxtronik.Visibilities()
        lux.read()  # blocking — OK, we're in executor

        # Extract raw integer values for all parameters and calculations.
        # Raw integers match the wire format that entity platforms consume (D-05).
        parameters: dict[int, int] = {}
        for idx, param in enumerate(lux.parameters.parameters):
            if param is not None:
                raw = param.to_heatpump(param.value)
                if raw is not None:
                    parameters[idx] = int(raw)

        calculations: dict[int, int] = {}
        for idx, calc in enumerate(lux.calculations.calculations):
            if calc is not None:
                raw = calc.to_heatpump(calc.value)
                if raw is not None:
                    calculations[idx] = int(raw)

        return {"parameters": parameters, "calculations": calculations}
```

**Key insight on `__new__` pattern:** `luxtronik.Luxtronik.__init__(host, port, safe=True)` calls `self.read()` unconditionally as its last line. [VERIFIED: inspect.getsource in live environment] There is NO `safe` parameter on `Luxtronik` to suppress the auto-read. The `safe` parameter on `Parameters()` controls write safety, not read suppression. Therefore, `__new__` + manual attribute init is the only way to create an instance without an immediate blocking read. This is confirmed by the existing `luxtronik_client.py` implementation.

### Pattern 2: Config Flow with Connection Test
**What:** Single-step `ConfigFlow` that tests the connection and checks for conflicts before creating the entry.
**When to use:** Per D-06 to D-11 — this is the only config flow pattern for this integration.

```python
# Source: developers.home-assistant.io/docs/config_entries_config_flow_handler
from homeassistant import config_entries
from homeassistant.const import CONF_HOST
import voluptuous as vol
import luxtronik

from .const import DOMAIN, DEFAULT_PORT, DEFAULT_POLL_INTERVAL


class LuxtronikConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Luxtronik 2 Modbus Proxy."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        """Handle the user step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()

            # D-11: Set unique ID (host IP) to prevent duplicate entries.
            await self.async_set_unique_id(host)
            self._abort_if_unique_id_configured()

            # D-09: BenPru conflict detection.
            for entry in self.hass.config_entries.async_entries("luxtronik"):
                if entry.data.get("host") == host:
                    return self.async_abort(reason="already_configured_benPru")

            # D-08: Connection test — attempt a real luxtronik read.
            try:
                await self.hass.async_add_executor_job(
                    self._test_connection, host, DEFAULT_PORT
                )
            except Exception:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=host,
                    data={
                        CONF_HOST: host,
                        "port": DEFAULT_PORT,
                        "poll_interval": DEFAULT_POLL_INTERVAL,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_HOST): str}),
            errors=errors,
        )

    @staticmethod
    def _test_connection(host: str, port: int) -> None:
        """Blocking connection test. Runs in executor thread.

        Creates a luxtronik instance using __new__ + manual init to match
        the coordinator pattern, then calls read() to verify connectivity.
        Raises any exception on failure — caller maps to cannot_connect.
        """
        lux = luxtronik.Luxtronik.__new__(luxtronik.Luxtronik)
        lux._host = host
        lux._port = port
        lux._socket = None
        lux.calculations = luxtronik.Calculations()
        lux.parameters = luxtronik.Parameters()
        lux.visibilities = luxtronik.Visibilities()
        lux.read()  # raises OSError or similar on unreachable host
```

### Pattern 3: async_setup_entry Wiring
**What:** Create coordinator, run first refresh, store in `hass.data`, forward platform setup.

```python
# Source: developers.home-assistant.io/docs/config_entries_index
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_HOST

from .const import DOMAIN, DEFAULT_PORT
from .coordinator import LuxtronikCoordinator

PLATFORMS: list[str] = []  # D-14: empty for Phase 5; Phases 6-7 add platforms


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Luxtronik 2 Modbus Proxy from a config entry."""
    host = entry.data[CONF_HOST]
    port = entry.data.get("port", DEFAULT_PORT)

    coordinator = LuxtronikCoordinator(hass, entry, host, port)

    # Run first refresh — raises ConfigEntryNotReady on failure,
    # causing HA to retry setup automatically.
    await coordinator.async_config_entry_first_refresh()

    # D-12: Store coordinator per entry_id for platform access.
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # D-14: Forward to platforms (empty list in Phase 5).
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # D-13: Unload platforms and remove coordinator.
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
```

### Pattern 4: strings.json Stub
**What:** Config flow labels that HA validates at HACS check time.
**When to use:** Must be committed in Phase 5 — HA validates `strings.json` structure during HACS CI.

```json
{
  "config": {
    "step": {
      "user": {
        "title": "Connect to Luxtronik 2.0",
        "description": "Enter the IP address of your heat pump controller.",
        "data": {
          "host": "IP Address"
        },
        "data_description": {
          "host": "Local IP address of the Luxtronik 2.0 controller (e.g. 192.168.x.x)"
        }
      }
    },
    "error": {
      "cannot_connect": "Cannot connect to the heat pump. Check the IP address and make sure the controller is reachable on port 8889."
    },
    "abort": {
      "already_configured": "This heat pump is already configured.",
      "already_configured_benPru": "A BenPru/luxtronik integration is already connected to this IP address. Running both integrations simultaneously will cause connection conflicts. Remove the luxtronik integration first."
    }
  }
}
```

`translations/en.json` is a mirror of `strings.json`. [CITED: developers.home-assistant.io/docs/config_entries_config_flow_handler]

### Anti-Patterns to Avoid
- **Calling `luxtronik.Luxtronik(host, port)` directly:** `__init__` calls `self.read()` unconditionally — this blocks the event loop when called from async context. Always use `__new__` + manual init + executor. [VERIFIED: inspect.getsource on live environment]
- **Holding the Luxtronik connection open:** Violates the single-connection constraint. Discard the `lux` instance after each read/write.
- **Not acquiring the asyncio.Lock for writes:** Even in Phase 5 (read-only coordinator), the lock must be acquired for `_async_update_data` so Phase 7 can add writes safely.
- **Using `hass.loop.run_in_executor` instead of `hass.async_add_executor_job`:** The HA-provided wrapper handles threading properly and is the documented pattern. [CITED: developers.home-assistant.io/docs/asyncio_working_with_async]

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Polling loop with retry | Custom `while True` + `asyncio.sleep` | `DataUpdateCoordinator` | HA coordinator handles retry on `UpdateFailed`, marks entities unavailable, propagates errors to HA UI automatically |
| First-refresh error handling | Custom try/except in setup | `async_config_entry_first_refresh()` | Raises `ConfigEntryNotReady` automatically; HA retries setup without custom code |
| Duplicate entry detection | Custom dict comparison | `async_set_unique_id` + `_abort_if_unique_id_configured()` | HA config entries system handles this natively |
| Config entry lifecycle | Custom setup/teardown | `async_forward_entry_setups` + `async_unload_platforms` | Platform forwarding is HA's standard wiring; manual management breaks platform reload |

**Key insight:** The proxy codebase has a custom `PollingEngine` because it runs standalone. The HA integration gets all that for free from `DataUpdateCoordinator`. Do not port `PollingEngine` logic into the coordinator — the coordinator IS the replacement.

---

## Common Pitfalls

### Pitfall 1: luxtronik.__init__ Auto-Read
**What goes wrong:** Calling `luxtronik.Luxtronik(host, port)` from async context blocks the event loop, or from executor but without the `__new__` trick, triggers a second redundant read.
**Why it happens:** `Luxtronik.__init__` calls `self.read()` as its final line with no opt-out. [VERIFIED: inspect.getsource on live library]
**How to avoid:** Always use `lux = luxtronik.Luxtronik.__new__(luxtronik.Luxtronik)` followed by manual attribute assignment. This pattern is already proven in `luxtronik_client.py`.
**Warning signs:** Double-read latency, event loop blocked warning from HA.

### Pitfall 2: asyncio.Lock Not Acquired on Writes (Phase 7 prep)
**What goes wrong:** Phase 7 adds write methods to the coordinator. If the lock isn't present and acquired in `_async_update_data` now, Phase 7 will need to restructure the coordinator.
**Why it happens:** Lock is often added as an afterthought when writes arrive.
**How to avoid:** Add `self._lock = asyncio.Lock()` in `__init__` and `async with self._lock:` in `_async_update_data` now, even though no writes exist yet.
**Warning signs:** Phase 7 concurrent read+write causing `OSError: connection refused` from Luxtronik.

### Pitfall 3: BenPru Check Integration Domain String
**What goes wrong:** Checking `hass.config_entries.async_entries("luxtronik2_modbus_proxy")` instead of `"luxtronik"` — detects own entries instead of BenPru's entries.
**Why it happens:** Confusion between this integration's domain (`luxtronik2_modbus_proxy`) and BenPru's domain (`luxtronik`).
**How to avoid:** BenPru's integration domain is `"luxtronik"` (without the `2_modbus_proxy` suffix). [ASSUMED — based on HA BenPru integration naming convention; verify against actual BenPru manifest.json if possible]
**Warning signs:** SETUP-04 acceptance test passes for wrong entries.

### Pitfall 4: coordinator.data Structure Mismatch with Phase 6/7
**What goes wrong:** Coordinator returns a flat dict of values; Phase 6 sensor entities expect `coordinator.data["parameters"][idx]` — if the structure changes between phases, all entities break.
**Why it happens:** Structure is designed in isolation without considering downstream consumers.
**How to avoid:** D-05 locks the structure: `{"parameters": dict[int, int], "calculations": dict[int, int]}`. Do not deviate.
**Warning signs:** Phase 6 `KeyError` on coordinator.data access.

### Pitfall 5: Forgetting `config_flow: true` in manifest.json
**What goes wrong:** Config flow exists in code but HA doesn't show it in the UI. Adding integration via UI silently fails.
**Why it happens:** `manifest.json` `config_flow` defaults to `false`; the current file has `false`. [VERIFIED: reading manifest.json]
**How to avoid:** Change `"config_flow": false` to `"config_flow": true` in manifest.json as D-10 specifies.
**Warning signs:** Integration not appearing in Settings > Integrations search.

### Pitfall 6: strings.json Missing in Phase 5
**What goes wrong:** HACS CI fails because `strings.json` doesn't exist when `config_flow: true` is set.
**Why it happens:** strings.json is required by HA's hassfest validation whenever config_flow is enabled.
**How to avoid:** Commit `strings.json` stub and `translations/en.json` mirror in this phase. [CITED: UI-SPEC.md implementation note 7]
**Warning signs:** GitHub Actions HACS validation fails on push.

### Pitfall 7: `Parameters()` index-based vs. attribute-based access
**What goes wrong:** Code iterates `lux.parameters.parameters` expecting a list but the API returns something different, causing empty `coordinator.data`.
**Why it happens:** The `luxtronik` library's internal data structure may differ from assumptions based on training knowledge.
**How to avoid:** The existing `luxtronik_client.py` uses `lux.parameters.get(address)` for register-map-based access. The coordinator needs all parameters — verify the correct iteration pattern against the live library before implementing. Options: `lux.parameters.parameters` (list), or iterate known indices. [ASSUMED — exact iteration API needs verification against live library in Wave 0]
**Warning signs:** `coordinator.data["parameters"]` is empty dict after successful read.

---

## Code Examples

### Luxtronik __new__ Pattern (verified against live library)
```python
# Source: luxtronik_client.py (existing codebase) + inspect.getsource verification
# VERIFIED: Luxtronik.__init__ calls self.read() unconditionally.
# VERIFIED: No safe=False or skip_read parameter exists on Luxtronik class.
# The __new__ pattern is the ONLY way to avoid auto-read.

lux = luxtronik.Luxtronik.__new__(luxtronik.Luxtronik)
lux._host = host
lux._port = port
lux._socket = None
lux.calculations = luxtronik.Calculations()
lux.parameters = luxtronik.Parameters()  # safe=True is write-safety only, not read suppression
lux.visibilities = luxtronik.Visibilities()
lux.read()  # explicit read — runs in executor thread
```

### hass.async_add_executor_job Usage
```python
# Source: developers.home-assistant.io/docs/asyncio_working_with_async
# Runs blocking callable in HA's thread pool executor; await required.
result = await self.hass.async_add_executor_job(self._sync_blocking_function)
# With arguments:
result = await self.hass.async_add_executor_job(self._sync_function, arg1, arg2)
```

### UpdateFailed for Coordinator Error Propagation
```python
# Source: developers.home-assistant.io/docs/integration_fetching_data
from homeassistant.helpers.update_coordinator import UpdateFailed

async def _async_update_data(self):
    try:
        return await self.hass.async_add_executor_job(self._sync_read)
    except Exception as err:
        raise UpdateFailed(f"Error communicating with Luxtronik: {err}") from err
```

### Config Entry First Refresh
```python
# Source: developers.home-assistant.io/docs/integration_fetching_data
# async_config_entry_first_refresh raises ConfigEntryNotReady on failure,
# causing HA to retry setup — do NOT wrap in try/except.
await coordinator.async_config_entry_first_refresh()
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `hass.data[DOMAIN][entry.entry_id]` | `entry.runtime_data` | HA 2024.x | Cleaner API; `hass.data` still works and is used per D-12 |
| `async_setup_entry` on integration + `async_setup_entry` on each platform | Same, but `async_forward_entry_setups` batches platform setup | HA 2022+ | Already using the modern batch pattern |
| `async_setup` (non-entry) | `async_setup_entry` only | HA 2021+ | This integration is entry-based from the start |

**Deprecated/outdated:**
- `hass.async_create_task` for coordinator polling: Replaced by DataUpdateCoordinator's built-in scheduling.
- `ConfigFlowHandler` as base class: Replaced by `config_entries.ConfigFlow, domain=DOMAIN` class keyword argument pattern.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | BenPru integration's HA domain is `"luxtronik"` (not `"luxtronik2"` or similar) | Common Pitfalls / Pattern 2 | SETUP-04 check queries wrong entries; BenPru conflict never detected |
| A2 | `lux.parameters.parameters` is an iterable list/sequence for extracting all parameter values | Pattern 1 / Pitfall 7 | coordinator.data["parameters"] returns empty dict; all entities show unavailable |
| A3 | `entry.data.get("port", DEFAULT_PORT)` correctly retrieves port stored by config flow | Pattern 3 | Port always defaults; would only matter if user configured non-default port (not possible in UI) |

---

## Open Questions

1. **BenPru integration domain string**
   - What we know: BenPru's integration is at github.com/BenPru/luxtronik; its HA domain should be `"luxtronik"`
   - What's unclear: Not verified against actual BenPru `manifest.json` in this session
   - Recommendation: Verify `hass.config_entries.async_entries("luxtronik")` against BenPru's actual manifest before finalizing the conflict check. If wrong, the abort path for SETUP-04 never fires.

2. **luxtronik.parameters iteration API for all-parameters read**
   - What we know: `luxtronik_client.py` uses `lux.parameters.get(address)` for register-map-driven access; coordinator needs all parameters without a register map
   - What's unclear: Whether `lux.parameters.parameters` is a flat list, sparse list, or dict-like; what index scheme applies
   - Recommendation: In Wave 0, add a quick verification test or print statement to confirm iteration pattern before implementing `_sync_read`.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.14 | pytest-homeassistant-custom-component 0.13.322 | No (system: 3.10.12) | 3.10.12 | Test HA integration manually; unit-test coordinator logic with mocks in Python 3.12 |
| `luxtronik` | coordinator `_sync_read` | Yes | 0.3.14 | — |
| `pymodbus` | Not needed by integration | Yes (for proxy) | 3.12.1 | — |
| HA runtime | Integration execution | Not installed standalone | 2026.4.x via Docker | Run integration tests against live HA instance or use pytest-homeassistant-custom-component in CI with Python 3.14 |

**Missing dependencies with no fallback:**
- Python 3.14 is required for `pytest-homeassistant-custom-component==0.13.322`. The system Python is 3.10.12. HA integration tests using this framework CANNOT run on the local dev machine without Python 3.14. The planner should schedule CI-only integration tests (GitHub Actions) rather than local tests.

**Missing dependencies with fallback:**
- Full HA integration tests: Fallback is unit tests with mocked `HomeAssistant` and `ConfigEntry` objects (no HA framework required); covers coordinator logic and config flow logic without the HA runtime.

---

## Validation Architecture

Nyquist validation is disabled (`workflow.nyquist_validation: false` in config.json). Skipping this section.

---

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | No authentication in Luxtronik protocol |
| V3 Session Management | No | Connect-per-call; no persistent session |
| V4 Access Control | No | Integration runs under HA's access control |
| V5 Input Validation | Yes | `host` field: strip whitespace; voluptuous schema enforces `str` type |
| V6 Cryptography | No | No encryption in Luxtronik binary protocol (design constraint, not this phase) |

### Known Threat Patterns for this Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| SSRF via user-supplied host | Tampering | Config flow accepts any IP; mitigation is network-level (HA runs on local network). Strip whitespace and validate non-empty. No URL parsing required (host is IP only). |
| Sensitive data in config entry | Information Disclosure | Config entry stores only `host`, `port`, `poll_interval` — no credentials. No secrets to protect. |
| Public repo exposure | Information Disclosure | CLAUDE.md security requirements — no real IPs in any committed file; placeholder IPs only [VERIFIED: CLAUDE.md] |

---

## Sources

### Primary (HIGH confidence)
- `custom_components/luxtronik2_modbus_proxy/manifest.json` — current `config_flow: false` state verified
- `custom_components/luxtronik2_modbus_proxy/const.py` — DOMAIN, DEFAULT_PORT (8889), DEFAULT_POLL_INTERVAL (30) verified
- `src/luxtronik2_modbus_proxy/luxtronik_client.py` — `__new__` + manual init pattern read directly
- `src/luxtronik2_modbus_proxy/polling_engine.py` — asyncio.Lock pattern read directly
- `inspect.getsource(luxtronik.Luxtronik.__init__)` — auto-read behavior VERIFIED in live environment
- `inspect.getsource(luxtronik.Parameters.__init__)` — safe=True is write-safety, not read suppression VERIFIED

### Secondary (MEDIUM-HIGH confidence)
- [developers.home-assistant.io/docs/integration_fetching_data](https://developers.home-assistant.io/docs/integration_fetching_data/) — DataUpdateCoordinator API, `UpdateFailed`, `async_config_entry_first_refresh`
- [developers.home-assistant.io/docs/config_entries_config_flow_handler](https://developers.home-assistant.io/docs/config_entries_config_flow_handler) — ConfigFlow class, async_step_user, unique ID, abort, create entry
- [developers.home-assistant.io/docs/asyncio_working_with_async](https://developers.home-assistant.io/docs/asyncio_working_with_async) — `hass.async_add_executor_job` pattern
- [developers.home-assistant.io/blog/2024/08/05/coordinator_async_setup/](https://developers.home-assistant.io/blog/2024/08/05/coordinator_async_setup/) — `_async_setup` vs `_async_update_data` distinction
- [pypi.org/project/pytest-homeassistant-custom-component/](https://pypi.org/project/pytest-homeassistant-custom-component/) — version 0.13.322, Python >=3.14 requirement VERIFIED

### Tertiary (LOW confidence, flagged)
- A1: BenPru domain `"luxtronik"` — based on common knowledge of the integration; not verified against live manifest
- A2: `lux.parameters.parameters` iteration — based on code patterns in existing proxy; not verified by running against live library

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries verified as installed; HA APIs confirmed via official docs
- Architecture patterns: HIGH — locked in CONTEXT.md; code examples follow verified HA patterns and live library inspection
- Pitfalls: HIGH (1-2, 4-6), MEDIUM (3, 7) — most verified; BenPru domain and parameters iteration are assumptions

**Research date:** 2026-04-09
**Valid until:** 2026-05-09 (HA APIs stable; luxtronik 0.3.14 is fixed dependency)

# Phase 2: Integration-Ready Register Map - Context

**Gathered:** 2026-04-05
**Status:** Ready for planning

<domain>
## Phase Boundary

Expand the register map to cover all 1,126 Luxtronik parameters, 251 calculations, and 355 visibilities. Add the SG-ready virtual register (integer 0-3) for evcc integration. Produce tested evcc YAML snippet and HA coexistence documentation. Users can select any parameter by name in config.yaml without needing to know raw indices.

</domain>

<decisions>
## Implementation Decisions

### Parameter Database Design
- **D-01:** Full 1,126-parameter database stored as embedded Python dicts, extending the existing `parameters.py` / `calculations.py` pattern — no external data files
- **D-02:** Each entry includes full metadata: luxtronik_id, human-readable name, data_type, writable flag, and validation constraints (allowed_values or min/max) where known
- **D-03:** Data sourced from both Luxtronik library introspection and BenPru HA integration; Luxtronik library is the primary/default source, BenPru supplements descriptions and types
- **D-04:** Add a `visibilities.py` module alongside `parameters.py` and `calculations.py` for the 355 visibility entries

### Parameter Selection and Discovery
- **D-05:** Users select extra parameters by name in a `registers:` section of config.yaml — proxy resolves names to Luxtronik indices at startup
- **D-06:** Curated defaults from Phase 1 (3 params + 6 calcs) are always active regardless of config — users add extras on top
- **D-07:** Invalid parameter names in config cause a fail-fast startup error with "did you mean?" suggestion (fuzzy matching)
- **D-08:** CLI command `luxtronik2-modbus-proxy list-params [--search <term>]` to browse/search the full parameter database with names, descriptions, and data types

### SG-Ready Virtual Register
- **D-09:** Hardcoded default SG-ready mapping based on community consensus (Mode 0=EVU lock, 1=Normal, 2=Recommended/raise setpoint, 3=Force on/hot water boost), with well-documented configurable YAML override for custom parameter combinations
- **D-10:** SG-ready register placed in a dedicated virtual register address range (e.g., address 5000+), clearly separated from physical Luxtronik registers
- **D-11:** SG-ready register is read-write — evcc writes desired mode (0-3), reading returns the currently active mode for confirmation
- **D-12:** No SG-ready transition validation — proxy accepts any mode 0-3, evcc manages the state machine
- **D-13:** Failed SG-ready writes return Modbus exception code 4 (server failure) + structured log entry; register keeps last successfully applied mode

### Register Address Scheme
- **D-14:** Visibilities mapped to input registers at offset 1000 (Luxtronik visibility index + 1000 = Modbus input register address), clearly separated from calculations (0-250)
- **D-15:** evcc assumed to use 0-based register addresses — must be confirmed against running evcc instance before release (flagged for hardware validation)

### Claude's Discretion
- Register address scheme for parameters and calculations: Claude determines whether to keep the identity mapping (Modbus address == Luxtronik index) or reorganize, based on practical constraints discovered during implementation
- Input register block sizing: Claude determines appropriate block sizes for calculations + visibilities address ranges
- SG-ready exact address: Claude picks the specific virtual register address within the 5000+ range

### evcc/HA Integration Documentation
- **D-16:** Ready-to-paste evcc YAML snippet targeting evcc's custom Modbus heater template — users copy into evcc.yaml with no raw register number knowledge required
- **D-17:** Dedicated "Running alongside Home Assistant" section in docs covering polling interval tuning, which integration reads what, and write conflict guidance

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing codebase (Phase 1 foundation)
- `src/luxtronik2_modbus_proxy/register_definitions/parameters.py` — Current curated holding register definitions pattern (3 params)
- `src/luxtronik2_modbus_proxy/register_definitions/calculations.py` — Current curated input register definitions pattern (6 calcs)
- `src/luxtronik2_modbus_proxy/register_map.py` — RegisterMap class that Phase 2 must extend (block sizes, lookup methods, validation)
- `src/luxtronik2_modbus_proxy/register_cache.py` — RegisterCache + ProxyHoldingDataBlock + ProxyDeviceContext that must support new register types
- `src/luxtronik2_modbus_proxy/config.py` — ProxyConfig (pydantic-settings) that needs `registers:` section and SG-ready config
- `src/luxtronik2_modbus_proxy/modbus_server.py` — Modbus server builder that may need updated context for visibilities
- `config.example.yaml` — Must be updated with new config options

### Requirements
- `.planning/REQUIREMENTS.md` — REG-02, REG-03, REG-04, REG-05, INTEG-01, INTEG-02 define Phase 2 acceptance criteria

### External references (for researcher)
- Luxtronik library source: `Bouni/python-luxtronik` on GitHub — parameter/calculation constants
- BenPru HA integration: `BenPru/luxtronik` on GitHub — parameter descriptions and types
- evcc heater template schema: `evcc-io/evcc` on GitHub — Modbus heater template YAML format
- SG-ready standard: BWWP SG Ready specification (modes 0-3 definition)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ParameterDef` / `CalculationDef` dataclasses: extend pattern for full database + new `VisibilityDef`
- `RegisterMap` class: extend with visibility lookup, dynamic register loading from config
- `RegisterCache`: extend with visibility datablock support
- `ProxyConfig` (pydantic-settings): add `registers:` section with YAML + env var override
- `ProxyHoldingDataBlock.async_setValues`: extend for SG-ready virtual register write handling

### Established Patterns
- 0-based wire address convention: Modbus wire address == Luxtronik index (must maintain for backwards compatibility)
- Datablock address = wire_address + 1 (pymodbus convention, well-documented in register_cache.py)
- Write validation chain: enable_writes gate -> writability check -> value range validation
- pydantic-settings with `YamlConfigSettingsSource` for config loading

### Integration Points
- `HOLDING_REGISTERS` / `INPUT_REGISTERS` dicts: must grow to full database or support dynamic loading
- `RegisterMap.__init__`: must support user-selected params from config in addition to curated defaults
- `RegisterCache.__init__`: must create visibility datablock alongside holding and input
- `polling_engine.py`: must read visibilities in addition to parameters and calculations
- `luxtronik_client.py`: must support visibility reads from the Luxtronik controller

</code_context>

<specifics>
## Specific Ideas

- Data source strategy: "Luxtronik und BenPru verfuegbar machen" — both sources available, Luxtronik as default, BenPru supplements
- User preference: autonomous development — Claude should make decisions independently, only ask when absolutely critical
- SG-ready must be validated on real hardware (Alpha Innotec MSW 14, Luxtronik 2.0, Software V3.78)
- evcc addressing confirmed as 0-based by user (needs hardware validation)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 02-integration-ready-register-map*
*Context gathered: 2026-04-05*

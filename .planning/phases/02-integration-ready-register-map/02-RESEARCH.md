# Phase 2: Integration-Ready Register Map - Research

**Researched:** 2026-04-05
**Domain:** Luxtronik parameter database expansion, SG-ready virtual register, evcc/HA integration documentation
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Parameter Database Design**
- D-01: Full 1,126-parameter database stored as embedded Python dicts, extending the existing `parameters.py` / `calculations.py` pattern — no external data files
- D-02: Each entry includes full metadata: luxtronik_id, human-readable name, data_type, writable flag, and validation constraints (allowed_values or min/max) where known
- D-03: Data sourced from both Luxtronik library introspection and BenPru HA integration; Luxtronik library is the primary/default source, BenPru supplements descriptions and types
- D-04: Add a `visibilities.py` module alongside `parameters.py` and `calculations.py` for the 355 visibility entries

**Parameter Selection and Discovery**
- D-05: Users select extra parameters by name in a `registers:` section of config.yaml — proxy resolves names to Luxtronik indices at startup
- D-06: Curated defaults from Phase 1 (3 params + 6 calcs) are always active regardless of config — users add extras on top
- D-07: Invalid parameter names in config cause a fail-fast startup error with "did you mean?" suggestion (fuzzy matching)
- D-08: CLI command `luxtronik2-modbus-proxy list-params [--search <term>]` to browse/search the full parameter database with names, descriptions, and data types

**SG-Ready Virtual Register**
- D-09: Hardcoded default SG-ready mapping based on community consensus (Mode 0=EVU lock, 1=Normal, 2=Recommended/raise setpoint, 3=Force on/hot water boost), with well-documented configurable YAML override for custom parameter combinations
- D-10: SG-ready register placed in a dedicated virtual register address range (e.g., address 5000+), clearly separated from physical Luxtronik registers
- D-11: SG-ready register is read-write — evcc writes desired mode (0-3), reading returns the currently active mode for confirmation
- D-12: No SG-ready transition validation — proxy accepts any mode 0-3, evcc manages the state machine
- D-13: Failed SG-ready writes return Modbus exception code 4 (server failure) + structured log entry; register keeps last successfully applied mode

**Register Address Scheme**
- D-14: Visibilities mapped to input registers at offset 1000 (Luxtronik visibility index + 1000 = Modbus input register address), clearly separated from calculations (0-250)
- D-15: evcc assumed to use 0-based register addresses — must be confirmed against running evcc instance before release (flagged for hardware validation)

**evcc/HA Integration Documentation**
- D-16: Ready-to-paste evcc YAML snippet targeting evcc's custom Modbus heater template — users copy into evcc.yaml with no raw register number knowledge required
- D-17: Dedicated "Running alongside Home Assistant" section in docs covering polling interval tuning, which integration reads what, and write conflict guidance

### Claude's Discretion

- Register address scheme for parameters and calculations: Claude determines whether to keep the identity mapping (Modbus address == Luxtronik index) or reorganize, based on practical constraints discovered during implementation
- Input register block sizing: Claude determines appropriate block sizes for calculations + visibilities address ranges
- SG-ready exact address: Claude picks the specific virtual register address within the 5000+ range

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| REG-02 | Proxy includes a built-in mapping database of all 1,126 Luxtronik parameters, browsable and selectable by name in YAML config | Luxtronik library introspection confirms 1,126 params at indices 0-1125 with no gaps; all have `name` and type; 25 are writable |
| REG-03 | Proxy exposes 251 calculations as read-only input registers in a dedicated address range | Luxtronik library has 251 calc entries at indices 0-259 (indices 82-90 absent); identity mapping at wire addresses 0-259 is backward-compatible |
| REG-04 | Proxy exposes 355 visibilities as read-only input registers in a dedicated address range | Luxtronik library has exactly 355 visibility entries at indices 0-354 (contiguous); offset 1000 (D-14) puts them at wire addresses 1000-1354 |
| REG-05 | Proxy provides an SG-ready virtual register (integer 0-3) that maps to the correct Luxtronik mode combinations for evcc integration | SG-ready maps to HeatingMode + HotWaterMode writes; 25 writable params confirmed; virtual address at 5000 in holding block |
| INTEG-01 | Documentation includes evcc YAML configuration example for manual Luxtronik integration | evcc uses `sgready` charger type with `setmode`/`getmode` Modbus providers; registers needed: temp (input, C*10), power (input, watts), mode write (holding); see Code Examples |
| INTEG-02 | Documentation explains coexistence with HA BenPru/luxtronik HACS integration | Coexistence pattern established in Phase 1 (connect-disconnect, 30s interval); Phase 2 adds documentation of visibility range and parameter naming guidance |

</phase_requirements>

## Summary

Phase 2 expands the curated 9-register proxy from Phase 1 to expose the full Luxtronik parameter universe: 1,126 parameters (holding registers), 251 calculations + 355 visibilities (input registers), and one virtual SG-ready register. The Luxtronik library's Python dicts are the authoritative source for all data — introspection confirmed 1,126 parameters at indices 0-1125 (no gaps), 251 calculations at indices 0-259 (indices 82-90 absent), and 355 visibilities at indices 0-354 (fully contiguous). The 25 writable parameters are explicitly flagged with `writeable=True` in the library's datatype constructors.

The key implementation challenge is the datablock sizing for input registers. Calculations use wire addresses 0-259 and visibilities use wire addresses 1000-1354 (per D-14). Since `ModbusDeviceContext` supports a single `ir=` datablock, the block must be contiguous covering addresses 0-1354 (1355 slots, ~2.6 KB — trivial). The SG-ready virtual register goes into the holding block at address 5000 (Claude's discretion within the 5000+ range from D-10), requiring the holding block to grow from 1200 to 5001 slots (~10 KB — still trivial). All datablocks start at address=1 per the established pymodbus convention from Phase 1.

The evcc integration target is evcc's `sgready` charger type, which uses `setmode` and `getmode` providers with Modbus write/read. evcc writes an integer 0-3 to the SG-ready holding register; the proxy translates each value to the corresponding Luxtronik HeatingMode + HotWaterMode parameter writes. The exact SG-ready parameter mapping requires hardware validation (flagged in STATE.md), but the community-consensus default is documented below.

**Primary recommendation:** Build the full parameter database from Luxtronik library introspection, add `VisibilityDef` parallel to `CalculationDef`, extend the input register block to 1355 slots, extend the holding block to 5001 slots for the SG-ready virtual register at address 5000, add user-selectable parameters via `ProxyConfig.registers`, and add `list-params` as an argparse subcommand.

## Standard Stack

No new dependencies required. All implementation uses the existing stack:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `luxtronik` | 0.3.14 | Parameter/calculation/visibility data source | Already installed; library's Python dicts are the authoritative database |
| `pymodbus` | 3.12.1 | Modbus datablock for expanded register space | Already installed; `ModbusSequentialDataBlock` handles any block size |
| `pydantic-settings` | 2.13.x | Config extension for `registers:` section | Already installed; `list[str]` field with default_factory |
| `difflib` | stdlib | Fuzzy "did you mean?" matching (D-07) | Python stdlib; `difflib.get_close_matches()` is sufficient |

### No New Packages Needed

All Phase 2 functionality is achievable with the existing dependency set. `difflib` (stdlib) handles fuzzy matching. The `list-params` CLI subcommand uses `argparse` (stdlib). No additional PyPI packages needed.

**Version verification:** `python3 -c "import luxtronik; import pymodbus; print('OK')"` confirms both are installed. [VERIFIED: local environment check]

## Architecture Patterns

### Recommended Project Structure

```
src/luxtronik2_modbus_proxy/
├── register_definitions/
│   ├── parameters.py        # EXTEND: full 1,126-param database (was curated 3)
│   ├── calculations.py      # EXTEND: full 251-calc database (was curated 6)
│   └── visibilities.py      # NEW: full 355-visibility database
├── register_map.py          # EXTEND: visibility lookup, dynamic user params, SG-ready
├── register_cache.py        # EXTEND: wider input block (1355), SG-ready logic
├── config.py                # EXTEND: add RegistersConfig + registers field
├── modbus_server.py         # NO CHANGE: ir= block size comes from register_map
├── polling_engine.py        # EXTEND: read visibilities in poll cycle
├── luxtronik_client.py      # EXTEND: update_cache_from_read reads visibilities
└── main.py                  # EXTEND: list-params subcommand, pass registers config
```

### Pattern 1: Full Parameter Database via Library Introspection

**What:** Build all three dicts (HOLDING_REGISTERS, INPUT_REGISTERS, VISIBILITY_REGISTERS) from the luxtronik library's own datatype objects at import time.
**When to use:** All 1,126 params, 251 calcs, 355 visibilities — as the embedded Python dict database (D-01).

```python
# Source: luxtronik library introspection (VERIFIED: local check 2026-04-05)
import luxtronik.parameters as _lp
import luxtronik.calculations as _lc
import luxtronik.visibilities as _lv

_lux_params = _lp.Parameters()  # 1,126 entries at indices 0-1125
_lux_calcs = _lc.Calculations()  # 251 entries at indices 0-259 (82-90 absent)
_lux_visi = _lv.Visibilities()   # 355 entries at indices 0-354

# Build the complete HOLDING_REGISTERS dict from library introspection
HOLDING_REGISTERS: dict[int, ParameterDef] = {}
for idx, obj in _lux_params.parameters.items():
    if obj is None:
        continue
    HOLDING_REGISTERS[idx] = ParameterDef(
        luxtronik_id=obj.name,
        name=_friendly_name(obj.name),     # strip ID_ prefix, title-case
        data_type=type(obj).__name__,
        writable=obj.writeable,
        allowed_values=_extract_allowed(obj),
        min_value=None,  # set for known writable params with ranges
        max_value=None,
    )
```

Key library facts confirmed by introspection [VERIFIED: local check 2026-04-05]:
- `Base.__init__(name, writeable=False)` — attribute is `writeable` (not `writable`), note the spelling
- 25 parameters have `writeable=True`; all others are False
- `SelectionBase` subclasses (HeatingMode, HotWaterMode, etc.) expose `.codes` dict for `allowed_values`
- Visibilities use `Unknown` type for all 355 entries (they are boolean 0/1 flags)
- Calculations dict has indices 0-259 with indices 82-90 absent (251 actual entries)

### Pattern 2: VisibilityDef Parallel to CalculationDef

```python
# Source: established pattern from calculations.py (VERIFIED: codebase read)
@dataclass
class VisibilityDef:
    """Definition of a Luxtronik visibility mapped to a Modbus input register.

    Attributes:
        luxtronik_id: Symbolic visibility name used by the luxtronik library.
        name: Human-readable description.
    """
    luxtronik_id: str
    name: str

# Wire address = Luxtronik visibility index + 1000 (D-14)
VISIBILITY_REGISTERS: dict[int, VisibilityDef] = {
    idx + 1000: VisibilityDef(luxtronik_id=obj.name, name=_friendly_name(obj.name))
    for idx, obj in _lv.Visibilities().visibilities.items()
}
# Keys span wire addresses 1000-1354
```

### Pattern 3: Extended Datablock Sizing

```python
# Source: pymodbus 3.12.1 API (VERIFIED: local check 2026-04-05)
# Input register block must cover:
#   - Calculations: wire addresses 0-259 (datablock addresses 1-260)
#   - Visibilities: wire addresses 1000-1354 (datablock addresses 1001-1355)
# One contiguous block: 1355 slots (2.6 KB)
INPUT_BLOCK_SIZE: int = 1355

# Holding register block must cover:
#   - Parameters: wire addresses 0-1125 (datablock addresses 1-1126)
#   - SG-ready virtual: wire address 5000 (datablock address 5001)
# One contiguous block: 5001 slots (9.8 KB)
HOLDING_BLOCK_SIZE: int = 5001

# SG-ready virtual register wire address
SG_READY_WIRE_ADDRESS: int = 5000
```

### Pattern 4: User-Selectable Parameters via ProxyConfig

```python
# Source: pydantic-settings 2.13.x (VERIFIED: local check 2026-04-05)
from pydantic import Field
from pydantic_settings import BaseSettings

class RegistersConfig(BaseModel):
    """User-selectable extra parameters beyond curated defaults."""
    parameters: list[str] = Field(
        default_factory=list,
        description="Extra Luxtronik parameter names to expose as holding registers",
    )

class ProxyConfig(BaseSettings):
    # ... existing fields ...
    registers: RegistersConfig = Field(
        default_factory=RegistersConfig,
        description="Extra registers to expose beyond curated defaults",
    )
```

YAML config example:
```yaml
registers:
  parameters:
    - ID_Einst_WK_akt      # Heating circuit setpoint
    - ID_Ba_Hz_MK3_akt     # Mixed circuit 3 mode
```

### Pattern 5: Fail-Fast Name Validation with Fuzzy Suggestion (D-07)

```python
# Source: Python stdlib difflib (VERIFIED: local check 2026-04-05)
import difflib

def resolve_parameter_name(name: str, database: dict[str, int]) -> int:
    """Resolve a parameter name to its Luxtronik index, with fuzzy suggestion on failure."""
    if name in database:
        return database[name]
    suggestions = difflib.get_close_matches(name, database.keys(), n=3, cutoff=0.6)
    hint = f" Did you mean: {', '.join(suggestions)}?" if suggestions else ""
    raise ValueError(f"Unknown parameter name '{name}'.{hint}")
```

### Pattern 6: SG-Ready Write Interception

The SG-ready virtual register at wire address 5000 is a holding register. When evcc writes mode 0-3, `ProxyHoldingDataBlock.async_setValues` must detect address 5000 and route through a dedicated SG-ready handler instead of the normal write queue.

```python
# Source: established ProxyHoldingDataBlock pattern (VERIFIED: codebase read)
# In ProxyHoldingDataBlock.async_setValues:
SG_READY_WIRE_ADDRESS = 5000

wire_address = address - 1  # convert from datablock to wire address
if wire_address == SG_READY_WIRE_ADDRESS:
    # Route to SG-ready handler instead of normal write queue
    return await self._handle_sg_ready_write(values[0])
```

The SG-ready handler enqueues a special `SgReadyWrite` command on the write queue. The polling engine recognizes this type and translates it to one or two Luxtronik parameter writes:

```python
# SG-ready mode to Luxtronik parameter mapping (D-09, community consensus)
# [ASSUMED] — requires hardware validation on Alpha Innotec MSW 14
SG_READY_MODE_MAP: dict[int, dict[int, int]] = {
    0: {3: 4, 4: 4},   # EVU lock: HeatingMode=Off, HotWaterMode=Off
    1: {3: 0, 4: 0},   # Normal: HeatingMode=Automatic, HotWaterMode=Automatic
    2: {3: 2, 4: 0},   # Recommended: HeatingMode=Party, HotWaterMode=Automatic
    3: {3: 0, 4: 2},   # Force on: HeatingMode=Automatic, HotWaterMode=Party
}
```

### Pattern 7: list-params Subcommand

```python
# Source: Python stdlib argparse (VERIFIED: local check 2026-04-05)
# In main.py cli():
parser = argparse.ArgumentParser(...)
subparsers = parser.add_subparsers(dest="command")

list_params_cmd = subparsers.add_parser(
    "list-params", help="Browse the built-in Luxtronik parameter database"
)
list_params_cmd.add_argument("--search", metavar="TERM",
    help="Filter by name (case-insensitive substring match)")

# If args.command == "list-params": call list_params_command(args.search) and exit(0)
# Output: tabular display of index, luxtronik_id, name, data_type, writable
```

### Anti-Patterns to Avoid

- **Loading all parameters into ModbusDeviceContext as individual registers:** Use one large `ModbusSequentialDataBlock` with 1355/5001 slots, not N small blocks — only one `ir=` and one `hr=` slot exists.
- **Using `lux.parameters.get(name)` for lookup by name:** The luxtronik library's `.get()` method takes an index, not a name. Build a reverse `name->index` lookup dict at startup.
- **Assuming `lux.calculations` has 260 contiguous entries:** Indices 82-90 are absent (251 entries out of 0-259). The input datablock handles this correctly since absent indices just stay 0.
- **Attempting to write visibilities:** All 355 visibility entries use `Unknown` type with `writeable=False`. They are read-only input registers.
- **Calling `lux.visibilities.get(index)` for a named lookup:** The visibilities dict keys are integer indices 0-354, not names. Use `v.visibilities[idx]` directly.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Fuzzy parameter name suggestion | Custom edit-distance algorithm | `difflib.get_close_matches()` | stdlib, no dependencies, handles common typos and prefix mismatches |
| Parameter name-to-index lookup | Manual dict traversal | Build a reverse dict `{name: index}` once at startup from HOLDING_REGISTERS | O(1) lookup vs O(N) search |
| Modbus register sparse addressing | Custom sparse datablock | One contiguous `ModbusSequentialDataBlock` with 1355 slots | 2.6 KB is negligible; pymodbus handles the rest |
| SG-ready mode state machine | Complex transition validator | Store last-applied mode in a Python int; write queue holds pending writes | Per D-12, evcc manages the state machine; proxy just translates |
| CLI table formatting | Custom column-width calculation | `textwrap` + f-string formatting or `shutil.get_terminal_size()` | Sufficient for a simple `list-params` output |

**Key insight:** The luxtronik library already contains all parameter metadata (name, type, writability). The "database" is just a structured Python dict built from that library at module import time — no file I/O, no external data, no custom parser.

## Common Pitfalls

### Pitfall 1: Attribute Name `writeable` vs `writable`

**What goes wrong:** The luxtronik library's `Base.__init__` uses the parameter name `writeable` (British spelling). Phase 1 `ParameterDef` uses `writable`. Accessing `obj.writable` on a luxtronik datatype object raises `AttributeError` silently if not caught.

**Why it happens:** Inconsistent spelling across library vs. proxy domain model.

**How to avoid:** Always use `obj.writeable` when reading from luxtronik objects. Map to `writable` in `ParameterDef` constructor. Add a unit test that verifies the writable count from the full database matches 25.

**Warning signs:** All 1,126 parameters show `writable=False` in `list-params` output — `AttributeError` fell through silently.

### Pitfall 2: Input Block Size Underestimation

**What goes wrong:** If `INPUT_BLOCK_SIZE` remains 260 (Phase 1 value), visibility reads at wire address 1000+ crash with `ExcCodes.ILLEGAL_ADDRESS` because the datablock doesn't cover those addresses.

**Why it happens:** Phase 1 only covered calculations (0-259). Phase 2 adds visibilities at 1000-1354.

**How to avoid:** Set `INPUT_BLOCK_SIZE = 1355` in `register_map.py`. Add a test that verifies the input datablock accepts `setValues(1001, [0])` and `setValues(1355, [0])` without error.

**Warning signs:** Modbus FC4 read of any input register >= 1000 returns exception code 2 (Illegal Data Address).

### Pitfall 3: Holding Block Size Insufficient for SG-Ready

**What goes wrong:** If `HOLDING_BLOCK_SIZE` remains 1200 (Phase 1), writes to SG-ready wire address 5000 fail with `ExcCodes.ILLEGAL_ADDRESS`.

**Why it happens:** Phase 1 sized the block for 1,126 parameters + margin. SG-ready at 5000 is outside that range.

**How to avoid:** Set `HOLDING_BLOCK_SIZE = 5001`. Add a test that verifies `is_writable(5000)` returns True after SG-ready is registered.

**Warning signs:** evcc write to the SG-ready register returns Modbus exception code 2.

### Pitfall 4: Luxtronik `get()` Method Takes Index, Not Name

**What goes wrong:** Calling `lux.parameters.get("ID_Ba_Hz_akt")` returns None — the method takes an integer index or None check fails.

**Why it happens:** The luxtronik library's `get()` method signature is `get(target)` where target is the integer index. The `update_cache_from_read` in `luxtronik_client.py` calls `lux.parameters.get(address)` with an integer, which works. But the new "lookup by name" path needs the reverse mapping.

**How to avoid:** Build a `name_to_index: dict[str, int]` at `RegisterMap.__init__` by inverting the HOLDING_REGISTERS dict. Never call `lux.parameters.get(name_string)`.

**Warning signs:** All parameter reads return None; cache never updates for user-selected parameters.

### Pitfall 5: SG-Ready Write Must Not Go Through Normal Write Queue Without Disambiguation

**What goes wrong:** If SG-ready mode=2 is translated to `{3: 2}` (HeatingMode=Party) and enqueued as a normal write, the rate limiter applies the 60-second minimum — but SG-ready mode transitions should be more responsive than write rate limiting for individual parameters.

**Why it happens:** The write rate limiter tracks per-register-address; SG-ready writes are at address 5000 and the translated param writes are at addresses 3 and 4. Both should be rate-limited independently, but the SG-ready translation should not be blocked by a prior user write to address 3.

**How to avoid:** Route SG-ready writes as a dedicated `SgReadyWrite` command type in the write queue. The polling engine processes it separately, applying normal rate limits only to the underlying Luxtronik parameter addresses (3, 4, etc.) — not to the SG-ready virtual address 5000.

**Warning signs:** SG-ready mode changes are silently dropped if the user previously wrote HeatingMode within the last 60 seconds.

### Pitfall 6: Visibility Poll Adds 355 Luxtronik Attribute Reads Per Cycle

**What goes wrong:** Reading all 355 visibilities on every poll cycle adds ~355 dict lookups plus cache writes per cycle. This is fast (in-memory Python), but also pointless since visibilities are static hardware configuration flags that almost never change.

**Why it happens:** Visibilities reflect which UI elements are visible on the controller display — they depend on hardware configuration, not runtime state. A heat pump without a swimming pool will always show 0 for `ID_Visi_Schwimmbad`.

**How to avoid:** Read visibilities once at startup (or on first successful poll), then skip them in subsequent poll cycles. Add a `visibilities_loaded` flag to the polling engine; once True, skip the visibility read step. Expose a config option `poll_visibilities: false` (default) to make this explicit.

**Warning signs:** Poll cycle duration increases noticeably when visibilities are enabled; logs show 355 `cache_input_updated` events per cycle.

## Code Examples

### Building the Full Parameter Database (Module-Level)

```python
# Source: luxtronik library API (VERIFIED: local check 2026-04-05)
import luxtronik.parameters as _lp
import luxtronik.datatypes as _dt

_lib_params = _lp.Parameters()

HOLDING_REGISTERS: dict[int, ParameterDef] = {}
for _idx, _obj in _lib_params.parameters.items():
    if _obj is None:
        continue
    # Extract allowed_values from SelectionBase subclasses (HeatingMode, HotWaterMode, etc.)
    _allowed: list[int] | None = None
    if isinstance(_obj, _dt.SelectionBase) and _obj.codes:
        _allowed = list(_obj.codes.keys())
    HOLDING_REGISTERS[_idx] = ParameterDef(
        luxtronik_id=_obj.name,
        name=_obj.name,         # D-02: human name added in follow-up pass
        data_type=type(_obj).__name__,
        writable=_obj.writeable,   # Note: 'writeable' spelling in library
        allowed_values=_allowed,
    )
```

### Full Visibility Database

```python
# Source: luxtronik library API (VERIFIED: local check 2026-04-05)
import luxtronik.visibilities as _lv

_lib_visi = _lv.Visibilities()

VISIBILITY_REGISTERS: dict[int, VisibilityDef] = {}
for _idx, _obj in _lib_visi.visibilities.items():
    if _obj is None:
        continue
    # Wire address = Luxtronik index + 1000 (D-14)
    VISIBILITY_REGISTERS[_idx + 1000] = VisibilityDef(
        luxtronik_id=_obj.name,
        name=_obj.name,
    )
# Result: keys 1000-1354, all 355 entries
```

### Update Cache for Visibilities in LuxtronikClient

```python
# Source: established update_cache_from_read pattern (VERIFIED: codebase read)
# In LuxtronikClient.update_cache_from_read:
for wire_address in self._register_map.all_visibility_addresses():
    entry = self._register_map.get_visibility_entry(wire_address)
    if entry is None:
        continue
    # Wire address = lux_index + 1000, so lux_index = wire_address - 1000
    lux_index = wire_address - 1000
    visi = lux.visibilities.visibilities.get(lux_index)
    if visi is None:
        continue
    # Visibilities are Unknown type; raw integer value is 0 or 1
    raw_value = visi.to_heatpump(visi.value) if visi.value is not None else 0
    cache.update_input_values(wire_address, [int(raw_value) if raw_value is not None else 0])
```

### evcc YAML Configuration Snippet (INTEG-01 target)

The evcc `sgready` charger type is the correct target [CITED: github.com/evcc-io/evcc/blob/master/templates/definition/charger/stiebel-lwa.yaml]. evcc writes integer 1 (Normal), 2 (Boost), or 3 (Dimm/Stop) to the `setmode` Modbus register. The proxy maps these to Luxtronik parameter combinations.

```yaml
# evcc.yaml — Luxtronik2 Modbus Proxy integration
# [ASSUMED] — address 0-based convention needs hardware validation (D-15)
chargers:
  - name: heat_pump
    type: sgready
    modbus: tcpip
    id: 1
    host: 192.168.x.x      # proxy host
    port: 502
    setmode:
      source: modbus
      register:
        address: 5000       # SG-ready virtual register (0-based wire address)
        type: writeholding
        decode: uint16
    getmode:
      source: modbus
      register:
        address: 5000
        type: holding
        decode: uint16
    temp:
      source: modbus
      register:
        address: 17         # ID_WEB_Temperatur_TBW (hot water tank, C*10)
        type: input
        decode: int16
      scale: 0.1
    power:
      source: modbus
      register:
        address: 257        # Heat_Output (watts)
        type: input
        decode: uint16
```

Note: evcc's `sgready` charger uses modes 1 (Normal/off), 2 (Boost/on), 3 (Dimm/reduced). The proxy maps:
- evcc writes 1 → proxy SG-ready mode 1 (Normal)
- evcc writes 2 → proxy SG-ready mode 3 (Force on / hot water boost)
- evcc writes 3 → proxy SG-ready mode 0 (EVU lock / stop)

This mapping must be documented clearly since the evcc mode numbering (1-3) differs from the BWWP SG-ready standard (0-3). [ASSUMED] — requires confirmation against running evcc instance.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual register map in config | Library introspection + name-based selection | Phase 2 | Users use names, not indices |
| Fixed curated 9-register set | User-extensible via `registers:` YAML section | Phase 2 | Any of 1,126 params accessible |
| No SG-ready support | Virtual SG-ready register at 5000 | Phase 2 | evcc integration enabled |
| Input registers = calcs only (0-259) | Input registers = calcs (0-259) + visibilities (1000-1354) | Phase 2 | HA dashboards can show visibility flags |

**Deprecated/outdated:**
- `INPUT_BLOCK_SIZE = 260`: Must grow to 1355 to cover visibility range
- `HOLDING_BLOCK_SIZE = 1200`: Must grow to 5001 to cover SG-ready at 5000

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | SG-ready mode mapping: 0=EVU lock (Hz=Off, Bw=Off), 1=Normal (Hz=Auto, Bw=Auto), 2=Recommended (Hz=Party, Bw=Auto), 3=Force on (Hz=Auto, Bw=Party) | Code Examples, Pattern 6 | Wrong parameter combination reaches real hardware; heat pump could enter unexpected state. Hardware validation required before release (flagged in STATE.md). |
| A2 | evcc `sgready` charger type sends integer 1/2/3 via Modbus holding register write (not 0/1/2/3) | Code Examples (evcc YAML) | SG-ready mode numbering off by 1; proxy translates wrong modes. Verify by reading evcc source or testing against running instance. |
| A3 | evcc uses 0-based Modbus wire addresses | User Constraints D-15 | Register address mismatch; every evcc read/write lands on wrong parameter. User confirmed 0-based but hardware validation required. |
| A4 | Visibilities rarely or never change at runtime (static HW config flags) | Architecture Pattern (Pitfall 6) | If visibilities change during operation (e.g., dynamic system reconfiguration), poll-once approach misses updates. Mitigation: document that visibility cache refreshes on proxy restart. |

**If this table is empty:** Not applicable — 4 assumptions require hardware validation before release.

## Open Questions

1. **SG-ready mode integer value evcc sends**
   - What we know: evcc's `sgready` charger type uses modes internally labeled Normal(1), Boost(2), Dimm(3). The `setmode` provider writes these integers via Modbus.
   - What's unclear: Does evcc write 1/2/3 or 0/1/2? The stiebel-lwa.yaml template writes 0/1/0 as a pair of register bits — the proxy's single-register approach is different.
   - Recommendation: Document the proxy's SG-ready register as accepting 0-3 per BWWP standard. Map from evcc's integer to proxy's integer in documentation. Verify with real evcc.

2. **Operating mode readback for SG-ready getmode**
   - What we know: D-11 specifies SG-ready register is read-write; reading returns last applied mode.
   - What's unclear: evcc's `getmode` may expect specific integer values that correspond to SG-ready state names.
   - Recommendation: Store last-written SG-ready mode in a Python int; return it on FC3 reads of address 5000. Initialize to 1 (Normal) on startup.

3. **BenPru HA integration: does it read visibilities?**
   - What we know: BenPru reads parameters and calculations from port 8889. Phase 2 adds visibility reads.
   - What's unclear: Does adding visibility reads to the proxy's poll cycle materially increase contention with BenPru?
   - Recommendation: Implement poll-once for visibilities (Pitfall 6 mitigation). Document that visibility data is cached from first successful poll, not refreshed per cycle.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.10+ | Runtime | Yes | 3.10.12 | — |
| `luxtronik==0.3.14` | Parameter database source | Yes | 0.3.14 | — |
| `pymodbus==3.12.1` | Modbus server | Yes | 3.12.1 | — |
| `pydantic==2.12.5` | Config validation | Yes | 2.12.5 | — |
| `pydantic-settings` | YAML config | Yes | installed | — |
| `pytest 9.0.2` | Unit tests | Yes | 9.0.2 | — |
| `difflib` | Fuzzy matching (D-07) | Yes | stdlib | — |
| `argparse` | list-params CLI (D-08) | Yes | stdlib | — |

**No missing dependencies.** All Phase 2 implementation uses installed packages or Python stdlib.

**Test run command:** `PYTHONPATH=src python3 -m pytest tests/unit/ -q`
(Package not installed as editable due to pip constraint in environment; PYTHONPATH workaround is established pattern.)

## Project Constraints (from CLAUDE.md)

All constraints from Phase 1 remain in force:

- **Language:** US English for all code, comments, variable names, commit messages
- **Comments:** Every function, every module, complex logic explained; Google-style docstrings
- **No private data:** No real IPs, hostnames, passwords in any file; pre-commit hook enforces
- **Config files:** `config.example.yaml` in repo (placeholders only); `config.yaml` gitignored
- **Tech stack:** Python 3.10+, `luxtronik==0.3.14`, `pymodbus==3.12.1`, Docker
- **Security:** `enable_writes: false` default; all writes validated before reaching controller
- **Public repo:** Every file may appear on GitHub — no internal network data ever

**Phase 2-specific constraints:**
- The full 1,126-parameter database is included in source but only curated defaults + user-selected params are exposed at runtime (from REQUIREMENTS.md "Out of Scope: Expose all registers by default — Security risk")
- SG-ready parameter combinations must be validated on real hardware before release; default map is documented as [ASSUMED] until validated
- `list-params` output must not include real IP addresses or sensitive operational data

## Sources

### Primary (HIGH confidence)
- luxtronik 0.3.14 library introspection — confirmed: 1,126 params at 0-1125, 25 writable, 251 calcs at 0-259 (indices 82-90 absent), 355 visibilities at 0-354 (contiguous), `writeable` attribute spelling
- pymodbus 3.12.1 API — confirmed: `ModbusDeviceContext` accepts single `ir=` and `hr=` datablock; `ModbusSequentialDataBlock(address=1, values=[0]*N)` for N-slot block
- Existing codebase (Phase 1) — confirmed: wire address convention, datablock address = wire + 1, `ProxyHoldingDataBlock.async_setValues` pattern, `RegisterMap` structure

### Secondary (MEDIUM confidence)
- [evcc stiebel-lwa.yaml template](https://github.com/evcc-io/evcc/blob/master/templates/definition/charger/stiebel-lwa.yaml) — sgready charger type structure with setmode/getmode Modbus providers, mode integers 1/2/3
- [evcc discussion #7153](https://github.com/evcc-io/evcc/discussions/7153) — Modbus TCP heat pump integration patterns; meter + charger combination
- [evcc issue #20760](https://github.com/evcc-io/evcc/issues/20760) — Alpha Innotec / Luxtronik support; referenced Modbus register documentation
- [evcc discussion #19288](https://github.com/evcc-io/evcc/discussions/19288) — SG-ready EVU Sperre modes; confirmed BWWP 4-state standard vs. evcc 3-mode implementation

### Tertiary (LOW confidence / needs hardware validation)
- Community consensus on SG-ready Luxtronik parameter mapping (HeatingMode + HotWaterMode) — widely cited but differs between forum posts; requires hardware validation on Alpha Innotec MSW 14

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new packages; all verified installed
- Architecture: HIGH — based on verified library API and existing codebase patterns
- SG-ready parameter mapping: LOW — [ASSUMED], community sources agree on concept, hardware validation required
- evcc integration: MEDIUM — template structure verified from official repo; mode integer mapping needs hardware confirmation

**Research date:** 2026-04-05
**Valid until:** 2026-05-05 (luxtronik 0.3.14 stable since Jun 2024; pymodbus 3.x API stable)

---
phase: 02-integration-ready-register-map
verified: 2026-04-05T21:00:00Z
status: human_needed
score: 4/4 must-haves verified
human_verification:
  - test: "Run evcc against the proxy using the documented evcc.yaml snippet and confirm heat pump power, temperatures, and operating mode are read without raw register number knowledge"
    expected: "evcc dashboard shows heat pump power (register 257), flow temp (register 10), and current operating mode (register 80) populated from the proxy"
    why_human: "Requires live evcc instance connected to a running proxy connected to actual or simulated Luxtronik controller — cannot verify without a running stack"
  - test: "Write SG-ready modes 0, 1, 2, 3 to holding register 5000 via a Modbus client and confirm the Luxtronik controller's HeatingMode and HotWaterMode change to the correct values"
    expected: "Mode 0 sets HeatingMode=Off/HotWaterMode=Off; mode 1 sets both to Automatic; mode 2 sets HeatingMode=Party; mode 3 sets HotWaterMode=Party"
    why_human: "SG-ready mode map is marked [ASSUMED] in documentation — requires hardware validation on an actual Alpha Innotec or compatible unit to confirm parameter mapping is correct"
---

# Phase 02: Integration-Ready Register Map — Verification Report

**Phase Goal:** The proxy covers all registers needed by evcc and Home Assistant, including the SG-ready virtual register, the full parameter database is accessible by name in YAML config, and a tested evcc YAML snippet is ready for documentation
**Verified:** 2026-04-05T21:00:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | An evcc instance reads heat pump power, temperatures, and operating mode from the proxy using the documented YAML configuration snippet without any raw register number knowledge | ? HUMAN NEEDED | `docs/en/evcc-integration.md` exists with heatsources YAML snippet; registers 10/11/15/17 for temperature and 257 for power are documented and backed by INPUT_REGISTERS (251 entries). End-to-end test requires running stack. |
| 2 | The SG-ready virtual register accepts integer 0-3 and the proxy translates each value to the correct Luxtronik parameter combination, confirmed by observing controller state change | ? HUMAN NEEDED | `sg_ready.py` implements `SG_READY_MODE_MAP` with 4 entries; `translate_sg_ready_mode` verified programmatically; 34/34 SG-ready + register cache tests pass. Hardware confirmation required for mode map correctness. |
| 3 | A user can add any of the 1,126 Luxtronik parameters to the register map by name in config.yaml without needing to look up raw parameter indices | ✓ VERIFIED | `RegistersConfig.parameters` in config.py; `resolve_parameter_names()` in register_map.py uses `NAME_TO_INDEX` (1,126 entries); fail-fast with fuzzy "Did you mean?" on invalid names; 35/35 tests pass. |
| 4 | Calculation registers (251 entries) and visibility registers (355 entries) are accessible as read-only input registers in their dedicated address ranges | ✓ VERIFIED | `INPUT_REGISTERS` has 251 entries; `VISIBILITY_REGISTERS` has 355 entries at wire addresses 1000-1354; `RegisterMap.input_block_size == 1355`; all 355 visibility entries have `writable=False`; 87/87 unit tests pass. |

**Score:** 4/4 truths verified (2 require human confirmation for end-to-end / hardware behavior)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/luxtronik2_modbus_proxy/register_definitions/parameters.py` | 1,126-parameter database, NAME_TO_INDEX | ✓ VERIFIED | `len(HOLDING_REGISTERS)==1126`, `len(NAME_TO_INDEX)==1126`, 25 writable params, SelectionBase allowed_values populated |
| `src/luxtronik2_modbus_proxy/register_definitions/calculations.py` | 251-calculation database, CALC_NAME_TO_INDEX | ✓ VERIFIED | `len(INPUT_REGISTERS)==251`, indices 82-90 absent as expected |
| `src/luxtronik2_modbus_proxy/register_definitions/visibilities.py` | 355-visibility database at 1000-1354 | ✓ VERIFIED | `len(VISIBILITY_REGISTERS)==355`, keys 1000-1354, VISI_NAME_TO_INDEX present |
| `src/luxtronik2_modbus_proxy/register_map.py` | Visibility support, block sizes 1355/5001, SG-ready entry | ✓ VERIFIED | `input_block_size==1355`, `holding_block_size==5001`, `get_visibility_entry(1000)` returns entry, `get_holding_entry(5000)` returns SGReadyMode entry |
| `src/luxtronik2_modbus_proxy/sg_ready.py` | SG_READY_MODE_MAP, SgReadyWrite, translate_sg_ready_mode | ✓ VERIFIED | All 4 mode entries correct; `translate_sg_ready_mode(1)=={3:0, 4:0}`; ValueError on invalid modes |
| `src/luxtronik2_modbus_proxy/config.py` | RegistersConfig, sg_ready_mode_map | ✓ VERIFIED | `class RegistersConfig(BaseModel)` with `parameters: list[str]`; `registers: RegistersConfig` on ProxyConfig; `sg_ready_mode_map: dict[int, dict[int, int]] | None` present |
| `src/luxtronik2_modbus_proxy/main.py` | list-params subcommand | ✓ VERIFIED | `subparsers`, `list-params` parser, `def _list_params()`; outputs "1126 parameters"; `--search` filter works |
| `config.example.yaml` | Documented registers: section | ✓ VERIFIED | `# registers:` section present with discovery instructions |
| `docs/en/evcc-integration.md` | evcc YAML snippet, mode table, register reference | ✓ VERIFIED | `heatsources` YAML at address 5000; mode table; temperature registers 10/11/15/17; `192.168.x.x` placeholder (no real IPs) |
| `docs/en/ha-coexistence.md` | BenPru coexistence, poll_interval, write conflict guidance | ✓ VERIFIED | BenPru referenced throughout; `poll_interval` configuration section; write conflict guidance present; no real IPs |
| `tests/unit/test_register_definitions.py` | Tests for database completeness | ✓ VERIFIED | 18 tests passing (1126 params, 25 writable, 251 calcs, 355 visibilities at 1000-1354) |
| `tests/unit/test_sg_ready.py` | SG-ready module tests | ✓ VERIFIED | 13 tests passing (mode map, translate, validate, SgReadyWrite dataclass) |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `parameters.py` | `luxtronik.parameters` | `_lp.Parameters()` introspection at import | ✓ WIRED | `_lp.Parameters()` call confirmed; `NAME_TO_INDEX` built from 1,126 entries |
| `visibilities.py` | `luxtronik.visibilities` | `_lv.Visibilities()` introspection at import | ✓ WIRED | `_lv.Visibilities()` call confirmed; 355 entries at offset +1000 |
| `register_map.py` | `register_definitions/visibilities.py` | `from ... import VISIBILITY_REGISTERS` | ✓ WIRED | Import confirmed; `get_visibility_entry()` and `all_visibility_addresses()` use `self._visibility` dict built from VISIBILITY_REGISTERS |
| `register_cache.py` | `sg_ready.py` | `SG_READY_WIRE_ADDRESS` interception in `async_setValues` | ✓ WIRED | `SG_READY_WIRE_ADDRESS`, `SG_READY_DATABLOCK_ADDRESS`, `SgReadyWrite` imported; wire_address==5000 branch confirmed at line 155 |
| `polling_engine.py` | `sg_ready.py` | `SgReadyWrite` isinstance check in `_drain_and_write` | ✓ WIRED | `from sg_ready import SG_READY_WIRE_ADDRESS, SgReadyWrite`; `isinstance(item, SgReadyWrite)` check at line 204; deferred cache update at line 291 |
| `register_map.py` | `register_definitions/parameters.py` | `NAME_TO_INDEX` in `resolve_parameter_names` | ✓ WIRED | `resolve_parameter_names()` function uses `NAME_TO_INDEX` for lookup + `difflib.get_close_matches` for fuzzy suggestions |
| `main.py` | `register_definitions/parameters.py` | `HOLDING_REGISTERS` import for list-params | ✓ WIRED | `_list_params()` imports and iterates `HOLDING_REGISTERS` |
| `docs/en/evcc-integration.md` | `sg_ready.py` | Documents register address 5000 and mode values | ✓ WIRED | Address 5000 appears at least 6 times; mode table maps 0-3 to HeatingMode + HotWaterMode combinations |
| `luxtronik_client.py` | `register_map.all_visibility_addresses()` | `skip_visibilities` parameter loop | ✓ WIRED | `all_visibility_addresses()` call at line 255; `address - 1000` offset at line 261 |
| `polling_engine.py` | `luxtronik_client.py` | `skip_visibilities=self._visibilities_loaded` | ✓ WIRED | `_visibilities_loaded` set False in `__init__`; set True after first successful read |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `parameters.py` | `HOLDING_REGISTERS` | `_lp.Parameters().parameters` luxtronik library | Yes — library introspection, not hardcoded | ✓ FLOWING |
| `calculations.py` | `INPUT_REGISTERS` | `_lc.Calculations().calculations` luxtronik library | Yes — library introspection | ✓ FLOWING |
| `visibilities.py` | `VISIBILITY_REGISTERS` | `_lv.Visibilities().visibilities` luxtronik library | Yes — library introspection | ✓ FLOWING |
| `sg_ready.py` | `SG_READY_MODE_MAP` | Hardcoded constant (community consensus mapping) | Hardcoded by design; [ASSUMED] marker present in docs | ✓ FLOWING (by design, hardware validation deferred) |
| `evcc-integration.md` | YAML snippet | `sg_ready.py` register address 5000 | Yes — address matches actual SG_READY_WIRE_ADDRESS | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| HOLDING_REGISTERS has 1,126 entries | `python3 -c "from luxtronik2_modbus_proxy.register_definitions.parameters import HOLDING_REGISTERS; print(len(HOLDING_REGISTERS))"` | 1126 | ✓ PASS |
| INPUT_REGISTERS has 251 entries | `python3 -c "from luxtronik2_modbus_proxy.register_definitions.calculations import INPUT_REGISTERS; print(len(INPUT_REGISTERS))"` | 251 | ✓ PASS |
| VISIBILITY_REGISTERS at 1000-1354 | `python3 -c "from luxtronik2_modbus_proxy.register_definitions.visibilities import VISIBILITY_REGISTERS; print(len(VISIBILITY_REGISTERS), min(VISIBILITY_REGISTERS), max(VISIBILITY_REGISTERS))"` | 355 1000 1354 | ✓ PASS |
| RegisterMap block sizes correct | `python3 -c "from luxtronik2_modbus_proxy.register_map import RegisterMap; rm=RegisterMap(); print(rm.input_block_size, rm.holding_block_size)"` | 1355 5001 | ✓ PASS |
| SG-ready mode translation | `python3 -c "from luxtronik2_modbus_proxy.sg_ready import translate_sg_ready_mode; print(translate_sg_ready_mode(1))"` | {3: 0, 4: 0} | ✓ PASS |
| Invalid param name raises with suggestion | `python3 -c "from luxtronik2_modbus_proxy.register_map import RegisterMap; RegisterMap(extra_param_names=['ID_Ba_Hz_akx'])"` | ValueError with "Did you mean" | ✓ PASS |
| list-params prints 1126 entries | `python3 -m luxtronik2_modbus_proxy.main list-params \| tail -1` | "1126 parameters" | ✓ PASS |
| All unit tests pass | `pytest tests/unit/ -x -q` | 87 passed in 0.19s | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| REG-02 | 02-01, 02-02 | Built-in mapping database of all 1,126 parameters, browsable and selectable by name in YAML config | ✓ SATISFIED | HOLDING_REGISTERS(1126), NAME_TO_INDEX(1126), RegistersConfig.parameters, resolve_parameter_names() |
| REG-03 | 02-01 | 251 calculations as read-only input registers | ✓ SATISFIED | INPUT_REGISTERS(251), input block 0-259 (gaps 82-90), all writable=False |
| REG-04 | 02-01 | 355 visibilities as read-only input registers in dedicated address range | ✓ SATISFIED | VISIBILITY_REGISTERS(355) at 1000-1354, all writable=False, INPUT_BLOCK_SIZE=1355 |
| REG-05 | 02-03 | SG-ready virtual register (integer 0-3) mapping to Luxtronik mode combinations | ✓ SATISFIED | sg_ready.py with SG_READY_MODE_MAP, register at address 5000 in RegisterMap, write interception in register_cache.py |
| INTEG-01 | 02-03 | Documentation includes evcc YAML configuration example | ✓ SATISFIED | docs/en/evcc-integration.md with heatsources YAML, mode table, temperature register reference |
| INTEG-02 | 02-03 | Documentation explains coexistence with HA BenPru/luxtronik integration | ✓ SATISFIED | docs/en/ha-coexistence.md with single-connection model, poll_interval guidance, write conflict section |

All 6 requirements mapped to Phase 2 are accounted for. No orphaned requirements found.

### Anti-Patterns Found

| File | Pattern | Severity | Impact |
|------|---------|----------|--------|
| `sg_ready.py` (documented in evcc-integration.md) | `SG_READY_MODE_MAP` is hardcoded (community consensus, not validated) | ℹ️ Info | Mode mapping is marked [ASSUMED] in documentation; requires hardware validation before production use. Not a code stub — this is intentional design pending hardware confirmation. |

No TODO/FIXME/placeholder comments found in implementation files. No empty return stubs. No orphaned wiring.

### Human Verification Required

#### 1. evcc End-to-End Read Test

**Test:** Start the proxy against a real or simulated Luxtronik 2.0 controller. Configure evcc using the YAML snippet from `docs/en/evcc-integration.md`. Observe that evcc reads heat pump power (register 257), flow temperature (register 10), and operating mode (register 80) without the user needing to specify raw register numbers.

**Expected:** evcc dashboard or logs show non-zero values for the mapped registers. The snippet works without modification beyond replacing `192.168.x.x` with the actual proxy IP.

**Why human:** Requires a running evcc instance, a running proxy, and a reachable Luxtronik controller (or high-fidelity emulator). Cannot be verified with static code analysis or unit tests.

#### 2. SG-Ready Mode Map Hardware Validation

**Test:** Using a Modbus client (e.g., `modpoll` or evcc test mode), write values 0, 1, 2, and 3 to holding register 5000 on the running proxy. After each write, observe the Luxtronik controller's HeatingMode and HotWaterMode parameters via the HA BenPru integration or Luxtronik web interface.

**Expected:**
- Mode 0: HeatingMode = Off (4), HotWaterMode = Off (4)
- Mode 1: HeatingMode = Automatic (0), HotWaterMode = Automatic (0)
- Mode 2: HeatingMode = Party (2), HotWaterMode = Automatic (0)
- Mode 3: HeatingMode = Automatic (0), HotWaterMode = Party (2)

**Why human:** The `SG_READY_MODE_MAP` is based on community consensus and explicitly marked [ASSUMED] in the documentation. The proxy code correctly translates and forwards the writes, but whether the chosen HeatingMode/HotWaterMode values achieve the intended SG-ready behavior on actual hardware requires physical controller observation.

### Gaps Summary

No programmatic gaps found. All 6 phase requirements are implemented and tested. The two human verification items represent end-to-end integration and hardware validation that cannot be confirmed without a live system — they are not defects in the implementation.

The SG-ready mode mapping [ASSUMED] annotation in the documentation correctly sets user expectations for hardware validation before production use.

---

_Verified: 2026-04-05T21:00:00Z_
_Verifier: Claude (gsd-verifier)_

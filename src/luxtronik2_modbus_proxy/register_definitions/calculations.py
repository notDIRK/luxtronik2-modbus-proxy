"""Full Luxtronik calculation database mapped to Modbus input register addresses.

Input registers (FC4 read-only) map to Luxtronik calculations — the computed,
read-only sensor values of the controller. Modbus wire addresses are 0-based.

The full database of all 251 calculations is built at module import time by
introspecting the luxtronik library. This covers all computed sensor values
of the Luxtronik 2.0 controller (temperatures, operating modes, power, etc.).

Register address convention:
  - Modbus wire address == Luxtronik calculation index (0-based)
  - No offset applied; address N == calcs[N] in the luxtronik library
  - Indices 82-90 are absent (None in the luxtronik library); they are skipped

Reverse lookup:
  - CALC_NAME_TO_INDEX: dict[str, int] maps luxtronik_id -> wire_address for all entries.
"""

from __future__ import annotations

from dataclasses import dataclass

import luxtronik.calculations as _lc


@dataclass
class CalculationDef:
    """Definition of a Luxtronik calculation mapped to a Modbus input register.

    Attributes:
        luxtronik_id: Symbolic calculation name used by the luxtronik library.
        name: Human-readable description of the calculation.
        data_type: Logical type string (e.g., 'Celsius', 'OperationMode', 'Power').
    """

    luxtronik_id: str
    name: str
    data_type: str


# Introspect the luxtronik library to build the full 251-entry calculation database.
# This runs once at module import time. The library is pure Python with no I/O.
_lib_calcs = _lc.Calculations()

# Build INPUT_REGISTERS by iterating all calculation entries.
# Key: 0-based Modbus wire address == Luxtronik calculation index.
# None entries (indices 82-90) are skipped — they are gaps in the library's index space.
INPUT_REGISTERS: dict[int, CalculationDef] = {}
for _idx, _obj in _lib_calcs.calculations.items():
    if _obj is None:
        # Skip None entries (indices 82-90 are absent in the luxtronik library).
        continue

    INPUT_REGISTERS[_idx] = CalculationDef(
        luxtronik_id=_obj.name,
        name=_obj.name,  # Use luxtronik_id as name; no separate human name in library
        data_type=type(_obj).__name__,
    )

# Reverse lookup: luxtronik_id -> wire_address for all 251 calculations.
# Enables name-based lookup without traversing the full INPUT_REGISTERS dict.
CALC_NAME_TO_INDEX: dict[str, int] = {
    calc_def.luxtronik_id: addr for addr, calc_def in INPUT_REGISTERS.items()
}

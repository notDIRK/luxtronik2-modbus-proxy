"""Full Luxtronik parameter database mapped to Modbus holding register addresses.

Holding registers (FC3 read, FC6/FC16 write) map to Luxtronik parameters —
the read/write data points of the controller. Modbus wire addresses are 0-based.

The full database of all 1,126 parameters is built at module import time by
introspecting the luxtronik library. This covers the complete parameter space
of the Luxtronik 2.0 controller (Alpha Innotec, Novelan, Buderus, Nibe, etc.).

Register address convention:
  - Modbus wire address == Luxtronik parameter index (0-based)
  - No offset applied; address N == params[N] in the luxtronik library

Writable parameters:
  - Exactly 25 parameters are marked writable (writeable=True in luxtronik library).
  - The luxtronik library uses British spelling: 'writeable' (not 'writable').
  - For SelectionBase-derived types, allowed_values is populated from obj.codes.
  - Well-known critical writable params (addresses 3, 4, 105) have their metadata
    overlaid with explicit human-readable names and validated range/allowed_values.

Reverse lookup:
  - NAME_TO_INDEX: dict[str, int] maps luxtronik_id -> wire_address for all 1,126 entries.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import luxtronik.datatypes as _dt
import luxtronik.parameters as _lp


@dataclass
class ParameterDef:
    """Definition of a Luxtronik parameter mapped to a Modbus holding register.

    Attributes:
        luxtronik_id: Symbolic parameter name used by the luxtronik library.
        name: Human-readable description of the parameter.
        data_type: Logical type string (e.g., 'HeatingMode', 'Celsius').
        writable: Whether this parameter can be written via Modbus FC6/FC16.
        allowed_values: Explicit set of valid integer values, for enum-type params.
        min_value: Minimum valid integer value (inclusive), for range-type params.
        max_value: Maximum valid integer value (inclusive), for range-type params.
    """

    luxtronik_id: str
    name: str
    data_type: str
    writable: bool
    allowed_values: list[int] | None = field(default=None)
    min_value: int | None = field(default=None)
    max_value: int | None = field(default=None)


# Introspect the luxtronik library to build the full 1,126-entry parameter database.
# This runs once at module import time. The library is pure Python with no I/O.
_lib_params = _lp.Parameters()

# Build HOLDING_REGISTERS by iterating all parameter entries.
# Key: 0-based Modbus wire address == Luxtronik parameter index.
HOLDING_REGISTERS: dict[int, ParameterDef] = {}
for _idx, _obj in _lib_params.parameters.items():
    if _obj is None:
        # Defensive: skip any None entries (should not occur in 0-1125 range).
        continue

    # Determine allowed_values for SelectionBase-derived types (enum parameters).
    _allowed: list[int] | None = None
    if isinstance(_obj, _dt.SelectionBase) and hasattr(_obj, "codes") and _obj.codes:
        _allowed = list(_obj.codes.keys())

    HOLDING_REGISTERS[_idx] = ParameterDef(
        luxtronik_id=_obj.name,
        name=_obj.name,  # Use luxtronik_id as name; no separate human name in library
        data_type=type(_obj).__name__,
        writable=_obj.writeable,  # Note: luxtronik library uses British spelling
        allowed_values=_allowed,
        min_value=None,
        max_value=None,
    )

# Overlay well-known writable parameters with explicit human-readable metadata.
# These curated entries retain their Phase 1 quality: human names + validated ranges.
# The overlay replaces the introspected entry with richer metadata.

# Heating circuit operating mode.
# {0: Automatic, 1: Second heatsource, 2: Party, 3: Holidays, 4: Off}
HOLDING_REGISTERS[3] = ParameterDef(
    luxtronik_id="ID_Ba_Hz_akt",
    name="Heating circuit mode",
    data_type="HeatingMode",
    writable=True,
    allowed_values=[0, 1, 2, 3, 4],
)

# Domestic hot water operating mode.
# {0: Automatic, 1: Second heatsource, 2: Party, 3: Holidays, 4: Off}
HOLDING_REGISTERS[4] = ParameterDef(
    luxtronik_id="ID_Ba_Bw_akt",
    name="Hot water mode",
    data_type="HotWaterMode",
    writable=True,
    allowed_values=[0, 1, 2, 3, 4],
)

# DHW (domestic hot water) target temperature setpoint.
# 300=30.0C min, 650=65.0C max; raw value is Celsius * 10.
HOLDING_REGISTERS[105] = ParameterDef(
    luxtronik_id="ID_Soll_BWS_akt",
    name="Hot water setpoint (raw, C*10)",
    data_type="Celsius",
    writable=True,
    min_value=300,
    max_value=650,
)

# Reverse lookup: luxtronik_id -> wire_address for all 1,126 parameters.
# Enables D-05 name resolution without traversing the full HOLDING_REGISTERS dict.
NAME_TO_INDEX: dict[str, int] = {
    param_def.luxtronik_id: addr for addr, param_def in HOLDING_REGISTERS.items()
}

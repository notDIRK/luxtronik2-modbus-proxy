"""Curated Luxtronik parameter definitions mapped to Modbus holding register addresses.

Holding registers (FC3 read, FC6/FC16 write) map to Luxtronik parameters —
the read/write data points of the controller. Modbus wire addresses are 0-based.

Only a curated subset of the 1,126 available parameters is included here.
The selection covers the evcc and Home Assistant integration essentials:
operating modes, setpoints, and safety-critical writable controls.

Register address convention:
  - Modbus wire address == Luxtronik parameter index (0-based)
  - No offset applied; address 3 == params[3] in the luxtronik library
"""

from __future__ import annotations

from dataclasses import dataclass, field


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


# Curated holding register definitions.
# Key: 0-based Modbus wire address == Luxtronik parameter index.
# These parameters are the writable control points used by evcc and Home Assistant.
HOLDING_REGISTERS: dict[int, ParameterDef] = {
    # Heating circuit operating mode.
    # {0: Automatic, 1: Second heatsource, 2: Party, 3: Holidays, 4: Off}
    3: ParameterDef(
        "ID_Ba_Hz_akt",
        "Heating circuit mode",
        "HeatingMode",
        True,
        allowed_values=[0, 1, 2, 3, 4],
    ),
    # Domestic hot water operating mode.
    # {0: Automatic, 1: Second heatsource, 2: Party, 3: Holidays, 4: Off}
    4: ParameterDef(
        "ID_Ba_Bw_akt",
        "Hot water mode",
        "HotWaterMode",
        True,
        allowed_values=[0, 1, 2, 3, 4],
    ),
    # DHW (domestic hot water) target temperature setpoint.
    # 300=30.0C min, 650=65.0C max; raw value is Celsius * 10.
    # Writing requires enable_writes=True in ProxyConfig.
    105: ParameterDef(
        "ID_Soll_BWS_akt",
        "Hot water setpoint (raw, C*10)",
        "Celsius",
        True,
        min_value=300,
        max_value=650,
    ),
}

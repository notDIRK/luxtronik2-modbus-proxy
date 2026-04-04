"""Curated Luxtronik calculation definitions mapped to Modbus input register addresses.

Input registers (FC4 read-only) map to Luxtronik calculations — the computed,
read-only sensor values of the controller. Modbus wire addresses are 0-based.

Only a curated subset of the 251 available calculations is included here.
The selection covers the evcc and Home Assistant integration essentials:
temperature sensors, operating mode, and power output.

Register address convention:
  - Modbus wire address == Luxtronik calculation index (0-based)
  - No offset applied; address 10 == calcs[10] in the luxtronik library
"""

from __future__ import annotations

from dataclasses import dataclass


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


# Curated input register definitions.
# Key: 0-based Modbus wire address == Luxtronik calculation index.
# Temperature values are raw Celsius * 10 (e.g., 215 = 21.5 C).
INPUT_REGISTERS: dict[int, CalculationDef] = {
    # Supply flow temperature from heat pump to heating circuit (raw, C*10).
    10: CalculationDef("ID_WEB_Temperatur_TVL", "Flow temperature (raw, C*10)", "Celsius"),
    # Return temperature from heating circuit back to heat pump (raw, C*10).
    11: CalculationDef("ID_WEB_Temperatur_TRL", "Return temperature (raw, C*10)", "Celsius"),
    # Outdoor ambient temperature sensor (raw, C*10).
    15: CalculationDef("ID_WEB_Temperatur_TA", "Outside temperature (raw, C*10)", "Celsius"),
    # Domestic hot water tank temperature (raw, C*10).
    17: CalculationDef("ID_WEB_Temperatur_TBW", "Hot water temperature (raw, C*10)", "Celsius"),
    # Current operating mode of the heat pump compressor.
    # {0: heating, 1: hot water, 2: swimming pool/solar, 3: evu, 4: defrost, 5: no request}
    80: CalculationDef("ID_WEB_WP_BZ_akt", "Operating mode", "OperationMode"),
    # Thermal heat output of the heat pump in watts.
    257: CalculationDef("Heat_Output", "Heat output (W)", "Power"),
}

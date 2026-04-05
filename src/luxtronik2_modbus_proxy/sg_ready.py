"""SG-ready virtual register module for luxtronik2-modbus-proxy.

Implements the SG-ready (Smart Grid ready) virtual Modbus holding register at
wire address 5000. SG-ready is a German smart grid signal standard that uses
four operating modes to coordinate energy consumption with grid availability.

Register address 5000 is a virtual register — it does not map directly to a
single Luxtronik parameter. Instead, each SG-ready mode (0-3) translates to a
combination of HeatingMode (parameter index 3) and HotWaterMode (parameter
index 4) writes.

Mode definitions (D-09, community consensus):

    Mode 0 — EVU lock: Grid operator blocks heat pump. Both modes set to Off.
    Mode 1 — Normal: Normal operation. Both modes set to Automatic.
    Mode 2 — Recommended: Increased consumption recommended. HeatingMode=Party.
    Mode 3 — Force on: Maximum consumption (surplus energy). HotWaterMode=Party.

Note [ASSUMED]: The mode-to-parameter mapping is based on community consensus
from evcc and Home Assistant forums. Behavior may differ on specific hardware
variants. Validate on your heat pump before production use.

Security (T-02-07): Incoming mode values are validated against [0, 1, 2, 3]
before any translation or write occurs. Invalid modes are rejected at the
register_cache level before this module is called.
"""

from __future__ import annotations

from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Address constants
# ---------------------------------------------------------------------------

# 0-based Modbus wire address for the SG-ready virtual register (D-09).
# This address is above the Luxtronik parameter range (0-1125) to avoid
# collisions with real parameters.
SG_READY_WIRE_ADDRESS: int = 5000

# 1-based datablock address for the SG-ready register.
# ModbusDeviceContext adds +1 to incoming wire addresses before calling
# async_setValues on the datablock. When address 5000 arrives on the wire,
# async_setValues is called with address 5001.
SG_READY_DATABLOCK_ADDRESS: int = 5001  # wire address + 1

# ---------------------------------------------------------------------------
# Mode map
# ---------------------------------------------------------------------------

# Default SG-ready mode to Luxtronik parameter mapping.
# Keys: SG-ready mode integer (0-3, per the SG-ready standard).
# Values: dict of Luxtronik parameter index -> raw integer value to write.
#
# Luxtronik parameter indices (from register_definitions/parameters.py):
#   3: HeatingMode (ID_Ba_Hz_akt) — 0=Auto, 1=Second heater, 2=Party, 3=Holiday, 4=Off
#   4: HotWaterMode (ID_Ba_Bw_akt) — 0=Auto, 1=Second heater, 2=Party, 3=Holiday, 4=Off
#
# [ASSUMED]: Requires hardware validation on Alpha Innotec MSW 14 and
# other Luxtronik 2.0 variants. Community consensus from evcc and HA forums.
SG_READY_MODE_MAP: dict[int, dict[int, int]] = {
    0: {3: 4, 4: 4},   # EVU lock: HeatingMode=Off, HotWaterMode=Off
    1: {3: 0, 4: 0},   # Normal: HeatingMode=Automatic, HotWaterMode=Automatic
    2: {3: 2, 4: 0},   # Recommended: HeatingMode=Party, HotWaterMode=Automatic
    3: {3: 0, 4: 2},   # Force on: HeatingMode=Automatic, HotWaterMode=Party
}

# ---------------------------------------------------------------------------
# SgReadyWrite dataclass
# ---------------------------------------------------------------------------


@dataclass
class SgReadyWrite:
    """A pending SG-ready mode change to be translated to Luxtronik parameter writes.

    Placed on the write queue by ProxyHoldingDataBlock.async_setValues when an
    SG-ready write is validated. The polling engine drains the queue and uses
    param_writes to issue the actual Luxtronik parameter writes.

    Attributes:
        mode: The validated SG-ready mode (0-3).
        param_writes: Dict of Luxtronik parameter index -> value to write.
            For the default map this is {3: <HeatingMode>, 4: <HotWaterMode>}.
    """

    mode: int
    param_writes: dict[int, int]


# ---------------------------------------------------------------------------
# Translation functions
# ---------------------------------------------------------------------------


def translate_sg_ready_mode(
    mode: int,
    mode_map: dict[int, dict[int, int]] | None = None,
) -> dict[int, int]:
    """Translate an SG-ready mode integer to Luxtronik parameter writes.

    Uses the provided mode_map, falling back to the built-in SG_READY_MODE_MAP.
    Raises ValueError for any mode not present in the map.

    Args:
        mode: SG-ready mode integer (0-3 for the default map).
        mode_map: Optional custom mode map. Keys are mode integers, values are
            dicts of Luxtronik parameter index -> value. If None, uses the
            built-in SG_READY_MODE_MAP.

    Returns:
        Dict of Luxtronik parameter index -> value for the requested mode.

    Raises:
        ValueError: If mode is not a valid key in the (possibly custom) mode map.
    """
    active_map = mode_map if mode_map is not None else SG_READY_MODE_MAP
    if mode not in active_map:
        valid_modes = sorted(active_map.keys())
        raise ValueError(
            f"Invalid SG-ready mode {mode}. Valid modes: {valid_modes}"
        )
    return active_map[mode]


def validate_sg_ready_mode(mode: int) -> bool:
    """Return True if the mode is a valid key in the built-in SG_READY_MODE_MAP.

    Convenience helper used for quick boolean checks (e.g., in test assertions).
    For actual translation, use translate_sg_ready_mode which raises on invalid.

    Args:
        mode: SG-ready mode integer to validate.

    Returns:
        True if mode is in {0, 1, 2, 3}, False otherwise.
    """
    return mode in SG_READY_MODE_MAP

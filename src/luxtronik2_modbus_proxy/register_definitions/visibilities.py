"""Full Luxtronik visibility database mapped to Modbus input register addresses.

Input registers (FC4 read-only) map to Luxtronik visibilities — the display
visibility flags of the controller. Modbus wire addresses use an offset of 1000
to avoid collision with the calculation address space (indices 0-259).

The full database of all 355 visibilities is built at module import time by
introspecting the luxtronik library.

Register address convention (D-14 offset):
  - Modbus wire address = Luxtronik visibility index + 1000
  - Example: visibility index 0 -> wire address 1000
  - Example: visibility index 354 -> wire address 1354
  - This places all visibilities at wire addresses 1000-1354, safely above the
    calculation space (0-259) and avoiding any future calculation index expansion.

All visibility registers are read-only (writable=False). Values are 0 or 1
integers indicating whether a UI element is visible on the controller display.

Reverse lookup:
  - VISI_NAME_TO_INDEX: dict[str, int] maps luxtronik_id -> wire_address (with offset).
"""

from __future__ import annotations

from dataclasses import dataclass

import luxtronik.visibilities as _lv


@dataclass
class VisibilityDef:
    """Definition of a Luxtronik visibility mapped to a Modbus input register.

    All visibility registers are read-only. Values are 0 (hidden) or 1 (visible).

    Attributes:
        luxtronik_id: Symbolic visibility name used by the luxtronik library.
        name: Human-readable description (same as luxtronik_id; no separate name in library).
    """

    luxtronik_id: str
    name: str


# Introspect the luxtronik library to build the full 355-entry visibility database.
# This runs once at module import time. The library is pure Python with no I/O.
_lib_visi = _lv.Visibilities()

# Build VISIBILITY_REGISTERS by iterating all visibility entries.
# Key: Luxtronik visibility index + 1000 (D-14 offset to avoid calc address collision).
# None entries are skipped defensively (should not occur in 0-354 range).
VISIBILITY_REGISTERS: dict[int, VisibilityDef] = {}
for _idx, _obj in _lib_visi.visibilities.items():
    if _obj is None:
        # Defensive: skip any None entries.
        continue

    VISIBILITY_REGISTERS[_idx + 1000] = VisibilityDef(
        luxtronik_id=_obj.name,
        name=_obj.name,  # Use luxtronik_id as name; no separate human name in library
    )

# Reverse lookup: luxtronik_id -> wire_address (with 1000 offset) for all 355 visibilities.
# Enables name-based lookup without traversing the full VISIBILITY_REGISTERS dict.
VISI_NAME_TO_INDEX: dict[str, int] = {
    visi_def.luxtronik_id: addr for addr, visi_def in VISIBILITY_REGISTERS.items()
}

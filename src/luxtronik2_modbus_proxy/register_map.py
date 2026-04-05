"""Register map for luxtronik2-modbus-proxy.

Provides address-based lookup between Modbus wire addresses and Luxtronik
parameter/calculation/visibility IDs, along with writability checks and write
value validation to protect the Luxtronik controller from invalid commands.

Register spaces:
  - Holding registers (FC3/FC6/FC16): Luxtronik parameters, wire addresses 0-1125.
    Block size 5001 to accommodate the SG-ready virtual register at address 5000.
  - Input registers (FC4): Luxtronik calculations (0-259) and visibilities (1000-1354).
    Block size 1355 to cover both calculation and visibility address ranges.
  - Visibility registers are a subset of the input register space; they are read-only
    and mapped at wire addresses 1000-1354 (D-14 offset from visibility index).

Usage:
    from luxtronik2_modbus_proxy.register_map import RegisterMap

    reg_map = RegisterMap()
    entry = reg_map.get_holding_entry(3)  # HeatingMode
    if reg_map.is_writable(3) and reg_map.validate_write_value(3, 2):
        # safe to write mode 2 (Party) to address 3
        pass

    visi_entry = reg_map.get_visibility_entry(1000)  # First visibility
    for addr in reg_map.all_visibility_addresses():
        ...
"""

from __future__ import annotations

import difflib
from dataclasses import dataclass, field

from luxtronik2_modbus_proxy.register_definitions.calculations import INPUT_REGISTERS, CalculationDef
from luxtronik2_modbus_proxy.register_definitions.parameters import HOLDING_REGISTERS, NAME_TO_INDEX, ParameterDef
from luxtronik2_modbus_proxy.register_definitions.visibilities import VISIBILITY_REGISTERS, VisibilityDef


def resolve_parameter_names(names: list[str]) -> dict[int, ParameterDef]:
    """Resolve a list of Luxtronik parameter names to their wire addresses.

    Validates each name against the full NAME_TO_INDEX database. On unknown names,
    uses fuzzy matching to provide a helpful 'Did you mean?' suggestion in the error.

    This implements the T-02-04 mitigation: all user-supplied parameter names are
    validated against the database at startup before any network activity.

    Args:
        names: List of Luxtronik symbolic parameter names (e.g., ['ID_Einst_WK_akt']).

    Returns:
        Dict mapping wire address (int) to ParameterDef for each resolved name.

    Raises:
        ValueError: If any name is not found in NAME_TO_INDEX. Message includes
            a 'Did you mean?' hint when close matches exist.
    """
    resolved: dict[int, ParameterDef] = {}
    for name in names:
        if name in NAME_TO_INDEX:
            address = NAME_TO_INDEX[name]
            resolved[address] = HOLDING_REGISTERS[address]
        else:
            suggestions = difflib.get_close_matches(name, NAME_TO_INDEX.keys(), n=3, cutoff=0.6)
            hint = f" Did you mean: {', '.join(suggestions)}?" if suggestions else ""
            raise ValueError(f"Unknown parameter name '{name}'.{hint}")
    return resolved


@dataclass
class RegisterEntry:
    """A resolved register entry combining Modbus address with Luxtronik metadata.

    Attributes:
        address: 0-based Modbus wire address.
        luxtronik_id: Symbolic name used by the luxtronik library.
        name: Human-readable description of the register.
        data_type: Logical type string (e.g., 'HeatingMode', 'Celsius').
        writable: Whether this register accepts Modbus write commands.
        allowed_values: Explicit set of valid integer values, for enum-type registers.
        min_value: Minimum valid integer value (inclusive), for range-type registers.
        max_value: Maximum valid integer value (inclusive), for range-type registers.
    """

    address: int
    luxtronik_id: str
    name: str
    data_type: str
    writable: bool = False
    allowed_values: list[int] | None = field(default=None)
    min_value: int | None = field(default=None)
    max_value: int | None = field(default=None)


class RegisterMap:
    """Maps Modbus wire addresses to Luxtronik parameter, calculation, and visibility IDs.

    Provides lookup, writability checks, and write value validation for all
    registers. The block sizes define the total register space that the Modbus
    datablock must allocate, covering all defined addresses plus margin.

    Holding registers (FC3/FC6/FC16) map to Luxtronik parameters (read/write).
    Input registers (FC4) map to Luxtronik calculations and visibilities (read-only).

    Visibility registers occupy wire addresses 1000-1354 within the input register
    space. They are read-only and accessed via get_visibility_entry() / all_visibility_addresses().
    """

    # Block size for holding registers datablock.
    # Covers Luxtronik parameter indices 0-1125 (1126 params) plus the SG-ready
    # virtual register at address 5000 (Plan 03). Total: 5001 slots.
    HOLDING_BLOCK_SIZE: int = 5001

    # Block size for input registers datablock.
    # Covers Luxtronik calculation indices 0-259 plus visibilities at 1000-1354.
    # Total: 1355 slots (addresses 0-1354).
    INPUT_BLOCK_SIZE: int = 1355

    def __init__(self, extra_param_names: list[str] | None = None) -> None:
        """Build internal lookup dictionaries from the full register definitions.

        Args:
            extra_param_names: Optional list of Luxtronik symbolic parameter names
                to expose as additional holding registers beyond the curated defaults.
                Names are validated at init time; invalid names raise ValueError.
                If None or empty, only curated defaults are exposed.

        Raises:
            ValueError: If any name in extra_param_names is not a known Luxtronik
                parameter name. Includes a 'Did you mean?' hint when close matches exist.
        """
        # Build holding register lookup: address -> RegisterEntry (1,126 entries).
        self._holding: dict[int, RegisterEntry] = {}
        for address, param_def in HOLDING_REGISTERS.items():
            self._holding[address] = RegisterEntry(
                address=address,
                luxtronik_id=param_def.luxtronik_id,
                name=param_def.name,
                data_type=param_def.data_type,
                writable=param_def.writable,
                allowed_values=param_def.allowed_values,
                min_value=param_def.min_value,
                max_value=param_def.max_value,
            )

        # Resolve extra user-specified parameter names and merge into holding lookup.
        # Curated defaults (already in self._holding) take precedence: skip duplicates.
        extra_params = resolve_parameter_names(extra_param_names or [])
        for address, param_def in extra_params.items():
            if address not in self._holding:
                self._holding[address] = RegisterEntry(
                    address=address,
                    luxtronik_id=param_def.luxtronik_id,
                    name=param_def.name,
                    data_type=param_def.data_type,
                    writable=param_def.writable,
                    allowed_values=param_def.allowed_values,
                    min_value=param_def.min_value,
                    max_value=param_def.max_value,
                )

        # Build input register lookup: address -> RegisterEntry (251 entries, 0-259).
        self._input: dict[int, RegisterEntry] = {}
        for address, calc_def in INPUT_REGISTERS.items():
            self._input[address] = RegisterEntry(
                address=address,
                luxtronik_id=calc_def.luxtronik_id,
                name=calc_def.name,
                data_type=calc_def.data_type,
                writable=False,  # Calculations are always read-only
            )

        # Build visibility lookup: address -> RegisterEntry (355 entries, 1000-1354).
        # Visibility wire addresses already have the 1000 offset applied in the definitions.
        # All visibility registers are read-only (T-02-02 mitigation).
        self._visibility: dict[int, RegisterEntry] = {}
        for address, visi_def in VISIBILITY_REGISTERS.items():
            self._visibility[address] = RegisterEntry(
                address=address,
                luxtronik_id=visi_def.luxtronik_id,
                name=visi_def.name,
                data_type="Unknown",  # All visibility types are Unknown in the library
                writable=False,  # Visibilities are always read-only (T-02-02)
            )

    @property
    def holding_block_size(self) -> int:
        """Total number of holding register slots to allocate in the Modbus datablock."""
        return self.HOLDING_BLOCK_SIZE

    @property
    def input_block_size(self) -> int:
        """Total number of input register slots to allocate in the Modbus datablock."""
        return self.INPUT_BLOCK_SIZE

    def get_holding_entry(self, address: int) -> RegisterEntry | None:
        """Return the RegisterEntry for a holding register address, or None if unmapped.

        Args:
            address: 0-based Modbus wire address.

        Returns:
            RegisterEntry if the address is mapped, None otherwise.
        """
        return self._holding.get(address)

    def get_input_entry(self, address: int) -> RegisterEntry | None:
        """Return the RegisterEntry for an input register address, or None if unmapped.

        Args:
            address: 0-based Modbus wire address.

        Returns:
            RegisterEntry if the address is mapped, None otherwise.
        """
        return self._input.get(address)

    def get_visibility_entry(self, address: int) -> RegisterEntry | None:
        """Return the RegisterEntry for a visibility register address, or None if unmapped.

        Visibility registers occupy wire addresses 1000-1354. Addresses outside
        this range (including calculation addresses 0-259) always return None.

        Args:
            address: 0-based Modbus wire address (must be 1000-1354 for visibilities).

        Returns:
            RegisterEntry if the address is a mapped visibility, None otherwise.
        """
        return self._visibility.get(address)

    def is_writable(self, address: int) -> bool:
        """Return True only if the holding register at this address exists and is writable.

        Args:
            address: 0-based Modbus wire address.

        Returns:
            True if the address maps to a writable holding register, False otherwise.
        """
        entry = self._holding.get(address)
        return entry is not None and entry.writable

    def validate_write_value(self, address: int, value: int) -> bool:
        """Validate a write value against the register's allowed values or range constraints.

        Protects the Luxtronik controller from out-of-range or invalid values.
        Returns False if:
        - The address is not mapped or not writable.
        - The value is not in the allowed_values list (for enum-type registers).
        - The value is outside [min_value, max_value] (for range-type registers).

        Args:
            address: 0-based Modbus wire address.
            value: 16-bit integer value to validate.

        Returns:
            True if the value is valid for this register, False otherwise.
        """
        entry = self._holding.get(address)
        if entry is None or not entry.writable:
            return False

        # Validate against explicit allowed values list (enum-type registers).
        if entry.allowed_values is not None:
            return value in entry.allowed_values

        # Validate against min/max range (range-type registers).
        if entry.min_value is not None and value < entry.min_value:
            return False
        if entry.max_value is not None and value > entry.max_value:
            return False

        return True

    def all_holding_addresses(self) -> list[int]:
        """Return a sorted list of all mapped holding register (0-based) addresses.

        Returns:
            Sorted list of holding register addresses.
        """
        return sorted(self._holding.keys())

    def all_input_addresses(self) -> list[int]:
        """Return a sorted list of all mapped input register (0-based) addresses.

        Returns:
            Sorted list of input register addresses (calculations only, 0-259).
        """
        return sorted(self._input.keys())

    def all_visibility_addresses(self) -> list[int]:
        """Return a sorted list of all mapped visibility register addresses (1000-1354).

        Returns:
            Sorted list of visibility wire addresses with 1000 offset applied.
        """
        return sorted(self._visibility.keys())

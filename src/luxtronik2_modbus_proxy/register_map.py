"""Register map for luxtronik2-modbus-proxy.

Provides address-based lookup between Modbus wire addresses and Luxtronik
parameter/calculation IDs, along with writability checks and write value
validation to protect the Luxtronik controller from invalid commands.

Usage:
    from luxtronik2_modbus_proxy.register_map import RegisterMap

    reg_map = RegisterMap()
    entry = reg_map.get_holding_entry(3)  # HeatingMode
    if reg_map.is_writable(3) and reg_map.validate_write_value(3, 2):
        # safe to write mode 2 (Party) to address 3
        pass
"""

from __future__ import annotations

from dataclasses import dataclass, field

from luxtronik2_modbus_proxy.register_definitions.calculations import INPUT_REGISTERS, CalculationDef
from luxtronik2_modbus_proxy.register_definitions.parameters import HOLDING_REGISTERS, ParameterDef


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
    """Maps Modbus wire addresses to Luxtronik parameter and calculation IDs.

    Provides lookup, writability checks, and write value validation for all
    curated registers. The block sizes define the total register space that
    the Modbus datablock must allocate, covering all defined addresses plus margin.

    Holding registers (FC3/FC6/FC16) map to Luxtronik parameters (read/write).
    Input registers (FC4) map to Luxtronik calculations (read-only).
    """

    # Block size for holding registers datablock.
    # Covers Luxtronik parameter indices 0-1125 (1126 params) + margin.
    HOLDING_BLOCK_SIZE: int = 1200

    # Block size for input registers datablock.
    # Covers Luxtronik calculation indices 0-257 + margin.
    INPUT_BLOCK_SIZE: int = 260

    def __init__(self) -> None:
        """Build internal lookup dictionaries from the curated register definitions."""
        # Build holding register lookup: address -> RegisterEntry
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

        # Build input register lookup: address -> RegisterEntry
        self._input: dict[int, RegisterEntry] = {}
        for address, calc_def in INPUT_REGISTERS.items():
            self._input[address] = RegisterEntry(
                address=address,
                luxtronik_id=calc_def.luxtronik_id,
                name=calc_def.name,
                data_type=calc_def.data_type,
                writable=False,  # Calculations are always read-only
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
            Sorted list of input register addresses.
        """
        return sorted(self._input.keys())

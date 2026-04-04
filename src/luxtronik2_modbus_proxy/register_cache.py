"""Register cache for luxtronik2-modbus-proxy.

Provides the in-memory Modbus datastore that Modbus clients read from between
polling cycles. Consists of three components:

- ``ProxyHoldingDataBlock``: Subclasses ``ModbusSequentialDataBlock`` to intercept
  Modbus write commands. Validates each write against the register map before
  accepting, then enqueues valid writes for the polling engine to forward to the
  Luxtronik controller. ``async_setValues`` is called directly (NOT via ModbusDeviceContext,
  which only calls the sync ``setValues`` on the datablock).

- ``ProxyDeviceContext``: Subclasses ``ModbusDeviceContext`` to override ``async_setValues``
  so that holding register write requests (FC6/FC16) are routed to
  ``ProxyHoldingDataBlock.async_setValues``. This is required because pymodbus 3.x calls
  ``context.async_setValues`` at the server level but ``ModbusDeviceContext`` only delegates
  to the sync ``setValues`` on the datablock — bypassing any async override on the datablock.

- ``RegisterCache``: Wraps both the holding (read/write) and input (read-only)
  datablocks. Exposes wire-address-aware update methods called by the polling
  engine when fresh Luxtronik data arrives.

Address convention (see Research Pattern 2):
    Modbus wire address N -> ModbusDeviceContext adds +1 -> datablock index N+1.
    All datablocks must start at address=1. When converting back:
        datablock_address - 1 = wire_address.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Union

import structlog
from pymodbus.datastore import ModbusDeviceContext, ModbusSequentialDataBlock
from pymodbus.datastore.sequential import ExcCodes

from luxtronik2_modbus_proxy.register_map import RegisterMap

logger = structlog.get_logger(__name__)


class ProxyHoldingDataBlock(ModbusSequentialDataBlock):
    """Holding register datablock that validates and queues writes to the Luxtronik controller.

    Overrides ``async_setValues`` (called by the pymodbus async server when a Modbus
    FC6 or FC16 write request arrives) to:

    1. Reject all writes when ``enable_writes`` is False.
    2. Reject writes to non-writable or unmapped addresses with ILLEGAL_VALUE.
    3. Validate each write value against the register map's allowed_values/min_max.
    4. On success: update the local datablock and enqueue the write for upstream delivery.

    The write queue is drained by the polling engine, which forwards pending writes
    to the Luxtronik controller in a connect-write-disconnect cycle.

    Security note (T-02-01, T-02-02): All incoming write values are validated before
    they can influence the physical hardware. ``enable_writes=False`` by default.
    """

    def __init__(
        self,
        write_queue: asyncio.Queue,
        register_map: RegisterMap,
        enable_writes: bool,
        address: int,
        values: list[int],
    ) -> None:
        """Initialize the datablock with validation dependencies.

        Args:
            write_queue: Queue for pending upstream writes. The polling engine
                reads from this queue and forwards writes to the Luxtronik controller.
            register_map: Register map used to validate write values and writability.
            enable_writes: Safety gate — if False, all write commands are rejected
                regardless of address or value.
            address: Starting address of the datablock (must be 1 for Modbus convention).
            values: Initial register values list (length determines block size).
        """
        super().__init__(address=address, values=values)
        self._write_queue = write_queue
        self._register_map = register_map
        self._enable_writes = enable_writes

    async def async_setValues(
        self, address: int, values: list[int]
    ) -> None | ExcCodes:
        """Intercept Modbus write requests with validation before accepting.

        Called by the pymodbus async server for FC6 (write single register) and
        FC16 (write multiple registers) commands. The address received here is
        1-based (ModbusDeviceContext adds +1 to the wire address before calling).

        Validation order:
        1. Global write enable check.
        2. Writability check against register map (wire address = address - 1).
        3. Per-value validation against allowed_values or min/max range.
        4. If all pass: update datablock and enqueue (wire_address, values).

        Args:
            address: 1-based datablock address (wire address + 1 from ModbusDeviceContext).
            values: List of 16-bit integer values to write.

        Returns:
            None on success, ExcCodes.ILLEGAL_VALUE if validation fails.
        """
        # Gate 1: global write enable (T-02-02)
        if not self._enable_writes:
            logger.warning(
                "write_rejected_disabled",
                datablock_address=address,
                reason="enable_writes is False",
            )
            return ExcCodes.ILLEGAL_VALUE

        # Convert from 1-based datablock address back to 0-based wire address.
        # ModbusDeviceContext adds +1 before calling setValues, so we subtract 1 here
        # to recover the original wire address for register map lookups.
        wire_address = address - 1

        # Gate 2: writability check — address must be mapped and flagged writable (T-02-01)
        if not self._register_map.is_writable(wire_address):
            logger.warning(
                "write_rejected_not_writable",
                wire_address=wire_address,
                datablock_address=address,
            )
            return ExcCodes.ILLEGAL_VALUE

        # Gate 3: value range validation — all values must pass for the write to proceed (T-02-01)
        for value in values:
            if not self._register_map.validate_write_value(wire_address, value):
                logger.warning(
                    "write_rejected_invalid_value",
                    wire_address=wire_address,
                    value=value,
                )
                return ExcCodes.ILLEGAL_VALUE

        # All validation passed — update the datablock and enqueue for upstream delivery.
        result = await super().async_setValues(address, values)
        if result is None:
            await self._write_queue.put((wire_address, values))
            logger.info(
                "write_accepted",
                wire_address=wire_address,
                values=values,
            )

        return result


class ProxyDeviceContext(ModbusDeviceContext):
    """Modbus device context that routes holding register writes through async validation.

    pymodbus 3.x calls ``context.async_setValues`` at the server level (in PDU handlers
    like ``WriteSingleRegisterRequest.datastore_update``). However, the base
    ``ModbusDeviceContext`` inherits ``async_setValues`` from ``ModbusBaseDeviceContext``,
    which simply delegates to the synchronous ``self.setValues`` — bypassing any async
    override defined on the datablock subclass.

    This subclass overrides ``async_setValues`` to call
    ``ProxyHoldingDataBlock.async_setValues`` directly for holding register function codes
    (FC3=3, FC6=6, FC16=16). This ensures write validation, the enable_writes gate, and
    write queuing run on every FC6/FC16 request from Modbus clients.

    For all other function codes (discrete inputs, coils, input registers), the default
    synchronous path is used because those datablocks do not require async interception.

    Address convention: ``ModbusDeviceContext`` (and this class) receives the wire address
    (0-based) from the PDU handler. ``ProxyHoldingDataBlock.async_setValues`` expects the
    datablock address (1-based), so this method adds +1 before calling it — matching the
    behavior of the parent ``setValues`` method.
    """

    # Function codes that map to holding registers (hr).
    _HOLDING_FC: frozenset[int] = frozenset({3, 6, 16, 22, 23})

    async def async_setValues(
        self,
        func_code: int,
        address: int,
        values: list[int],
    ) -> Union[None, ExcCodes]:
        """Route holding register writes to async validation; others use sync path.

        Args:
            func_code: Modbus function code (e.g., 6 = Write Single Register).
            address: 0-based wire address from the PDU handler.
            values: List of 16-bit integer values to write.

        Returns:
            None on success, ExcCodes value if validation or write fails.
        """
        if func_code in self._HOLDING_FC:
            # Holding register write — delegate to ProxyHoldingDataBlock.async_setValues.
            # Convert wire address (0-based) to datablock address (1-based) by adding +1,
            # matching what ModbusDeviceContext.setValues does in the sync path.
            datablock_address = address + 1
            hr_block = self.store["h"]
            return await hr_block.async_setValues(datablock_address, values)

        # Non-holding write (coils, discrete inputs) — use the standard sync path.
        return self.setValues(func_code, address, values)


class RegisterCache:
    """In-memory register cache backed by pymodbus datablocks.

    Manages two datablocks:
    - ``holding_datablock`` (ProxyHoldingDataBlock): writable holding registers
      corresponding to Luxtronik parameters (FC3/FC6/FC16).
    - ``input_datablock`` (ModbusSequentialDataBlock): read-only input registers
      corresponding to Luxtronik calculations (FC4).

    The polling engine calls ``update_holding_values`` and ``update_input_values``
    after each successful Luxtronik read to keep the cache current. Modbus clients
    read directly from the datablocks via the pymodbus server.

    Stale state: The cache starts as stale (``is_stale=True``) until the first
    successful Luxtronik read. The polling engine calls ``mark_fresh()`` after each
    successful read and ``mark_stale()`` after a read failure.
    """

    def __init__(
        self,
        register_map: RegisterMap,
        write_queue: asyncio.Queue,
        enable_writes: bool,
    ) -> None:
        """Initialize the register cache with two datablocks.

        Both datablocks start at address=1 (required by the Modbus address convention
        where ModbusDeviceContext adds +1 to incoming wire addresses).

        Args:
            register_map: Register map providing block sizes and validation metadata.
            write_queue: Queue for upstream writes (passed to ProxyHoldingDataBlock).
            enable_writes: Whether to accept Modbus write commands (safety gate).
        """
        # Holding registers: writable, backed by ProxyHoldingDataBlock for write interception.
        self._holding_datablock = ProxyHoldingDataBlock(
            write_queue=write_queue,
            register_map=register_map,
            enable_writes=enable_writes,
            address=1,
            values=[0] * register_map.holding_block_size,
        )

        # Input registers: read-only calculations, plain datablock (no write interception needed).
        self._input_datablock = ModbusSequentialDataBlock(
            address=1,
            values=[0] * register_map.input_block_size,
        )

        # Cache starts stale until the first successful Luxtronik read completes.
        self._is_stale: bool = True
        self._last_successful_read: datetime | None = None

    @property
    def holding_datablock(self) -> ProxyHoldingDataBlock:
        """The holding register datablock (FC3/FC6/FC16), passed to ModbusDeviceContext."""
        return self._holding_datablock

    @property
    def input_datablock(self) -> ModbusSequentialDataBlock:
        """The input register datablock (FC4), passed to ModbusDeviceContext."""
        return self._input_datablock

    @property
    def is_stale(self) -> bool:
        """True if the cache has not been updated since the last read failure or initialization."""
        return self._is_stale

    @property
    def last_successful_read(self) -> datetime | None:
        """Timestamp of the most recent successful Luxtronik read, or None if never read."""
        return self._last_successful_read

    def update_holding_values(self, wire_address: int, values: list[int]) -> None:
        """Update holding register cache from a freshly read Luxtronik parameter value.

        Converts from 0-based wire address to 1-based datablock address before
        calling setValues, matching the ModbusDeviceContext address convention.

        Args:
            wire_address: 0-based Modbus wire address (equals Luxtronik parameter index).
            values: List of 16-bit integer values to store.
        """
        # Convert wire address to datablock address (+1) to match the convention
        # that ModbusDeviceContext uses when Modbus clients access the datablock.
        datablock_address = wire_address + 1
        self._holding_datablock.setValues(datablock_address, values)

    def update_input_values(self, wire_address: int, values: list[int]) -> None:
        """Update input register cache from a freshly read Luxtronik calculation value.

        Converts from 0-based wire address to 1-based datablock address.

        Args:
            wire_address: 0-based Modbus wire address (equals Luxtronik calculation index).
            values: List of 16-bit integer values to store.
        """
        datablock_address = wire_address + 1
        self._input_datablock.setValues(datablock_address, values)

    def mark_stale(self) -> None:
        """Mark the cache as stale after a Luxtronik read failure.

        Stale caches still serve Modbus clients but return the last known values,
        which may be outdated. The polling engine marks stale on connection errors.
        """
        self._is_stale = True
        logger.warning("cache_marked_stale")

    def mark_fresh(self) -> None:
        """Mark the cache as fresh after a successful Luxtronik read cycle.

        Updates ``last_successful_read`` to the current local time.
        Called by the polling engine after each complete read-and-update cycle.
        """
        self._is_stale = False
        self._last_successful_read = datetime.now()
        logger.debug("cache_marked_fresh", last_read=self._last_successful_read.isoformat())

"""Luxtronik client wrapper for luxtronik2-modbus-proxy.

Provides an async-safe adapter around the blocking ``luxtronik`` library.
Each read or write operation creates a NEW ``luxtronik.Luxtronik`` instance,
performs the operation, and lets the instance be garbage-collected immediately.

This connect-per-call pattern is mandatory because:
1. The Luxtronik 2.0 controller allows exactly ONE TCP connection at a time.
   Holding a persistent connection would block Home Assistant's BenPru integration
   and any other tools that connect to port 8889. (PROTO-05)
2. The ``luxtronik`` library's read()/write() methods internally connect, operate,
   and disconnect — creating a new instance ensures no stale socket state persists
   between polling cycles. (Pitfall 3)
3. The blocking socket calls (connect, read, write, disconnect) must run in a
   thread pool executor via ``run_in_executor`` to avoid stalling the asyncio event
   loop, which would delay Modbus client responses. (Pitfall 3)

Usage::

    client = LuxtronikClient(host="192.168.x.x", port=8889, register_map=reg_map)
    lux = await client.async_read()
    client.update_cache_from_read(lux, cache)

    await client.async_write({3: 2})  # Write HeatingMode=2 (Party)
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import luxtronik
import structlog

from luxtronik2_modbus_proxy.register_map import RegisterMap

if TYPE_CHECKING:
    from luxtronik2_modbus_proxy.register_cache import RegisterCache

logger = structlog.get_logger(__name__)


class LuxtronikClient:
    """Async-safe wrapper around the blocking ``luxtronik`` library.

    Creates a new ``luxtronik.Luxtronik`` instance for every read or write
    operation to enforce the connect-per-call pattern required by the
    Luxtronik 2.0 single-connection constraint.

    All blocking network calls are dispatched to a thread pool executor via
    ``asyncio.get_event_loop().run_in_executor`` to prevent event loop starvation.
    """

    def __init__(self, host: str, port: int, register_map: RegisterMap) -> None:
        """Initialize the Luxtronik client.

        Args:
            host: Hostname or IP address of the Luxtronik 2.0 controller.
            port: TCP port of the Luxtronik binary protocol server (default 8889).
            register_map: Register map used to enumerate mapped addresses when
                updating the cache from a fresh read.
        """
        self._host = host
        self._port = port
        self._register_map = register_map

    async def async_read(self) -> luxtronik.Luxtronik:
        """Connect to the Luxtronik controller, read all data, and disconnect.

        Creates a new ``luxtronik.Luxtronik`` instance and calls ``read()`` in a
        thread pool executor (because ``read()`` blocks on socket I/O). After the
        call returns, the instance holds all parameters and calculations in memory.

        CRITICAL: A new instance is created on every call. Never reuse a Luxtronik
        instance across polling cycles — the internal socket state is not safe for
        reuse after disconnect. (Pitfall 3, PROTO-05)

        Returns:
            The populated ``luxtronik.Luxtronik`` instance with parameters and
            calculations read from the controller. Caller should extract needed
            values and discard the instance.

        Raises:
            OSError: If the connection to the controller fails.
            Exception: Any exception raised by the ``luxtronik`` library.
        """
        log = logger.bind(host=self._host, port=self._port)
        log.debug("luxtronik_read_start")

        # Create a fresh instance for this read cycle. The constructor calls
        # read() automatically when safe=True (default), so we create with
        # safe=False to avoid a double-read, then call read() explicitly in executor.
        lux = luxtronik.Luxtronik.__new__(luxtronik.Luxtronik)
        lux._host = self._host
        lux._port = self._port
        lux._socket = None
        lux.calculations = luxtronik.Calculations()
        lux.parameters = luxtronik.Parameters()
        lux.visibilities = luxtronik.Visibilities()

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lux.read)

        log.debug("luxtronik_read_complete")
        return lux

    async def async_write(self, param_writes: dict[int, int]) -> None:
        """Write parameter values to the Luxtronik controller.

        Creates a new ``luxtronik.Luxtronik`` instance, populates the write queue,
        and calls ``write()`` in a thread pool executor.

        CRITICAL: The write queue MUST be populated BEFORE calling write(). The
        ``luxtronik`` library reads ``parameters.queue`` at write-time — any values
        set after the write() call starts are silently lost. (Pitfall 4, WRITE-01)

        Args:
            param_writes: Mapping of Luxtronik parameter index to raw integer value.
                Values must already be validated by the register map before calling
                this method. The polling engine is responsible for this validation.

        Raises:
            OSError: If the connection to the controller fails.
            Exception: Any exception raised by the ``luxtronik`` library.
        """
        if not param_writes:
            return

        log = logger.bind(host=self._host, port=self._port, param_writes=param_writes)
        log.info("luxtronik_write_start")

        # Create a fresh Luxtronik instance for this write cycle.
        lux = luxtronik.Luxtronik.__new__(luxtronik.Luxtronik)
        lux._host = self._host
        lux._port = self._port
        lux._socket = None
        lux.calculations = luxtronik.Calculations()
        lux.parameters = luxtronik.Parameters()
        lux.visibilities = luxtronik.Visibilities()

        # CRITICAL: Populate the write queue BEFORE dispatching write() to the executor.
        # The write() method iterates parameters.queue at call time.
        lux.parameters.queue = {index: value for index, value in param_writes.items()}

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lux.write)

        log.info("luxtronik_write_complete")

    def update_cache_from_read(
        self,
        lux: luxtronik.Luxtronik,
        cache: "RegisterCache",
        skip_visibilities: bool = False,
    ) -> None:
        """Extract mapped register values from a Luxtronik read result and update cache.

        Iterates over all mapped holding, input, and visibility register addresses,
        extracts the corresponding value from the Luxtronik instance, and stores the
        raw integer (heatpump-format) value in the register cache.

        The raw integer value is used because Modbus holding and input registers
        are 16-bit integers. Converted values (e.g., floating-point Celsius) would
        lose precision when stored as integers. The Modbus client is responsible for
        applying any scaling defined in its device configuration.

        Visibility optimization: Visibilities are static UI display flags that do not
        change during normal operation. The caller (PollingEngine) passes
        ``skip_visibilities=True`` after the first successful poll to avoid 355
        unnecessary cache writes per cycle (Pitfall 6).

        Args:
            lux: Populated ``luxtronik.Luxtronik`` instance from a completed ``async_read()``
                call. Must not be reused after this call.
            cache: Register cache to update with the freshly read values.
            skip_visibilities: If True, skip updating visibility registers in the cache.
                Use after the first successful poll since visibilities rarely change.
        """
        log = logger.bind(host=self._host)

        # Update holding registers (Luxtronik parameters, read/write).
        for address in self._register_map.all_holding_addresses():
            entry = self._register_map.get_holding_entry(address)
            if entry is None:
                continue

            param = lux.parameters.get(address)
            if param is None:
                log.warning(
                    "luxtronik_param_not_found",
                    register=address,
                    param_name=entry.name,
                )
                continue

            # Convert the parameter's .value (post-from_heatpump conversion) back to
            # the raw heatpump integer. This is the wire-format integer that Modbus
            # clients expect (e.g., 200 for 20.0°C, 2 for HeatingMode "Party").
            raw_value = param.to_heatpump(param.value)
            if raw_value is None:
                log.warning(
                    "luxtronik_param_value_none",
                    register=address,
                    param_name=entry.name,
                    value=param.value,
                )
                continue

            cache.update_holding_values(address, [int(raw_value)])
            log.debug(
                "cache_holding_updated",
                register=address,
                param_name=entry.name,
                value=int(raw_value),
            )

        # Update input registers (Luxtronik calculations, read-only).
        for address in self._register_map.all_input_addresses():
            entry = self._register_map.get_input_entry(address)
            if entry is None:
                continue

            calc = lux.calculations.get(address)
            if calc is None:
                log.warning(
                    "luxtronik_calc_not_found",
                    register=address,
                    calc_name=entry.name,
                )
                continue

            # Same raw-value extraction as holding registers.
            raw_value = calc.to_heatpump(calc.value)
            if raw_value is None:
                log.warning(
                    "luxtronik_calc_value_none",
                    register=address,
                    calc_name=entry.name,
                    value=calc.value,
                )
                continue

            cache.update_input_values(address, [int(raw_value)])
            log.debug(
                "cache_input_updated",
                register=address,
                calc_name=entry.name,
                value=int(raw_value),
            )

        # Update input registers for visibilities (read-only, mapped at wire address = index + 1000).
        # Skipped after the first successful poll since visibilities rarely change (Pitfall 6).
        if not skip_visibilities:
            visi_count = 0
            for address in self._register_map.all_visibility_addresses():
                entry = self._register_map.get_visibility_entry(address)
                if entry is None:
                    continue

                # Wire address = lux_index + 1000, so lux_index = wire_address - 1000.
                lux_index = address - 1000
                visi = lux.visibilities.visibilities.get(lux_index)
                if visi is None:
                    continue

                # Visibility values are Unknown type; value is 0 (hidden) or 1 (visible).
                # Use to_heatpump to get the raw integer; fall back to 0 if None.
                raw_value = visi.to_heatpump(visi.value) if visi.value is not None else 0
                cache.update_input_values(address, [int(raw_value) if raw_value is not None else 0])
                visi_count += 1

            log.debug(
                "cache_visibilities_updated",
                count=visi_count,
            )

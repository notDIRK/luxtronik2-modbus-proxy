"""Modbus TCP server builder for luxtronik2-modbus-proxy.

Creates and configures the pymodbus async TCP server that exposes the Luxtronik
register cache to Modbus clients (evcc, Home Assistant, etc.) over the standard
Modbus TCP protocol.

Supported function codes (handled automatically by pymodbus based on datastores):
- FC3 (Read Holding Registers): reads from the holding register datablock
- FC4 (Read Input Registers): reads from the input register datablock
- FC6 (Write Single Register): writes to the holding register datablock
- FC16 (Write Multiple Registers): writes to the holding register datablock

FC6 and FC16 writes go through ``ProxyHoldingDataBlock.async_setValues``, which
validates the write against the register map before accepting it and enqueuing
it for the polling engine to forward to the Luxtronik controller.

API notes (pymodbus 3.12.1):
- Use ``ModbusDeviceContext`` NOT ``ModbusSlaveContext`` (renamed in pymodbus 3.x).
- Use ``devices=`` keyword NOT ``slaves=`` in ``ModbusServerContext`` (renamed in 3.x).
- ``single=True`` tells the server context there is only one device (slave unit 0xFF).
"""

from __future__ import annotations

import structlog
from pymodbus.datastore import ModbusServerContext
from pymodbus.server import ModbusTcpServer

from luxtronik2_modbus_proxy.config import ProxyConfig
from luxtronik2_modbus_proxy.register_cache import ProxyDeviceContext, RegisterCache

log = structlog.get_logger(__name__)


def build_modbus_server(cache: RegisterCache, config: ProxyConfig) -> ModbusTcpServer:
    """Create a configured pymodbus async Modbus TCP server.

    Builds the server context from the register cache's holding and input
    datablocks, binds to the configured address and port, and returns a
    ``ModbusTcpServer`` ready for ``await server.serve_forever()``.

    The server handles FC3/FC4 reads directly from the cached datablocks.
    FC6/FC16 writes are intercepted by ``ProxyHoldingDataBlock.async_setValues``
    for validation and queuing before reaching the controller.

    Args:
        cache: Register cache holding both datablocks. The cache is kept
            current by the polling engine; the Modbus server reads from it
            directly without contacting the Luxtronik controller.
        config: Proxy configuration providing ``bind_address`` and ``modbus_port``.

    Returns:
        A configured ``ModbusTcpServer`` instance. Call
        ``await server.serve_forever()`` to start accepting connections.

    Note:
        Uses ``ModbusDeviceContext`` (not ``ModbusSlaveContext``) and
        ``devices=`` (not ``slaves=``) as required by pymodbus 3.x API.
        ``single=True`` configures a single-device context, which satisfies
        all Modbus clients including evcc and Home Assistant.
    """
    # Build the device context linking function codes to datablocks:
    # hr= maps FC3/FC6/FC16 (holding registers) to the proxy's validated datablock.
    # ir= maps FC4 (input registers) to the read-only calculations datablock.
    # CRITICAL: Use ProxyDeviceContext (not ModbusDeviceContext directly) — the proxy
    # subclass overrides async_setValues to route FC6/FC16 writes through
    # ProxyHoldingDataBlock.async_setValues for validation and queuing. The base
    # ModbusDeviceContext only calls the sync setValues on the datablock, bypassing
    # any async override. (Rule 1 fix: write validation was silently bypassed.)
    device_context = ProxyDeviceContext(
        hr=cache.holding_datablock,
        ir=cache.input_datablock,
    )

    # Wrap in a server context. single=True means all client unit IDs map to the
    # same device context (standard for single-device Modbus proxies).
    # CRITICAL: Use devices= keyword (not slaves=) — renamed in pymodbus 3.x.
    server_context = ModbusServerContext(devices=device_context, single=True)

    log.info(
        "modbus_server_configured",
        bind=config.bind_address,
        port=config.modbus_port,
    )

    return ModbusTcpServer(
        context=server_context,
        address=(config.bind_address, config.modbus_port),
    )

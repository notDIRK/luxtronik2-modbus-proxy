"""Application entry point for luxtronik2-modbus-proxy.

Wires all components together (config, register map, cache, Luxtronik client,
polling engine, Modbus server) and starts the asyncio event loop.

Startup sequence:
1. Load and validate configuration from YAML file.
2. Configure structlog logging.
3. Create register map, write queue, register cache, Luxtronik client.
4. Create polling engine and Modbus TCP server.
5. Register SIGTERM handler for graceful Docker shutdown.
6. Start the Modbus server and polling engine as concurrent async tasks.
7. Await both tasks until cancelled.

Shutdown sequence (triggered by SIGTERM or CTRL+C):
1. Cancel the polling task.
2. Stop the Modbus TCP server gracefully.
3. Log the shutdown complete event.

Usage::

    # Via CLI entry point (installed package):
    luxtronik2-modbus-proxy --config /app/config.yaml

    # Via Python module:
    python -m luxtronik2_modbus_proxy.main --config config.yaml
"""

from __future__ import annotations

import argparse
import asyncio
import signal
import sys

import structlog

from luxtronik2_modbus_proxy import __version__
from luxtronik2_modbus_proxy.config import load_config
from luxtronik2_modbus_proxy.logging_config import configure_logging
from luxtronik2_modbus_proxy.luxtronik_client import LuxtronikClient
from luxtronik2_modbus_proxy.modbus_server import build_modbus_server
from luxtronik2_modbus_proxy.polling_engine import PollingEngine
from luxtronik2_modbus_proxy.register_cache import RegisterCache
from luxtronik2_modbus_proxy.register_map import RegisterMap


async def main(config_path: str | None = None) -> None:
    """Load configuration, wire all components, and run the proxy.

    Creates all application components in dependency order, registers a SIGTERM
    handler for graceful shutdown, then runs the Modbus server and polling engine
    concurrently until cancelled.

    Args:
        config_path: Optional path to the YAML configuration file. If not provided,
            defaults to ``config.yaml`` in the working directory.

    Raises:
        pydantic.ValidationError: If the configuration file contains invalid values.
        FileNotFoundError: If the configuration file does not exist and
            ``LUXTRONIK_HOST`` environment variable is not set.
    """
    # Step 1: Load and validate configuration. Fails fast on invalid config
    # before any network activity, so startup errors are immediately visible.
    config = load_config(config_path)

    # Step 2: Configure logging. Do this before any other log calls so all
    # subsequent messages use the correct renderer and log level.
    configure_logging(config.log_level)

    log = structlog.get_logger(__name__)

    log.info(
        "proxy_starting",
        version=__version__,
        luxtronik_host=config.luxtronik_host,
        luxtronik_port=config.luxtronik_port,
        modbus_port=config.modbus_port,
        poll_interval=config.poll_interval,
        writes_enabled=config.enable_writes,
    )

    # Warn if poll interval is very low — this increases the chance of contention
    # with HA's BenPru integration which also connects to port 8889. (Pitfall 7)
    if config.poll_interval < 15:
        log.warning(
            "poll_interval_low",
            interval=config.poll_interval,
            recommendation="Consider 15s+ to avoid HA BenPru contention",
        )

    # Step 3: Create components in dependency order.
    # register_map provides address lookup, writability, and value validation.
    # Pass user-selected parameter names from config for dynamic register loading.
    register_map = RegisterMap(extra_param_names=config.registers.parameters)

    # write_queue connects ProxyHoldingDataBlock (producer) to PollingEngine (consumer).
    write_queue: asyncio.Queue = asyncio.Queue()

    # cache wraps both datablocks; the Modbus server reads from it directly.
    cache = RegisterCache(register_map, write_queue, config.enable_writes)

    # client wraps the blocking luxtronik library with async run_in_executor.
    client = LuxtronikClient(config.luxtronik_host, config.luxtronik_port, register_map)

    # engine manages the polling loop: drain writes, read, update cache.
    engine = PollingEngine(config, client, cache, write_queue)

    # server exposes the cache to Modbus clients over TCP.
    server = build_modbus_server(cache, config)

    # Step 4: Start both long-running tasks concurrently.
    # server_task runs the Modbus TCP server (accepts and serves connections).
    # polling_task runs the Luxtronik polling loop.
    server_task: asyncio.Task = asyncio.create_task(
        server.serve_forever(), name="modbus_server"
    )
    polling_task: asyncio.Task = asyncio.create_task(
        engine.run_forever(), name="polling_engine"
    )

    # Step 5: Register SIGTERM handler for graceful shutdown (Docker stop).
    # On SIGTERM, cancels both tasks and shuts down the server cleanly.
    # This ensures in-flight Modbus responses are completed before exit. (Pitfall 8)
    loop = asyncio.get_event_loop()
    loop.add_signal_handler(
        signal.SIGTERM,
        lambda: asyncio.create_task(
            shutdown(server, polling_task, server_task),
            name="shutdown",
        ),
    )

    log.info("proxy_running")

    # Step 6: Wait for both tasks. Under normal operation they run indefinitely.
    # On SIGTERM or CTRL+C, the shutdown coroutine cancels them.
    try:
        await asyncio.gather(polling_task, server_task)
    except asyncio.CancelledError:
        # Tasks were cancelled by the shutdown handler — this is expected.
        pass


async def shutdown(
    server,
    polling_task: asyncio.Task,
    server_task: asyncio.Task,
) -> None:
    """Gracefully shut down the proxy.

    Cancels the polling task, stops the Modbus TCP server, and logs the
    shutdown complete event. Called by the SIGTERM handler.

    Args:
        server: The running ``ModbusTcpServer`` to shut down.
        polling_task: The polling engine async task to cancel.
        server_task: The Modbus server async task to cancel.
    """
    log = structlog.get_logger(__name__)
    log.info("proxy_shutting_down")

    # Cancel the polling loop first — it holds the Luxtronik connection lock.
    polling_task.cancel()

    # Shut down the Modbus server gracefully (waits for in-flight responses).
    await server.shutdown()

    # Cancel the server task after shutdown completes.
    server_task.cancel()

    log.info("proxy_stopped")


def cli() -> None:
    """Command-line entry point for the luxtronik2-modbus-proxy.

    Parses the ``--config`` argument and starts the proxy using ``asyncio.run``.
    Installed as the ``luxtronik2-modbus-proxy`` console script via
    ``[project.scripts]`` in pyproject.toml.

    The default config path is ``/app/config.yaml`` to match the Docker volume
    mount convention (``-v ./config.yaml:/app/config.yaml``).
    """
    parser = argparse.ArgumentParser(
        prog="luxtronik2-modbus-proxy",
        description="Modbus TCP proxy for Luxtronik 2.0 heat pump controllers",
    )
    parser.add_argument(
        "--config",
        default="/app/config.yaml",
        metavar="PATH",
        help="Path to the YAML configuration file (default: /app/config.yaml)",
    )
    args = parser.parse_args()

    try:
        asyncio.run(main(config_path=args.config))
    except KeyboardInterrupt:
        # CTRL+C is normal interactive exit — no traceback needed.
        sys.exit(0)


if __name__ == "__main__":
    cli()

"""Polling engine for luxtronik2-modbus-proxy.

Implements the asynchronous polling loop that periodically connects to the
Luxtronik 2.0 controller, reads all mapped register values, updates the in-memory
register cache, and forwards any pending write commands queued by Modbus clients.

The polling loop uses a connect-read/write-disconnect pattern on every cycle,
releasing the Luxtronik TCP connection immediately after each operation. This
allows the HA BenPru integration and other tools to share port 8889 during the
idle interval between polling cycles. (PROTO-03, PROTO-05)

Write rate limiting (T-03-01): Each register address is limited to one write per
``write_rate_limit`` seconds (default: 60s). Excess writes are dropped with a
WARNING log. This protects the Luxtronik controller's NAND flash from excessive
write wear. (WRITE-03)

Error resilience (T-03-02): Transient upstream errors (network failures, Luxtronik
controller busy) are caught by the polling loop, the cache is marked stale, and the
loop continues. The proxy does not crash on upstream errors — it retries on the next
polling cycle.
"""

from __future__ import annotations

import asyncio
import time

import structlog

from luxtronik2_modbus_proxy.config import ProxyConfig
from luxtronik2_modbus_proxy.luxtronik_client import LuxtronikClient
from luxtronik2_modbus_proxy.register_cache import RegisterCache


class PollingEngine:
    """Async polling engine that reads from Luxtronik and updates the Modbus cache.

    Manages the polling loop lifecycle:
    1. Drains the write queue and forwards validated writes to the controller.
    2. Reads all mapped registers from the controller.
    3. Updates the register cache with fresh values.
    4. Marks the cache as fresh on success, stale on failure.

    A single ``asyncio.Lock`` serializes all Luxtronik TCP access, preventing
    concurrent read and write calls from corrupting the connection. (Pitfall 5)

    Write rate limiting tracks the last write timestamp per register address and
    silently drops writes that arrive too quickly after the previous write.
    (T-03-01, WRITE-03)
    """

    def __init__(
        self,
        config: ProxyConfig,
        client: LuxtronikClient,
        cache: RegisterCache,
        write_queue: asyncio.Queue,
    ) -> None:
        """Initialize the polling engine with its dependencies.

        Args:
            config: Proxy configuration providing ``poll_interval`` and
                ``write_rate_limit`` settings.
            client: Luxtronik client for async read/write operations.
            cache: Register cache to update after each successful read.
            write_queue: Queue of ``(wire_address, values)`` tuples from
                ``ProxyHoldingDataBlock.async_setValues`` for upstream delivery.
        """
        self._config = config
        self._client = client
        self._cache = cache
        self._write_queue = write_queue

        # Serializes all Luxtronik TCP access. Prevents concurrent reads and writes
        # from corrupting the single-connection Luxtronik protocol. (Pitfall 5)
        self._lock = asyncio.Lock()

        # Tracks last write time per register address for rate limiting (T-03-01).
        # Key: wire_address (0-based Modbus address).
        # Value: float timestamp from time.time() of the last accepted write.
        self._write_timestamps: dict[int, float] = {}

        self._log = structlog.get_logger().bind(component="polling_engine")

    async def run_forever(self) -> None:
        """Run the polling loop indefinitely.

        Waits ``poll_interval`` seconds, then executes one complete poll cycle
        (drain writes, read from controller, update cache). Continues regardless
        of transient errors — exceptions in ``_poll_cycle`` are caught, logged,
        and the loop resumes at the next interval.

        This method runs until the task is cancelled (e.g., on SIGTERM).

        Note:
            The sleep happens BEFORE the poll, so the proxy starts serving
            cached values immediately (even if stale) without blocking on an
            initial Luxtronik connection. The first poll occurs after one
            interval.
        """
        self._log.info(
            "polling_started",
            interval=self._config.poll_interval,
        )

        while True:
            # Sleep first, then poll. This allows the Modbus server to start
            # accepting clients immediately without waiting for the first read.
            await asyncio.sleep(self._config.poll_interval)

            try:
                await self._poll_cycle()
            except Exception:
                # Transient errors (network, controller busy) must not crash the proxy.
                # The cache is already marked stale inside _poll_cycle on exception.
                # Log at ERROR so operators can diagnose persistent failures.
                self._log.error(
                    "poll_cycle_failed",
                    exc_info=True,
                )

    async def _poll_cycle(self) -> None:
        """Execute one complete poll cycle: drain writes, read, update cache.

        Acquires the Luxtronik access lock before any network activity to prevent
        concurrent reads and writes from corrupting the single-connection protocol.

        On success, marks the cache fresh. On any exception, marks the cache stale
        and re-raises so ``run_forever`` can log it.

        Raises:
            Exception: Any exception from write or read operations. The cache will
                be marked stale before re-raising.
        """
        async with self._lock:
            self._log.debug("poll_cycle_start")

            try:
                # Step 1: Forward any pending Modbus writes to the controller.
                # Writes happen before reads so Modbus clients see updated values
                # in the same poll cycle that the write was accepted.
                await self._drain_and_write()

                # Step 2: Read fresh values from the Luxtronik controller.
                lux = await self._client.async_read()

                # Step 3: Update the in-memory register cache with the fresh values.
                self._client.update_cache_from_read(lux, self._cache)

                # Step 4: Mark the cache fresh — clients can trust the values.
                self._cache.mark_fresh()

                self._log.debug("poll_cycle_complete")

            except Exception:
                # Mark the cache stale so Modbus clients know values may be outdated.
                # Re-raise for run_forever to log with exc_info.
                self._cache.mark_stale()
                raise

    async def _drain_and_write(self) -> None:
        """Drain the write queue and forward rate-limited writes to the controller.

        Collects all pending writes from the queue, deduplicates by address (keeping
        only the last value for each address), applies per-register rate limiting, and
        forwards the remaining writes to the Luxtronik controller in a single call.

        Rate limiting (T-03-01): Each register address is limited to one write per
        ``write_rate_limit`` seconds. Writes that arrive too quickly after the
        previous write are dropped with a WARNING log. This protects NAND flash.

        If the queue is empty or all writes are rate-limited, no network call is made.
        """
        # Collect all pending writes from the queue (non-blocking drain).
        # Use get_nowait() so this doesn't block the event loop.
        pending: dict[int, list[int]] = {}
        while True:
            try:
                wire_address, values = self._write_queue.get_nowait()
                # Keep only the last value for duplicate addresses.
                pending[wire_address] = values
            except asyncio.QueueEmpty:
                break

        if not pending:
            return

        # Apply rate limiting: filter out writes that are too recent.
        now = time.time()
        param_writes: dict[int, int] = {}

        for address, values in pending.items():
            last_write = self._write_timestamps.get(address, 0.0)
            seconds_since_last = now - last_write

            if seconds_since_last < self._config.write_rate_limit:
                # Rate limit exceeded — drop this write and log a warning.
                seconds_remaining = self._config.write_rate_limit - seconds_since_last
                self._log.warning(
                    "write_rate_limited",
                    register=address,
                    seconds_remaining=round(seconds_remaining, 1),
                )
                continue

            # Rate limit passed — include this write in the upstream batch.
            # Use the first value in the list (FC6 single write provides one value;
            # FC16 multi-write might provide multiple, but we use the first).
            param_writes[address] = values[0]

        if not param_writes:
            return

        # Forward the validated writes to the Luxtronik controller.
        await self._client.async_write(param_writes)

        # Update timestamps for successfully forwarded writes.
        for address, value in param_writes.items():
            self._write_timestamps[address] = now
            self._log.info(
                "write_forwarded",
                register=address,
                value=value,
            )

"""Structured logging configuration for luxtronik2-modbus-proxy.

Configures structlog to produce JSON output in non-TTY environments (Docker/production)
and colorized human-readable output when running in a terminal (development).

Usage:
    from luxtronik2_modbus_proxy.logging_config import configure_logging
    configure_logging("INFO")
    logger = structlog.get_logger()
    logger.info("proxy started", port=502)
"""

from __future__ import annotations

import logging
import os

import structlog


def configure_logging(log_level: str) -> None:
    """Configure structlog for JSON output in production, colored in development.

    Detects whether stdout is a TTY. In a terminal (dev), uses ConsoleRenderer for
    colorized, human-readable output. In Docker/CI (non-TTY), uses JSONRenderer for
    machine-parseable structured logs.

    Args:
        log_level: Logging level string (DEBUG, INFO, WARNING, ERROR).
            Case-insensitive. Defaults to INFO if unrecognized.
    """
    is_tty = os.isatty(1)  # stdout connected to a terminal?

    # Choose renderer based on environment: colored for dev, JSON for production.
    renderer: structlog.types.Processor
    if is_tty:
        renderer = structlog.dev.ConsoleRenderer()
    else:
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=[
            # Merge any context variables bound to the current context.
            structlog.contextvars.merge_contextvars,
            # Add log level string (e.g., "info", "error") to every event.
            structlog.processors.add_log_level,
            # Add ISO 8601 timestamp to every event.
            structlog.processors.TimeStamper(fmt="iso"),
            # Render to JSON (production) or colored text (development).
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper(), logging.INFO)
        ),
        logger_factory=structlog.PrintLoggerFactory(),
    )

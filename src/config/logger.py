"""Centralized logger configuration for the application."""

import os
import sys
from typing import Any  # Add Any

from loguru import logger


def setup_app_logger() -> None:
    """Configure the Loguru logger for standard application runs.

    Reads LOG_FORMAT (json or pretty, defaults to pretty) and
    LOG_LEVEL (defaults to INFO) environment variables.
    """
    log_format = os.getenv("LOG_FORMAT", "pretty").lower()
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    logger.remove()  # Remove existing handlers

    if log_format == "json":
        logger.add(
            sys.stderr,
            level=log_level,
            format="{message}",  # Loguru handles JSON structure with serialize=True
            serialize=True,  # Output logs as JSON strings
            backtrace=True,  # Include traceback in logs
            diagnose=True,  # Include diagnostic information on errors
            enqueue=True,  # Make logging non-blocking
        )
        logger.info(f"Configured JSON logging with level {log_level}.")
    else:
        pretty_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
            # Add {extra} for app pretty logs too?
            " <level>{extra}</level>"
        )
        logger.add(
            sys.stderr,
            level=log_level,
            format=pretty_format,
            colorize=True,
            backtrace=True,
            diagnose=True,
            enqueue=True,
        )
        logger.info(f"Configured Pretty logging with level {log_level}.")


def setup_test_logger() -> None:
    """Configure the Loguru logger specifically for test runs.

    Uses a fixed format (pretty, console) and DEBUG level.
    Intended to be called from test fixtures.
    """
    logger.remove()  # Remove existing handlers (like app handlers)

    # Add {extra} with a specific color tag (e.g., magenta)
    pretty_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        # Append the extra dictionary content wrapped in a specific color tag
        " | <magenta>{extra}</magenta>"
    )

    logger.add(
        # Use a simple print sink for tests, similar to the original test logger
        lambda msg: print(msg),  # type: ignore[reportUnknownLambdaType] # noqa: T201
        level="DEBUG",  # Always DEBUG for tests using this setup
        format=pretty_format,
        colorize=True,
        backtrace=True,
        diagnose=True,
        enqueue=False,  # Don't enqueue for tests, simpler output
        catch=True,
    )


def log_test_step(step: str, **kwargs: Any) -> None:
    """Log a test step with additional context.
        to show them run pytest with --log-debug or use log_debug from project.scripts

    Args:
        step: The test step being executed (e.g., "Arrange", "Act", "Assert")
        **kwargs: Additional context to include in the log
    """
    logger.debug(
        "Test step",
        extra={
            "step": step,
            **kwargs,
        },
    )


# Note: Both functions configure the *same* global logger instance imported from loguru.
# Other modules still just `from loguru import logger`.

"""Logging configuration with Rich handler support.

This module provides a centralized logging setup function that configures
the Python logging system with Rich formatting for attractive console output.
Supports both console and file logging.
"""

import logging
import sys
from pathlib import Path
from typing import Literal

from rich.console import Console
from rich.logging import RichHandler

# Type alias for log levels
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


def setup_logging(
    level: str = "INFO",
    use_rich: bool = True,
    log_file: Path | str | None = None,
    console: Console | None = None
) -> None:
    """Configure the root logger with Rich handler and optional file output.

    Sets up the Python logging system with:
    - Rich formatting for console output (optional)
    - File output to specified path (optional)
    - Configurable log level
    - Timestamp formatting

    Args:
        level: Logging level as string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        use_rich: Whether to use Rich handler for console output (default: True)
        log_file: Optional path to log file for persistent logging
        console: Optional Rich console instance (creates new one if not provided)

    Examples:
        >>> # Basic setup with Rich console output at INFO level
        >>> setup_logging()

        >>> # Debug level with Rich console output
        >>> setup_logging(level="DEBUG")

        >>> # Console and file output
        >>> setup_logging(level="INFO", log_file="game.log")

        >>> # Plain console output (no Rich formatting)
        >>> setup_logging(level="INFO", use_rich=False)

    Note:
        This function modifies the root logger configuration. Call it once
        at application startup before creating any loggers.
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Get root logger and clear any existing handlers
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    root_logger.handlers.clear()

    # Create formatters
    if use_rich:
        # Rich handler has its own formatting
        console_handler = RichHandler(
            console=console,
            show_time=True,
            show_path=True,
            markup=True,
            rich_tracebacks=True,
            tracebacks_show_locals=True
        )
        console_handler.setLevel(numeric_level)
        root_logger.addHandler(console_handler)
    else:
        # Standard console handler with basic formatting
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

    # Add file handler if specified
    if log_file is not None:
        file_path = Path(log_file)
        # Create parent directories if they don't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(file_path, mode="a", encoding="utf-8")
        file_handler.setLevel(numeric_level)
        file_formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    # Log the configuration
    logger = logging.getLogger(__name__)
    logger.debug(f"Logging configured: level={level}, use_rich={use_rich}, log_file={log_file}")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name.

    This is a convenience function that wraps logging.getLogger().
    The logger will inherit the configuration from setup_logging().

    Args:
        name: The name for the logger (typically __name__)

    Returns:
        A configured logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Starting game")
        >>> logger.debug("Player 1 drew card: NumberCard(5)")
    """
    return logging.getLogger(name)

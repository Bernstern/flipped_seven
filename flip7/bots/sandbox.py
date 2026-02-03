"""
Sandbox execution environment for bots with timeout enforcement.

This module provides timeout enforcement for bot decision-making using signal.setitimer.
Bots that exceed their time limit will have a BotTimeout exception raised.

PLATFORM COMPATIBILITY:
    This module requires Unix/Linux signal support and will NOT work on Windows.
    Use WSL (Windows Subsystem for Linux) if running on Windows.
"""

import signal
import sys
from typing import Any, Callable, TypeVar

from flip7.types.errors import BotTimeout

T = TypeVar("T")


def _timeout_handler(signum: int, frame: Any) -> None:
    """
    Signal handler for timeout events.

    This function is called when the alarm signal fires, indicating
    that the bot has exceeded its time limit.

    Args:
        signum: The signal number (SIGALRM)
        frame: The current stack frame

    Raises:
        BotTimeout: Always raised to interrupt bot execution
    """
    raise BotTimeout("Bot exceeded time limit for decision")


def execute_with_sandbox(
    bot_name: str, timeout_seconds: float, func: Callable[..., T], *args: Any
) -> T:
    """
    Execute a bot function with a timeout limit.

    Uses signal.setitimer to enforce a timeout on bot decision-making. If the bot
    function does not return within the specified time limit, a BotTimeout
    exception is raised.

    Note: This implementation uses signal.setitimer which:
    - Only works on Unix-like systems (Linux, macOS)
    - Supports subsecond precision (e.g., 0.25 seconds)
    - Cannot be used in multi-threaded programs
    - Uses SIGALRM signal

    Args:
        bot_name: The name of the bot (for error reporting)
        timeout_seconds: Maximum time allowed in seconds (supports subsecond precision)
        func: The function to execute
        *args: Arguments to pass to the function

    Returns:
        The return value from the function

    Raises:
        BotTimeout: If the function exceeds the time limit
        RuntimeError: If running on an unsupported platform (Windows)
        Any other exception raised by the function
    """
    # Check platform compatibility
    if sys.platform.startswith('win'):
        raise RuntimeError(
            "Bot sandbox execution is not supported on Windows.\n\n"
            "The timeout system uses Unix signal handling (signal.SIGALRM) which is not available on Windows.\n\n"
            "Solutions:\n"
            "  1. Use WSL (Windows Subsystem for Linux) - Recommended\n"
            "     - Install WSL: https://docs.microsoft.com/en-us/windows/wsl/install\n"
            "     - Run the tournament from within WSL\n\n"
            "  2. Use a Linux virtual machine or Docker container\n\n"
            "  3. Run on a Linux or macOS system"
        )

    # Store the old signal handler to restore it later
    old_handler = signal.signal(signal.SIGALRM, _timeout_handler)

    try:
        # Set the timer with subsecond precision
        signal.setitimer(signal.ITIMER_REAL, timeout_seconds)

        # Execute the function
        result = func(*args)

        # Cancel the timer if function completed in time
        signal.setitimer(signal.ITIMER_REAL, 0)

        return result

    except BotTimeout:
        # Re-raise BotTimeout with bot name context
        raise BotTimeout(f"Bot '{bot_name}' exceeded time limit of {timeout_seconds}s")

    finally:
        # Always cancel the timer and restore the old handler
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old_handler)

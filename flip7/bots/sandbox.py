"""
Sandbox execution environment for bots with timeout enforcement.

This module provides timeout enforcement for bot decision-making using signal.alarm.
Bots that exceed their time limit will have a BotTimeout exception raised.
"""

import signal
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

    Uses signal.alarm to enforce a timeout on bot decision-making. If the bot
    function does not return within the specified time limit, a BotTimeout
    exception is raised.

    Note: This implementation uses signal.alarm which:
    - Only works on Unix-like systems (Linux, macOS)
    - Only supports integer second timeouts
    - Cannot be used in multi-threaded programs
    - Uses SIGALRM signal

    Args:
        bot_name: The name of the bot (for error reporting)
        timeout_seconds: Maximum time allowed in seconds (will be rounded up to int)
        func: The function to execute
        *args: Arguments to pass to the function

    Returns:
        The return value from the function

    Raises:
        BotTimeout: If the function exceeds the time limit
        Any other exception raised by the function
    """
    # Convert timeout to integer seconds (round up)
    timeout_int = int(timeout_seconds) if timeout_seconds == int(timeout_seconds) else int(timeout_seconds) + 1

    # Store the old signal handler to restore it later
    old_handler = signal.signal(signal.SIGALRM, _timeout_handler)

    try:
        # Set the alarm
        signal.alarm(timeout_int)

        # Execute the function
        result = func(*args)

        # Cancel the alarm if function completed in time
        signal.alarm(0)

        return result

    except BotTimeout:
        # Re-raise BotTimeout with bot name context
        raise BotTimeout(f"Bot '{bot_name}' exceeded time limit of {timeout_seconds}s")

    finally:
        # Always cancel the alarm and restore the old handler
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)

"""Configuration validation for tournament settings.

This module validates tournament configuration to catch errors early with
helpful error messages before tournaments start.
"""

import os
import sys
from pathlib import Path
from typing import Any


class ConfigurationError(Exception):
    """Raised when configuration validation fails."""
    pass


def validate_tournament_config(
    games_per_matchup_h2h: int,
    games_per_matchup_all: int,
    bot_timeout_seconds: float,
    output_dir_h2h: Path,
    output_dir_all: Path,
) -> None:
    """Validate tournament configuration parameters.

    Args:
        games_per_matchup_h2h: Number of games for head-to-head matchups
        games_per_matchup_all: Number of games for all-vs-all matchups
        bot_timeout_seconds: Bot execution timeout in seconds
        output_dir_h2h: Output directory for head-to-head results
        output_dir_all: Output directory for all-vs-all results

    Raises:
        ConfigurationError: If any validation check fails with helpful message
    """
    errors = []

    # Validate GAMES_PER_MATCHUP_HEAD_TO_HEAD
    if not isinstance(games_per_matchup_h2h, int):
        errors.append(
            f"GAMES_PER_MATCHUP_HEAD_TO_HEAD must be an integer, got {type(games_per_matchup_h2h).__name__}"
        )
    elif games_per_matchup_h2h <= 0:
        errors.append(
            f"GAMES_PER_MATCHUP_HEAD_TO_HEAD must be > 0, got {games_per_matchup_h2h}\n"
            "  Suggestion: Use at least 100 for testing, 1000+ for meaningful results"
        )
    elif games_per_matchup_h2h > 100_000_000:
        errors.append(
            f"GAMES_PER_MATCHUP_HEAD_TO_HEAD is very large ({games_per_matchup_h2h:,})\n"
            "  This may take a very long time to run. Consider starting with 100,000-1,000,000."
        )

    # Validate GAMES_PER_MATCHUP_ALL_VS_ALL
    if not isinstance(games_per_matchup_all, int):
        errors.append(
            f"GAMES_PER_MATCHUP_ALL_VS_ALL must be an integer, got {type(games_per_matchup_all).__name__}"
        )
    elif games_per_matchup_all <= 0:
        errors.append(
            f"GAMES_PER_MATCHUP_ALL_VS_ALL must be > 0, got {games_per_matchup_all}\n"
            "  Suggestion: Use at least 100 for testing, 1000+ for meaningful results"
        )
    elif games_per_matchup_all > 100_000_000:
        errors.append(
            f"GAMES_PER_MATCHUP_ALL_VS_ALL is very large ({games_per_matchup_all:,})\n"
            "  This may take a very long time to run. Consider starting with 100,000-1,000,000."
        )

    # Validate BOT_TIMEOUT_SECONDS
    if not isinstance(bot_timeout_seconds, (int, float)):
        errors.append(
            f"BOT_TIMEOUT_SECONDS must be a number, got {type(bot_timeout_seconds).__name__}"
        )
    elif bot_timeout_seconds <= 0:
        errors.append(
            f"BOT_TIMEOUT_SECONDS must be > 0, got {bot_timeout_seconds}\n"
            "  Suggestion: Use 0.1-5.0 seconds (1.0 is typical)"
        )
    elif bot_timeout_seconds > 300:
        errors.append(
            f"BOT_TIMEOUT_SECONDS is very large ({bot_timeout_seconds} seconds)\n"
            "  Timeouts > 300 seconds (5 minutes) are unreasonable.\n"
            "  Suggestion: Use 0.1-5.0 seconds (1.0 is typical)"
        )
    elif bot_timeout_seconds < 0.01:
        errors.append(
            f"BOT_TIMEOUT_SECONDS is very small ({bot_timeout_seconds} seconds)\n"
            "  Timeouts < 0.01 seconds may cause legitimate bots to timeout.\n"
            "  Suggestion: Use at least 0.1 seconds"
        )

    # Validate output directories are writable
    for output_dir, name in [
        (output_dir_h2h, "OUTPUT_DIR_HEAD_TO_HEAD"),
        (output_dir_all, "OUTPUT_DIR_ALL_VS_ALL")
    ]:
        if not isinstance(output_dir, Path):
            errors.append(
                f"{name} must be a Path object, got {type(output_dir).__name__}\n"
                f"  Use: {name} = Path('./your_directory')"
            )
            continue

        # Try to create parent directory if it doesn't exist
        try:
            output_dir.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            errors.append(
                f"{name} parent directory cannot be created: {output_dir.parent}\n"
                f"  Error: {e}"
            )
            continue

        # Check if parent directory is writable
        if not os.access(output_dir.parent, os.W_OK):
            errors.append(
                f"{name} parent directory is not writable: {output_dir.parent}\n"
                f"  Check directory permissions or choose a different location"
            )

    # Raise all errors together with clear formatting
    if errors:
        error_message = "\n\n".join([
            "Configuration validation failed:",
            "",
            *[f"  ERROR: {error}" for error in errors],
            "",
            "Please fix these issues in tournament_config.py and try again."
        ])
        raise ConfigurationError(error_message)


def check_platform_compatibility() -> None:
    """Check if the platform supports signal-based timeouts.

    Raises:
        ConfigurationError: If running on an unsupported platform (Windows)
    """
    if sys.platform.startswith('win'):
        raise ConfigurationError(
            "Windows is not supported for bot sandboxing.\n\n"
            "The bot timeout system uses Unix signal handling (signal.SIGALRM) which is not available on Windows.\n\n"
            "Solutions:\n"
            "  1. Use WSL (Windows Subsystem for Linux) - Recommended\n"
            "     - Install WSL: https://docs.microsoft.com/en-us/windows/wsl/install\n"
            "     - Run the tournament from within WSL\n\n"
            "  2. Use a Linux virtual machine or Docker container\n\n"
            "  3. Run on a Linux or macOS system\n\n"
            "For more information on signal limitations, see:\n"
            "https://docs.python.org/3/library/signal.html#note-on-signal-handlers-and-exceptions"
        )

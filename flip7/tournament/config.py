"""
Tournament configuration for Flip 7.

This module defines the configuration dataclass for running tournaments with
parallel execution of matches.
"""

import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from flip7.types.errors import InvalidConfiguration

if TYPE_CHECKING:
    from flip7.bots.base import BaseBot


@dataclass
class TournamentConfig:
    """
    Configuration for a tournament.

    Attributes:
        tournament_name: Unique identifier for this tournament
        players_per_game: Number of players in each game (2, 3, or 4)
        best_of_n: Number of games per match (must be odd for clear winner)
        bot_classes: List of bot classes to compete in the tournament
        bot_timeout_seconds: Maximum time allowed for each bot decision
        output_dir: Directory where results and replays will be saved
        save_replays: Whether to save game replays for later analysis
        max_workers: Maximum number of parallel workers (None = CPU count)
        tournament_seed: Random seed for reproducibility (None = random)
    """

    tournament_name: str
    players_per_game: int
    best_of_n: int
    bot_classes: list[type["BaseBot"]]
    bot_timeout_seconds: float
    output_dir: Path
    save_replays: bool
    max_workers: int | None = None
    tournament_seed: int | None = None

    def __post_init__(self) -> None:
        """Validate configuration parameters."""
        if self.players_per_game not in (2, 3, 4):
            raise ValueError(f"players_per_game must be 2, 3, or 4, got {self.players_per_game}")

        if self.best_of_n < 1 or self.best_of_n % 2 == 0:
            raise ValueError(f"best_of_n must be a positive odd number, got {self.best_of_n}")

        if len(self.bot_classes) < self.players_per_game:
            raise ValueError(
                f"Need at least {self.players_per_game} bots for "
                f"{self.players_per_game}-player games, got {len(self.bot_classes)}"
            )

        if self.bot_timeout_seconds <= 0:
            raise ValueError(
                f"bot_timeout_seconds must be positive, got {self.bot_timeout_seconds}"
            )

        if self.max_workers is not None and self.max_workers < 1:
            raise ValueError(f"max_workers must be positive or None, got {self.max_workers}")

        # Check for duplicate bot class names
        bot_names = [bot_class.__name__ for bot_class in self.bot_classes]
        duplicate_names = [name for name in set(bot_names) if bot_names.count(name) > 1]
        if duplicate_names:
            raise InvalidConfiguration(
                f"Duplicate bot class names found: {', '.join(sorted(duplicate_names))}. "
                "All bot classes must have unique names."
            )

        # Validate output directory is writable
        self._validate_output_directory()

    def _validate_output_directory(self) -> None:
        """
        Validate that the output directory is writable and has sufficient disk space.

        Raises:
            InvalidConfiguration: If directory cannot be created or is not writable
        """
        # Ensure output directory exists
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise InvalidConfiguration(
                f"Cannot create output directory '{self.output_dir}': {e}\n"
                f"Suggestion: Check parent directory exists and you have write permissions."
            ) from e

        # Check if directory is writable
        if not os.access(self.output_dir, os.W_OK):
            raise InvalidConfiguration(
                f"Output directory '{self.output_dir}' is not writable.\n"
                f"Suggestion: Check directory permissions (need write access)."
            )

        # Check available disk space (warn if less than 100MB)
        try:
            stat = shutil.disk_usage(self.output_dir)
            available_mb = stat.free / (1024 * 1024)

            if available_mb < 10:
                raise InvalidConfiguration(
                    f"Insufficient disk space in '{self.output_dir}': {available_mb:.1f}MB available.\n"
                    f"Suggestion: Free up disk space or choose a different output directory."
                )
            elif available_mb < 100:
                # This is just a warning, not an error - we'll let it proceed
                import warnings
                warnings.warn(
                    f"Low disk space in '{self.output_dir}': {available_mb:.1f}MB available. "
                    f"Consider freeing up space if running large tournaments.",
                    UserWarning
                )
        except OSError:
            # If we can't check disk space, continue anyway
            # (some filesystems don't support this)
            pass

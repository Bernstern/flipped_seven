"""
Round-robin matchup generation for tournaments.

This module provides functions to generate all possible matchups for a
round-robin tournament with configurable player counts.
"""

from itertools import combinations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flip7.bots.base import BaseBot


def generate_round_robin_matchups(
    bot_classes: list[type["BaseBot"]], players_per_game: int
) -> list[tuple[str, ...]]:
    """
    Generate all possible round-robin matchups.

    Creates all unique combinations of bots for the given number of players
    per game. The matchups are deterministically ordered.

    Args:
        bot_classes: List of bot classes to generate matchups for
        players_per_game: Number of players in each game (2, 3, or 4)

    Returns:
        List of matchup tuples, where each tuple contains player IDs (bot class names)

    Raises:
        ValueError: If players_per_game is invalid or there are too few bots

    Example:
        >>> bot_classes = [BotA, BotB, BotC]
        >>> generate_round_robin_matchups(bot_classes, 2)
        [('BotA', 'BotB'), ('BotA', 'BotC'), ('BotB', 'BotC')]
    """
    if players_per_game not in (2, 3, 4):
        raise ValueError(f"players_per_game must be 2, 3, or 4, got {players_per_game}")

    if len(bot_classes) < players_per_game:
        raise ValueError(
            f"Need at least {players_per_game} bots for "
            f"{players_per_game}-player games, got {len(bot_classes)}"
        )

    # Extract bot class names for player IDs
    bot_names = [bot_class.__name__ for bot_class in bot_classes]

    # Generate all combinations
    matchups = list(combinations(bot_names, players_per_game))

    return matchups


def count_matchups(num_bots: int, players_per_game: int) -> int:
    """
    Calculate the number of matchups for a round-robin tournament.

    Uses the binomial coefficient: C(n, k) = n! / (k! * (n-k)!)

    Args:
        num_bots: Total number of bots
        players_per_game: Number of players per game

    Returns:
        Total number of unique matchups

    Example:
        >>> count_matchups(4, 2)  # 4 bots, 2 players per game
        6
        >>> count_matchups(4, 3)  # 4 bots, 3 players per game
        4
    """
    if players_per_game not in (2, 3, 4):
        raise ValueError(f"players_per_game must be 2, 3, or 4, got {players_per_game}")

    if num_bots < players_per_game:
        return 0

    # Calculate binomial coefficient
    from math import factorial

    return factorial(num_bots) // (factorial(players_per_game) * factorial(num_bots - players_per_game))

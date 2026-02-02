"""
Match execution for best-of-N series.

This module provides functionality to execute a best-of-N match between
a set of bots, running multiple games until one bot wins the majority.
"""

import uuid
from pathlib import Path
from typing import TYPE_CHECKING

from flip7.core.game_engine import GameEngine
from flip7.tournament.results import GameResult, MatchResult

if TYPE_CHECKING:
    from flip7.bots.base import BaseBot
    from flip7.tournament.config import TournamentConfig


def execute_match(
    config: "TournamentConfig",
    player_ids: tuple[str, ...],
    bots: dict[str, "BaseBot"],
    match_id: str,
) -> MatchResult:
    """
    Execute a best-of-N match between the given bots.

    Runs games sequentially until one bot wins the majority (best_of_n // 2 + 1).
    Each game is independent with its own random seed.

    Args:
        config: Tournament configuration
        player_ids: Tuple of player IDs (bot names) in this match
        bots: Dictionary mapping player IDs to bot instances
        match_id: Unique identifier for this match

    Returns:
        MatchResult containing game results and overall winner

    Example:
        >>> config = TournamentConfig(...)
        >>> bots = {'BotA': BotA('BotA'), 'BotB': BotB('BotB')}
        >>> player_ids = ('BotA', 'BotB')
        >>> result = execute_match(config, player_ids, bots, 'match_001')
        >>> print(f"Winner: {result.winner}")
    """
    games: list[GameResult] = []
    win_counts: dict[str, int] = {pid: 0 for pid in player_ids}
    wins_needed = config.best_of_n // 2 + 1

    game_number = 0

    while True:
        game_number += 1

        # Generate unique game ID
        game_id = f"{match_id}_game_{game_number}"

        # Determine seed for this game if tournament seed is set
        game_seed = None
        if config.tournament_seed is not None:
            game_seed = config.tournament_seed + hash(game_id) % 1000000

        # Set up event log path if saving replays
        if config.save_replays:
            event_log_path = (
                config.output_dir / "replays" / match_id / f"{game_id}.jsonl"
            )
        else:
            # Use a temporary path that won't be saved
            event_log_path = config.output_dir / ".tmp" / f"{game_id}.jsonl"

        # Create game engine
        from typing import cast
        from flip7.types import Bot

        engine = GameEngine(
            game_id=game_id,
            player_ids=list(player_ids),
            bots=cast(dict[str, Bot], bots),  # BaseBot implements Bot protocol
            event_log_path=event_log_path,
            seed=game_seed,
            bot_timeout=config.bot_timeout_seconds,
        )

        # Execute game
        final_state = engine.execute_game()

        # Record game result
        game_result = GameResult(
            game_id=game_id,
            winner=final_state.winner or "",  # Should always have winner
            final_scores=final_state.scores,
            rounds_played=final_state.current_round,
        )
        games.append(game_result)

        # Update win counts
        if final_state.winner:
            win_counts[final_state.winner] += 1

            # Check if this bot has won the match
            if win_counts[final_state.winner] >= wins_needed:
                match_result = MatchResult(
                    match_id=match_id,
                    player_ids=player_ids,
                    games=games,
                    winner=final_state.winner,
                    win_counts=win_counts,
                )
                return match_result

    # This should never be reached, but satisfy type checker
    raise RuntimeError("Match execution ended without a winner")


def create_bot_instances(
    bot_classes: list[type["BaseBot"]], player_ids: tuple[str, ...]
) -> dict[str, "BaseBot"]:
    """
    Create bot instances for a match.

    Each bot is instantiated with the corresponding player ID as its name.

    Args:
        bot_classes: List of bot classes (same length as player_ids)
        player_ids: Tuple of player IDs (bot class names)

    Returns:
        Dictionary mapping player IDs to bot instances

    Raises:
        ValueError: If the number of bot classes doesn't match player IDs
    """
    if len(bot_classes) != len(player_ids):
        raise ValueError(
            f"Number of bot classes ({len(bot_classes)}) must match "
            f"number of player IDs ({len(player_ids)})"
        )

    # Create bot instances
    bots: dict[str, BaseBot] = {}
    for bot_class, player_id in zip(bot_classes, player_ids):
        bots[player_id] = bot_class(player_id)

    return bots


def prepare_match(
    config: "TournamentConfig",
    player_ids: tuple[str, ...],
) -> tuple[dict[str, "BaseBot"], str]:
    """
    Prepare a match by creating bot instances and generating a match ID.

    Args:
        config: Tournament configuration
        player_ids: Tuple of player IDs (bot class names)

    Returns:
        Tuple of (bots dictionary, match_id)
    """
    # Create match ID
    match_id = f"match_{uuid.uuid4().hex[:8]}_{'_vs_'.join(player_ids)}"

    # Find bot classes for these player IDs
    bot_classes_for_match: list[type[BaseBot]] = []
    for player_id in player_ids:
        # Find the bot class with this name
        bot_class = next(
            (bc for bc in config.bot_classes if bc.__name__ == player_id), None
        )
        if bot_class is None:
            raise ValueError(f"No bot class found with name {player_id}")
        bot_classes_for_match.append(bot_class)

    # Create bot instances
    bots = create_bot_instances(bot_classes_for_match, player_ids)

    return bots, match_id

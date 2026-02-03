"""
Tournament system for Flip 7.

This module provides a complete tournament system with parallel execution,
round-robin matchups, and comprehensive results tracking.

Main Components:
    - TournamentConfig: Configuration for tournament execution
    - TournamentOrchestrator: Parallel tournament execution
    - TournamentResults: Results aggregation and export
    - MatchResult: Individual match results
    - GameResult: Individual game results

Example:
    >>> from pathlib import Path
    >>> from flip7.tournament import TournamentConfig, TournamentOrchestrator
    >>> from flip7.bots import RandomBot, ScaredyBot
    >>>
    >>> config = TournamentConfig(
    ...     tournament_name="test_tournament",
    ...     players_per_game=2,
    ...     best_of_n=3,
    ...     bot_classes=[RandomBot, ScaredyBot],
    ...     bot_timeout_seconds=1.0,
    ...     output_dir=Path("./results"),
    ...     save_replays=True,
    ...     max_workers=4,
    ...     tournament_seed=42,
    ... )
    >>>
    >>> orchestrator = TournamentOrchestrator(config)
    >>> results = orchestrator.run_tournament()
    >>>
    >>> print(f"Winner: {results.get_leaderboard()[0][0]}")
"""

from flip7.tournament.config import TournamentConfig
from flip7.tournament.match import execute_match, prepare_match
from flip7.tournament.orchestrator import TournamentOrchestrator
from flip7.tournament.results import (
    BotStatistics,
    GameResult,
    MatchResult,
    TournamentResults,
)
from flip7.tournament.round_robin import (
    count_matchups,
    generate_round_robin_matchups,
)

__all__ = [
    "TournamentConfig",
    "TournamentOrchestrator",
    "TournamentResults",
    "MatchResult",
    "GameResult",
    "BotStatistics",
    "execute_match",
    "prepare_match",
    "generate_round_robin_matchups",
    "count_matchups",
]

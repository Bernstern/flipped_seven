"""
Tournament results aggregation and export.

This module defines data structures for tournament results and provides
functionality to export results to JSON format.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class GameResult:
    """
    Result of a single game.

    Attributes:
        game_id: Unique identifier for the game
        winner: Name of the winning bot
        final_scores: Mapping of bot names to final scores
        rounds_played: Number of rounds in the game
    """

    game_id: str
    winner: str
    final_scores: dict[str, int]
    rounds_played: int


@dataclass
class MatchResult:
    """
    Result of a best-of-N match between specific bots.

    Attributes:
        match_id: Unique identifier for the match
        player_ids: Tuple of player IDs in this match
        games: List of game results
        winner: Name of the winning bot
        win_counts: Mapping of bot names to number of games won
    """

    match_id: str
    player_ids: tuple[str, ...]
    games: list[GameResult]
    winner: str
    win_counts: dict[str, int]


@dataclass
class BotStatistics:
    """
    Aggregated statistics for a single bot across all matches.

    Attributes:
        bot_name: Name of the bot class
        matches_played: Total number of matches played
        matches_won: Number of matches won
        matches_lost: Number of matches lost
        games_played: Total number of individual games played
        games_won: Number of individual games won
        games_lost: Number of individual games lost
        total_points_scored: Sum of all points across all games
        average_points_per_game: Mean points scored per game
        win_rate: Percentage of matches won
    """

    bot_name: str
    matches_played: int = 0
    matches_won: int = 0
    matches_lost: int = 0
    games_played: int = 0
    games_won: int = 0
    games_lost: int = 0
    total_points_scored: int = 0
    average_points_per_game: float = 0.0
    win_rate: float = 0.0


@dataclass
class TournamentResults:
    """
    Complete results of a tournament.

    Attributes:
        tournament_name: Name of the tournament
        config_summary: Summary of tournament configuration
        matches: List of all match results
        bot_statistics: Statistics for each bot
        total_matches: Total number of matches completed
        total_games: Total number of games played
    """

    tournament_name: str
    config_summary: dict[str, Any]
    matches: list[MatchResult] = field(default_factory=list)
    bot_statistics: dict[str, BotStatistics] = field(default_factory=dict)
    total_matches: int = 0
    total_games: int = 0

    def add_match(self, match: MatchResult) -> None:
        """
        Add a match result and update statistics.

        Args:
            match: The match result to add
        """
        self.matches.append(match)
        self.total_matches += 1
        self.total_games += len(match.games)

        # Update bot statistics
        for player_id in match.player_ids:
            if player_id not in self.bot_statistics:
                self.bot_statistics[player_id] = BotStatistics(bot_name=player_id)

            stats = self.bot_statistics[player_id]
            stats.matches_played += 1

            if match.winner == player_id:
                stats.matches_won += 1
            else:
                stats.matches_lost += 1

            # Update game-level statistics
            for game in match.games:
                stats.games_played += 1
                if game.winner == player_id:
                    stats.games_won += 1
                else:
                    stats.games_lost += 1

                stats.total_points_scored += game.final_scores.get(player_id, 0)

        # Recalculate derived statistics
        self._recalculate_statistics()

    def _recalculate_statistics(self) -> None:
        """Recalculate derived statistics for all bots."""
        for stats in self.bot_statistics.values():
            if stats.games_played > 0:
                stats.average_points_per_game = stats.total_points_scored / stats.games_played
            else:
                stats.average_points_per_game = 0.0

            if stats.matches_played > 0:
                stats.win_rate = (stats.matches_won / stats.matches_played) * 100
            else:
                stats.win_rate = 0.0

    def to_dict(self) -> dict[str, Any]:
        """
        Convert results to a dictionary for JSON serialization.

        Returns:
            Dictionary representation of tournament results
        """
        return {
            "tournament_name": self.tournament_name,
            "config_summary": self.config_summary,
            "total_matches": self.total_matches,
            "total_games": self.total_games,
            "bot_statistics": {
                bot_name: {
                    "bot_name": stats.bot_name,
                    "matches_played": stats.matches_played,
                    "matches_won": stats.matches_won,
                    "matches_lost": stats.matches_lost,
                    "games_played": stats.games_played,
                    "games_won": stats.games_won,
                    "games_lost": stats.games_lost,
                    "total_points_scored": stats.total_points_scored,
                    "average_points_per_game": round(stats.average_points_per_game, 2),
                    "win_rate": round(stats.win_rate, 2),
                }
                for bot_name, stats in self.bot_statistics.items()
            },
            "matches": [
                {
                    "match_id": match.match_id,
                    "player_ids": list(match.player_ids),
                    "winner": match.winner,
                    "win_counts": match.win_counts,
                    "games": [
                        {
                            "game_id": game.game_id,
                            "winner": game.winner,
                            "final_scores": game.final_scores,
                            "rounds_played": game.rounds_played,
                        }
                        for game in match.games
                    ],
                }
                for match in self.matches
            ],
        }

    def export_to_json(self, output_path: Path) -> None:
        """
        Export results to a JSON file.

        Args:
            output_path: Path where the JSON file should be saved
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    def get_leaderboard(self) -> list[tuple[str, BotStatistics]]:
        """
        Get bots ranked by win rate.

        Returns:
            List of (bot_name, statistics) tuples sorted by win rate descending
        """
        return sorted(
            self.bot_statistics.items(), key=lambda x: (x[1].win_rate, x[1].matches_won), reverse=True
        )

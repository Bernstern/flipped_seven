"""Sample tournament configuration file.

This file demonstrates how to configure a tournament for the Flip 7 CLI.
Use this as a template for your own tournament configurations.

Usage:
    flip7 run-tournament examples/sample_tournament_config.py
"""

from flip7.bots.conservative_bot import ConservativeBot
from flip7.bots.random_bot import RandomBot

# This is a placeholder for the actual TournamentConfig class
# which will be implemented in the tournament module
class TournamentConfig:
    """Tournament configuration (placeholder).

    In the actual implementation, this will be imported from
    flip7.tournament.config and will include fields like:
    - bots: List of bot classes to compete
    - games_per_matchup: Number of games between each pair of bots
    - players_per_game: Number of players in each game
    - max_rounds: Maximum rounds per game before declaring a draw
    - timeout_seconds: Time limit for bot decisions
    """

    def __init__(
        self,
        bots: list[type],
        games_per_matchup: int = 5,
        players_per_game: int = 2,
        max_rounds: int = 100,
        timeout_seconds: float = 1.0,
    ):
        self.bots = bots
        self.games_per_matchup = games_per_matchup
        self.players_per_game = players_per_game
        self.max_rounds = max_rounds
        self.timeout_seconds = timeout_seconds

    def __repr__(self) -> str:
        return (
            f"TournamentConfig("
            f"bots={[b.__name__ for b in self.bots]}, "
            f"games_per_matchup={self.games_per_matchup}, "
            f"players_per_game={self.players_per_game}, "
            f"max_rounds={self.max_rounds}, "
            f"timeout_seconds={self.timeout_seconds})"
        )


# Tournament configuration
config = TournamentConfig(
    bots=[
        RandomBot,
        ConservativeBot,
    ],
    games_per_matchup=5,
    players_per_game=2,
    max_rounds=100,
    timeout_seconds=1.0,
)

# You can also add multiple configurations if needed
config_quick = TournamentConfig(
    bots=[RandomBot, ConservativeBot],
    games_per_matchup=3,
    players_per_game=2,
    max_rounds=50,
    timeout_seconds=0.5,
)

config_multiplayer = TournamentConfig(
    bots=[RandomBot, RandomBot, ConservativeBot],
    games_per_matchup=3,
    players_per_game=3,
    max_rounds=100,
    timeout_seconds=1.0,
)

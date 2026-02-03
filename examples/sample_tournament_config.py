"""Sample tournament configuration file.

This file demonstrates how to configure tournaments for the Flip 7 CLI.
Use this as a template for your own tournament configurations.

Note: The main CLI (`uv run flip7`) uses tournament_config.py in the root directory.
This example shows alternative configuration patterns you can use programmatically.
"""

from pathlib import Path
from flip7.bots import ConservativeBot, Hit17Bot, RandomBot
from flip7.tournament.config import TournamentConfig

# Example 1: Simple head-to-head configuration
config_simple = TournamentConfig(
    tournament_name="Simple Test",
    players_per_game=2,
    best_of_n=5,
    bot_classes=[RandomBot, ConservativeBot],
    bot_timeout_seconds=1.0,
    output_dir=Path("./tournament_results_simple"),
    save_replays=False,
    max_workers=None,  # Auto-detect CPU count
    tournament_seed=42,
)

# Example 2: Quick test configuration (for development)
config_quick = TournamentConfig(
    tournament_name="Quick Test",
    players_per_game=2,
    best_of_n=11,  # Small odd number for quick testing
    bot_classes=[RandomBot, ConservativeBot],
    bot_timeout_seconds=1.0,
    output_dir=Path("./tournament_results_quick"),
    save_replays=False,
    max_workers=1,  # Single worker for debugging
    tournament_seed=42,
)

# Example 3: Multiplayer configuration
config_multiplayer = TournamentConfig(
    tournament_name="Multiplayer Test",
    players_per_game=3,  # Three bots per game
    best_of_n=101,  # Must be odd number
    bot_classes=[RandomBot, ConservativeBot, Hit17Bot],
    bot_timeout_seconds=1.0,
    output_dir=Path("./tournament_results_multiplayer"),
    save_replays=False,
    max_workers=None,
    tournament_seed=42,
)

# Example 4: Large tournament with replay saving (for analysis)
config_with_replays = TournamentConfig(
    tournament_name="Analysis Run",
    players_per_game=2,
    best_of_n=1001,  # Must be odd number
    bot_classes=[RandomBot, ConservativeBot, Hit17Bot],
    bot_timeout_seconds=1.0,
    output_dir=Path("./tournament_results_analysis"),
    save_replays=True,  # Enable replay saving for behavioral analysis
    max_workers=None,
    tournament_seed=42,
)

# Default config for programmatic use
config = config_simple

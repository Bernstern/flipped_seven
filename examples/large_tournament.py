"""Large-scale tournament configuration for extensive bot testing.

This tournament runs 100,000+ matches to gather comprehensive statistics
on bot performance and behavior patterns.

Usage:
    1. Copy this file to tournament_config.py in the root directory:
       cp examples/large_tournament.py tournament_config.py

    2. Run the tournament:
       uv run flip7

Alternatively, you can use this configuration programmatically in your own scripts
by importing the config object and passing it to the tournament runner.
"""

from pathlib import Path

from flip7.bots import ScaredyBot, RandomBot
from flip7.tournament.config import TournamentConfig

# Configuration for 100,000+ matches
config = TournamentConfig(
    tournament_name="Large Scale Bot Analysis - 100K Matches",

    # Game setup
    players_per_game=2,  # 2-player games for simplicity

    # Best-of-N determines matches per matchup
    # With 2 bots and best_of_200001, we get ~100,000 games
    # (each matchup runs until one bot wins 100,001 games)
    best_of_n=200001,  # Odd number: 100,001 wins needed = ~100,000-200,000 games

    # Bots to test
    # Add your custom bots here for testing
    bot_classes=[
        RandomBot,
        ScaredyBot,
        # Add more bots here:
        # MyCustomBot,
        # AggressiveBot,
        # SmartBot,
    ],

    # Performance settings
    bot_timeout_seconds=5.0,
    max_workers=8,  # Adjust based on CPU cores (recommend CPU count - 1)

    # Output configuration
    output_dir=Path("./tournament_results_100k"),
    save_replays=False,  # Disable to save disk space (100k games = lots of data)

    # Reproducibility
    tournament_seed=42,
)

# Print configuration summary
if __name__ == "__main__":
    print("=" * 80)
    print("LARGE TOURNAMENT CONFIGURATION")
    print("=" * 80)
    print(f"Tournament: {config.tournament_name}")
    print(f"Bots: {[b.__name__ for b in config.bot_classes]}")
    print(f"Players per game: {config.players_per_game}")
    print(f"Best of: {config.best_of_n:,}")
    print(f"Expected games: ~{(config.best_of_n // 2):,}-{config.best_of_n:,}")
    print(f"Parallel workers: {config.max_workers}")
    print(f"Save replays: {config.save_replays}")
    print(f"Output: {config.output_dir}")
    print("=" * 80)
    print()
    print("To run this configuration:")
    print("  1. Copy to root: cp examples/large_tournament.py tournament_config.py")
    print("  2. Run tournament: uv run flip7")
    print()
    print("Estimated time (8 workers):")
    print("  - ~2-5 seconds per game")
    print("  - 100,000 games / 8 workers = 12,500 games per worker")
    print("  - 12,500 * 3 seconds = ~10.5 hours")
    print()
    print("Note: For the dual-tournament system used by the CLI,")
    print("      edit the root tournament_config.py and set:")
    print("      GAMES_PER_MATCHUP_HEAD_TO_HEAD = 100_000")
    print("      GAMES_PER_MATCHUP_ALL_VS_ALL = 1_000_000")
    print("=" * 80)

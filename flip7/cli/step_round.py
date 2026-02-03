#!/usr/bin/env python3
"""Command-line tool to step through a round turn-by-turn for debugging.

Usage:
    uv run flip7-step [bot1_class] [bot2_class] [OPTIONS]

Examples:
    # Default: RandomBot vs ConservativeBot
    uv run flip7-step

    # Specify bots
    uv run flip7-step RandomBot ConservativeBot

    # With custom seed
    uv run flip7-step RandomBot ConservativeBot --seed 42

    # Simulate mid-game scenario (bot1 has 100 points, bot2 has 150 points, round 8)
    uv run flip7-step RandomBot ConservativeBot --scores 100,150 --round 8

    # Custom bot from module
    uv run flip7-step my_bot.MyBot ConservativeBot
"""

import argparse
import importlib
import sys
from typing import Any, Type

from flip7.bots import ConservativeBot, RandomBot
from flip7.bots.base import BaseBot
from flip7.types.bot_interface import Bot
from flip7.utils.round_stepper import RoundStepper

# Built-in bots
BUILTIN_BOTS: dict[str, Type[BaseBot]] = {
    "RandomBot": RandomBot,
    "ConservativeBot": ConservativeBot,
}


def load_bot_class(spec: str) -> Type[BaseBot]:
    """Load a bot class from a specification string.

    Args:
        spec: Either a builtin bot name (e.g., "RandomBot") or
              a module path (e.g., "my_bot.MyBot")

    Returns:
        The bot class

    Raises:
        ValueError: If the bot cannot be loaded
    """
    # Check if it's a builtin bot
    if spec in BUILTIN_BOTS:
        return BUILTIN_BOTS[spec]

    # Try to load from module path
    if "." not in spec:
        raise ValueError(
            f"Bot '{spec}' not found. Available builtin bots: {', '.join(BUILTIN_BOTS.keys())}\n"
            f"For custom bots, use module.ClassName format (e.g., my_bot.MyBot)"
        )

    module_path, class_name = spec.rsplit(".", 1)

    try:
        module = importlib.import_module(module_path)
        bot_class = getattr(module, class_name)

        # Verify it's a bot
        if not isinstance(bot_class, type) or not issubclass(bot_class, BaseBot):
            raise ValueError(f"{spec} is not a valid bot class")

        return bot_class
    except ImportError as e:
        raise ValueError(f"Could not import module {module_path}: {e}")
    except AttributeError:
        raise ValueError(f"Class {class_name} not found in module {module_path}")


def main() -> None:
    """Run the interactive round stepper."""
    parser = argparse.ArgumentParser(
        description="Step through a Flip 7 round turn-by-turn for debugging",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Default: RandomBot vs ConservativeBot
  uv run flip7-step

  # Specify bots
  uv run flip7-step RandomBot ConservativeBot

  # With custom seed
  uv run flip7-step RandomBot ConservativeBot --seed 42

  # Simulate mid-game (bot1=100pts, bot2=150pts, round 8)
  uv run flip7-step RandomBot ConservativeBot --scores 100,150 --round 8

  # Custom bot from module
  uv run flip7-step my_bot.MyBot ConservativeBot
        """,
    )

    parser.add_argument(
        "bot1",
        nargs="?",
        default="RandomBot",
        help="First bot (default: RandomBot)",
    )

    parser.add_argument(
        "bot2",
        nargs="?",
        default="ConservativeBot",
        help="Second bot (default: ConservativeBot)",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility",
    )

    parser.add_argument(
        "--scores",
        type=str,
        default=None,
        help="Starting scores (comma-separated, e.g., '100,150' for bot1=100, bot2=150)",
    )

    parser.add_argument(
        "--round",
        type=int,
        default=1,
        help="Round number to display (default: 1)",
    )

    args = parser.parse_args()

    # Load bot classes
    try:
        bot1_class = load_bot_class(args.bot1)
        bot2_class = load_bot_class(args.bot2)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Create bot instances
    player1_id = f"{bot1_class.__name__}_1"
    player2_id = f"{bot2_class.__name__}_2"

    player_ids = [player1_id, player2_id]
    bots: dict[str, Bot] = {
        player1_id: bot1_class(bot_name=player1_id),
        player2_id: bot2_class(bot_name=player2_id),
    }

    # Parse starting scores if provided
    starting_scores: dict[str, int] | None = None
    if args.scores:
        try:
            score_values = [int(s.strip()) for s in args.scores.split(",")]
            if len(score_values) != 2:
                print("Error: --scores must have exactly 2 values (one per bot)", file=sys.stderr)
                sys.exit(1)
            starting_scores = {
                player1_id: score_values[0],
                player2_id: score_values[1],
            }
        except ValueError:
            print("Error: --scores must be comma-separated integers (e.g., '100,150')", file=sys.stderr)
            sys.exit(1)

    # Create stepper
    stepper = RoundStepper(
        player_ids=player_ids,
        bots=bots,
        seed=args.seed,
        bot_timeout=5.0,
        starting_scores=starting_scores,
        round_number=args.round,
    )

    # Run interactively
    try:
        scores = stepper.run_interactive()
        print(f"\n[bold green]Round Complete![/bold green]")
        print(f"\nFinal Scores:")
        for player_id, score in scores.items():
            print(f"  {player_id}: {score}")
    except KeyboardInterrupt:
        print("\n\nStepper interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

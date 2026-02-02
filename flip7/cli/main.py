"""Command-line interface for Flip 7 tournament system."""

import logging
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel

from flip7.utils.logging_config import setup_logging

console = Console()
logger = logging.getLogger(__name__)


def _load_config_from_file(config_file: Path) -> object:
    """Load tournament configuration from Python file."""
    import importlib.util

    try:
        spec = importlib.util.spec_from_file_location("config_module", config_file)
        if spec is None or spec.loader is None:
            raise click.ClickException(f"Could not load config from {config_file}")

        module = importlib.util.module_from_spec(spec)
        sys.modules["config_module"] = module
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        raise click.ClickException(f"Error loading config file: {e}")


@click.command()
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Enable verbose debug logging"
)
def cli(verbose: bool) -> None:
    """Flip 7 Tournament System - Run bot tournaments and analyze performance.

    Edit tournament_config.py to configure:
    - Which bots to test (BOT_CLASSES)
    - Number of games (NUM_GAMES)
    - Players per game (PLAYERS_PER_GAME)
    - Output settings (OUTPUT_DIR, SAVE_REPLAYS)

    Example usage:

    \b
        # Edit tournament_config.py, then run:
        $ flip7

        # With verbose logging:
        $ flip7 -v
    """
    # Setup logging
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(level=log_level, use_rich=True)

    # Load configuration from tournament_config.py in current directory
    config_file = Path("tournament_config.py")
    if not config_file.exists():
        raise click.ClickException(
            "tournament_config.py not found in current directory.\n"
            "Copy it from the repository root or create your own."
        )

    console.print(Panel.fit(
        "[bold cyan]Running tournament from:[/bold cyan] tournament_config.py",
        border_style="cyan"
    ))

    try:
        # Load configuration module
        config_module = _load_config_from_file(config_file)

        # Run simple sequential tournament
        from flip7.tournament.simple_runner import run_simple_tournament, print_tournament_results

        # Extract config values
        num_games = getattr(config_module, "NUM_GAMES", 1000)
        players_per_game = getattr(config_module, "PLAYERS_PER_GAME", 2)
        bot_classes = getattr(config_module, "BOT_CLASSES", [])
        bot_timeout = getattr(config_module, "BOT_TIMEOUT_SECONDS", 5.0)
        output_dir = getattr(config_module, "OUTPUT_DIR", Path("./tournament_results"))
        save_replays = getattr(config_module, "SAVE_REPLAYS", False)
        tournament_seed = getattr(config_module, "TOURNAMENT_SEED", None)
        tournament_name = getattr(config_module, "TOURNAMENT_NAME", "Tournament")

        # Validate config
        if not bot_classes:
            raise click.ClickException("BOT_CLASSES cannot be empty")

        # Run tournament
        stats = run_simple_tournament(
            tournament_name=tournament_name,
            num_games=num_games,
            players_per_game=players_per_game,
            bot_classes=bot_classes,
            bot_timeout_seconds=bot_timeout,
            output_dir=output_dir,
            save_replays=save_replays,
            tournament_seed=tournament_seed,
        )

        # Display results
        print_tournament_results(stats)

    except click.ClickException:
        raise
    except Exception as e:
        logger.exception("Tournament failed")
        raise click.ClickException(f"Tournament failed: {e}")


if __name__ == "__main__":
    cli()

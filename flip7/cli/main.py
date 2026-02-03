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
    """Flip 7 Tournament System - Run round-robin tournaments with head-to-head analysis.

    Runs a complete all-against-all tournament where every matchup plays the same
    number of games, then displays both overall standings and head-to-head records.

    Edit tournament_config.py to configure:
    - Which bots to test (BOT_CLASSES)
    - Games per matchup (GAMES_PER_MATCHUP)
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
        # Check platform compatibility first
        from flip7.utils.config_validator import check_platform_compatibility
        check_platform_compatibility()

        # Load configuration module
        config_module = _load_config_from_file(config_file)

        # Auto-discover all bots
        from flip7.utils.bot_discovery import discover_all_bots, get_bot_names

        bot_classes = discover_all_bots()

        if not bot_classes:
            raise click.ClickException(
                "No bots found in flip7/bots/ directory. "
                "Create a bot class that inherits from BaseBot."
            )

        console.print(f"\n[bold cyan]Discovered {len(bot_classes)} bots:[/bold cyan]")
        for bot_name in sorted(get_bot_names(bot_classes)):
            console.print(f"  • {bot_name}")
        console.print()

        # Extract config values
        bot_timeout = getattr(config_module, "BOT_TIMEOUT_SECONDS", 1.0)
        save_replays = getattr(config_module, "SAVE_REPLAYS", False)
        tournament_seed = getattr(config_module, "TOURNAMENT_SEED", None)
        tournament_name = getattr(config_module, "TOURNAMENT_NAME", "Tournament")

        # Get tournament-specific settings
        games_h2h = getattr(config_module, "GAMES_PER_MATCHUP_HEAD_TO_HEAD", 100_000)
        games_all = getattr(config_module, "GAMES_PER_MATCHUP_ALL_VS_ALL", 1_000_000)
        output_h2h = getattr(config_module, "OUTPUT_DIR_HEAD_TO_HEAD", Path("./tournament_results_head_to_head"))
        output_all = getattr(config_module, "OUTPUT_DIR_ALL_VS_ALL", Path("./tournament_results_all_vs_all"))

        # Validate configuration before starting tournament
        from flip7.utils.config_validator import validate_tournament_config, ConfigurationError
        try:
            validate_tournament_config(
                games_per_matchup_h2h=games_h2h,
                games_per_matchup_all=games_all,
                bot_timeout_seconds=bot_timeout,
                output_dir_h2h=output_h2h,
                output_dir_all=output_all,
            )
        except ConfigurationError as e:
            raise click.ClickException(str(e))

        from flip7.tournament.round_robin_runner import (
            run_round_robin_tournament,
            print_round_robin_results,
        )

        # Run head-to-head tournament (2-player)
        console.print("[bold yellow]═" * 40)
        console.print("[bold yellow]TOURNAMENT 1: HEAD-TO-HEAD (2-Player)[/bold yellow]")
        console.print("[bold yellow]═" * 40)
        console.print()

        results_h2h = run_round_robin_tournament(
            tournament_name=f"{tournament_name} - Head-to-Head",
            games_per_matchup=games_h2h,
            players_per_game=2,
            bot_classes=bot_classes,
            bot_timeout_seconds=bot_timeout,
            output_dir=output_h2h,
            save_replays=save_replays,
            tournament_seed=tournament_seed,
        )

        print_round_robin_results(results_h2h)

        # Run all-vs-all tournament (all bots in each game)
        console.print("\n\n")
        console.print("[bold yellow]═" * 40)
        console.print(f"[bold yellow]TOURNAMENT 2: ALL-VS-ALL ({len(bot_classes)}-Player)[/bold yellow]")
        console.print("[bold yellow]═" * 40)
        console.print()

        results_all = run_round_robin_tournament(
            tournament_name=f"{tournament_name} - All-vs-All",
            games_per_matchup=games_all,
            players_per_game=len(bot_classes),
            bot_classes=bot_classes,
            bot_timeout_seconds=bot_timeout,
            output_dir=output_all,
            save_replays=save_replays,
            tournament_seed=tournament_seed if tournament_seed is None else tournament_seed + 1_000_000,
        )

        print_round_robin_results(results_all)

        # Summary
        console.print("\n\n")
        console.print("[bold green]═" * 40)
        console.print("[bold green]TOURNAMENTS COMPLETE![/bold green]")
        console.print("[bold green]═" * 40)
        console.print()
        console.print(f"[cyan]Head-to-Head results:[/cyan] {output_h2h}/tournament_results.json")
        console.print(f"[cyan]All-vs-All results:[/cyan] {output_all}/tournament_results.json")
        console.print()

    except click.ClickException:
        raise
    except Exception as e:
        logger.exception("Tournament failed")
        raise click.ClickException(f"Tournament failed: {e}")


if __name__ == "__main__":
    cli()

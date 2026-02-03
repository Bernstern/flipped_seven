"""Simple sequential tournament runner.

Runs a fixed number of games sequentially, cycling through bot matchups.
"""

import random
from itertools import combinations, cycle
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from rich.table import Table

from flip7.core.game_engine import GameEngine
from flip7.types import Bot

console = Console()


def run_simple_tournament(
    tournament_name: str,
    num_games: int,
    players_per_game: int,
    bot_classes: list[type[Any]],
    bot_timeout_seconds: float,
    output_dir: Path,
    save_replays: bool,
    tournament_seed: int | None,
) -> dict[str, Any]:
    """Run a simple sequential tournament.

    Args:
        tournament_name: Name of the tournament
        num_games: Total number of games to run
        players_per_game: Number of players per game
        bot_classes: List of bot classes to test
        bot_timeout_seconds: Timeout for bot decisions
        output_dir: Directory for output files
        save_replays: Whether to save game event logs
        tournament_seed: Random seed for reproducibility

    Returns:
        Dictionary with tournament results
    """
    # Create output directories
    output_dir.mkdir(exist_ok=True, parents=True)
    if save_replays:
        replays_dir = output_dir / "replays"
        replays_dir.mkdir(exist_ok=True)

    # Set random seed
    if tournament_seed is not None:
        random.seed(tournament_seed)

    # Generate all possible matchups
    if len(bot_classes) < players_per_game:
        raise ValueError(
            f"Need at least {players_per_game} bots for {players_per_game}-player games. "
            f"Only {len(bot_classes)} bots provided."
        )

    matchups = list(combinations(bot_classes, players_per_game))
    console.print(f"[cyan]Found {len(matchups)} unique matchups[/cyan]")

    # Create a cycle of matchups to rotate through
    matchup_cycle = cycle(matchups)

    # Track statistics
    stats: dict[str, dict[str, Any]] = {}
    for bot_class in bot_classes:
        stats[bot_class.__name__] = {
            "games_played": 0,
            "games_won": 0,
            "total_score": 0,
            "rounds_played": 0,
        }

    # Run games sequentially
    console.print(f"\n[bold cyan]Running {num_games} games sequentially...[/bold cyan]\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        task = progress.add_task(f"Playing games...", total=num_games)

        for game_num in range(num_games):
            # Get next matchup
            matchup = next(matchup_cycle)

            # Create bot instances
            player_ids = [f"{bot_class.__name__}_{i}" for i, bot_class in enumerate(matchup)]
            bots: dict[str, Any] = {}
            for player_id, bot_class in zip(player_ids, matchup):
                bots[player_id] = bot_class(bot_name=player_id)

            # Determine output path
            game_id = f"game_{game_num + 1:06d}"
            if save_replays:
                event_log_path = replays_dir / f"{game_id}.jsonl"
            else:
                event_log_path = output_dir / ".tmp" / f"{game_id}.jsonl"
                event_log_path.parent.mkdir(exist_ok=True, parents=True)

            # Run game
            game_seed = (tournament_seed + game_num) if tournament_seed is not None else None
            from typing import cast

            engine = GameEngine(
                game_id=game_id,
                player_ids=player_ids,
                bots=cast(dict[str, Bot], bots),
                event_log_path=event_log_path,
                seed=game_seed,
                bot_timeout=bot_timeout_seconds,
                enable_logging=False,  # Disable logging for tournament performance
            )

            final_state = engine.execute_game()

            # Update statistics
            for player_id in player_ids:
                bot_name = player_id.rsplit("_", 1)[0]  # Remove _0, _1 suffix
                stats[bot_name]["games_played"] += 1
                stats[bot_name]["total_score"] += final_state.scores[player_id]
                stats[bot_name]["rounds_played"] += final_state.current_round

                if final_state.winner == player_id:
                    stats[bot_name]["games_won"] += 1

            progress.update(task, advance=1)

    # Calculate derived statistics
    for bot_name in stats:
        bot_stats = stats[bot_name]
        if bot_stats["games_played"] > 0:
            bot_stats["win_rate"] = (
                bot_stats["games_won"] / bot_stats["games_played"] * 100
            )
            bot_stats["avg_score"] = bot_stats["total_score"] / bot_stats["games_played"]
            bot_stats["avg_rounds"] = (
                bot_stats["rounds_played"] / bot_stats["games_played"]
            )
        else:
            bot_stats["win_rate"] = 0.0
            bot_stats["avg_score"] = 0.0
            bot_stats["avg_rounds"] = 0.0

    # Save results to JSON
    import json

    results_file = output_dir / "tournament_results.json"
    try:
        with open(results_file, "w") as f:
            json.dump(
                {
                    "tournament_name": tournament_name,
                    "total_games": num_games,
                    "players_per_game": players_per_game,
                    "bot_statistics": stats,
                },
                f,
                indent=2,
            )
    except OSError as e:
        console.print(
            f"[red]Failed to save results to {results_file}[/red]\n"
            f"[yellow]Error: {e}[/yellow]\n"
            f"[yellow]Suggestion: Check that the directory exists and you have write permissions.[/yellow]"
        )
        raise
    except (TypeError, ValueError) as e:
        console.print(
            f"[red]Failed to serialize results to JSON[/red]\n"
            f"[yellow]Error: {e}[/yellow]\n"
            f"[yellow]Suggestion: Results contain non-serializable data. This is likely a bug.[/yellow]"
        )
        raise

    console.print(f"\n[green]Results saved to: {results_file}[/green]\n")

    # Auto-run behavior analysis if replays were saved
    if save_replays:
        console.print("[cyan]Running behavioral analysis...[/cyan]\n")
        from flip7.utils.tournament_analyzer import analyze_tournament_directory, print_behavior_report

        behavior_stats = analyze_tournament_directory(output_dir)
        if behavior_stats:
            print_behavior_report(behavior_stats)

    return stats


def print_tournament_results(stats: dict[str, dict[str, Any]]) -> None:
    """Print tournament results table."""
    console.print()
    console.rule("[bold cyan]Tournament Results[/bold cyan]")
    console.print()

    # Overall statistics table
    results_table = Table(title="Final Standings", show_header=True, header_style="bold cyan")
    results_table.add_column("Rank", style="yellow", justify="right")
    results_table.add_column("Bot", style="cyan")
    results_table.add_column("Games", justify="right", style="white")
    results_table.add_column("Wins", justify="right", style="green")
    results_table.add_column("Win Rate %", justify="right", style="magenta")
    results_table.add_column("Avg Score", justify="right", style="blue")
    results_table.add_column("Avg Rounds", justify="right", style="yellow")

    # Sort by win rate
    sorted_bots = sorted(stats.items(), key=lambda x: x[1]["win_rate"], reverse=True)

    for rank, (bot_name, bot_stats) in enumerate(sorted_bots, 1):
        results_table.add_row(
            str(rank),
            bot_name,
            f"{bot_stats['games_played']:,}",
            f"{bot_stats['games_won']:,}",
            f"{bot_stats['win_rate']:.1f}%",
            f"{bot_stats['avg_score']:.2f}",
            f"{bot_stats['avg_rounds']:.1f}",
        )

    console.print(results_table)
    console.print()

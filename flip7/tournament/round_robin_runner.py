"""Round-robin tournament runner with head-to-head matrix.

Runs a complete all-against-all tournament where every unique matchup
plays the same number of games, and generates detailed head-to-head statistics.
"""

import random
from collections import defaultdict
from itertools import combinations
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from rich.table import Table
from rich.text import Text

from flip7.core.game_engine import GameEngine
from flip7.types import Bot

console = Console()


def run_round_robin_tournament(
    tournament_name: str,
    games_per_matchup: int,
    players_per_game: int,
    bot_classes: list[type[Any]],
    bot_timeout_seconds: float,
    output_dir: Path,
    save_replays: bool,
    tournament_seed: int | None,
) -> dict[str, Any]:
    """Run a complete round-robin tournament.

    Every unique matchup plays exactly `games_per_matchup` games.

    Args:
        tournament_name: Name of the tournament
        games_per_matchup: Number of games for each unique matchup
        players_per_game: Number of players per game
        bot_classes: List of bot classes to test
        bot_timeout_seconds: Timeout for bot decisions
        output_dir: Directory for output files
        save_replays: Whether to save game event logs
        tournament_seed: Random seed for reproducibility

    Returns:
        Dictionary with tournament results including head-to-head matrix
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
    total_games = len(matchups) * games_per_matchup

    console.print()
    console.print(f"[cyan]Tournament: {tournament_name}[/cyan]")
    console.print(f"[cyan]Bots competing: {len(bot_classes)}[/cyan]")
    console.print(f"[cyan]Unique matchups: {len(matchups)}[/cyan]")
    console.print(f"[cyan]Games per matchup: {games_per_matchup}[/cyan]")
    console.print(f"[bold cyan]Total games: {total_games}[/bold cyan]")
    console.print()

    # Track overall statistics
    stats: dict[str, dict[str, Any]] = {}
    for bot_class in bot_classes:
        stats[bot_class.__name__] = {
            "games_played": 0,
            "games_won": 0,
            "total_score": 0,
            "rounds_played": 0,
        }

    # Track head-to-head statistics
    # For 2-player: head_to_head[bot1][bot2] = {"wins": X, "losses": Y, "games": Z}
    # For 3+ players: head_to_head[bot1][bot2] = {"wins_vs": X, "losses_vs": Y, "games_together": Z}
    head_to_head: dict[str, dict[str, dict[str, int]]] = defaultdict(
        lambda: defaultdict(lambda: {"wins": 0, "losses": 0, "games": 0})
    )

    # Run all matchups
    console.print(f"[bold cyan]Running {total_games} games...[/bold cyan]\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Playing games...", total=total_games)

        game_num = 0
        for matchup in matchups:
            # Play games_per_matchup games for this matchup
            for repeat_num in range(games_per_matchup):
                game_num += 1

                # Create bot instances
                player_ids = [f"{bot_class.__name__}_{i}" for i, bot_class in enumerate(matchup)]
                bots: dict[str, Any] = {}
                for player_id, bot_class in zip(player_ids, matchup):
                    bots[player_id] = bot_class(bot_name=player_id)

                # Determine output path
                matchup_str = "_vs_".join([bc.__name__ for bc in matchup])
                game_id = f"{matchup_str}_{repeat_num + 1:03d}"
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
                    enable_logging=save_replays,  # Only log if replays are requested
                )

                final_state = engine.execute_game()

                # Extract bot names (remove _0, _1 suffixes)
                bot_names = [player_id.rsplit("_", 1)[0] for player_id in player_ids]

                # Update overall statistics
                for player_id, bot_name in zip(player_ids, bot_names):
                    stats[bot_name]["games_played"] += 1
                    stats[bot_name]["total_score"] += final_state.scores[player_id]
                    stats[bot_name]["rounds_played"] += final_state.current_round

                    if final_state.winner == player_id:
                        stats[bot_name]["games_won"] += 1

                # Update head-to-head statistics
                winner_name = final_state.winner.rsplit("_", 1)[0]

                if players_per_game == 2:
                    # Direct head-to-head for 2-player games
                    bot1, bot2 = bot_names
                    head_to_head[bot1][bot2]["games"] += 1
                    head_to_head[bot2][bot1]["games"] += 1

                    if winner_name == bot1:
                        head_to_head[bot1][bot2]["wins"] += 1
                        head_to_head[bot2][bot1]["losses"] += 1
                    else:
                        head_to_head[bot2][bot1]["wins"] += 1
                        head_to_head[bot1][bot2]["losses"] += 1
                else:
                    # Multi-player: track who won when playing together
                    for bot_name in bot_names:
                        for opponent_name in bot_names:
                            if bot_name != opponent_name:
                                head_to_head[bot_name][opponent_name]["games"] += 1
                                if winner_name == bot_name:
                                    head_to_head[bot_name][opponent_name]["wins"] += 1
                                else:
                                    head_to_head[bot_name][opponent_name]["losses"] += 1

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

    results = {
        "tournament_name": tournament_name,
        "tournament_type": "round_robin",
        "total_games": total_games,
        "games_per_matchup": games_per_matchup,
        "players_per_game": players_per_game,
        "unique_matchups": len(matchups),
        "bot_statistics": stats,
        "head_to_head": {
            bot1: dict(opponents) for bot1, opponents in head_to_head.items()
        },
    }

    results_file = output_dir / "tournament_results.json"
    try:
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2)
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

    return results


def print_round_robin_results(results: dict[str, Any]) -> None:
    """Print round-robin tournament results with head-to-head matrix."""
    console.print()
    console.rule("[bold cyan]Round-Robin Tournament Results[/bold cyan]")
    console.print()

    stats = results["bot_statistics"]
    head_to_head = results.get("head_to_head", {})
    players_per_game = results.get("players_per_game", 2)

    # Overall standings
    standings_table = Table(
        title="Final Standings", show_header=True, header_style="bold cyan"
    )
    standings_table.add_column("Rank", style="yellow", justify="right", width=6)
    standings_table.add_column("Bot", style="cyan", width=20)
    standings_table.add_column("Games", justify="right", style="white", width=8)
    standings_table.add_column("Wins", justify="right", style="green", width=8)
    standings_table.add_column("Win Rate", justify="right", style="magenta", width=10)
    standings_table.add_column("Avg Score", justify="right", style="blue", width=10)

    # Sort by win rate
    sorted_bots = sorted(stats.items(), key=lambda x: x[1]["win_rate"], reverse=True)

    for rank, (bot_name, bot_stats) in enumerate(sorted_bots, 1):
        standings_table.add_row(
            str(rank),
            bot_name,
            f"{bot_stats['games_played']:,}",
            f"{bot_stats['games_won']:,}",
            f"{bot_stats['win_rate']:.1f}%",
            f"{bot_stats['avg_score']:.1f}",
        )

    console.print(standings_table)
    console.print()

    # Head-to-head matrix
    if head_to_head:
        console.rule("[bold yellow]Head-to-Head Matrix[/bold yellow]")
        console.print()

        if players_per_game == 2:
            _print_2player_matrix(head_to_head, sorted_bots)
        else:
            _print_multiplayer_matrix(head_to_head, sorted_bots)

        console.print()


def _print_2player_matrix(
    head_to_head: dict[str, dict[str, dict[str, int]]],
    sorted_bots: list[tuple[str, dict[str, Any]]],
) -> None:
    """Print head-to-head matrix for 2-player games."""
    bot_names = [name for name, _ in sorted_bots]

    # Create matrix table
    h2h_table = Table(
        title="Win-Loss Records (Row vs Column)",
        show_header=True,
        header_style="bold cyan",
    )

    # Add columns
    h2h_table.add_column("Bot", style="cyan", width=15)
    for bot_name in bot_names:
        h2h_table.add_column(bot_name[:12], justify="center", width=12)

    # Add rows
    for row_bot in bot_names:
        row_data = [row_bot]
        for col_bot in bot_names:
            if row_bot == col_bot:
                row_data.append("[dim]---[/dim]")
            else:
                h2h_data = head_to_head.get(row_bot, {}).get(col_bot, {})
                wins = h2h_data.get("wins", 0)
                losses = h2h_data.get("losses", 0)
                games = h2h_data.get("games", 0)

                if games > 0:
                    win_pct = (wins / games) * 100
                    if win_pct >= 60:
                        style = "bold green"
                    elif win_pct >= 50:
                        style = "green"
                    elif win_pct >= 40:
                        style = "yellow"
                    else:
                        style = "red"
                    row_data.append(f"[{style}]{wins}-{losses}[/{style}]")
                else:
                    row_data.append("[dim]0-0[/dim]")

        h2h_table.add_row(*row_data)

    console.print(h2h_table)


def _print_multiplayer_matrix(
    head_to_head: dict[str, dict[str, dict[str, int]]],
    sorted_bots: list[tuple[str, dict[str, Any]]],
) -> None:
    """Print head-to-head matrix for 3+ player games."""
    bot_names = [name for name, _ in sorted_bots]

    console.print(
        "[yellow]Note: For multiplayer games, this shows wins when playing together[/yellow]\n"
    )

    # Create detailed table
    for row_bot in bot_names:
        detail_table = Table(
            title=f"{row_bot}'s Record vs Opponents",
            show_header=True,
            header_style="bold cyan",
        )
        detail_table.add_column("Opponent", style="cyan", width=20)
        detail_table.add_column("Games Together", justify="right", width=15)
        detail_table.add_column("Wins", justify="right", width=10)
        detail_table.add_column("Win Rate", justify="right", width=10)

        for col_bot in bot_names:
            if row_bot != col_bot:
                h2h_data = head_to_head.get(row_bot, {}).get(col_bot, {})
                games = h2h_data.get("games", 0)
                wins = h2h_data.get("wins", 0)

                if games > 0:
                    win_rate = (wins / games) * 100
                    detail_table.add_row(
                        col_bot,
                        str(games),
                        str(wins),
                        f"{win_rate:.1f}%",
                    )

        console.print(detail_table)
        console.print()

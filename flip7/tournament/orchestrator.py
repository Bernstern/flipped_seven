"""
Tournament orchestrator with parallel match execution.

This module provides the TournamentOrchestrator class which coordinates
tournament execution, running matches in parallel using ProcessPoolExecutor
with asyncio integration.
"""

import asyncio
import os
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)

from flip7.tournament.match import execute_match, prepare_match
from flip7.tournament.results import TournamentResults
from flip7.tournament.round_robin import generate_round_robin_matchups

if TYPE_CHECKING:
    from flip7.tournament.config import TournamentConfig
    from flip7.tournament.results import MatchResult


class TournamentOrchestrator:
    """
    Orchestrates tournament execution with parallel match processing.

    The orchestrator:
    - Generates all round-robin matchups
    - Executes matches in parallel using ProcessPoolExecutor
    - Tracks progress with rich progress bars
    - Aggregates results into TournamentResults
    - Exports results to JSON

    Attributes:
        config: Tournament configuration
        console: Rich console for output
        results: Tournament results (populated after execution)
    """

    def __init__(self, config: "TournamentConfig") -> None:
        """
        Initialize the tournament orchestrator.

        Args:
            config: Tournament configuration
        """
        self.config = config
        self.console = Console()
        self.results: TournamentResults | None = None

    def run_tournament(self) -> TournamentResults:
        """
        Execute the complete tournament with parallel match execution.

        This is the main entry point for running a tournament. It:
        1. Generates all matchups
        2. Executes matches in parallel
        3. Aggregates results
        4. Exports results to JSON

        Returns:
            TournamentResults with complete statistics

        Example:
            >>> config = TournamentConfig(...)
            >>> orchestrator = TournamentOrchestrator(config)
            >>> results = orchestrator.run_tournament()
            >>> print(f"Tournament complete: {results.total_matches} matches")
        """
        # Create output directory
        self.config.output_dir.mkdir(parents=True, exist_ok=True)

        # Print tournament header
        self._print_tournament_header()

        # Generate matchups
        matchups = generate_round_robin_matchups(
            self.config.bot_classes, self.config.players_per_game
        )

        # Initialize results
        self.results = TournamentResults(
            tournament_name=self.config.tournament_name,
            config_summary=self._get_config_summary(),
        )

        # Execute matches with asyncio event loop
        match_results = asyncio.run(self._execute_matches_parallel(matchups))

        # Aggregate results
        for match_result in match_results:
            self.results.add_match(match_result)

        # Export results
        results_path = self.config.output_dir / "tournament_results.json"
        self.results.export_to_json(results_path)

        # Print summary
        self._print_tournament_summary()

        return self.results

    async def _execute_matches_parallel(
        self, matchups: list[tuple[str, ...]]
    ) -> list["MatchResult"]:
        """
        Execute all matches in parallel using ProcessPoolExecutor.

        Args:
            matchups: List of matchup tuples (player IDs)

        Returns:
            List of match results
        """
        # Determine number of workers
        max_workers = self.config.max_workers or os.cpu_count() or 1

        # Create progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TextColumn("•"),
            TimeElapsedColumn(),
            console=self.console,
        ) as progress:
            task = progress.add_task(
                "Executing matches...", total=len(matchups)
            )

            # Execute matches in parallel
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                loop = asyncio.get_event_loop()
                futures = []

                for matchup in matchups:
                    # Generate unique match ID
                    import uuid
                    match_id = f"match_{uuid.uuid4().hex[:8]}_{'_vs_'.join(matchup)}"

                    # Submit to executor - bot instances will be created in subprocess
                    future = loop.run_in_executor(
                        executor,
                        _execute_match_wrapper,
                        self.config,
                        matchup,
                        match_id,
                    )
                    futures.append(future)

                # Gather results as they complete
                results: list[MatchResult] = []
                for coro in asyncio.as_completed(futures):
                    result = await coro
                    results.append(result)
                    progress.advance(task)

        return results

    def _get_config_summary(self) -> dict[str, object]:
        """
        Get a summary of tournament configuration.

        Returns:
            Dictionary with configuration details
        """
        return {
            "tournament_name": self.config.tournament_name,
            "players_per_game": self.config.players_per_game,
            "best_of_n": self.config.best_of_n,
            "bot_classes": [bc.__name__ for bc in self.config.bot_classes],
            "bot_timeout_seconds": self.config.bot_timeout_seconds,
            "save_replays": self.config.save_replays,
            "max_workers": self.config.max_workers,
            "tournament_seed": self.config.tournament_seed,
            "timestamp": datetime.now().isoformat(),
        }

    def _print_tournament_header(self) -> None:
        """Print tournament information header."""
        self.console.print()
        self.console.print(f"[bold cyan]Tournament:[/bold cyan] {self.config.tournament_name}")
        self.console.print(f"[bold cyan]Players per game:[/bold cyan] {self.config.players_per_game}")
        self.console.print(f"[bold cyan]Best of:[/bold cyan] {self.config.best_of_n}")
        self.console.print(
            f"[bold cyan]Bots:[/bold cyan] {', '.join(bc.__name__ for bc in self.config.bot_classes)}"
        )

        # Calculate total matchups
        from flip7.tournament.round_robin import count_matchups

        total_matchups = count_matchups(len(self.config.bot_classes), self.config.players_per_game)
        self.console.print(f"[bold cyan]Total matches:[/bold cyan] {total_matchups}")
        self.console.print()

    def _print_tournament_summary(self) -> None:
        """Print tournament results summary."""
        if self.results is None:
            return

        self.console.print()
        self.console.print("[bold green]Tournament Complete![/bold green]")
        self.console.print()
        self.console.print("[bold cyan]Leaderboard:[/bold cyan]")
        self.console.print()

        # Print leaderboard
        leaderboard = self.results.get_leaderboard()
        for rank, (bot_name, stats) in enumerate(leaderboard, 1):
            self.console.print(
                f"  {rank}. [bold]{bot_name}[/bold] - "
                f"Win Rate: {stats.win_rate:.1f}% "
                f"({stats.matches_won}/{stats.matches_played} matches, "
                f"{stats.games_won}/{stats.games_played} games)"
            )

        self.console.print()
        self.console.print(
            f"[bold cyan]Results saved to:[/bold cyan] {self.config.output_dir / 'tournament_results.json'}"
        )
        self.console.print()


def _execute_match_wrapper(
    config: "TournamentConfig",
    player_ids: tuple[str, ...],
    match_id: str,
) -> "MatchResult":
    """
    Wrapper function for executing a match in a subprocess.

    This function is necessary because ProcessPoolExecutor requires
    top-level functions (not methods) to be pickled. Bot instances are
    created within this function to avoid serialization issues.

    Args:
        config: Tournament configuration
        player_ids: Tuple of player IDs (bot class names)
        match_id: Match identifier

    Returns:
        MatchResult
    """
    # Create bot instances in this subprocess
    bots, _ = prepare_match(config, player_ids)
    return execute_match(config, player_ids, bots, match_id)

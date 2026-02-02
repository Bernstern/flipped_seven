"""Tournament analysis utilities for detailed behavior statistics.

Analyzes tournament event logs to extract behavioral patterns like:
- Average hand values when passing
- Bust vs pass decisions at different hand values
- Action card usage patterns
- Flip 7 achievement rates

Usage:
    python -m flip7.utils.tournament_analyzer tournament_results/
"""

import json
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

console = Console()


@dataclass
class BotBehaviorStats:
    """Detailed behavioral statistics for a bot."""

    bot_name: str

    # Decision statistics
    total_decisions: int = 0
    hit_decisions: int = 0
    pass_decisions: int = 0

    # Hand value when passing
    pass_hand_values: list[int] = field(default_factory=list)

    # Bust statistics
    total_busts: int = 0
    busts_with_second_chance_used: int = 0

    # Hand values when busting
    bust_hand_values: list[int] = field(default_factory=list)

    # Flip 7 statistics
    flip_7_achieved: int = 0

    # Action card usage
    freeze_used: int = 0
    flip_three_used: int = 0

    # Round performance
    rounds_played: int = 0
    total_score: int = 0
    rounds_won: int = 0

    @property
    def avg_pass_hand_value(self) -> float:
        """Average hand value when deciding to pass."""
        return sum(self.pass_hand_values) / len(self.pass_hand_values) if self.pass_hand_values else 0.0

    @property
    def avg_bust_hand_value(self) -> float:
        """Average hand value when busting."""
        return sum(self.bust_hand_values) / len(self.bust_hand_values) if self.bust_hand_values else 0.0

    @property
    def hit_rate(self) -> float:
        """Percentage of decisions that were 'hit'."""
        return (self.hit_decisions / self.total_decisions * 100) if self.total_decisions > 0 else 0.0

    @property
    def pass_rate(self) -> float:
        """Percentage of decisions that were 'pass'."""
        return (self.pass_decisions / self.total_decisions * 100) if self.total_decisions > 0 else 0.0

    @property
    def bust_rate(self) -> float:
        """Percentage of rounds that ended in a bust."""
        return (self.total_busts / self.rounds_played * 100) if self.rounds_played > 0 else 0.0

    @property
    def flip_7_rate(self) -> float:
        """Percentage of rounds with Flip 7 achieved."""
        return (self.flip_7_achieved / self.rounds_played * 100) if self.rounds_played > 0 else 0.0

    @property
    def avg_score_per_round(self) -> float:
        """Average score per round."""
        return self.total_score / self.rounds_played if self.rounds_played > 0 else 0.0


def analyze_tournament_directory(results_dir: Path) -> dict[str, BotBehaviorStats]:
    """Analyze all event logs in a tournament results directory.

    Args:
        results_dir: Path to tournament results directory

    Returns:
        Dictionary mapping bot names to their behavioral statistics
    """
    stats: dict[str, BotBehaviorStats] = {}

    # Find all event log files
    replays_dir = results_dir / "replays"
    if not replays_dir.exists():
        console.print("[yellow]No replays directory found. Set save_replays=True in config.[/yellow]")
        return {}

    event_files = list(replays_dir.glob("*.jsonl"))
    if not event_files:
        console.print("[yellow]No event logs found in replays directory.[/yellow]")
        return {}

    console.print(f"[cyan]Analyzing {len(event_files)} game logs...[/cyan]")

    # Track current game state
    current_game_players: set[str] = set()
    player_tableaus: dict[str, list[int]] = {}

    for event_file in event_files:
        with open(event_file, 'r') as f:
            for line in f:
                if not line.strip():
                    continue

                event = json.loads(line)
                event_type = event['event_type']
                player_id = event.get('player_id')

                # Track game start
                if event_type == 'game_started':
                    current_game_players = set(event['data']['players'])
                    for player in current_game_players:
                        if player not in stats:
                            stats[player] = BotBehaviorStats(bot_name=player)

                # Track round start
                elif event_type == 'round_started':
                    player_tableaus = {}
                    for player in current_game_players:
                        stats[player].rounds_played += 1
                        player_tableaus[player] = []

                # Track player decisions
                elif event_type == 'player_hit' and player_id:
                    stats[player_id].total_decisions += 1
                    stats[player_id].hit_decisions += 1

                elif event_type == 'player_passed' and player_id:
                    stats[player_id].total_decisions += 1
                    stats[player_id].pass_decisions += 1

                    # Calculate hand value at pass
                    if player_id in player_tableaus:
                        hand_value = sum(player_tableaus[player_id])
                        stats[player_id].pass_hand_values.append(hand_value)

                # Track busts
                elif event_type == 'player_busted' and player_id:
                    stats[player_id].total_busts += 1

                    # Calculate hand value at bust
                    if player_id in player_tableaus:
                        hand_value = sum(player_tableaus[player_id])
                        stats[player_id].bust_hand_values.append(hand_value)

                # Track second chance usage
                elif event_type == 'second_chance_used' and player_id:
                    stats[player_id].busts_with_second_chance_used += 1

                # Track Flip 7
                elif event_type == 'flip_7_achieved' and player_id:
                    stats[player_id].flip_7_achieved += 1

                # Track action cards
                elif event_type == 'freeze_applied':
                    source = event['data'].get('source_player')
                    if source and source in stats:
                        stats[source].freeze_used += 1

                elif event_type == 'flip_three_triggered':
                    source = event['data'].get('source_player')
                    if source and source in stats:
                        stats[source].flip_three_used += 1

                # Track card dealt to update tableau state
                elif event_type == 'card_dealt' and player_id:
                    if player_id not in player_tableaus:
                        player_tableaus[player_id] = []

                    card = event['data'].get('card', {})
                    if card.get('_card_type') == 'NumberCard':
                        player_tableaus[player_id].append(card['value'])

                # Track round scores
                elif event_type == 'round_ended':
                    scores = event['data'].get('scores', {})
                    for player, score in scores.items():
                        if player in stats:
                            stats[player].total_score += score
                            if score > 0 and score == max(scores.values()):
                                stats[player].rounds_won += 1

    return stats


def print_behavior_report(stats: dict[str, BotBehaviorStats]) -> None:
    """Print a detailed behavior analysis report."""
    console.print("\n")
    console.rule("[bold cyan]Tournament Behavior Analysis[/bold cyan]")
    console.print()

    # Overall statistics table
    overall_table = Table(title="Overall Performance", show_header=True, header_style="bold cyan")
    overall_table.add_column("Bot", style="yellow")
    overall_table.add_column("Rounds", justify="right", style="white")
    overall_table.add_column("Avg Score", justify="right", style="green")
    overall_table.add_column("Rounds Won", justify="right", style="magenta")
    overall_table.add_column("Win Rate %", justify="right", style="cyan")

    for bot_name, bot_stats in sorted(stats.items()):
        win_rate = (bot_stats.rounds_won / bot_stats.rounds_played * 100) if bot_stats.rounds_played > 0 else 0
        overall_table.add_row(
            bot_name,
            f"{bot_stats.rounds_played:,}",
            f"{bot_stats.avg_score_per_round:.2f}",
            f"{bot_stats.rounds_won:,}",
            f"{win_rate:.1f}%",
        )

    console.print(overall_table)
    console.print()

    # Decision behavior table
    decision_table = Table(title="Decision Patterns", show_header=True, header_style="bold cyan")
    decision_table.add_column("Bot", style="yellow")
    decision_table.add_column("Total Decisions", justify="right", style="white")
    decision_table.add_column("Hit %", justify="right", style="green")
    decision_table.add_column("Pass %", justify="right", style="red")
    decision_table.add_column("Avg Pass Value", justify="right", style="cyan")

    for bot_name, bot_stats in sorted(stats.items()):
        decision_table.add_row(
            bot_name,
            f"{bot_stats.total_decisions:,}",
            f"{bot_stats.hit_rate:.1f}%",
            f"{bot_stats.pass_rate:.1f}%",
            f"{bot_stats.avg_pass_hand_value:.2f}",
        )

    console.print(decision_table)
    console.print()

    # Risk/Bust behavior table
    risk_table = Table(title="Risk & Bust Behavior", show_header=True, header_style="bold cyan")
    risk_table.add_column("Bot", style="yellow")
    risk_table.add_column("Total Busts", justify="right", style="red")
    risk_table.add_column("Bust Rate %", justify="right", style="red")
    risk_table.add_column("Avg Bust Value", justify="right", style="yellow")
    risk_table.add_column("2nd Chance Used", justify="right", style="green")

    for bot_name, bot_stats in sorted(stats.items()):
        risk_table.add_row(
            bot_name,
            f"{bot_stats.total_busts:,}",
            f"{bot_stats.bust_rate:.1f}%",
            f"{bot_stats.avg_bust_hand_value:.2f}",
            f"{bot_stats.busts_with_second_chance_used:,}",
        )

    console.print(risk_table)
    console.print()

    # Special achievements table
    achievements_table = Table(title="Special Achievements", show_header=True, header_style="bold cyan")
    achievements_table.add_column("Bot", style="yellow")
    achievements_table.add_column("Flip 7 Count", justify="right", style="magenta")
    achievements_table.add_column("Flip 7 Rate %", justify="right", style="magenta")
    achievements_table.add_column("Freeze Used", justify="right", style="blue")
    achievements_table.add_column("Flip 3 Used", justify="right", style="cyan")

    for bot_name, bot_stats in sorted(stats.items()):
        achievements_table.add_row(
            bot_name,
            f"{bot_stats.flip_7_achieved:,}",
            f"{bot_stats.flip_7_rate:.2f}%",
            f"{bot_stats.freeze_used:,}",
            f"{bot_stats.flip_three_used:,}",
        )

    console.print(achievements_table)
    console.print()


def main() -> None:
    """CLI entry point for tournament analyzer."""
    import sys

    if len(sys.argv) < 2:
        console.print("[red]Usage: python -m flip7.utils.tournament_analyzer <results_directory>[/red]")
        sys.exit(1)

    results_dir = Path(sys.argv[1])
    if not results_dir.exists():
        console.print(f"[red]Directory not found: {results_dir}[/red]")
        sys.exit(1)

    stats = analyze_tournament_directory(results_dir)

    if not stats:
        console.print("[yellow]No statistics generated. Make sure save_replays=True in tournament config.[/yellow]")
        sys.exit(1)

    print_behavior_report(stats)


if __name__ == "__main__":
    main()

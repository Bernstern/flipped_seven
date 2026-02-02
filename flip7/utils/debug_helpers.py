"""Pretty-printing utilities for debugging and display using Rich.

This module provides Rich-based visualization of game state for debugging,
testing, and player-facing output. All functions use Rich tables, trees, and
panels for attractive console output.
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from flip7.types.cards import ActionCard, Card, ModifierCard, NumberCard
from flip7.types.game_state import GameState, PlayerTableau, ScoreBreakdown


def format_card(card: Card) -> str:
    """Convert a card to a human-readable string representation.

    Args:
        card: Any card type (NumberCard, ActionCard, or ModifierCard)

    Returns:
        A formatted string representing the card

    Examples:
        >>> format_card(NumberCard(5))
        '[5]'

        >>> format_card(ActionCard(ActionType.FREEZE))
        '[FREEZE]'

        >>> format_card(ModifierCard("+10"))
        '[+10]'

        >>> format_card(ModifierCard("X2"))
        '[X2]'
    """
    if isinstance(card, NumberCard):
        return f"[{card.value}]"
    elif isinstance(card, ActionCard):
        return f"[{card.action_type.value}]"
    elif isinstance(card, ModifierCard):
        return f"[{card.modifier}]"
    else:
        return str(card)


def print_tableau(tableau: PlayerTableau, console: Console | None = None) -> None:
    """Print a player's tableau as a Rich table.

    Displays all cards in the tableau, organized by type, along with
    the player's current status flags.

    Args:
        tableau: The player's tableau to display
        console: Optional Rich console instance (creates new one if not provided)

    Example output:
        ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
        ║ Player: player1                        ║
        ║ Number Cards: [3] [5] [7] [10]        ║
        ║ Modifiers: [+4] [X2]                  ║
        ║ Second Chance: Yes                    ║
        ║ Status: Active                         ║
        ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
    """
    if console is None:
        console = Console()

    table = Table(title=f"Tableau: {tableau.player_id}", show_header=False, border_style="blue")
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")

    # Number cards
    number_cards_str = " ".join(format_card(card) for card in tableau.number_cards)
    if not number_cards_str:
        number_cards_str = "(none)"
    table.add_row("Number Cards", number_cards_str)

    # Modifier cards
    modifier_cards_str = " ".join(format_card(card) for card in tableau.modifier_cards)
    if not modifier_cards_str:
        modifier_cards_str = "(none)"
    table.add_row("Modifiers", modifier_cards_str)

    # Second Chance
    second_chance_str = "Yes" if tableau.second_chance else "No"
    table.add_row("Second Chance", second_chance_str)

    # Status
    status_parts = []
    if tableau.is_busted:
        status_parts.append("[red]BUSTED[/red]")
    elif tableau.is_frozen:
        status_parts.append("[blue]FROZEN[/blue]")
    elif tableau.is_passed:
        status_parts.append("[yellow]PASSED[/yellow]")
    elif tableau.is_active:
        status_parts.append("[green]ACTIVE[/green]")
    else:
        status_parts.append("[dim]INACTIVE[/dim]")

    table.add_row("Status", " ".join(status_parts))

    console.print(table)


def print_game_state(state: GameState, console: Console | None = None) -> None:
    """Print the complete game state as a Rich tree structure.

    Displays cumulative scores, current round, and game completion status
    in a hierarchical tree view.

    Args:
        state: The game state to display
        console: Optional Rich console instance (creates new one if not provided)

    Example output:
        Game: game_123
        ├── Round: 3
        ├── Status: In Progress
        └── Scores
            ├── player1: 125
            ├── player2: 98
            └── player3: 156
    """
    if console is None:
        console = Console()

    # Create root tree
    tree = Tree(f"[bold cyan]Game: {state.game_id}[/bold cyan]")

    # Add round information
    tree.add(f"[yellow]Round:[/yellow] {state.current_round}")

    # Add game status
    if state.is_complete:
        status = f"[green]Complete - Winner: {state.winner}[/green]"
    else:
        status = "[blue]In Progress[/blue]"
    tree.add(f"[yellow]Status:[/yellow] {status}")

    # Add player scores
    scores_branch = tree.add("[yellow]Scores[/yellow]")
    for player_id in state.players:
        score = state.scores.get(player_id, 0)
        score_color = "green" if score >= 200 else "white"
        scores_branch.add(f"[cyan]{player_id}:[/cyan] [{score_color}]{score}[/{score_color}]")

    console.print(tree)


def print_score_breakdown(
    breakdown: ScoreBreakdown,
    player_id: str | None = None,
    console: Console | None = None
) -> None:
    """Print a detailed score breakdown with Rich formatting.

    Shows each step of the score calculation including number card sum,
    multiplier application, modifier additions, and flip 7 bonus.

    Args:
        breakdown: The score breakdown to display
        player_id: Optional player ID to include in the title
        console: Optional Rich console instance (creates new one if not provided)

    Example output:
        ╭───────────────────────────────────────╮
        │ Score Breakdown: player1              │
        ├───────────────────────────────────────┤
        │ Number Cards Sum:        15           │
        │ After X2 Multiplier:     30           │
        │ Modifier Additions:      +10          │
        │ Flip 7 Bonus:            +15          │
        │ ─────────────────────────────────────  │
        │ FINAL SCORE:             55           │
        ╰───────────────────────────────────────╯
    """
    if console is None:
        console = Console()

    # Build the content
    lines = []
    lines.append("[cyan]Number Cards Sum:[/cyan]".ljust(35) + f"{breakdown.number_cards_sum}")

    # Show X2 application if it was applied
    if breakdown.after_x2_multiplier != breakdown.number_cards_sum:
        lines.append(
            "[cyan]After X2 Multiplier:[/cyan]".ljust(35) +
            f"{breakdown.after_x2_multiplier}"
        )

    # Show modifier additions if any
    if breakdown.modifier_additions > 0:
        lines.append(
            "[cyan]Modifier Additions:[/cyan]".ljust(35) +
            f"+{breakdown.modifier_additions}"
        )

    # Show Flip 7 bonus if achieved
    if breakdown.flip_7_bonus > 0:
        lines.append(
            "[cyan]Flip 7 Bonus:[/cyan]".ljust(35) +
            f"+{breakdown.flip_7_bonus}"
        )

    # Add separator and final score
    lines.append("─" * 40)
    lines.append(
        "[bold yellow]FINAL SCORE:[/bold yellow]".ljust(35) +
        f"[bold green]{breakdown.final_score}[/bold green]"
    )

    # Create panel with title
    title = "Score Breakdown"
    if player_id:
        title = f"Score Breakdown: {player_id}"

    panel = Panel(
        "\n".join(lines),
        title=title,
        border_style="green",
        padding=(1, 2)
    )

    console.print(panel)

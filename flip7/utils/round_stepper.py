"""Interactive turn-by-turn round stepper for debugging bot behavior.

This module provides an interactive tool for stepping through a single round
of Flip 7, showing detailed game state at each decision point.
"""

from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from flip7.bots.sandbox import execute_with_sandbox
from flip7.constants import FLIP_7_THRESHOLD, WINNING_SCORE
from flip7.core.deck import create_deck, shuffle_deck
from flip7.core.scoring import calculate_score, has_flip_7
from flip7.events.event_logger import EventLogger
from flip7.types.bot_interface import Bot
from flip7.types.cards import ActionCard, ActionType, Card, ModifierCard, NumberCard
from flip7.types.errors import BotTimeout
from flip7.types.events import BotDecisionContext, Event
from flip7.types.game_state import PlayerTableau

console = Console()


class RoundStepper:
    """Interactive stepper for a single round of Flip 7.

    This class extends the round engine logic with interactive stepping,
    allowing you to see game state at each decision point.
    """

    def __init__(
        self,
        player_ids: list[str],
        bots: dict[str, Bot],
        seed: int | None = None,
        bot_timeout: float = 5.0,
        starting_scores: dict[str, int] | None = None,
        round_number: int = 1,
    ) -> None:
        """Initialize the round stepper.

        Args:
            player_ids: List of player IDs in turn order
            bots: Mapping of player IDs to their Bot implementations
            seed: Optional random seed for deterministic shuffling
            bot_timeout: Timeout in seconds for bot decisions
            starting_scores: Optional cumulative scores to simulate mid-game (default: all 0)
            round_number: The round number to display (default: 1)
        """
        if not player_ids:
            raise ValueError("Must have at least one player")

        missing_bots = set(player_ids) - set(bots.keys())
        if missing_bots:
            raise ValueError(f"Missing bots for players: {missing_bots}")

        self.player_ids = player_ids
        self.bots = bots
        self.seed = seed
        self.bot_timeout = bot_timeout
        self.starting_scores = starting_scores or {pid: 0 for pid in player_ids}
        self.round_number = round_number

        # Initialize deck
        self.deck = shuffle_deck(create_deck(), seed=seed)
        self.discard_pile: list[Card] = []

        # Initialize tableaus
        self.tableaus: dict[str, PlayerTableau] = {
            player_id: PlayerTableau(
                player_id=player_id,
                number_cards=(),
                modifier_cards=(),
                second_chance=False,
                is_active=True,
                is_busted=False,
                is_frozen=False,
                is_passed=False,
            )
            for player_id in player_ids
        }

        self.current_player_index = 0
        self.turn_number = 0

    def run_interactive(self) -> dict[str, int]:
        """Run the round interactively, pausing at each decision point.

        Returns:
            Dictionary mapping player IDs to their final scores
        """
        console.print()
        console.rule("[bold cyan]Interactive Round Stepper[/bold cyan]")
        console.print()

        # Initial deal
        console.print("[yellow]Phase 1: Initial Deal[/yellow]\n")
        self._initial_deal_interactive()

        # Turn cycle
        console.print("\n[yellow]Phase 2: Turn Cycle[/yellow]\n")
        self._turn_cycle_interactive()

        # Final scoring
        console.print("\n[yellow]Phase 3: Final Scoring[/yellow]\n")
        scores = self._calculate_final_scores()

        return scores

    def _initial_deal_interactive(self) -> None:
        """Deal 1 card to each player, showing each card."""
        for player_id in self.player_ids:
            console.print(f"[cyan]{player_id}[/cyan] receives initial card...")
            self._wait_for_input()

            card = self._draw_card()
            console.print(f"  Drew: {self._format_card(card)}")

            if isinstance(card, ActionCard):
                self._handle_action_card(player_id, card)
            elif isinstance(card, NumberCard):
                self._handle_number_card(player_id, card)
            elif isinstance(card, ModifierCard):
                self._handle_modifier_card(player_id, card)

            self._show_tableau(player_id)
            console.print()

    def _turn_cycle_interactive(self) -> None:
        """Execute turns, pausing at each decision point."""
        while not self._is_round_complete():
            self.turn_number += 1
            player_id = self.player_ids[self.current_player_index]
            tableau = self.tableaus[player_id]

            console.rule(f"[bold]Turn {self.turn_number}[/bold]")
            console.print()

            if tableau.is_active:
                self._execute_turn_interactive(player_id)
            else:
                console.print(f"[dim]{player_id} is not active (already passed/busted/frozen)[/dim]\n")

            # Move to next player
            self.current_player_index = (self.current_player_index + 1) % len(self.player_ids)

        console.print("[green]✓ Round complete! All players have finished.[/green]\n")

    def _execute_turn_interactive(self, player_id: str) -> None:
        """Execute a single player turn with interactive stepping."""
        bot = self.bots[player_id]
        tableau = self.tableaus[player_id]

        # Show current game state
        console.print(f"[bold cyan]>>> {player_id}'s Turn[/bold cyan]\n")
        self._show_all_tableaus(highlight=player_id)
        console.print()

        # Build decision context
        context = self._build_decision_context(player_id)

        # Show decision context details
        self._show_decision_context(player_id, context)
        console.print()

        # Ask bot to decide
        console.print(f"[yellow]Asking {bot.name} to decide: hit or pass?[/yellow]")
        self._wait_for_input()

        try:
            decision = execute_with_sandbox(
                bot.name,
                self.bot_timeout,
                bot.decide_hit_or_pass,
                context,
            )
        except BotTimeout:
            console.print("[red]✗ Bot timed out! Treating as bust.[/red]\n")
            self.tableaus[player_id] = replace(
                tableau,
                is_active=False,
                is_busted=True,
            )
            return

        console.print(f"[green]→ Decision: {decision.upper()}[/green]\n")

        if decision == "pass":
            self.tableaus[player_id] = replace(
                tableau,
                is_active=False,
                is_passed=True,
            )
            console.print(f"[green]✓ {player_id} passed and locked in their score.[/green]\n")
        else:
            # Player hits - draw a card
            console.print(f"[cyan]{player_id} draws a card...[/cyan]")
            self._wait_for_input()

            card = self._draw_card()
            console.print(f"  Drew: {self._format_card(card)}\n")

            # Handle the drawn card
            if isinstance(card, ActionCard):
                self._handle_action_card(player_id, card)
            elif isinstance(card, NumberCard):
                self._handle_number_card(player_id, card)
            elif isinstance(card, ModifierCard):
                self._handle_modifier_card(player_id, card)

            self._show_tableau(player_id)
            console.print()

    def _draw_card(self) -> Card:
        """Draw a card from the deck."""
        if not self.deck:
            if not self.discard_pile:
                raise RuntimeError("No cards available to draw")

            console.print(f"[yellow]Deck exhausted! Reshuffling {len(self.discard_pile)} cards...[/yellow]\n")
            self.deck = shuffle_deck(self.discard_pile, seed=self.seed)
            self.discard_pile = []

        return self.deck.pop(0)

    def _handle_number_card(self, player_id: str, card: NumberCard) -> None:
        """Handle a number card."""
        tableau = self.tableaus[player_id]
        new_number_cards = tableau.number_cards + (card,)
        updated_tableau = replace(tableau, number_cards=new_number_cards)

        # Check for bust
        if self._check_bust(updated_tableau):
            console.print(f"[red]⚠ Duplicate card detected! {player_id} would bust![/red]\n")

            if tableau.second_chance:
                console.print(f"[yellow]{player_id} has Second Chance available.[/yellow]")
                self._handle_bust_interactive(player_id, card)
            else:
                console.print(f"[red]✗ {player_id} busted (no Second Chance)![/red]\n")
                self.tableaus[player_id] = replace(
                    updated_tableau,
                    is_active=False,
                    is_busted=True,
                )
        else:
            # No bust
            self.tableaus[player_id] = updated_tableau

            # Check for Flip 7
            if self._check_flip_7(updated_tableau):
                console.print(f"[bold green]★ FLIP 7! {player_id} achieved 7 unique cards![/bold green]\n")
                self.tableaus[player_id] = replace(
                    updated_tableau,
                    is_active=False,
                    is_passed=True,
                )

    def _handle_modifier_card(self, player_id: str, card: ModifierCard) -> None:
        """Handle a modifier card."""
        tableau = self.tableaus[player_id]
        new_modifier_cards = tableau.modifier_cards + (card,)
        self.tableaus[player_id] = replace(tableau, modifier_cards=new_modifier_cards)
        console.print(f"[green]✓ Modifier {card.modifier} added to tableau.[/green]\n")

    def _handle_action_card(self, player_id: str, card: ActionCard) -> None:
        """Handle an action card."""
        console.print(f"[magenta]Action card: {card.action_type.value}[/magenta]\n")

        eligible_targets = self._get_eligible_targets(card.action_type)

        if not eligible_targets:
            console.print("[dim]No eligible targets. Card discarded.[/dim]\n")
            self.discard_pile.append(card)
            return

        # Ask bot to choose target
        bot = self.bots[player_id]
        context = self._build_decision_context(player_id)

        console.print(f"[yellow]Eligible targets: {', '.join(eligible_targets)}[/yellow]")
        console.print(f"[yellow]Asking {bot.name} to choose target...[/yellow]")
        self._wait_for_input()

        try:
            target = execute_with_sandbox(
                bot.name,
                self.bot_timeout,
                bot.choose_action_target,
                context,
                card.action_type,
                eligible_targets,
            )
        except BotTimeout:
            target = eligible_targets[0]

        if target not in eligible_targets:
            target = eligible_targets[0]

        console.print(f"[green]→ Target: {target}[/green]\n")

        # Resolve the action
        if card.action_type == ActionType.FREEZE:
            self._resolve_freeze(target)
        elif card.action_type == ActionType.FLIP_THREE:
            self._resolve_flip_three(target)
        elif card.action_type == ActionType.SECOND_CHANCE:
            self._resolve_second_chance(target)

        self.discard_pile.append(card)

    def _handle_bust_interactive(self, player_id: str, duplicate: NumberCard) -> None:
        """Handle a bust by offering Second Chance."""
        bot = self.bots[player_id]
        context = self._build_decision_context(player_id)

        console.print(f"[yellow]Asking {bot.name} whether to use Second Chance...[/yellow]")
        self._wait_for_input()

        try:
            use_second_chance = execute_with_sandbox(
                bot.name,
                self.bot_timeout,
                bot.decide_use_second_chance,
                context,
                duplicate,
            )
        except BotTimeout:
            use_second_chance = False

        console.print(f"[green]→ Decision: {'USE' if use_second_chance else 'DECLINE'}[/green]\n")

        tableau = self.tableaus[player_id]

        if use_second_chance:
            new_number_cards = tableau.number_cards[:-1]
            self.tableaus[player_id] = replace(
                tableau,
                number_cards=new_number_cards,
                second_chance=False,
                is_active=False,
                is_passed=True,
            )
            console.print(f"[green]✓ {player_id} used Second Chance! Turn ends.[/green]\n")
        else:
            console.print(f"[red]✗ {player_id} declined Second Chance and busted![/red]\n")
            self.tableaus[player_id] = replace(
                tableau,
                is_active=False,
                is_busted=True,
            )

    def _resolve_freeze(self, player_id: str) -> None:
        """Apply freeze effect."""
        tableau = self.tableaus[player_id]
        self.tableaus[player_id] = replace(
            tableau,
            is_active=False,
            is_frozen=True,
        )
        console.print(f"[blue]❄ {player_id} has been frozen![/blue]\n")

    def _resolve_flip_three(self, player_id: str) -> None:
        """Apply Flip Three effect."""
        console.print(f"[magenta]↻ {player_id} must draw 3 cards![/magenta]\n")

        for i in range(3):
            current_tableau = self.tableaus[player_id]
            if not current_tableau.is_active:
                console.print(f"[dim]{player_id} is no longer active. Flip Three ends early.[/dim]\n")
                break

            console.print(f"[cyan]  Card {i+1}/3...[/cyan]")
            self._wait_for_input()

            card = self._draw_card()
            console.print(f"    Drew: {self._format_card(card)}\n")

            if isinstance(card, ActionCard):
                self._handle_action_card(player_id, card)
            elif isinstance(card, NumberCard):
                self._handle_number_card(player_id, card)
            elif isinstance(card, ModifierCard):
                self._handle_modifier_card(player_id, card)

            if not self.tableaus[player_id].is_active:
                break

    def _resolve_second_chance(self, player_id: str) -> None:
        """Give Second Chance card to target."""
        tableau = self.tableaus[player_id]

        if tableau.second_chance:
            console.print(f"[yellow]{player_id} already has Second Chance![/yellow]\n")
            # Would need to redistribute - skipping for simplicity
            return

        self.tableaus[player_id] = replace(tableau, second_chance=True)
        console.print(f"[green]✓ {player_id} received Second Chance![/green]\n")

    def _check_bust(self, tableau: PlayerTableau) -> bool:
        """Check if tableau has duplicate number cards."""
        values = [card.value for card in tableau.number_cards]
        return len(values) != len(set(values))

    def _check_flip_7(self, tableau: PlayerTableau) -> bool:
        """Check if player has achieved Flip 7."""
        return has_flip_7(tableau.number_cards)

    def _is_round_complete(self) -> bool:
        """Check if the round is complete."""
        return all(not tableau.is_active for tableau in self.tableaus.values())

    def _calculate_final_scores(self) -> dict[str, int]:
        """Calculate final scores for all players."""
        scores = {}

        for player_id, tableau in self.tableaus.items():
            breakdown = calculate_score(tableau)
            scores[player_id] = breakdown.final_score

            # Show detailed breakdown
            table = Table(title=f"{player_id} - Final Score", show_header=True, header_style="bold cyan")
            table.add_column("Component", style="yellow")
            table.add_column("Value", justify="right", style="white")

            table.add_row("Number Cards Sum", str(breakdown.number_cards_sum))
            table.add_row("After X2 Multiplier", str(breakdown.after_x2_multiplier))
            table.add_row("Modifier Additions", f"+{breakdown.modifier_additions}")
            table.add_row("Flip 7 Bonus", f"+{breakdown.flip_7_bonus}")
            table.add_row("[bold]FINAL SCORE[/bold]", f"[bold]{breakdown.final_score}[/bold]")

            console.print(table)
            console.print()

        return scores

    def _get_eligible_targets(self, action_type: ActionType) -> list[str]:
        """Get list of eligible targets for an action card."""
        if action_type == ActionType.SECOND_CHANCE:
            return [
                pid
                for pid in self.player_ids
                if self.tableaus[pid].is_active and not self.tableaus[pid].second_chance
            ]
        else:
            return [pid for pid in self.player_ids if self.tableaus[pid].is_active]

    def _build_decision_context(self, player_id: str) -> BotDecisionContext:
        """Build a decision context for a bot."""
        my_tableau = self.tableaus[player_id]
        opponent_tableaus = {
            pid: tableau for pid, tableau in self.tableaus.items() if pid != player_id
        }

        return BotDecisionContext(
            my_tableau=my_tableau,
            opponent_tableaus=opponent_tableaus,
            deck_remaining=len(self.deck),
            my_current_score=self.starting_scores[player_id],
            opponent_scores={pid: self.starting_scores[pid] for pid in opponent_tableaus},
            current_round=self.round_number,
            target_score=WINNING_SCORE,
        )

    def _wait_for_input(self) -> None:
        """Wait for user to press Enter to continue."""
        console.input("[dim]Press Enter to continue...[/dim] ")

    def _format_card(self, card: Card) -> str:
        """Format a card for display."""
        if isinstance(card, NumberCard):
            return f"[bold cyan]Number {card.value}[/bold cyan]"
        elif isinstance(card, ModifierCard):
            return f"[bold yellow]Modifier {card.modifier}[/bold yellow]"
        elif isinstance(card, ActionCard):
            return f"[bold magenta]Action {card.action_type.value}[/bold magenta]"
        return str(card)

    def _show_tableau(self, player_id: str) -> None:
        """Show a single player's tableau."""
        tableau = self.tableaus[player_id]

        table = Table(title=f"{player_id}'s Tableau", show_header=True, header_style="bold cyan")
        table.add_column("Card Type", style="yellow")
        table.add_column("Cards", style="white")

        # Number cards
        if tableau.number_cards:
            numbers = ", ".join(str(c.value) for c in tableau.number_cards)
            unique_count = len(set(c.value for c in tableau.number_cards))
            table.add_row("Number Cards", f"{numbers} ({unique_count} unique)")
        else:
            table.add_row("Number Cards", "[dim]None[/dim]")

        # Modifier cards
        if tableau.modifier_cards:
            modifiers = ", ".join(c.modifier for c in tableau.modifier_cards)
            table.add_row("Modifier Cards", modifiers)
        else:
            table.add_row("Modifier Cards", "[dim]None[/dim]")

        # Second Chance
        table.add_row("Second Chance", "✓" if tableau.second_chance else "✗")

        # Status
        status_parts = []
        if tableau.is_busted:
            status_parts.append("[red]BUSTED[/red]")
        if tableau.is_frozen:
            status_parts.append("[blue]FROZEN[/blue]")
        if tableau.is_passed:
            status_parts.append("[green]PASSED[/green]")
        if tableau.is_active:
            status_parts.append("[yellow]ACTIVE[/yellow]")

        table.add_row("Status", " ".join(status_parts) if status_parts else "[dim]Inactive[/dim]")

        console.print(table)

    def _show_all_tableaus(self, highlight: str | None = None) -> None:
        """Show all player tableaus."""
        for player_id in self.player_ids:
            if player_id == highlight:
                console.print(f"[bold]>>> {player_id} (Current Player) <<<[/bold]")
            else:
                console.print(f"[dim]{player_id}[/dim]")

            self._show_tableau(player_id)
            console.print()

    def _show_decision_context(self, player_id: str, context: BotDecisionContext) -> None:
        """Show complete decision context that the bot receives."""
        table = Table(title="Decision Context (What the Bot Sees)", show_header=True, header_style="bold yellow")
        table.add_column("Property", style="cyan", width=25)
        table.add_column("Value", style="white")

        # My tableau info
        my_numbers = [c.value for c in context.my_tableau.number_cards]
        hand_value = sum(my_numbers)
        unique_numbers = len(set(my_numbers))
        my_modifiers = [c.modifier for c in context.my_tableau.modifier_cards]

        table.add_row("[bold]My Tableau[/bold]", "")
        table.add_row("  Hand Value", str(hand_value))
        table.add_row("  Unique Numbers", f"{unique_numbers}/7")
        table.add_row("  Number Cards", ", ".join(map(str, my_numbers)) if my_numbers else "None")
        table.add_row("  Modifier Cards", ", ".join(my_modifiers) if my_modifiers else "None")
        table.add_row("  Has Second Chance", "Yes" if context.my_tableau.second_chance else "No")

        # Opponent info
        table.add_row("[bold]Opponents[/bold]", "")
        for opp_id, opp_tableau in context.opponent_tableaus.items():
            opp_numbers = [c.value for c in opp_tableau.number_cards]
            opp_hand_value = sum(opp_numbers)
            opp_unique = len(set(opp_numbers))
            opp_status = []
            if opp_tableau.is_busted:
                opp_status.append("BUSTED")
            elif opp_tableau.is_frozen:
                opp_status.append("FROZEN")
            elif opp_tableau.is_passed:
                opp_status.append("PASSED")
            elif opp_tableau.is_active:
                opp_status.append("ACTIVE")
            status_str = " ".join(opp_status) if opp_status else "Inactive"
            table.add_row(f"  {opp_id}", f"Value: {opp_hand_value}, Unique: {opp_unique}, {status_str}")

        # Game state
        table.add_row("[bold]Game State[/bold]", "")
        table.add_row("  Cards Remaining in Deck", str(context.deck_remaining))
        table.add_row("  Current Round", str(context.current_round))
        table.add_row("  Target Score", str(context.target_score))

        # Scores (cumulative across rounds)
        table.add_row("[bold]Cumulative Scores[/bold]", "")
        table.add_row(f"  My Score ({player_id})", str(context.my_current_score))
        for opp_id, opp_score in context.opponent_scores.items():
            table.add_row(f"  {opp_id}", str(opp_score))

        console.print(table)

"""Round execution engine for Flip 7 game.

This module implements the RoundEngine class which orchestrates a complete round
of Flip 7, including card dealing, turn management, action card resolution, and
scoring. This is the core game logic that ties together all game mechanics.
"""

from dataclasses import replace
from datetime import datetime, timezone
from typing import Any

from flip7.bots.sandbox import execute_with_sandbox
from flip7.constants import FLIP_7_THRESHOLD, WINNING_SCORE
from flip7.core.deck import create_deck, shuffle_deck
from flip7.core.scoring import calculate_score, has_flip_7
from flip7.events.event_logger import EventLogger
from flip7.types.bot_interface import Bot
from flip7.types.cards import ActionCard, ActionType, Card, ModifierCard, NumberCard
from flip7.types.errors import BotTimeout
from flip7.types.events import BotDecisionContext, Event
from flip7.types.game_state import PlayerTableau, RoundState


# Default bot timeout in seconds
DEFAULT_BOT_TIMEOUT = 5.0


class RoundEngine:
    """
    Orchestrates a complete round of Flip 7 with all game mechanics.

    The RoundEngine manages the complete lifecycle of a round, from initial deal
    through turn execution to final scoring. It handles all game mechanics including:
    - Card drawing and dealing
    - Action card resolution (Freeze, Flip Three, Second Chance)
    - Bust detection and handling
    - Flip 7 bonus detection
    - Turn management and player state tracking
    - Event logging for replay and analytics

    Attributes:
        player_ids: List of player IDs in turn order
        bots: Mapping of player IDs to their Bot implementations
        event_logger: Logger for recording game events
        seed: Random seed for deterministic deck shuffling
        bot_timeout: Timeout in seconds for bot decisions
        deck: Current draw pile (as list, top card is at index 0)
        discard_pile: Discarded cards (as list, most recent on top)
        tableaus: Current state of each player's tableau
        current_player_index: Index into player_ids for current turn
        round_number: The current round number (for logging)
        game_id: Unique identifier for the game (for logging)
    """

    def __init__(
        self,
        player_ids: list[str],
        bots: dict[str, Bot],
        event_logger: EventLogger,
        deck: list[Card],
        discard_pile: list[Card],
        round_number: int = 1,
        game_id: str = "game",
        seed: int | None = None,
        bot_timeout: float = DEFAULT_BOT_TIMEOUT,
    ) -> None:
        """
        Initialize a new round engine.

        Args:
            player_ids: List of player IDs participating in the round, in turn order
            bots: Mapping of player IDs to their Bot implementations
            event_logger: EventLogger for recording game events
            deck: The current draw pile (modified in place during round)
            discard_pile: The current discard pile (modified in place during round)
            round_number: The current round number (default: 1)
            game_id: Unique identifier for the game (default: "game")
            seed: Optional random seed for deterministic shuffling (used for reshuffling)
            bot_timeout: Timeout in seconds for bot decisions (default: 5.0)

        Raises:
            ValueError: If player_ids is empty or bots don't match player_ids
        """
        if not player_ids:
            raise ValueError("Must have at least one player")

        missing_bots = set(player_ids) - set(bots.keys())
        if missing_bots:
            raise ValueError(f"Missing bots for players: {missing_bots}")

        self.player_ids = player_ids
        self.bots = bots
        self.event_logger = event_logger
        self.round_number = round_number
        self.game_id = game_id
        self.seed = seed
        self.bot_timeout = bot_timeout

        # Use provided deck and discard pile (persistent across rounds)
        self.deck = deck
        self.discard_pile = discard_pile

        # Initialize tableaus for all players
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

    def execute_round(self) -> dict[str, int]:
        """
        Execute a complete round and return final scores for each player.

        This is the main entry point for round execution. It orchestrates:
        1. Initial deal (1 card to each player)
        2. Turn cycle (players take turns until round ends)
        3. Final scoring

        Returns:
            Dictionary mapping player IDs to their scores for this round

        Example:
            >>> engine = RoundEngine(["p1", "p2"], bots, logger, seed=42)
            >>> scores = engine.execute_round()
            >>> scores["p1"]
            25
        """
        # Log round start
        self._log_event(
            "round_started",
            data={
                "player_ids": self.player_ids,
                "deck_size": len(self.deck),
            },
        )

        # Phase 1: Initial deal
        self._initial_deal()

        # Phase 2: Turn cycle
        self._execute_turn_cycle()

        # Phase 3: Calculate final scores
        scores = self._calculate_final_scores()

        # Phase 4: Cleanup - move all tableau cards to discard pile
        self._cleanup_tableaus()

        # Log round end
        self._log_event(
            "round_ended",
            data={"scores": scores},
        )

        return scores

    def _initial_deal(self) -> None:
        """
        Deal 1 card to each player and handle action cards immediately.

        During initial deal:
        - Each player receives one card in turn order
        - If a player receives an action card, it's resolved immediately
        - Number and modifier cards are added to the player's tableau normally
        """
        for player_id in self.player_ids:
            card = self._draw_card(player_id)

            # Handle action cards immediately during initial deal
            if isinstance(card, ActionCard):
                self._handle_action_card(player_id, card)
            elif isinstance(card, NumberCard):
                self._handle_number_card(player_id, card)
            elif isinstance(card, ModifierCard):
                self._handle_modifier_card(player_id, card)

    def _execute_turn_cycle(self) -> None:
        """
        Loop through active players until the round ends.

        The turn cycle continues until all players have either:
        - Passed voluntarily
        - Busted from duplicate cards
        - Been frozen by a Freeze action
        - Achieved Flip 7 (auto-pass)
        """
        while not self._is_round_complete():
            player_id = self.player_ids[self.current_player_index]
            tableau = self.tableaus[player_id]

            # Only execute turn if player is still active
            if tableau.is_active:
                self._execute_player_turn(player_id)

            # Move to next player
            self.current_player_index = (self.current_player_index + 1) % len(self.player_ids)

    def _execute_player_turn(self, player_id: str) -> None:
        """
        Execute a single player's turn with bot decision.

        The player decides whether to hit or pass. If they hit, they draw a card
        and handle its effects. If they pass, they end their participation in the round.

        Args:
            player_id: The ID of the player taking their turn
        """
        bot = self.bots[player_id]
        tableau = self.tableaus[player_id]

        # Build decision context
        context = self._build_decision_context(player_id)

        # Ask bot to decide: hit or pass
        try:
            decision = execute_with_sandbox(
                bot.name,
                self.bot_timeout,
                bot.decide_hit_or_pass,
                context,
            )
        except BotTimeout:
            # Bot timed out - treat as bust
            self._log_event(
                "player_busted",
                player_id=player_id,
                data={"reason": "timeout"},
            )
            self.tableaus[player_id] = replace(
                tableau,
                is_active=False,
                is_busted=True,
            )
            return

        if decision == "pass":
            # Player passes - lock in their score
            self._log_event("player_passed", player_id=player_id)
            self.tableaus[player_id] = replace(
                tableau,
                is_active=False,
                is_passed=True,
            )
        else:
            # Player hits - draw a card
            card = self._draw_card(player_id)

            # Handle the drawn card
            if isinstance(card, ActionCard):
                self._handle_action_card(player_id, card)
            elif isinstance(card, NumberCard):
                self._handle_number_card(player_id, card)
            elif isinstance(card, ModifierCard):
                self._handle_modifier_card(player_id, card)

    def _draw_card(self, player_id: str) -> Card:
        """
        Draw a card from the deck, handling deck exhaustion/reshuffle.

        If the deck is empty, shuffles the discard pile to create a new deck.
        Note: Cards currently in player tableaus are NOT shuffled back.

        Args:
            player_id: The ID of the player drawing the card

        Returns:
            The drawn card

        Raises:
            RuntimeError: If both deck and discard pile are empty (should never happen)
        """
        # Check if deck is empty
        if not self.deck:
            # Reshuffle discard pile into deck
            if not self.discard_pile:
                raise RuntimeError("No cards available to draw")

            self._log_event(
                "round_started",  # Reusing event type for deck reshuffle
                data={"reason": "deck_exhausted", "cards_reshuffled": len(self.discard_pile)},
            )

            self.deck = shuffle_deck(self.discard_pile, seed=self.seed)
            self.discard_pile = []

        # Draw top card
        card = self.deck.pop(0)

        # Log the draw
        self._log_event(
            "card_dealt",
            player_id=player_id,
            data={"card": card, "deck_remaining": len(self.deck)},
        )

        return card

    def _handle_number_card(self, player_id: str, card: NumberCard) -> None:
        """
        Handle a number card: check for duplicate, bust, or Flip 7.

        When a player receives a number card:
        1. Add it to their tableau
        2. Check if it creates a duplicate (bust condition)
        3. If bust, offer Second Chance if available
        4. Check if player achieved Flip 7 (7 unique numbers)

        Args:
            player_id: The ID of the player receiving the card
            card: The number card that was drawn
        """
        tableau = self.tableaus[player_id]

        # Add card to tableau temporarily to check for bust
        new_number_cards = tableau.number_cards + (card,)
        updated_tableau = replace(tableau, number_cards=new_number_cards)

        # Check for bust (duplicate number cards)
        if self._check_bust(updated_tableau):
            # Player has a duplicate - offer Second Chance if available
            if tableau.second_chance:
                self._handle_bust(player_id, card)
            else:
                # Bust without Second Chance
                self._log_event(
                    "player_busted",
                    player_id=player_id,
                    data={"duplicate": card},
                )
                self.tableaus[player_id] = replace(
                    updated_tableau,
                    is_active=False,
                    is_busted=True,
                )
        else:
            # No bust - update tableau
            self.tableaus[player_id] = updated_tableau

            # Log the hit
            self._log_event(
                "player_hit",
                player_id=player_id,
                data={"card": card},
            )

            # Check for Flip 7
            if self._check_flip_7(updated_tableau):
                self._auto_pass_on_flip_7(player_id)

    def _handle_modifier_card(self, player_id: str, card: ModifierCard) -> None:
        """
        Add a modifier card to the player's tableau.

        Modifier cards don't count as number cards and can't cause busts.
        They are simply added to the tableau for scoring at the end of the round.

        Args:
            player_id: The ID of the player receiving the card
            card: The modifier card that was drawn
        """
        tableau = self.tableaus[player_id]
        new_modifier_cards = tableau.modifier_cards + (card,)

        self.tableaus[player_id] = replace(
            tableau,
            modifier_cards=new_modifier_cards,
        )

        self._log_event(
            "player_hit",
            player_id=player_id,
            data={"card": card},
        )

    def _handle_action_card(self, player_id: str, card: ActionCard) -> None:
        """
        Resolve an action card by having the bot choose a target.

        Action cards are immediately resolved when drawn. The drawing player
        chooses which eligible player receives the effect.

        Args:
            player_id: The ID of the player who drew the action card
            card: The action card that was drawn
        """
        self._log_event(
            "action_card_drawn",
            player_id=player_id,
            data={"action": card.action_type.value},
        )

        # Determine eligible targets based on action type
        eligible_targets = self._get_eligible_targets(card.action_type)

        # If no eligible targets, discard the card
        if not eligible_targets:
            self.discard_pile.append(card)
            return

        # Ask bot to choose target
        bot = self.bots[player_id]
        context = self._build_decision_context(player_id)

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
            # Bot timed out - choose first eligible target
            target = eligible_targets[0]

        # Validate target
        if target not in eligible_targets:
            target = eligible_targets[0]

        # Resolve the action
        if card.action_type == ActionType.FREEZE:
            self._resolve_freeze(target)
        elif card.action_type == ActionType.FLIP_THREE:
            self._resolve_flip_three(target)
        elif card.action_type == ActionType.SECOND_CHANCE:
            self._resolve_second_chance(target)

        # Action card has been used - add to discard pile
        self.discard_pile.append(card)

        self._log_event(
            "action_card_resolved",
            player_id=player_id,
            data={
                "action": card.action_type.value,
                "target": target,
            },
        )

    def _resolve_freeze(self, player_id: str) -> None:
        """
        Apply freeze effect: player immediately passes.

        The frozen player locks in their current score and becomes inactive.
        They cannot take any more turns this round.

        Args:
            player_id: The ID of the player being frozen
        """
        tableau = self.tableaus[player_id]

        self.tableaus[player_id] = replace(
            tableau,
            is_active=False,
            is_frozen=True,
        )

        self._log_event(
            "freeze_applied",
            player_id=player_id,
        )

    def _resolve_flip_three(self, player_id: str) -> None:
        """
        Apply Flip Three effect: player draws 3 cards recursively.

        The target player draws 3 cards, handling each card as normal:
        - Number cards may cause busts
        - Action cards are resolved recursively
        - Modifier cards are added to tableau
        - Stop early if player busts or achieves Flip 7

        Args:
            player_id: The ID of the player receiving Flip Three
        """
        self._log_event(
            "flip_three_triggered",
            player_id=player_id,
        )

        tableau = self.tableaus[player_id]

        # Draw 3 cards (or until bust/Flip 7)
        for i in range(3):
            # Check if player is still active (might have busted or achieved Flip 7)
            current_tableau = self.tableaus[player_id]
            if not current_tableau.is_active:
                break

            # Draw a card
            card = self._draw_card(player_id)

            # Handle the card based on its type
            if isinstance(card, ActionCard):
                # Resolve action card immediately
                self._handle_action_card(player_id, card)
            elif isinstance(card, NumberCard):
                self._handle_number_card(player_id, card)
            elif isinstance(card, ModifierCard):
                self._handle_modifier_card(player_id, card)

            # Check again if player is still active after handling the card
            if not self.tableaus[player_id].is_active:
                break

    def _resolve_second_chance(self, player_id: str) -> None:
        """
        Give Second Chance card to target player.

        If the target already has a Second Chance, they must choose another player
        to give it to. If no other eligible players exist, the card is discarded.

        Args:
            player_id: The ID of the player receiving Second Chance
        """
        tableau = self.tableaus[player_id]

        # Check if player already has Second Chance
        if tableau.second_chance:
            # Must give it to another active player without Second Chance
            eligible = [
                pid
                for pid in self.player_ids
                if pid != player_id
                and self.tableaus[pid].is_active
                and not self.tableaus[pid].second_chance
            ]

            if not eligible:
                # No eligible recipients - discard the card
                # Note: We don't add the card to discard pile as it was never materialized
                return

            # Ask bot to choose who gets it
            bot = self.bots[player_id]
            context = self._build_decision_context(player_id)

            try:
                new_target = execute_with_sandbox(
                    bot.name,
                    self.bot_timeout,
                    bot.choose_action_target,
                    context,
                    ActionType.SECOND_CHANCE,
                    eligible,
                )
            except BotTimeout:
                new_target = eligible[0]

            # Validate target
            if new_target not in eligible:
                new_target = eligible[0]

            # Give Second Chance to new target
            player_id = new_target

        # Give Second Chance to player
        self.tableaus[player_id] = replace(
            self.tableaus[player_id],
            second_chance=True,
        )

        self._log_event(
            "action_card_resolved",
            player_id=player_id,
            data={"action": "SECOND_CHANCE"},
        )

    def _check_bust(self, tableau: PlayerTableau) -> bool:
        """
        Check if a tableau has duplicate number cards (bust condition).

        A player busts when they have two or more cards with the same number value.

        Args:
            tableau: The player's tableau to check

        Returns:
            True if the tableau contains duplicate number cards, False otherwise
        """
        values = [card.value for card in tableau.number_cards]
        return len(values) != len(set(values))

    def _handle_bust(self, player_id: str, duplicate: NumberCard) -> None:
        """
        Handle a bust by offering Second Chance to the bot.

        If the player has a Second Chance card, they can choose to use it to
        discard the duplicate and avoid busting. If they use it, their turn ends.

        Args:
            player_id: The ID of the player who would bust
            duplicate: The duplicate number card that caused the bust
        """
        tableau = self.tableaus[player_id]
        bot = self.bots[player_id]
        context = self._build_decision_context(player_id)

        # Ask bot if they want to use Second Chance
        try:
            use_second_chance = execute_with_sandbox(
                bot.name,
                self.bot_timeout,
                bot.decide_use_second_chance,
                context,
                duplicate,
            )
        except BotTimeout:
            # Bot timed out - treat as bust
            use_second_chance = False

        if use_second_chance:
            # Use Second Chance - remove it and the duplicate card
            # The duplicate is the last card added
            new_number_cards = tableau.number_cards[:-1]  # Remove the duplicate

            self.tableaus[player_id] = replace(
                tableau,
                number_cards=new_number_cards,
                second_chance=False,
                is_active=False,  # Turn ends immediately
                is_passed=True,   # Count as passed (not busted)
            )

            self._log_event(
                "second_chance_used",
                player_id=player_id,
                data={"duplicate": duplicate},
            )
        else:
            # Bust normally
            self._log_event(
                "player_busted",
                player_id=player_id,
                data={"duplicate": duplicate},
            )

            self.tableaus[player_id] = replace(
                tableau,
                is_active=False,
                is_busted=True,
            )

    def _check_flip_7(self, tableau: PlayerTableau) -> bool:
        """
        Check if a player has achieved Flip 7 (7 unique number cards).

        Args:
            tableau: The player's tableau to check

        Returns:
            True if the player has exactly 7 unique number card values
        """
        return has_flip_7(tableau.number_cards)

    def _auto_pass_on_flip_7(self, player_id: str) -> None:
        """
        Automatically pass when Flip 7 is achieved.

        When a player collects 7 unique number cards, they automatically pass
        and receive the Flip 7 bonus.

        Args:
            player_id: The ID of the player who achieved Flip 7
        """
        tableau = self.tableaus[player_id]

        self.tableaus[player_id] = replace(
            tableau,
            is_active=False,
            is_passed=True,
        )

        self._log_event(
            "flip_7_achieved",
            player_id=player_id,
        )

    def _is_round_complete(self) -> bool:
        """
        Check if the round is complete.

        A round is complete when all players have either:
        - Passed voluntarily
        - Busted from duplicate cards
        - Been frozen by a Freeze action
        - Achieved Flip 7 (auto-pass)

        Returns:
            True if the round is complete, False otherwise
        """
        return all(not tableau.is_active for tableau in self.tableaus.values())

    def _calculate_final_scores(self) -> dict[str, int]:
        """
        Calculate final scores for all players using scoring.py.

        Returns:
            Dictionary mapping player IDs to their scores for this round
        """
        scores = {}

        for player_id, tableau in self.tableaus.items():
            breakdown = calculate_score(tableau)
            scores[player_id] = breakdown.final_score

            # Log the score breakdown
            self._log_event(
                "round_ended",
                player_id=player_id,
                data={
                    "score": breakdown.final_score,
                    "breakdown": {
                        "number_cards_sum": breakdown.number_cards_sum,
                        "after_x2_multiplier": breakdown.after_x2_multiplier,
                        "modifier_additions": breakdown.modifier_additions,
                        "flip_7_bonus": breakdown.flip_7_bonus,
                    },
                },
            )

        return scores

    def _cleanup_tableaus(self) -> None:
        """
        Collect all cards from player tableaus and add to discard pile.

        This is called at the end of a round to return all cards to the discard pile.
        According to the rules, all cards (including Second Chance) are discarded at
        the end of each round, regardless of whether they were used.

        Note: Cards are added to the discard pile (NOT the deck), so they will only
        be reshuffled if the deck runs out during a future round.
        """
        for player_id, tableau in self.tableaus.items():
            # Collect all number cards
            for num_card in tableau.number_cards:
                self.discard_pile.append(num_card)

            # Collect all modifier cards
            for mod_card in tableau.modifier_cards:
                self.discard_pile.append(mod_card)

            # Note: Second Chance and action cards are not physical cards in the tableau
            # in this implementation (they're boolean flags), so nothing to discard for them

    def _get_eligible_targets(self, action_type: ActionType) -> list[str]:
        """
        Get list of eligible targets for an action card.

        Eligibility depends on the action type:
        - FREEZE: Active players (not frozen, not passed, not busted)
        - FLIP_THREE: Active players
        - SECOND_CHANCE: Active players without Second Chance

        Args:
            action_type: The type of action card

        Returns:
            List of player IDs that can be targeted
        """
        if action_type == ActionType.SECOND_CHANCE:
            # Can target active players without Second Chance
            return [
                pid
                for pid in self.player_ids
                if self.tableaus[pid].is_active and not self.tableaus[pid].second_chance
            ]
        else:
            # FREEZE and FLIP_THREE target active players
            return [pid for pid in self.player_ids if self.tableaus[pid].is_active]

    def _build_decision_context(self, player_id: str) -> BotDecisionContext:
        """
        Build a decision context for a bot.

        Provides the bot with complete information about the game state,
        including their own tableau, opponent tableaus, and remaining deck size.

        Args:
            player_id: The ID of the player whose context to build

        Returns:
            BotDecisionContext with complete game information
        """
        my_tableau = self.tableaus[player_id]
        opponent_tableaus = {
            pid: tableau for pid, tableau in self.tableaus.items() if pid != player_id
        }

        # For now, we don't track cumulative scores in RoundEngine
        # The caller (Game) would track those
        return BotDecisionContext(
            my_tableau=my_tableau,
            opponent_tableaus=opponent_tableaus,
            deck_remaining=len(self.deck),
            my_current_score=0,  # Placeholder - would be provided by Game
            opponent_scores={pid: 0 for pid in opponent_tableaus},  # Placeholder
            current_round=self.round_number,
            target_score=WINNING_SCORE,
        )

    def _log_event(
        self,
        event_type: str,
        player_id: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> None:
        """
        Log a game event.

        Creates an Event object and logs it via the EventLogger.

        Args:
            event_type: The type of event
            player_id: The player associated with the event (None for round-level events)
            data: Additional event data
        """
        event = Event(
            event_type=event_type,  # type: ignore[arg-type]
            timestamp=datetime.now(timezone.utc),
            game_id=self.game_id,
            round_number=self.round_number,
            player_id=player_id,
            data=data or {},
        )
        self.event_logger.log_event(event)

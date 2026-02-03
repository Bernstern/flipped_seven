"""
ScaredyBot implementation - plays it safe to avoid busting.

This bot implements a conservative strategy that minimizes risk:
- Passes when hand value reaches 15 or higher
- Always uses Second Chance to avoid busting
- Randomly selects action targets
"""

import random
from typing import Literal

from flip7.bots.base import BaseBot
from flip7.types.cards import ActionType, NumberCard
from flip7.types.events import BotDecisionContext


class ScaredyBot(BaseBot):
    """
    A bot that plays conservatively to minimize busting.

    Strategy:
    - Calculates current hand value from number cards
    - Passes if hand value is 15 or higher
    - Hits if hand value is below 15
    - Always uses Second Chance when available to avoid busting
    - Randomly selects action card targets

    This bot prioritizes safety over maximizing score, making it a good
    opponent for testing aggressive strategies.
    """

    def __init__(self, bot_name: str = "ScaredyBot") -> None:
        """
        Initialize the ScaredyBot.

        Args:
            bot_name: The unique identifier for this bot instance
        """
        super().__init__(bot_name)
        self._pass_threshold = 15

    def _calculate_hand_value(self, context: BotDecisionContext) -> int:
        """
        Calculate the current value of number cards in hand.

        Sums the values of all number cards currently in the bot's tableau.

        Args:
            context: Game state information

        Returns:
            Total value of number cards
        """
        # my_tableau.number_cards is a tuple of NumberCard objects
        return sum(card.value for card in context.my_tableau.number_cards)

    def decide_hit_or_pass(self, context: BotDecisionContext) -> Literal["hit", "pass"]:
        """
        Decide to pass if hand value is 15+, otherwise hit.

        This conservative strategy aims to minimize busting while building
        a reasonable score.

        Args:
            context: Complete game state information

        Returns:
            "pass" if hand value >= 15, otherwise "hit"
        """
        hand_value = self._calculate_hand_value(context)

        if hand_value >= self._pass_threshold:
            return "pass"
        return "hit"

    def decide_use_second_chance(
        self, context: BotDecisionContext, duplicate: NumberCard
    ) -> bool:
        """
        Always use Second Chance to avoid busting.

        The conservative strategy prioritizes avoiding busts, so Second Chance
        is always used when available.

        Args:
            context: Complete game state information (not used)
            duplicate: The duplicate card that would cause a bust (not used)

        Returns:
            Always returns True
        """
        return True

    def choose_action_target(
        self, context: BotDecisionContext, action: ActionType, eligible: list[str]
    ) -> str:
        """
        Randomly choose an action target from eligible players.

        The bot doesn't implement strategic targeting, so it randomly
        selects from available options.

        Args:
            context: Complete game state information (not used)
            action: The type of action card (not used)
            eligible: List of eligible player names

        Returns:
            A randomly selected player name from the eligible list

        Raises:
            ValueError: If eligible list is empty
        """
        if not eligible:
            raise ValueError("No eligible targets available for action card")

        return random.choice(eligible)

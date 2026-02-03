"""Hit17Bot - Hits until 17, then always stays.

Simple strategy bot that draws cards until hand value reaches 17,
then passes. Similar to dealer rules in Blackjack.
"""

from typing import Literal

from flip7.bots.base import BaseBot
from flip7.types.cards import ActionType, NumberCard
from flip7.types.events import BotDecisionContext


class Hit17Bot(BaseBot):
    """Bot that hits until hand value reaches 17, then stays."""

    def decide_hit_or_pass(self, context: BotDecisionContext) -> Literal["hit", "pass"]:
        """Hit until hand value >= 17, then pass.

        Args:
            context: Current game state

        Returns:
            "hit" if hand value < 17, "pass" otherwise
        """
        hand_value = sum(card.value for card in context.my_tableau.number_cards)

        if hand_value < 17:
            return "hit"
        else:
            return "pass"

    def decide_use_second_chance(
        self, context: BotDecisionContext, duplicate: NumberCard
    ) -> bool:
        """Use Second Chance if hand value >= 15.

        Worth saving the hand if we're close to the target.

        Args:
            context: Current game state
            duplicate: The duplicate card that caused the bust

        Returns:
            True if hand value >= 15, False otherwise
        """
        hand_value = sum(card.value for card in context.my_tableau.number_cards)
        return hand_value >= 15

    def choose_action_target(
        self,
        context: BotDecisionContext,
        action: ActionType,
        eligible: list[str],
    ) -> str:
        """Choose action card target.

        Simple strategy:
        - FREEZE: Target player with highest hand value
        - FLIP_THREE: Target player with fewest cards (risky for them)
        - SECOND_CHANCE: Give to self if eligible, else to lowest scorer

        Args:
            context: Current game state
            action: The action type to resolve
            eligible: List of eligible player IDs

        Returns:
            Player ID to target
        """
        if not eligible:
            return context.my_tableau.player_id

        if action == ActionType.FREEZE:
            # Freeze the player with the highest hand value
            best_target = max(
                eligible,
                key=lambda pid: (
                    sum(c.value for c in context.opponent_tableaus[pid].number_cards)
                    if pid in context.opponent_tableaus
                    else 0
                ),
            )
            return best_target

        elif action == ActionType.FLIP_THREE:
            # Force the player with fewest cards to draw more (risky)
            best_target = min(
                eligible,
                key=lambda pid: (
                    len(context.opponent_tableaus[pid].number_cards)
                    if pid in context.opponent_tableaus
                    else 999
                ),
            )
            return best_target

        elif action == ActionType.SECOND_CHANCE:
            # Give to self if eligible
            my_id = context.my_tableau.player_id
            if my_id in eligible:
                return my_id

            # Otherwise give to lowest scoring opponent
            best_target = min(
                eligible, key=lambda pid: context.opponent_scores.get(pid, 0)
            )
            return best_target

        return eligible[0]

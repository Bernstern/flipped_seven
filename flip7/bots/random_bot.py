"""
RandomBot implementation - makes random valid decisions.

This bot serves as a baseline opponent and testing reference. It makes
completely random choices for all decisions.
"""

import random
from typing import Literal

from flip7.bots.base import BaseBot
from flip7.types.cards import ActionType, NumberCard
from flip7.types.events import BotDecisionContext


class RandomBot(BaseBot):
    """
    A bot that makes random valid decisions.

    This bot:
    - Randomly chooses to hit or pass with 50/50 probability
    - Randomly decides whether to use Second Chance with 50/50 probability
    - Randomly selects action targets from eligible players

    This bot is useful as a baseline for testing and as a simple opponent
    for tournament play.
    """

    def __init__(self, bot_name: str = "RandomBot") -> None:
        """
        Initialize the RandomBot.

        Args:
            bot_name: The unique identifier for this bot instance
        """
        super().__init__(bot_name)

    def decide_hit_or_pass(self, context: BotDecisionContext) -> Literal["hit", "pass"]:
        """
        Randomly decide whether to hit or pass.

        Makes a random choice with 50% probability for each option.

        Args:
            context: Complete game state information (not used)

        Returns:
            "hit" or "pass" chosen randomly
        """
        return random.choice(["hit", "pass"])

    def decide_use_second_chance(
        self, context: BotDecisionContext, duplicate: NumberCard
    ) -> bool:
        """
        Randomly decide whether to use Second Chance.

        Makes a random choice with 50% probability for each option.

        Args:
            context: Complete game state information (not used)
            duplicate: The duplicate card that would cause a bust (not used)

        Returns:
            True or False chosen randomly
        """
        return random.choice([True, False])

    def choose_action_target(
        self, context: BotDecisionContext, action: ActionType, eligible: list[str]
    ) -> str:
        """
        Randomly choose an action target from eligible players.

        Selects a random player from the list of eligible targets.

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

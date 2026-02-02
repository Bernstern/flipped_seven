"""
Abstract base class for bots implementing the Bot protocol.

This module provides a base class that concrete bot implementations can inherit from.
While the Bot protocol defines the interface, this base class provides common
functionality and ensures proper implementation of the protocol.
"""

from abc import ABC, abstractmethod
from typing import Literal

from flip7.types.bot_interface import Bot
from flip7.types.cards import ActionType, NumberCard
from flip7.types.events import BotDecisionContext


class BaseBot(ABC):
    """
    Abstract base class for all bot implementations.

    Concrete bot classes should inherit from this class and implement
    the three required decision methods. This class ensures that all
    bots properly implement the Bot protocol.
    """

    def __init__(self, bot_name: str) -> None:
        """
        Initialize the bot with a unique name.

        Args:
            bot_name: The unique identifier for this bot instance
        """
        self._name = bot_name

    @property
    def name(self) -> str:
        """
        Returns the unique name/identifier for this bot.

        Returns:
            The bot's name
        """
        return self._name

    @abstractmethod
    def decide_hit_or_pass(self, context: BotDecisionContext) -> Literal["hit", "pass"]:
        """
        Decide whether to hit (draw another card) or pass (end turn).

        Args:
            context: Complete game state information

        Returns:
            "hit" to draw another card, or "pass" to end the turn
        """
        pass

    @abstractmethod
    def decide_use_second_chance(
        self, context: BotDecisionContext, duplicate: NumberCard
    ) -> bool:
        """
        Decide whether to use a Second Chance card to avoid busting.

        Args:
            context: Complete game state information
            duplicate: The duplicate number card that would cause a bust

        Returns:
            True to use the Second Chance card, False to bust normally
        """
        pass

    @abstractmethod
    def choose_action_target(
        self, context: BotDecisionContext, action: ActionType, eligible: list[str]
    ) -> str:
        """
        Choose which player should receive an action card effect.

        Args:
            context: Complete game state information
            action: The type of action card that was drawn
            eligible: List of player names who can be targeted

        Returns:
            The name of the player to target (must be in eligible list)
        """
        pass


# Verify that BaseBot properly implements the Bot protocol
def _check_protocol_implementation() -> None:
    """Type-checking helper to verify BaseBot implements Bot protocol."""
    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        _bot: Bot = BaseBot("test")  # type: ignore

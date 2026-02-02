"""
Bot interface and decision context for Flipped Seven.

This module defines the Protocol interface that all bots must implement.
It uses the existing PlayerTableau and BotDecisionContext from other modules.
"""

from typing import Literal, Protocol, runtime_checkable, TYPE_CHECKING

from flip7.types.cards import ActionType, NumberCard

if TYPE_CHECKING:
    from flip7.types.events import BotDecisionContext


@runtime_checkable
class Bot(Protocol):
    """
    Protocol interface that all bots must implement.

    Bots make decisions during gameplay based on the current game state.
    All decision methods receive a BotDecisionContext with complete game information.
    """

    @property
    def name(self) -> str:
        """
        Returns the unique name/identifier for this bot.

        The name is used for logging, tournament tracking, and display purposes.
        """
        ...

    def decide_hit_or_pass(self, context: "BotDecisionContext") -> Literal["hit", "pass"]:
        """
        Decide whether to hit (draw another card) or pass (end turn).

        This is called on the bot's turn when they are active and can choose
        to continue drawing or lock in their current score.

        Args:
            context: Complete game state information

        Returns:
            "hit" to draw another card, or "pass" to end the turn
        """
        ...

    def decide_use_second_chance(
        self, context: "BotDecisionContext", duplicate: NumberCard
    ) -> bool:
        """
        Decide whether to use a Second Chance card to avoid busting.

        This is called when the bot draws a duplicate number card and would bust.
        If the bot has a Second Chance card, they can choose to use it to discard
        the duplicate and avoid busting (but their turn ends immediately).

        Args:
            context: Complete game state information
            duplicate: The duplicate number card that would cause a bust

        Returns:
            True to use the Second Chance card, False to bust normally
        """
        ...

    def choose_action_target(
        self, context: "BotDecisionContext", action: ActionType, eligible: list[str]
    ) -> str:
        """
        Choose which player should receive an action card effect.

        This is called when the bot draws an action card and must choose a target
        player. The bot can choose any eligible player, including themselves.

        Args:
            context: Complete game state information
            action: The type of action card that was drawn
            eligible: List of player names who can be targeted

        Returns:
            The name of the player to target (must be in eligible list)
        """
        ...

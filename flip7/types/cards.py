"""
Card type hierarchy for Flipped Seven.

This module defines all card types used in the game using frozen dataclasses
for immutability. The type system enforces correct card usage at compile time.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Literal


class ActionType(Enum):
    """
    Enumeration of all action card types.

    Action cards provide special abilities:
    - FREEZE: Skip the next player's turn
    - FLIP_THREE: Draw and play three cards in one turn
    - SECOND_CHANCE: Allow replaying the current turn if not satisfied
    """

    FREEZE = "FREEZE"
    FLIP_THREE = "FLIP_THREE"
    SECOND_CHANCE = "SECOND_CHANCE"


# Type alias for modifier card values
ModifierType = Literal["+2", "+4", "+6", "+8", "+10", "X2"]


@dataclass(frozen=True)
class NumberCard:
    """
    A number card with a value from 0 to 12.

    Number cards form the basis of scoring. Players flip these cards
    and sum their values (collecting unique values for Flip 7 bonus).

    Attributes:
        value: The numeric value of the card (0-12)
    """

    value: int

    def __post_init__(self) -> None:
        """Validate that the card value is in the valid range."""
        if not 0 <= self.value <= 12:
            raise ValueError(f"NumberCard value must be 0-12, got {self.value}")


@dataclass(frozen=True)
class ActionCard:
    """
    An action card that provides a special ability.

    Action cards can be played to gain strategic advantages during gameplay.

    Attributes:
        action_type: The type of action this card performs
    """

    action_type: ActionType


@dataclass(frozen=True)
class ModifierCard:
    """
    A modifier card that changes the value of number cards.

    Modifier cards are applied to number cards to increase their value.
    The X2 modifier doubles the value, while +N modifiers add N to the value.

    Attributes:
        modifier: The modification to apply ("+2", "+4", "+6", "+8", "+10", "X2")
    """

    modifier: ModifierType


# Union type representing any valid card in the game
Card = NumberCard | ActionCard | ModifierCard

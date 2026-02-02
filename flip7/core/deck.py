"""
Deck creation and manipulation for Flipped Seven.

This module provides functions to create and shuffle the game deck according
to the rules defined in the constants module.
"""

import random
from typing import Optional

from flip7.constants import (
    ACTION_CARD_COUNTS,
    DECK_COMPOSITION,
    MODIFIER_CARD_COUNTS,
)
from flip7.types.cards import ActionCard, ActionType, Card, ModifierCard, NumberCard


def create_deck() -> list[Card]:
    """
    Create a complete deck of 94 cards according to game rules.

    The deck consists of:
    - 78 number cards (0-12, with count equal to value except 0 which has 1)
    - 9 action cards (3 each of FREEZE, FLIP_THREE, SECOND_CHANCE)
    - 6 modifier cards (1 each of +2, +4, +6, +8, +10, X2)
    - Total: 94 cards

    Returns:
        A list containing all 94 cards in the deck, unshuffled.

    Example:
        >>> deck = create_deck()
        >>> len(deck)
        94
        >>> # Deck contains correct number of each card type
    """
    deck: list[Card] = []

    # Add number cards according to DECK_COMPOSITION
    for value, count in DECK_COMPOSITION.items():
        for _ in range(count):
            deck.append(NumberCard(value=value))

    # Add action cards according to ACTION_CARD_COUNTS
    for action_name, count in ACTION_CARD_COUNTS.items():
        action_type = ActionType[action_name]
        for _ in range(count):
            deck.append(ActionCard(action_type=action_type))

    # Add modifier cards according to MODIFIER_CARD_COUNTS
    for modifier, count in MODIFIER_CARD_COUNTS.items():
        # Type checker knows modifier is ModifierType due to the constant's type
        for _ in range(count):
            deck.append(ModifierCard(modifier=modifier))  # type: ignore[arg-type]

    return deck


def shuffle_deck(deck: list[Card], seed: Optional[int] = None) -> list[Card]:
    """
    Shuffle a deck of cards with optional deterministic seeding.

    Creates a new shuffled copy of the deck without modifying the original.
    If a seed is provided, the shuffle will be deterministic and reproducible.

    Args:
        deck: The deck to shuffle (will not be modified)
        seed: Optional random seed for deterministic shuffling. If None,
              shuffling will be non-deterministic based on system entropy.

    Returns:
        A new list containing the same cards in shuffled order.

    Example:
        >>> deck = create_deck()
        >>> shuffled1 = shuffle_deck(deck, seed=42)
        >>> shuffled2 = shuffle_deck(deck, seed=42)
        >>> shuffled1 == shuffled2  # Same seed produces same shuffle
        True
        >>> shuffled3 = shuffle_deck(deck, seed=43)
        >>> shuffled1 == shuffled3  # Different seed produces different shuffle
        False
    """
    # Create a copy to avoid modifying the original
    shuffled = deck.copy()

    # Create a Random instance with the given seed
    rng = random.Random(seed)

    # Shuffle the copy in-place
    rng.shuffle(shuffled)

    return shuffled

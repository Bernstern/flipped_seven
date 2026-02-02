"""
Immutable game rules and constants for Flipped Seven.

This module defines all fixed game parameters that control deck composition,
scoring, and gameplay mechanics. All constants are typed as Final to prevent
modification at runtime.
"""

from typing import Final

# Deck composition: card value -> count in deck
# Cards 0-12, with count equal to value (except 0 which has 1)
DECK_COMPOSITION: Final[dict[int, int]] = {
    0: 1,
    1: 1,
    2: 2,
    3: 3,
    4: 4,
    5: 5,
    6: 6,
    7: 7,
    8: 8,
    9: 9,
    10: 10,
    11: 11,
    12: 12,
}

# Action cards: special ability cards and their counts
ACTION_CARD_COUNTS: Final[dict[str, int]] = {
    "FREEZE": 3,
    "FLIP_THREE": 3,
    "SECOND_CHANCE": 3,
}

# Modifier cards: value-changing cards and their counts
MODIFIER_CARD_COUNTS: Final[dict[str, int]] = {
    "+2": 1,
    "+4": 1,
    "+6": 1,
    "+8": 1,
    "+10": 1,
    "X2": 1,
}

# Winning score threshold
WINNING_SCORE: Final[int] = 200

# Bonus points awarded for flipping exactly 7 unique numbers
FLIP_7_BONUS: Final[int] = 15

# Number of unique cards needed to trigger Flip 7 bonus
FLIP_7_THRESHOLD: Final[int] = 7

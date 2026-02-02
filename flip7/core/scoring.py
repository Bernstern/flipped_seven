"""
Score calculation and breakdown for Flipped Seven.

This module implements the scoring logic for calculating player scores at the end
of a round. It handles number card summation, modifier application, and the Flip 7
bonus for achieving 7 unique number card values.

Scoring Rules:
1. Sum all number card values
2. If X2 modifier present: multiply sum by 2
3. Add all +N modifiers (+2, +4, +6, +8, +10)
4. If exactly 7 unique number cards: add FLIP_7_BONUS (15 points)
5. Busted players always score 0

The X2 multiplier is applied BEFORE adding +N modifiers.
"""

from flip7.constants import FLIP_7_BONUS, FLIP_7_THRESHOLD
from flip7.types import ModifierCard, NumberCard, PlayerTableau, ScoreBreakdown


def has_duplicate_numbers(number_cards: tuple[NumberCard, ...]) -> bool:
    """
    Check if there are any duplicate number values in the player's hand.

    A player busts when they have two or more cards with the same number value.
    This function detects such duplicates.

    Args:
        number_cards: Tuple of number cards in the player's tableau

    Returns:
        True if there are duplicate number values, False otherwise

    Examples:
        >>> has_duplicate_numbers((NumberCard(1), NumberCard(2), NumberCard(3)))
        False

        >>> has_duplicate_numbers((NumberCard(1), NumberCard(1)))
        True

        >>> has_duplicate_numbers((NumberCard(5), NumberCard(7), NumberCard(5)))
        True

        >>> has_duplicate_numbers(())
        False
    """
    values = [card.value for card in number_cards]
    return len(values) != len(set(values))


def has_flip_7(number_cards: tuple[NumberCard, ...]) -> bool:
    """
    Check if a player has achieved the Flip 7 bonus.

    The Flip 7 bonus is awarded when a player has exactly 7 unique number card
    values in their tableau. Duplicate values do not count toward this total.

    Args:
        number_cards: Tuple of number cards in the player's tableau

    Returns:
        True if the player has exactly 7 unique number card values, False otherwise

    Examples:
        >>> has_flip_7((NumberCard(1), NumberCard(2), NumberCard(3),
        ...            NumberCard(4), NumberCard(5), NumberCard(6), NumberCard(7)))
        True

        >>> has_flip_7((NumberCard(1), NumberCard(1), NumberCard(2)))
        False

        >>> has_flip_7(())
        False

        >>> # 8 unique cards - no bonus
        >>> has_flip_7((NumberCard(0), NumberCard(1), NumberCard(2),
        ...            NumberCard(3), NumberCard(4), NumberCard(5),
        ...            NumberCard(6), NumberCard(7)))
        False
    """
    unique_values = {card.value for card in number_cards}
    return len(unique_values) == FLIP_7_THRESHOLD


def calculate_modifier_sum(modifier_cards: tuple[ModifierCard, ...]) -> int:
    """
    Calculate the sum of all +N modifier cards.

    This function sums the additive bonuses from +2, +4, +6, +8, and +10 modifier
    cards. The X2 multiplier is not included in this sum as it's applied separately
    to the base number card total.

    Args:
        modifier_cards: Tuple of modifier cards in the player's tableau

    Returns:
        The sum of all +N modifier values (0 if no additive modifiers present)

    Examples:
        >>> calculate_modifier_sum((ModifierCard("+2"), ModifierCard("+4")))
        6

        >>> calculate_modifier_sum((ModifierCard("X2"),))
        0

        >>> calculate_modifier_sum((ModifierCard("+10"), ModifierCard("X2"),
        ...                         ModifierCard("+2")))
        12

        >>> calculate_modifier_sum(())
        0
    """
    total = 0
    for card in modifier_cards:
        # Only process additive modifiers (+2, +4, +6, +8, +10)
        # X2 is handled separately in the scoring calculation
        if card.modifier != "X2":
            # Extract the numeric value from the modifier string (e.g., "+2" -> 2)
            modifier_value = int(card.modifier[1:])  # Skip the '+' prefix
            total += modifier_value
    return total


def calculate_score(tableau: PlayerTableau) -> ScoreBreakdown:
    """
    Calculate the final score for a player's tableau with detailed breakdown.

    This function implements the complete scoring algorithm for Flipped Seven,
    including all modifiers and bonuses. The calculation follows these steps:

    1. Sum all number card values
    2. If X2 modifier present: multiply sum by 2
    3. Add all +N modifier bonuses
    4. If exactly 7 unique number cards: add FLIP_7_BONUS (15 points)
    5. Return 0 if player is busted

    The X2 multiplier is applied BEFORE adding +N modifiers, which can lead to
    significantly higher scores when combined strategically.

    Args:
        tableau: The player's tableau containing all cards and status flags

    Returns:
        ScoreBreakdown with detailed intermediate values for each scoring step

    Examples:
        >>> # Basic scoring: 3 + 5 + 7 = 15
        >>> tableau = PlayerTableau(
        ...     player_id="player1",
        ...     number_cards=(NumberCard(3), NumberCard(5), NumberCard(7)),
        ...     modifier_cards=(),
        ...     second_chance=False,
        ...     is_active=False,
        ...     is_busted=False,
        ...     is_frozen=False,
        ...     is_passed=True
        ... )
        >>> breakdown = calculate_score(tableau)
        >>> breakdown.final_score
        15

        >>> # With X2 modifier: (3 + 5 + 7) * 2 = 30
        >>> tableau = PlayerTableau(
        ...     player_id="player1",
        ...     number_cards=(NumberCard(3), NumberCard(5), NumberCard(7)),
        ...     modifier_cards=(ModifierCard("X2"),),
        ...     second_chance=False,
        ...     is_active=False,
        ...     is_busted=False,
        ...     is_frozen=False,
        ...     is_passed=True
        ... )
        >>> breakdown = calculate_score(tableau)
        >>> breakdown.final_score
        30

        >>> # With X2 and +10: (3 + 5 + 7) * 2 + 10 = 40
        >>> tableau = PlayerTableau(
        ...     player_id="player1",
        ...     number_cards=(NumberCard(3), NumberCard(5), NumberCard(7)),
        ...     modifier_cards=(ModifierCard("X2"), ModifierCard("+10")),
        ...     second_chance=False,
        ...     is_active=False,
        ...     is_busted=False,
        ...     is_frozen=False,
        ...     is_passed=True
        ... )
        >>> breakdown = calculate_score(tableau)
        >>> breakdown.final_score
        40

        >>> # Flip 7 bonus: 7 unique cards + 15 bonus
        >>> tableau = PlayerTableau(
        ...     player_id="player1",
        ...     number_cards=(NumberCard(1), NumberCard(2), NumberCard(3),
        ...                   NumberCard(4), NumberCard(5), NumberCard(6),
        ...                   NumberCard(7)),
        ...     modifier_cards=(),
        ...     second_chance=False,
        ...     is_active=False,
        ...     is_busted=False,
        ...     is_frozen=False,
        ...     is_passed=True
        ... )
        >>> breakdown = calculate_score(tableau)
        >>> breakdown.final_score
        43

        >>> # Busted player scores 0
        >>> tableau = PlayerTableau(
        ...     player_id="player1",
        ...     number_cards=(NumberCard(3), NumberCard(3)),
        ...     modifier_cards=(ModifierCard("X2"), ModifierCard("+10")),
        ...     second_chance=False,
        ...     is_active=False,
        ...     is_busted=True,
        ...     is_frozen=False,
        ...     is_passed=False
        ... )
        >>> breakdown = calculate_score(tableau)
        >>> breakdown.final_score
        0
    """
    # Busted players always score 0, regardless of cards
    if tableau.is_busted:
        return ScoreBreakdown(
            number_cards_sum=0,
            after_x2_multiplier=0,
            modifier_additions=0,
            flip_7_bonus=0,
            final_score=0,
        )

    # Step 1: Sum all number card values
    number_cards_sum = sum(card.value for card in tableau.number_cards)

    # Step 2: Apply X2 multiplier if present
    has_x2 = any(card.modifier == "X2" for card in tableau.modifier_cards)
    after_x2_multiplier = number_cards_sum * 2 if has_x2 else number_cards_sum

    # Step 3: Calculate and add all +N modifier bonuses
    modifier_additions = calculate_modifier_sum(tableau.modifier_cards)
    score_with_modifiers = after_x2_multiplier + modifier_additions

    # Step 4: Check for Flip 7 bonus (exactly 7 unique number card values)
    flip_7_bonus = FLIP_7_BONUS if has_flip_7(tableau.number_cards) else 0
    final_score = score_with_modifiers + flip_7_bonus

    # Return detailed breakdown for debugging and display
    return ScoreBreakdown(
        number_cards_sum=number_cards_sum,
        after_x2_multiplier=after_x2_multiplier,
        modifier_additions=modifier_additions,
        flip_7_bonus=flip_7_bonus,
        final_score=final_score,
    )

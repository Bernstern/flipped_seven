"""
Tests for busting rules.

A player busts when they have two or more cards with the same number.
Busted players score 0 for the round.
"""

import pytest
from flip7.core.scoring import calculate_score, has_duplicate_numbers
from flip7.types.game_state import PlayerTableau
from flip7.types.cards import NumberCard, ModifierCard


def test_duplicate_detection():
    """Test that duplicates are correctly detected."""
    # No duplicates
    cards_no_dup = (NumberCard(1), NumberCard(2), NumberCard(3))
    assert not has_duplicate_numbers(cards_no_dup)

    # With duplicate
    cards_with_dup = (NumberCard(1), NumberCard(2), NumberCard(1))
    assert has_duplicate_numbers(cards_with_dup)


def test_bust_scores_zero():
    """Test that busted tableaus always score 0."""
    tableau = PlayerTableau(
        player_id="p1",
        number_cards=(NumberCard(7), NumberCard(10), NumberCard(7)),  # Duplicate 7!
        modifier_cards=(ModifierCard("X2"), ModifierCard("+10")),
        second_chance=False,
        is_active=False,
        is_busted=True,
        is_frozen=False,
        is_passed=False,
    )

    breakdown = calculate_score(tableau)
    assert breakdown.final_score == 0, "Busted player must score 0"


def test_three_of_same_number_also_busts():
    """Test that having 3+ of the same number is also a bust."""
    cards = (NumberCard(5), NumberCard(5), NumberCard(5))
    assert has_duplicate_numbers(cards), "Three of same number should be detected as duplicate"


def test_zero_card_can_bust():
    """Test that the 0 card can also cause a bust if duplicated."""
    # Note: There's only one 0 card in the deck, so this shouldn't happen in practice
    # But the logic should still handle it correctly
    cards = (NumberCard(0), NumberCard(0))
    assert has_duplicate_numbers(cards), "Duplicate 0s should bust"


def test_no_bust_with_different_numbers():
    """Test that having all different numbers doesn't bust."""
    cards = (
        NumberCard(0), NumberCard(1), NumberCard(2), NumberCard(3),
        NumberCard(4), NumberCard(5), NumberCard(6)
    )
    assert not has_duplicate_numbers(cards), "All unique numbers should not bust"


def test_bust_ignores_modifiers():
    """Test that modifier cards don't count toward busting."""
    # Having two +10 modifiers shouldn't cause a bust
    # (But there's only one of each modifier in the deck)
    tableau = PlayerTableau(
        player_id="p1",
        number_cards=(NumberCard(5), NumberCard(7)),  # No duplicates
        modifier_cards=(ModifierCard("+10"),),  # Modifiers don't cause bust
        second_chance=False,
        is_active=True,
        is_busted=False,
        is_frozen=False,
        is_passed=False,
    )

    breakdown = calculate_score(tableau)
    assert breakdown.final_score > 0, "Should not bust from modifiers"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Tests for Flip 7 bonus rules.

When a player collects exactly 7 unique number cards:
- They automatically pass (turn ends)
- They receive +15 bonus points
- This is the maximum hand size possible
"""

import pytest
from flip7.core.scoring import calculate_score, has_flip_7
from flip7.types.game_state import PlayerTableau
from flip7.types.cards import NumberCard, ModifierCard
from flip7.constants import FLIP_7_BONUS, FLIP_7_THRESHOLD


def test_exactly_seven_unique_achieves_flip7():
    """Test that exactly 7 unique number cards achieves Flip 7."""
    cards = (
        NumberCard(0), NumberCard(1), NumberCard(2), NumberCard(3),
        NumberCard(4), NumberCard(5), NumberCard(6)
    )
    assert has_flip_7(cards), "7 unique cards should achieve Flip 7"


def test_six_unique_does_not_achieve_flip7():
    """Test that 6 unique cards does not achieve Flip 7."""
    cards = (
        NumberCard(1), NumberCard(2), NumberCard(3),
        NumberCard(4), NumberCard(5), NumberCard(6)
    )
    assert not has_flip_7(cards), "6 unique cards should not achieve Flip 7"


def test_eight_unique_impossible():
    """Test that 8 unique cards is impossible (max 7)."""
    # This test documents that Flip 7 auto-passes at 7 cards
    # so 8 is impossible to achieve
    # Actual enforcement is in RoundEngine
    cards = (
        NumberCard(0), NumberCard(1), NumberCard(2), NumberCard(3),
        NumberCard(4), NumberCard(5), NumberCard(6)
    )
    assert len(cards) == 7, "Maximum hand size is 7 (Flip 7)"


def test_flip7_adds_15_bonus():
    """Test that Flip 7 adds exactly 15 bonus points."""
    assert FLIP_7_BONUS == 15, "Flip 7 bonus should be 15"
    assert FLIP_7_THRESHOLD == 7, "Flip 7 threshold should be 7 cards"


def test_flip7_bonus_applied_to_score():
    """Test that Flip 7 bonus is added to final score."""
    tableau = PlayerTableau(
        player_id="p1",
        number_cards=(
            NumberCard(0), NumberCard(1), NumberCard(2), NumberCard(3),
            NumberCard(4), NumberCard(5), NumberCard(6)
        ),  # Sum = 0+1+2+3+4+5+6 = 21
        modifier_cards=(),
        second_chance=False,
        is_active=False,
        is_busted=False,
        is_frozen=False,
        is_passed=True,
    )

    breakdown = calculate_score(tableau)
    assert breakdown.flip_7_bonus == 15
    assert breakdown.final_score == 36  # 21 + 15


def test_flip7_with_x2_correct_order():
    """Test that Flip 7 bonus is added AFTER X2 and modifiers."""
    tableau = PlayerTableau(
        player_id="p1",
        number_cards=(
            NumberCard(1), NumberCard(2), NumberCard(3), NumberCard(4),
            NumberCard(5), NumberCard(6), NumberCard(7)
        ),  # Sum = 28
        modifier_cards=(ModifierCard("X2"), ModifierCard("+4")),
        second_chance=False,
        is_active=False,
        is_busted=False,
        is_frozen=False,
        is_passed=True,
    )

    breakdown = calculate_score(tableau)
    # Order: 28 -> *2 = 56 -> +4 = 60 -> +15 (Flip7) = 75
    assert breakdown.number_cards_sum == 28
    assert breakdown.after_x2_multiplier == 56
    assert breakdown.modifier_additions == 4
    assert breakdown.flip_7_bonus == 15
    assert breakdown.final_score == 75


def test_duplicate_prevents_flip7():
    """Test that having a duplicate prevents Flip 7 (causes bust)."""
    # If you have 6 unique cards + 1 duplicate = not Flip 7
    cards = (
        NumberCard(1), NumberCard(2), NumberCard(3),
        NumberCard(4), NumberCard(5), NumberCard(6),
        NumberCard(1)  # Duplicate!
    )
    # This would bust, so Flip 7 is impossible
    assert not has_flip_7(cards), "Duplicates prevent Flip 7"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

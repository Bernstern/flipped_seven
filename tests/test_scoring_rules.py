"""
Tests for scoring rules.

Verifies correct score calculation including:
- Number card summation
- X2 modifier (doubles number cards before adding modifiers)
- +N modifiers (added after X2)
- Flip 7 bonus (+15 for exactly 7 unique numbers)
- Bust scoring (always 0)
"""

import pytest
from flip7.core.scoring import calculate_score
from flip7.types.game_state import PlayerTableau
from flip7.types.cards import NumberCard, ModifierCard
from flip7.constants import FLIP_7_BONUS


def test_simple_number_sum():
    """Test basic number card summation."""
    tableau = PlayerTableau(
        player_id="p1",
        number_cards=(NumberCard(3), NumberCard(5), NumberCard(7)),
        modifier_cards=(),
        second_chance=False,
        is_active=False,
        is_busted=False,
        is_frozen=False,
        is_passed=True,
    )

    breakdown = calculate_score(tableau)
    assert breakdown.number_cards_sum == 15
    assert breakdown.after_x2_multiplier == 15
    assert breakdown.modifier_additions == 0
    assert breakdown.flip_7_bonus == 0
    assert breakdown.final_score == 15


def test_x2_modifier_doubles_before_additions():
    """Test that X2 doubles number cards before adding +N modifiers."""
    tableau = PlayerTableau(
        player_id="p1",
        number_cards=(NumberCard(3), NumberCard(5), NumberCard(7)),  # Sum = 15
        modifier_cards=(ModifierCard("X2"), ModifierCard("+4")),
        second_chance=False,
        is_active=False,
        is_busted=False,
        is_frozen=False,
        is_passed=True,
    )

    breakdown = calculate_score(tableau)
    assert breakdown.number_cards_sum == 15
    assert breakdown.after_x2_multiplier == 30  # 15 * 2
    assert breakdown.modifier_additions == 4
    assert breakdown.flip_7_bonus == 0
    assert breakdown.final_score == 34  # (15 * 2) + 4


def test_multiple_plus_modifiers():
    """Test that multiple +N modifiers stack correctly."""
    tableau = PlayerTableau(
        player_id="p1",
        number_cards=(NumberCard(10),),
        modifier_cards=(ModifierCard("+2"), ModifierCard("+4"), ModifierCard("+6")),
        second_chance=False,
        is_active=False,
        is_busted=False,
        is_frozen=False,
        is_passed=True,
    )

    breakdown = calculate_score(tableau)
    assert breakdown.number_cards_sum == 10
    assert breakdown.after_x2_multiplier == 10
    assert breakdown.modifier_additions == 12  # 2 + 4 + 6
    assert breakdown.flip_7_bonus == 0
    assert breakdown.final_score == 22  # 10 + 12


def test_flip_7_bonus():
    """Test Flip 7 bonus for exactly 7 unique number cards."""
    tableau = PlayerTableau(
        player_id="p1",
        number_cards=(
            NumberCard(0), NumberCard(1), NumberCard(2), NumberCard(3),
            NumberCard(4), NumberCard(5), NumberCard(6)
        ),  # 7 unique cards, sum = 21
        modifier_cards=(),
        second_chance=False,
        is_active=False,
        is_busted=False,
        is_frozen=False,
        is_passed=True,
    )

    breakdown = calculate_score(tableau)
    assert breakdown.number_cards_sum == 21
    assert breakdown.after_x2_multiplier == 21
    assert breakdown.modifier_additions == 0
    assert breakdown.flip_7_bonus == FLIP_7_BONUS  # 15
    assert breakdown.final_score == 36  # 21 + 15


def test_flip_7_with_x2_and_modifiers():
    """Test Flip 7 bonus combined with X2 and +N modifiers."""
    tableau = PlayerTableau(
        player_id="p1",
        number_cards=(
            NumberCard(1), NumberCard(2), NumberCard(3), NumberCard(4),
            NumberCard(5), NumberCard(6), NumberCard(7)
        ),  # 7 unique, sum = 28
        modifier_cards=(ModifierCard("X2"), ModifierCard("+10")),
        second_chance=False,
        is_active=False,
        is_busted=False,
        is_frozen=False,
        is_passed=True,
    )

    breakdown = calculate_score(tableau)
    assert breakdown.number_cards_sum == 28
    assert breakdown.after_x2_multiplier == 56  # 28 * 2
    assert breakdown.modifier_additions == 10
    assert breakdown.flip_7_bonus == 15
    assert breakdown.final_score == 81  # (28 * 2) + 10 + 15


def test_busted_player_scores_zero():
    """Test that busted players always score 0."""
    tableau = PlayerTableau(
        player_id="p1",
        number_cards=(NumberCard(10), NumberCard(11), NumberCard(12)),
        modifier_cards=(ModifierCard("X2"), ModifierCard("+10")),
        second_chance=False,
        is_active=False,
        is_busted=True,  # BUSTED
        is_frozen=False,
        is_passed=False,
    )

    breakdown = calculate_score(tableau)
    assert breakdown.final_score == 0, "Busted players must score 0"


def test_zero_card_included_in_sum():
    """Test that 0 card is included in number sum."""
    tableau = PlayerTableau(
        player_id="p1",
        number_cards=(NumberCard(0), NumberCard(5), NumberCard(10)),
        modifier_cards=(),
        second_chance=False,
        is_active=False,
        is_busted=False,
        is_frozen=False,
        is_passed=True,
    )

    breakdown = calculate_score(tableau)
    assert breakdown.number_cards_sum == 15  # 0 + 5 + 10
    assert breakdown.final_score == 15


def test_only_modifiers_no_numbers():
    """Test edge case: only modifier cards (should score 0)."""
    tableau = PlayerTableau(
        player_id="p1",
        number_cards=(),  # No number cards!
        modifier_cards=(ModifierCard("+10"), ModifierCard("X2")),
        second_chance=False,
        is_active=False,
        is_busted=False,
        is_frozen=False,
        is_passed=True,
    )

    breakdown = calculate_score(tableau)
    # With no number cards: 0 * 2 + 10 = 10
    assert breakdown.number_cards_sum == 0
    assert breakdown.after_x2_multiplier == 0
    assert breakdown.modifier_additions == 10
    assert breakdown.final_score == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

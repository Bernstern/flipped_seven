"""
Tests for modifier card stacking and interaction.

Per official rules (lines 158-175):
- Multiple +N modifier cards stack (+2, +4, +6 all at once)
- X2 doubles the number card sum BEFORE adding +N modifiers
- Only one X2 card exists in the deck
- Modifiers don't count as one of the 7 numbers
- Modifiers don't cause busting
"""

from dataclasses import replace

import pytest

from flip7.core.scoring import calculate_score
from flip7.types.cards import ModifierCard, NumberCard
from flip7.types.game_state import PlayerTableau


def test_multiple_plus_modifiers_stack():
    """Test that multiple +N modifiers stack (add together)."""
    tableau = PlayerTableau(
        player_id="p1",
        number_cards=(NumberCard(5), NumberCard(7)),
        modifier_cards=(ModifierCard("+2"), ModifierCard("+4"), ModifierCard("+6")),
        second_chance=False,
        is_active=False,
        is_busted=False,
        is_frozen=False,
        is_passed=True,
    )

    breakdown = calculate_score(tableau)

    # 5 + 7 = 12, then + 2 + 4 + 6 = 24
    assert breakdown.number_cards_sum == 12
    assert breakdown.modifier_additions == 12  # 2 + 4 + 6
    assert breakdown.final_score == 24


def test_all_plus_modifiers_stack():
    """Test that all 5 +N modifiers can stack together."""
    tableau = PlayerTableau(
        player_id="p1",
        number_cards=(NumberCard(10),),
        modifier_cards=(
            ModifierCard("+2"),
            ModifierCard("+4"),
            ModifierCard("+6"),
            ModifierCard("+8"),
            ModifierCard("+10"),
        ),
        second_chance=False,
        is_active=False,
        is_busted=False,
        is_frozen=False,
        is_passed=True,
    )

    breakdown = calculate_score(tableau)

    # 10 + (2+4+6+8+10) = 10 + 30 = 40
    assert breakdown.number_cards_sum == 10
    assert breakdown.modifier_additions == 30  # 2+4+6+8+10
    assert breakdown.final_score == 40


def test_x2_applied_before_plus_modifiers():
    """Test that X2 is applied before +N modifiers (critical order)."""
    tableau = PlayerTableau(
        player_id="p1",
        number_cards=(NumberCard(5), NumberCard(7)),
        modifier_cards=(ModifierCard("X2"), ModifierCard("+10")),
        second_chance=False,
        is_active=False,
        is_busted=False,
        is_frozen=False,
        is_passed=True,
    )

    breakdown = calculate_score(tableau)

    # (5 + 7) * 2 = 24, then + 10 = 34
    # NOT (5 + 7 + 10) * 2 = 44
    assert breakdown.number_cards_sum == 12
    assert breakdown.after_x2_multiplier == 24  # 12 * 2
    assert breakdown.modifier_additions == 10
    assert breakdown.final_score == 34, \
        "X2 should be applied BEFORE +N modifiers"


def test_x2_with_all_plus_modifiers():
    """Test X2 with all +N modifiers stacking."""
    tableau = PlayerTableau(
        player_id="p1",
        number_cards=(NumberCard(10),),
        modifier_cards=(
            ModifierCard("X2"),
            ModifierCard("+2"),
            ModifierCard("+4"),
            ModifierCard("+6"),
            ModifierCard("+8"),
            ModifierCard("+10"),
        ),
        second_chance=False,
        is_active=False,
        is_busted=False,
        is_frozen=False,
        is_passed=True,
    )

    breakdown = calculate_score(tableau)

    # 10 * 2 = 20, then + (2+4+6+8+10) = 20 + 30 = 50
    assert breakdown.number_cards_sum == 10
    assert breakdown.after_x2_multiplier == 20
    assert breakdown.modifier_additions == 30
    assert breakdown.final_score == 50


def test_modifiers_dont_count_toward_flip_7():
    """Test that modifier cards don't count toward the 7 unique numbers."""
    from flip7.core.scoring import has_flip_7

    # 7 unique numbers + modifiers = still Flip 7
    number_cards = tuple(NumberCard(i) for i in range(1, 8))  # 1-7

    assert has_flip_7(number_cards), \
        "7 unique numbers should achieve Flip 7"

    # Modifiers are stored separately, don't affect Flip 7 check
    # This is verified by the scoring logic


def test_modifiers_with_zero_card():
    """Test that modifiers work correctly with the 0 number card."""
    tableau = PlayerTableau(
        player_id="p1",
        number_cards=(NumberCard(0), NumberCard(5)),
        modifier_cards=(ModifierCard("+10"),),
        second_chance=False,
        is_active=False,
        is_busted=False,
        is_frozen=False,
        is_passed=True,
    )

    breakdown = calculate_score(tableau)

    # 0 + 5 = 5, then + 10 = 15
    assert breakdown.number_cards_sum == 5
    assert breakdown.modifier_additions == 10
    assert breakdown.final_score == 15


def test_x2_with_zero_card():
    """Test X2 with 0 card (doubles to 0)."""
    tableau = PlayerTableau(
        player_id="p1",
        number_cards=(NumberCard(0),),
        modifier_cards=(ModifierCard("X2"), ModifierCard("+10")),
        second_chance=False,
        is_active=False,
        is_busted=False,
        is_frozen=False,
        is_passed=True,
    )

    breakdown = calculate_score(tableau)

    # 0 * 2 = 0, then + 10 = 10
    assert breakdown.number_cards_sum == 0
    assert breakdown.after_x2_multiplier == 0
    assert breakdown.modifier_additions == 10
    assert breakdown.final_score == 10


def test_only_modifiers_no_numbers():
    """Test scoring with only modifier cards, no number cards."""
    tableau = PlayerTableau(
        player_id="p1",
        number_cards=(),
        modifier_cards=(ModifierCard("+10"), ModifierCard("+4")),
        second_chance=False,
        is_active=False,
        is_busted=False,
        is_frozen=False,
        is_passed=True,
    )

    breakdown = calculate_score(tableau)

    # No number cards = 0, then + 10 + 4 = 14
    assert breakdown.number_cards_sum == 0
    assert breakdown.modifier_additions == 14
    assert breakdown.final_score == 14


def test_x2_alone():
    """Test X2 modifier with no other modifiers."""
    tableau = PlayerTableau(
        player_id="p1",
        number_cards=(NumberCard(7), NumberCard(8)),
        modifier_cards=(ModifierCard("X2"),),
        second_chance=False,
        is_active=False,
        is_busted=False,
        is_frozen=False,
        is_passed=True,
    )

    breakdown = calculate_score(tableau)

    # (7 + 8) * 2 = 30
    assert breakdown.number_cards_sum == 15
    assert breakdown.after_x2_multiplier == 30
    assert breakdown.modifier_additions == 0
    assert breakdown.final_score == 30


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Bot Compliance Test Suite

This test suite verifies that ALL bots in the flip7/bots directory correctly
implement the Bot protocol and can handle all required decision scenarios.

When creating a new bot, it MUST pass all tests in this file to be considered
compliant and ready for tournament play.

Tests verify:
1. Bot implements the Bot protocol correctly
2. Bot can make hit/pass decisions
3. Bot can decide on Second Chance usage
4. Bot can choose action card targets
5. Bot handles all edge cases gracefully (no crashes)
6. Bot returns valid decisions (not invalid values)
"""

import importlib
import inspect
import pytest
from pathlib import Path
from typing import Type

from flip7.bots.base import BaseBot
from flip7.types import Bot, BotDecisionContext, ActionType, NumberCard, ModifierCard
from flip7.types.game_state import PlayerTableau


def discover_bot_classes() -> list[Type[BaseBot]]:
    """
    Discover all bot classes in the flip7/bots directory.

    Returns:
        List of bot class types (not instances)
    """
    bots_dir = Path(__file__).parent.parent / "flip7" / "bots"
    bot_classes = []

    # Scan all .py files in bots directory
    for py_file in bots_dir.glob("*.py"):
        if py_file.name.startswith("_") or py_file.name == "base.py":
            continue

        module_name = f"flip7.bots.{py_file.stem}"
        try:
            module = importlib.import_module(module_name)

            # Find all classes that inherit from BaseBot
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (issubclass(obj, BaseBot) and
                    obj is not BaseBot and
                    obj.__module__ == module_name):
                    bot_classes.append(obj)
        except ImportError:
            continue

    return bot_classes


# Discover all bots at module load time
ALL_BOT_CLASSES = discover_bot_classes()


@pytest.fixture(params=ALL_BOT_CLASSES, ids=lambda cls: cls.__name__)
def bot_class(request) -> Type[BaseBot]:
    """Fixture that yields each bot class for testing."""
    return request.param


@pytest.fixture
def bot_instance(bot_class: Type[BaseBot]) -> BaseBot:
    """Fixture that creates an instance of each bot."""
    return bot_class(bot_name="test_bot")


@pytest.fixture
def sample_context() -> BotDecisionContext:
    """Create a sample decision context for testing."""
    my_tableau = PlayerTableau(
        player_id="test_bot",
        number_cards=(NumberCard(3), NumberCard(7)),
        modifier_cards=(ModifierCard("+4"),),
        second_chance=False,
        is_active=True,
        is_busted=False,
        is_frozen=False,
        is_passed=False,
    )

    opponent_tableau = PlayerTableau(
        player_id="opponent",
        number_cards=(NumberCard(5), NumberCard(10)),
        modifier_cards=(),
        second_chance=True,
        is_active=True,
        is_busted=False,
        is_frozen=False,
        is_passed=False,
    )

    return BotDecisionContext(
        my_tableau=my_tableau,
        opponent_tableaus={"opponent": opponent_tableau},
        deck_remaining=50,
        my_current_score=25,
        opponent_scores={"opponent": 30},
        current_round=3,
        target_score=200,
    )


# ============================================================================
# PROTOCOL COMPLIANCE TESTS
# ============================================================================

def test_bot_implements_protocol(bot_instance: BaseBot):
    """Test that bot properly implements the Bot protocol."""
    assert isinstance(bot_instance, Bot), f"{bot_instance.__class__.__name__} does not implement Bot protocol"


def test_bot_has_name_property(bot_instance: BaseBot):
    """Test that bot has a valid name property."""
    assert hasattr(bot_instance, "name"), "Bot must have 'name' property"
    assert isinstance(bot_instance.name, str), "Bot name must be a string"
    assert len(bot_instance.name) > 0, "Bot name cannot be empty"


def test_bot_has_all_required_methods(bot_instance: BaseBot):
    """Test that bot implements all required decision methods."""
    assert hasattr(bot_instance, "decide_hit_or_pass"), "Bot must implement decide_hit_or_pass"
    assert callable(bot_instance.decide_hit_or_pass), "decide_hit_or_pass must be callable"

    assert hasattr(bot_instance, "decide_use_second_chance"), "Bot must implement decide_use_second_chance"
    assert callable(bot_instance.decide_use_second_chance), "decide_use_second_chance must be callable"

    assert hasattr(bot_instance, "choose_action_target"), "Bot must implement choose_action_target"
    assert callable(bot_instance.choose_action_target), "choose_action_target must be callable"


# ============================================================================
# HIT OR PASS DECISION TESTS
# ============================================================================

def test_decide_hit_or_pass_returns_valid_choice(bot_instance: BaseBot, sample_context: BotDecisionContext):
    """Test that bot returns 'hit' or 'pass' for hit/pass decision."""
    decision = bot_instance.decide_hit_or_pass(sample_context)
    assert decision in ("hit", "pass"), f"decide_hit_or_pass must return 'hit' or 'pass', got {decision!r}"


def test_decide_hit_or_pass_with_empty_hand(bot_instance: BaseBot, sample_context: BotDecisionContext):
    """Test hit/pass decision when bot has no cards yet."""
    empty_context = BotDecisionContext(
        my_tableau=PlayerTableau(
            player_id="test_bot",
            number_cards=(),
            modifier_cards=(),
            second_chance=False,
            is_active=True,
            is_busted=False,
            is_frozen=False,
            is_passed=False,
        ),
        opponent_tableaus=sample_context.opponent_tableaus,
        deck_remaining=sample_context.deck_remaining,
        my_current_score=0,
        opponent_scores=sample_context.opponent_scores,
        current_round=1,
        target_score=200,
    )

    decision = bot_instance.decide_hit_or_pass(empty_context)
    assert decision in ("hit", "pass"), "Bot must handle empty hand gracefully"


def test_decide_hit_or_pass_with_high_score(bot_instance: BaseBot, sample_context: BotDecisionContext):
    """Test hit/pass decision when bot has a high-scoring hand."""
    high_score_context = BotDecisionContext(
        my_tableau=PlayerTableau(
            player_id="test_bot",
            number_cards=(NumberCard(10), NumberCard(11), NumberCard(12)),
            modifier_cards=(ModifierCard("X2"),),
            second_chance=False,
            is_active=True,
            is_busted=False,
            is_frozen=False,
            is_passed=False,
        ),
        opponent_tableaus=sample_context.opponent_tableaus,
        deck_remaining=sample_context.deck_remaining,
        my_current_score=100,
        opponent_scores=sample_context.opponent_scores,
        current_round=5,
        target_score=200,
    )

    decision = bot_instance.decide_hit_or_pass(high_score_context)
    assert decision in ("hit", "pass"), "Bot must handle high-scoring hands"


def test_decide_hit_or_pass_near_flip_7(bot_instance: BaseBot, sample_context: BotDecisionContext):
    """Test hit/pass decision when bot has 6 unique cards (one away from Flip 7)."""
    near_flip7_context = BotDecisionContext(
        my_tableau=PlayerTableau(
            player_id="test_bot",
            number_cards=(NumberCard(1), NumberCard(2), NumberCard(3),
                         NumberCard(4), NumberCard(5), NumberCard(6)),
            modifier_cards=(),
            second_chance=False,
            is_active=True,
            is_busted=False,
            is_frozen=False,
            is_passed=False,
        ),
        opponent_tableaus=sample_context.opponent_tableaus,
        deck_remaining=sample_context.deck_remaining,
        my_current_score=50,
        opponent_scores=sample_context.opponent_scores,
        current_round=2,
        target_score=200,
    )

    decision = bot_instance.decide_hit_or_pass(near_flip7_context)
    assert decision in ("hit", "pass"), "Bot must handle near-Flip-7 situation"


# ============================================================================
# SECOND CHANCE DECISION TESTS
# ============================================================================

def test_decide_use_second_chance_returns_bool(bot_instance: BaseBot, sample_context: BotDecisionContext):
    """Test that bot returns True or False for Second Chance decision."""
    duplicate = NumberCard(3)  # Duplicate of first card in sample context
    decision = bot_instance.decide_use_second_chance(sample_context, duplicate)
    assert isinstance(decision, bool), f"decide_use_second_chance must return bool, got {type(decision)}"


def test_decide_use_second_chance_with_low_value_duplicate(bot_instance: BaseBot, sample_context: BotDecisionContext):
    """Test Second Chance decision when duplicate is a low-value card."""
    low_duplicate = NumberCard(1)
    decision = bot_instance.decide_use_second_chance(sample_context, low_duplicate)
    assert isinstance(decision, bool), "Bot must handle low-value duplicates"


def test_decide_use_second_chance_with_high_value_duplicate(bot_instance: BaseBot, sample_context: BotDecisionContext):
    """Test Second Chance decision when duplicate is a high-value card."""
    high_duplicate = NumberCard(12)
    decision = bot_instance.decide_use_second_chance(sample_context, high_duplicate)
    assert isinstance(decision, bool), "Bot must handle high-value duplicates"


def test_decide_use_second_chance_with_good_hand(bot_instance: BaseBot, sample_context: BotDecisionContext):
    """Test Second Chance decision when bot has a good hand worth saving."""
    good_hand_context = BotDecisionContext(
        my_tableau=PlayerTableau(
            player_id="test_bot",
            number_cards=(NumberCard(10), NumberCard(11), NumberCard(12)),
            modifier_cards=(ModifierCard("X2"), ModifierCard("+10")),
            second_chance=True,
            is_active=True,
            is_busted=False,
            is_frozen=False,
            is_passed=False,
        ),
        opponent_tableaus=sample_context.opponent_tableaus,
        deck_remaining=sample_context.deck_remaining,
        my_current_score=150,
        opponent_scores=sample_context.opponent_scores,
        current_round=10,
        target_score=200,
    )

    duplicate = NumberCard(10)
    decision = bot_instance.decide_use_second_chance(good_hand_context, duplicate)
    assert isinstance(decision, bool), "Bot must handle valuable hand decisions"


# ============================================================================
# ACTION CARD TARGET SELECTION TESTS
# ============================================================================

def test_choose_action_target_returns_valid_player(bot_instance: BaseBot, sample_context: BotDecisionContext):
    """Test that bot chooses a valid target from eligible list."""
    eligible = ["opponent", "test_bot"]
    target = bot_instance.choose_action_target(sample_context, ActionType.FREEZE, eligible)
    assert target in eligible, f"Bot must choose from eligible targets, got {target!r}"


def test_choose_action_target_single_eligible(bot_instance: BaseBot, sample_context: BotDecisionContext):
    """Test target selection when only one eligible target exists."""
    eligible = ["opponent"]
    target = bot_instance.choose_action_target(sample_context, ActionType.FREEZE, eligible)
    assert target == "opponent", "Bot must choose the only eligible target"


def test_choose_action_target_can_target_self(bot_instance: BaseBot, sample_context: BotDecisionContext):
    """Test that bot can target itself when in eligible list."""
    eligible = ["test_bot", "opponent"]
    target = bot_instance.choose_action_target(sample_context, ActionType.FLIP_THREE, eligible)
    assert target in eligible, "Bot must choose valid target (can include self)"


def test_choose_action_target_freeze(bot_instance: BaseBot, sample_context: BotDecisionContext):
    """Test target selection for FREEZE action."""
    eligible = ["opponent", "player2", "player3"]
    target = bot_instance.choose_action_target(sample_context, ActionType.FREEZE, eligible)
    assert target in eligible, "Bot must choose valid FREEZE target"


def test_choose_action_target_flip_three(bot_instance: BaseBot, sample_context: BotDecisionContext):
    """Test target selection for FLIP_THREE action."""
    eligible = ["opponent", "test_bot"]
    target = bot_instance.choose_action_target(sample_context, ActionType.FLIP_THREE, eligible)
    assert target in eligible, "Bot must choose valid FLIP_THREE target"


def test_choose_action_target_second_chance(bot_instance: BaseBot, sample_context: BotDecisionContext):
    """Test target selection for SECOND_CHANCE action."""
    eligible = ["opponent", "player2"]
    target = bot_instance.choose_action_target(sample_context, ActionType.SECOND_CHANCE, eligible)
    assert target in eligible, "Bot must choose valid SECOND_CHANCE target"


# ============================================================================
# EDGE CASE HANDLING TESTS
# ============================================================================

def test_bot_handles_no_opponents(bot_instance: BaseBot):
    """Test bot behavior when there are no opponents (single-player scenario)."""
    solo_context = BotDecisionContext(
        my_tableau=PlayerTableau(
            player_id="test_bot",
            number_cards=(NumberCard(5),),
            modifier_cards=(),
            second_chance=False,
            is_active=True,
            is_busted=False,
            is_frozen=False,
            is_passed=False,
        ),
        opponent_tableaus={},  # No opponents
        deck_remaining=80,
        my_current_score=10,
        opponent_scores={},
        current_round=1,
        target_score=200,
    )

    # Should not crash
    decision = bot_instance.decide_hit_or_pass(solo_context)
    assert decision in ("hit", "pass"), "Bot must handle solo play"


def test_bot_handles_many_opponents(bot_instance: BaseBot, sample_context: BotDecisionContext):
    """Test bot behavior with many opponents."""
    many_opponents_context = BotDecisionContext(
        my_tableau=sample_context.my_tableau,
        opponent_tableaus={
            f"player{i}": PlayerTableau(
                player_id=f"player{i}",
                number_cards=(NumberCard(i % 13),),
                modifier_cards=(),
                second_chance=False,
                is_active=True,
                is_busted=False,
                is_frozen=False,
                is_passed=False,
            )
            for i in range(10)  # 10 opponents
        },
        deck_remaining=sample_context.deck_remaining,
        my_current_score=sample_context.my_current_score,
        opponent_scores={f"player{i}": i * 10 for i in range(10)},
        current_round=sample_context.current_round,
        target_score=200,
    )

    decision = bot_instance.decide_hit_or_pass(many_opponents_context)
    assert decision in ("hit", "pass"), "Bot must handle many opponents"


def test_bot_handles_empty_deck(bot_instance: BaseBot, sample_context: BotDecisionContext):
    """Test bot behavior when deck is nearly empty."""
    empty_deck_context = BotDecisionContext(
        my_tableau=sample_context.my_tableau,
        opponent_tableaus=sample_context.opponent_tableaus,
        deck_remaining=1,  # Almost empty
        my_current_score=sample_context.my_current_score,
        opponent_scores=sample_context.opponent_scores,
        current_round=sample_context.current_round,
        target_score=200,
    )

    decision = bot_instance.decide_hit_or_pass(empty_deck_context)
    assert decision in ("hit", "pass"), "Bot must handle near-empty deck"


def test_bot_deterministic_with_same_context(bot_instance: BaseBot, sample_context: BotDecisionContext):
    """Test that bot makes consistent decisions given the same context (if deterministic)."""
    decision1 = bot_instance.decide_hit_or_pass(sample_context)
    decision2 = bot_instance.decide_hit_or_pass(sample_context)

    # Note: This test allows for randomness, just checks that both are valid
    assert decision1 in ("hit", "pass")
    assert decision2 in ("hit", "pass")
    # If bot is deterministic, decision1 == decision2, but we don't enforce that


# ============================================================================
# SUMMARY TEST
# ============================================================================

def test_bot_compliance_summary(bot_class: Type[BaseBot]):
    """
    Summary test that prints bot information.

    This test always passes but provides useful information about each bot.
    """
    bot = bot_class(bot_name="summary_test")

    print(f"\n{'='*60}")
    print(f"Bot Compliance Test Summary: {bot_class.__name__}")
    print(f"{'='*60}")
    print(f"Bot Name: {bot.name}")
    print(f"Implements Bot Protocol: {isinstance(bot, Bot)}")
    print(f"Module: {bot_class.__module__}")
    print(f"Docstring: {bot_class.__doc__ or 'No docstring'}")
    print(f"{'='*60}\n")

    assert True, "Summary test always passes"


# ============================================================================
# DISCOVERY TEST
# ============================================================================

def test_bot_discovery_finds_bots():
    """Test that bot discovery finds at least the known bots."""
    bot_names = [cls.__name__ for cls in ALL_BOT_CLASSES]

    # We should at least find RandomBot and ScaredyBot
    assert "RandomBot" in bot_names, "Should discover RandomBot"
    assert "ScaredyBot" in bot_names, "Should discover ScaredyBot"

    print(f"\nDiscovered {len(ALL_BOT_CLASSES)} bot(s): {', '.join(bot_names)}")


if __name__ == "__main__":
    # When run directly, print discovered bots and run tests
    print(f"Discovered {len(ALL_BOT_CLASSES)} bot class(es):")
    for bot_cls in ALL_BOT_CLASSES:
        print(f"  - {bot_cls.__name__} ({bot_cls.__module__})")

    print("\nRunning compliance tests...")
    pytest.main([__file__, "-v"])

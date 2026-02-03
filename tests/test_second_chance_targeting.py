"""
Tests for Second Chance targeting rules.

Per official rules (lines 72-74):
- Frozen/passed players can still receive Second Chance (for future rounds)

Per official rules (lines 142-149):
- Player can only hold ONE Second Chance at a time
- If receiving a second one, must choose another active player to give it to
- If no eligible targets exist, discard the Second Chance
"""

from dataclasses import replace
from pathlib import Path

import pytest

from flip7.bots import RandomBot
from flip7.core.deck import create_deck
from flip7.core.round_engine import RoundEngine
from flip7.events.event_logger import EventLogger
from flip7.types.cards import ActionCard, ActionType, NumberCard


def test_frozen_player_can_receive_second_chance():
    """Test that a frozen player can still receive Second Chance."""
    player_ids = ["p1", "p2"]
    bots = {
        "p1": RandomBot("p1"),
        "p2": RandomBot("p2"),
    }

    deck = [NumberCard(i) for i in range(1, 13)]
    discard: list = []

    with EventLogger(Path("/tmp/test_frozen_second_chance.jsonl")) as logger:
        engine = RoundEngine(
            player_ids=player_ids,
            bots=bots,
            event_logger=logger,
            deck=deck,
            discard_pile=discard,
            round_number=1,
            game_id="test",
            seed=42,
        )

        # Freeze p2
        engine.tableaus["p2"] = replace(
            engine.tableaus["p2"],
            is_active=False,
            is_frozen=True,
        )

        # Get eligible targets for Second Chance
        eligible = engine._get_eligible_targets(ActionType.SECOND_CHANCE)

        # P2 should be eligible even though frozen
        assert "p2" in eligible, \
            "Frozen players should be eligible for Second Chance (for future rounds)"


def test_passed_player_can_receive_second_chance():
    """Test that a passed player can still receive Second Chance."""
    player_ids = ["p1", "p2"]
    bots = {
        "p1": RandomBot("p1"),
        "p2": RandomBot("p2"),
    }

    deck = [NumberCard(i) for i in range(1, 13)]
    discard: list = []

    with EventLogger(Path("/tmp/test_passed_second_chance.jsonl")) as logger:
        engine = RoundEngine(
            player_ids=player_ids,
            bots=bots,
            event_logger=logger,
            deck=deck,
            discard_pile=discard,
            round_number=1,
            game_id="test",
            seed=42,
        )

        # Make p2 pass
        engine.tableaus["p2"] = replace(
            engine.tableaus["p2"],
            is_active=False,
            is_passed=True,
        )

        # Get eligible targets for Second Chance
        eligible = engine._get_eligible_targets(ActionType.SECOND_CHANCE)

        # P2 should be eligible even though passed
        assert "p2" in eligible, \
            "Passed players should be eligible for Second Chance (for future rounds)"


def test_second_chance_one_per_player_limit():
    """Test that a player can only hold one Second Chance at a time."""
    player_ids = ["p1", "p2", "p3"]
    bots = {
        "p1": RandomBot("p1"),
        "p2": RandomBot("p2"),
        "p3": RandomBot("p3"),
    }

    deck = [NumberCard(i) for i in range(1, 13)]
    discard: list = []

    with EventLogger(Path("/tmp/test_sc_one_per_player.jsonl")) as logger:
        engine = RoundEngine(
            player_ids=player_ids,
            bots=bots,
            event_logger=logger,
            deck=deck,
            discard_pile=discard,
            round_number=1,
            game_id="test",
            seed=42,
        )

        # Give p1 Second Chance
        engine.tableaus["p1"] = replace(
            engine.tableaus["p1"],
            second_chance=True,
        )

        # Try to give p1 another Second Chance
        engine._resolve_second_chance("p1")

        # P1 should still have only one Second Chance
        assert engine.tableaus["p1"].second_chance, "P1 should have Second Chance"

        # Another player should have received the second one
        other_players_with_sc = [
            pid for pid in ["p2", "p3"]
            if engine.tableaus[pid].second_chance
        ]

        assert len(other_players_with_sc) == 1, \
            "The second Second Chance should have been given to another player"


def test_second_chance_discarded_when_all_have_one():
    """Test that Second Chance is discarded if all players already have one."""
    player_ids = ["p1", "p2"]
    bots = {
        "p1": RandomBot("p1"),
        "p2": RandomBot("p2"),
    }

    deck = [NumberCard(i) for i in range(1, 13)]
    discard: list = []

    with EventLogger(Path("/tmp/test_sc_all_have_one.jsonl")) as logger:
        engine = RoundEngine(
            player_ids=player_ids,
            bots=bots,
            event_logger=logger,
            deck=deck,
            discard_pile=discard,
            round_number=1,
            game_id="test",
            seed=42,
        )

        # Give both players Second Chance
        for pid in player_ids:
            engine.tableaus[pid] = replace(
                engine.tableaus[pid],
                second_chance=True,
            )

        # Try to give another Second Chance
        engine._resolve_second_chance("p1")

        # Both should still have their Second Chance (no change)
        assert all(
            engine.tableaus[pid].second_chance for pid in player_ids
        ), "All players should still have their Second Chance"


def test_second_chance_discarded_when_only_active_player():
    """Test that Second Chance is discarded if drawer is the only active player."""
    player_ids = ["p1", "p2"]
    bots = {
        "p1": RandomBot("p1"),
        "p2": RandomBot("p2"),
    }

    deck = [NumberCard(i) for i in range(1, 13)]
    discard: list = []

    with EventLogger(Path("/tmp/test_sc_only_active.jsonl")) as logger:
        engine = RoundEngine(
            player_ids=player_ids,
            bots=bots,
            event_logger=logger,
            deck=deck,
            discard_pile=discard,
            round_number=1,
            game_id="test",
            seed=42,
        )

        # Give p1 Second Chance and make p2 busted (inactive)
        engine.tableaus["p1"] = replace(
            engine.tableaus["p1"],
            second_chance=True,
        )
        engine.tableaus["p2"] = replace(
            engine.tableaus["p2"],
            is_active=False,
            is_busted=True,
        )

        # Try to give p1 another Second Chance
        # Since p1 already has one and p2 is busted, it should be discarded
        engine._resolve_second_chance("p1")

        # P1 should still have only one Second Chance
        assert engine.tableaus["p1"].second_chance, "P1 should still have Second Chance"

        # P2 should NOT have received it (busted players can't receive it)
        assert not engine.tableaus["p2"].second_chance, \
            "Busted player should not receive Second Chance"


def test_frozen_and_passed_not_eligible_for_freeze():
    """Test that frozen/passed players are NOT eligible for Freeze action."""
    player_ids = ["p1", "p2"]
    bots = {
        "p1": RandomBot("p1"),
        "p2": RandomBot("p2"),
    }

    deck = [NumberCard(i) for i in range(1, 13)]
    discard: list = []

    with EventLogger(Path("/tmp/test_frozen_not_eligible_freeze.jsonl")) as logger:
        engine = RoundEngine(
            player_ids=player_ids,
            bots=bots,
            event_logger=logger,
            deck=deck,
            discard_pile=discard,
            round_number=1,
            game_id="test",
            seed=42,
        )

        # Freeze p2
        engine.tableaus["p2"] = replace(
            engine.tableaus["p2"],
            is_active=False,
            is_frozen=True,
        )

        # Get eligible targets for Freeze
        eligible_freeze = engine._get_eligible_targets(ActionType.FREEZE)

        # P2 should NOT be eligible for Freeze (already frozen)
        assert "p2" not in eligible_freeze, \
            "Frozen players should not be eligible for Freeze action"

        # Get eligible targets for Flip Three
        eligible_flip = engine._get_eligible_targets(ActionType.FLIP_THREE)

        # P2 should NOT be eligible for Flip Three (not active)
        assert "p2" not in eligible_flip, \
            "Frozen players should not be eligible for Flip Three action"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

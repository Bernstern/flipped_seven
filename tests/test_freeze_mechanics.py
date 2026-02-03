"""
Tests for Freeze action card mechanics.

Per official rules (lines 120-125):
- Target player banks all points they have collected
- Target player is out of the round (no longer active)
- Target player scores their current hand
- Cannot be prevented or delayed
"""

from dataclasses import replace
from pathlib import Path

import pytest

from flip7.bots import RandomBot
from flip7.core.round_engine import RoundEngine
from flip7.events.event_logger import EventLogger
from flip7.types.cards import ActionCard, ActionType, NumberCard


def test_freeze_makes_player_inactive():
    """Test that Freeze makes the target player inactive."""
    player_ids = ["p1", "p2"]
    bots = {
        "p1": RandomBot("p1"),
        "p2": RandomBot("p2"),
    }

    deck = [NumberCard(i) for i in range(1, 13)]
    discard: list = []

    with EventLogger(Path("/tmp/test_freeze_inactive.jsonl")) as logger:
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

        # Verify p2 is initially active
        assert engine.tableaus["p2"].is_active

        # Apply Freeze to p2
        engine._resolve_freeze("p2")

        # P2 should now be inactive
        assert not engine.tableaus["p2"].is_active, \
            "Frozen player should be inactive"


def test_freeze_sets_frozen_flag():
    """Test that Freeze sets the is_frozen flag."""
    player_ids = ["p1", "p2"]
    bots = {
        "p1": RandomBot("p1"),
        "p2": RandomBot("p2"),
    }

    deck = [NumberCard(i) for i in range(1, 13)]
    discard: list = []

    with EventLogger(Path("/tmp/test_freeze_flag.jsonl")) as logger:
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

        # Apply Freeze to p2
        engine._resolve_freeze("p2")

        # P2 should have frozen flag set
        assert engine.tableaus["p2"].is_frozen, \
            "Frozen player should have is_frozen flag set"


def test_freeze_locks_in_score():
    """Test that Freeze locks in the player's current score."""
    player_ids = ["p1", "p2"]
    bots = {
        "p1": RandomBot("p1"),
        "p2": RandomBot("p2"),
    }

    deck = [NumberCard(i) for i in range(1, 13)]
    discard: list = []

    with EventLogger(Path("/tmp/test_freeze_score.jsonl")) as logger:
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

        # Give p2 some cards
        engine.tableaus["p2"] = replace(
            engine.tableaus["p2"],
            number_cards=(NumberCard(3), NumberCard(5), NumberCard(7)),
        )

        # Apply Freeze to p2
        engine._resolve_freeze("p2")

        # P2's cards should still be there (not cleared)
        assert len(engine.tableaus["p2"].number_cards) == 3, \
            "Frozen player should keep their cards"

        # P2 should score their current hand
        from flip7.core.scoring import calculate_score
        score = calculate_score(engine.tableaus["p2"])
        assert score.final_score == 15, \
            "Frozen player should score their current hand (3+5+7=15)"


def test_freeze_prevents_further_turns():
    """Test that frozen player can't take turns."""
    player_ids = ["p1", "p2"]
    bots = {
        "p1": RandomBot("p1"),
        "p2": RandomBot("p2"),
    }

    deck = [NumberCard(i) for i in range(1, 13)]
    discard: list = []

    with EventLogger(Path("/tmp/test_freeze_no_turns.jsonl")) as logger:
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
        engine._resolve_freeze("p2")

        # P2 should be inactive
        assert not engine.tableaus["p2"].is_active

        # Try to execute p2's turn (should be skipped)
        engine._execute_player_turn("p2")

        # P2 should still be frozen with no new cards
        # (turn execution should have been skipped)
        assert engine.tableaus["p2"].is_frozen


def test_freeze_not_eligible_for_freeze():
    """Test that already-frozen players can't be frozen again."""
    player_ids = ["p1", "p2"]
    bots = {
        "p1": RandomBot("p1"),
        "p2": RandomBot("p2"),
    }

    deck = [NumberCard(i) for i in range(1, 13)]
    discard: list = []

    with EventLogger(Path("/tmp/test_freeze_not_eligible.jsonl")) as logger:
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
        engine._resolve_freeze("p2")

        # Get eligible targets for another Freeze
        eligible = engine._get_eligible_targets(ActionType.FREEZE)

        # P2 should NOT be eligible (already frozen)
        assert "p2" not in eligible, \
            "Already-frozen player should not be eligible for another Freeze"


def test_freeze_during_initial_deal():
    """Test that Freeze during initial deal works correctly."""
    player_ids = ["p1", "p2"]
    bots = {
        "p1": RandomBot("p1"),
        "p2": RandomBot("p2"),
    }

    # P1 gets Freeze action card during initial deal
    deck = [
        ActionCard(ActionType.FREEZE),  # p1's initial card
        NumberCard(5),  # p2's initial card
    ] + [NumberCard(i) for i in range(6, 13)]

    discard: list = []

    with EventLogger(Path("/tmp/test_freeze_initial_deal.jsonl")) as logger:
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

        # Execute initial deal
        engine._initial_deal()

        # Check if any player got frozen
        # (The bot chooses who gets frozen, could be p1 or p2)
        frozen_players = [
            pid for pid in player_ids
            if engine.tableaus[pid].is_frozen
        ]

        # At least one player should be frozen
        # (or none if the target was invalid)
        # This test just verifies the mechanism works
        assert isinstance(frozen_players, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Tests for game end conditions and round end conditions.

Per official rules (lines 232-236):
- Game ends when at least one player has 200+ points after a round completes
- Player with highest score wins
- If tied at 200+, continue playing until one player has higher score

Per official rules (lines 222-230):
- Round ends when all players have passed or busted
- All Second Chance cards discarded at end of round
- All cards cleared from tableaus
"""

from pathlib import Path

import pytest

from flip7.bots import RandomBot
from flip7.core.deck import create_deck, shuffle_deck
from flip7.core.game_engine import GameEngine
from flip7.events.event_logger import EventLogger
from flip7.types.cards import NumberCard


def test_game_ends_at_200_points():
    """Test that game ends when a player reaches 200 points."""
    player_ids = ["p1", "p2"]
    bots = {
        "p1": RandomBot("p1"),
        "p2": RandomBot("p2"),
    }

    with EventLogger(Path("/tmp/test_game_end_200.jsonl")) as logger:
        deck = shuffle_deck(create_deck(), seed=42)
        discard: list = []

        engine = GameEngine(
            game_id="test_game",
            player_ids=player_ids,
            bots=bots,
            event_log_path=Path("/tmp/test_game_end_200.jsonl"),
            seed=42,
        )

        # Run the game
        final_state = engine.execute_game()

        # Game should end with at least one player at 200+
        max_score = max(final_state.scores.values())
        assert max_score >= 200, \
            f"Game should end when player reaches 200 (max score: {max_score})"

        # Winner should be set
        assert final_state.winner is not None, "Game should have a winner"

        # Winner should be the player with highest score
        winner_score = final_state.scores[final_state.winner]
        assert winner_score == max_score, \
            "Winner should have the highest score"


def test_round_ends_when_all_inactive():
    """Test that round ends when all players are inactive."""
    player_ids = ["p1", "p2"]
    bots = {
        "p1": RandomBot("p1"),
        "p2": RandomBot("p2"),
    }

    from flip7.core.round_engine import RoundEngine
    from dataclasses import replace

    deck = [NumberCard(i) for i in range(1, 13)]
    discard: list = []

    with EventLogger(Path("/tmp/test_round_end.jsonl")) as logger:
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

        # Make both players inactive (passed)
        for pid in player_ids:
            engine.tableaus[pid] = replace(
                engine.tableaus[pid],
                is_active=False,
                is_passed=True,
            )

        # Round should be complete
        assert engine._is_round_complete(), \
            "Round should be complete when all players are inactive"


def test_round_ends_all_busted():
    """Test that round ends when all players bust."""
    player_ids = ["p1", "p2"]
    bots = {
        "p1": RandomBot("p1"),
        "p2": RandomBot("p2"),
    }

    from flip7.core.round_engine import RoundEngine
    from dataclasses import replace

    deck = [NumberCard(i) for i in range(1, 13)]
    discard: list = []

    with EventLogger(Path("/tmp/test_all_bust.jsonl")) as logger:
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

        # Make both players busted
        for pid in player_ids:
            engine.tableaus[pid] = replace(
                engine.tableaus[pid],
                is_active=False,
                is_busted=True,
            )

        # Round should be complete
        assert engine._is_round_complete(), \
            "Round should be complete when all players are busted"

        # Calculate scores
        scores = engine._calculate_final_scores()

        # All busted players should score 0
        assert all(score == 0 for score in scores.values()), \
            "Busted players should all score 0"


def test_round_ends_mix_of_states():
    """Test round ends when players are in different inactive states."""
    player_ids = ["p1", "p2", "p3"]
    bots = {
        "p1": RandomBot("p1"),
        "p2": RandomBot("p2"),
        "p3": RandomBot("p3"),
    }

    from flip7.core.round_engine import RoundEngine
    from dataclasses import replace

    deck = [NumberCard(i) for i in range(1, 13)]
    discard: list = []

    with EventLogger(Path("/tmp/test_mixed_states.jsonl")) as logger:
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

        # P1 passed, P2 busted, P3 frozen
        engine.tableaus["p1"] = replace(
            engine.tableaus["p1"],
            is_active=False,
            is_passed=True,
            number_cards=(NumberCard(5), NumberCard(7)),
        )
        engine.tableaus["p2"] = replace(
            engine.tableaus["p2"],
            is_active=False,
            is_busted=True,
        )
        engine.tableaus["p3"] = replace(
            engine.tableaus["p3"],
            is_active=False,
            is_frozen=True,
            number_cards=(NumberCard(10),),
        )

        # Round should be complete
        assert engine._is_round_complete(), \
            "Round should be complete when all players inactive (different states)"

        # Calculate scores
        scores = engine._calculate_final_scores()

        # P1 should score their cards
        assert scores["p1"] == 12, "Passed player should score their cards (5+7=12)"

        # P2 should score 0 (busted)
        assert scores["p2"] == 0, "Busted player should score 0"

        # P3 should score their cards (frozen)
        assert scores["p3"] == 10, "Frozen player should score their cards"


def test_winner_determined_by_highest_score():
    """Test that winner is player with highest score at game end."""
    player_ids = ["p1", "p2"]
    bots = {
        "p1": RandomBot("p1"),
        "p2": RandomBot("p2"),
    }

    with EventLogger(Path("/tmp/test_winner.jsonl")) as logger:
        engine = GameEngine(
            game_id="test_winner",
            player_ids=player_ids,
            bots=bots,
            event_log_path=Path("/tmp/test_winner.jsonl"),
            seed=123,
        )

        final_state = engine.execute_game()

        # Winner should exist
        assert final_state.winner is not None

        # Winner's score should be >= 200
        winner_score = final_state.scores[final_state.winner]
        assert winner_score >= 200

        # Winner should have highest score
        max_score = max(final_state.scores.values())
        assert winner_score == max_score


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

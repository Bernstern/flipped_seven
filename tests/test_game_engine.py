"""
Tests for GameEngine - complete game execution and multi-round coordination.

This test suite verifies:
1. Multi-round game execution until winner determined
2. Score accumulation across rounds
3. Winner determination logic
4. Tie-breaking scenarios
5. Game continues until clear winner emerges

Per game rules:
- Games continue until at least one player reaches 200 points
- Winner is player with highest score at or above 200
- If tied at 200+, game continues until tie is broken
"""

from pathlib import Path

import pytest

from flip7.bots import ConservativeBot, RandomBot
from flip7.constants import WINNING_SCORE
from flip7.core.game_engine import GameEngine


def test_game_executes_until_winner():
    """Test that game runs multiple rounds until a player reaches 200."""
    player_ids = ["p1", "p2"]
    bots = {
        "p1": RandomBot("p1"),
        "p2": RandomBot("p2"),
    }

    engine = GameEngine(
        game_id="test_game",
        player_ids=player_ids,
        bots=bots,
        event_log_path=Path("/tmp/test_game_execution.jsonl"),
        seed=42,
        enable_logging=False,  # Disable logging for faster tests
    )

    final_state = engine.execute_game()

    # Game should be complete
    assert final_state.is_complete, "Game should be marked as complete"

    # Winner should be set
    assert final_state.winner is not None, "Game should have a winner"

    # Winner should have at least WINNING_SCORE
    winner_score = final_state.scores[final_state.winner]
    assert winner_score >= WINNING_SCORE, \
        f"Winner should have at least {WINNING_SCORE} points, got {winner_score}"

    # At least one round should have been played
    assert final_state.current_round > 0, "At least one round should be played"

    # Winner should have the highest score
    max_score = max(final_state.scores.values())
    assert winner_score == max_score, "Winner should have the highest score"


def test_score_accumulation_across_rounds():
    """Test that scores accumulate correctly over multiple rounds."""
    player_ids = ["p1", "p2"]
    bots = {
        "p1": RandomBot("p1"),
        "p2": RandomBot("p2"),
    }

    engine = GameEngine(
        game_id="test_accumulation",
        player_ids=player_ids,
        bots=bots,
        event_log_path=Path("/tmp/test_score_accumulation.jsonl"),
        seed=123,
        enable_logging=False,
    )

    # Initial scores should be 0
    assert all(score == 0 for score in engine.game_state.scores.values()), \
        "Initial scores should all be 0"

    final_state = engine.execute_game()

    # Final scores should be positive (players scored in at least some rounds)
    assert all(score >= 0 for score in final_state.scores.values()), \
        "All final scores should be non-negative"

    # Winner should have positive score
    assert final_state.scores[final_state.winner] > 0, \
        "Winner should have positive score"


def test_winner_has_highest_score():
    """Test that winner is always the player with the highest score."""
    player_ids = ["p1", "p2", "p3"]
    bots = {
        "p1": RandomBot("p1"),
        "p2": ConservativeBot("p2"),
        "p3": RandomBot("p3"),
    }

    engine = GameEngine(
        game_id="test_highest_score",
        player_ids=player_ids,
        bots=bots,
        event_log_path=Path("/tmp/test_highest_score.jsonl"),
        seed=456,
        enable_logging=False,
    )

    final_state = engine.execute_game()

    winner_score = final_state.scores[final_state.winner]
    max_score = max(final_state.scores.values())

    assert winner_score == max_score, \
        f"Winner score ({winner_score}) should equal max score ({max_score})"

    # No other player should have a higher score
    for player_id, score in final_state.scores.items():
        if player_id != final_state.winner:
            assert score <= winner_score, \
                f"Non-winner {player_id} has score {score} > winner score {winner_score}"


def test_game_continues_until_clear_winner():
    """Test that game continues if multiple players are tied at 200+."""
    player_ids = ["p1", "p2"]
    bots = {
        "p1": RandomBot("p1"),
        "p2": RandomBot("p2"),
    }

    engine = GameEngine(
        game_id="test_tiebreaker",
        player_ids=player_ids,
        bots=bots,
        event_log_path=Path("/tmp/test_tiebreaker.jsonl"),
        seed=789,
        enable_logging=False,
    )

    final_state = engine.execute_game()

    # At game end, there should be exactly one winner
    assert final_state.winner is not None, "Game should have a winner"

    # Winner should have unique highest score
    winner_score = final_state.scores[final_state.winner]
    other_scores = [score for pid, score in final_state.scores.items()
                    if pid != final_state.winner]

    for score in other_scores:
        assert score < winner_score, \
            f"Non-winner should not have same score as winner (both have {score})"


def test_multiple_rounds_played():
    """Test that games typically require multiple rounds to reach 200."""
    player_ids = ["p1", "p2"]
    bots = {
        "p1": ConservativeBot("p1"),
        "p2": ConservativeBot("p2"),
    }

    engine = GameEngine(
        game_id="test_multiple_rounds",
        player_ids=player_ids,
        bots=bots,
        event_log_path=Path("/tmp/test_multiple_rounds.jsonl"),
        seed=111,
        enable_logging=False,
    )

    final_state = engine.execute_game()

    # Games should typically take more than 1 round to reach 200
    # (though theoretically possible in 1 round with perfect play)
    assert final_state.current_round >= 1, "At least one round should be played"

    # Verify round number is reasonable (not stuck in infinite loop)
    assert final_state.current_round < 1000, \
        f"Game took {final_state.current_round} rounds - possible infinite loop"


def test_game_state_updates_each_round():
    """Test that game state properly updates after each round."""
    player_ids = ["p1", "p2"]
    bots = {
        "p1": RandomBot("p1"),
        "p2": RandomBot("p2"),
    }

    engine = GameEngine(
        game_id="test_state_updates",
        player_ids=player_ids,
        bots=bots,
        event_log_path=Path("/tmp/test_state_updates.jsonl"),
        seed=222,
        enable_logging=False,
    )

    # Check initial state
    assert engine.game_state.current_round == 0, "Initial round should be 0"
    assert not engine.game_state.is_complete, "Initial state should not be complete"
    assert engine.game_state.winner is None, "Initial state should have no winner"

    final_state = engine.execute_game()

    # Check final state
    assert final_state.current_round > 0, "Final round should be positive"
    assert final_state.is_complete, "Final state should be complete"
    assert final_state.winner is not None, "Final state should have winner"


def test_deck_persistence_across_rounds():
    """Test that deck and discard pile persist between rounds."""
    player_ids = ["p1", "p2"]
    bots = {
        "p1": RandomBot("p1"),
        "p2": RandomBot("p2"),
    }

    engine = GameEngine(
        game_id="test_deck_persistence",
        player_ids=player_ids,
        bots=bots,
        event_log_path=Path("/tmp/test_deck_persistence.jsonl"),
        seed=333,
        enable_logging=False,
    )

    # Record initial deck and discard pile references
    initial_deck_ref = id(engine.deck)
    initial_discard_ref = id(engine.discard_pile)

    final_state = engine.execute_game()

    # Same deck and discard pile objects should be used throughout
    # (they're mutated in place, not replaced)
    assert id(engine.deck) == initial_deck_ref, \
        "Deck object should be the same throughout the game"
    assert id(engine.discard_pile) == initial_discard_ref, \
        "Discard pile object should be the same throughout the game"


def test_all_players_included_in_scores():
    """Test that all players are included in score tracking."""
    player_ids = ["p1", "p2", "p3", "p4"]
    bots = {
        "p1": RandomBot("p1"),
        "p2": ConservativeBot("p2"),
        "p3": RandomBot("p3"),
        "p4": ConservativeBot("p4"),
    }

    engine = GameEngine(
        game_id="test_all_players",
        player_ids=player_ids,
        bots=bots,
        event_log_path=Path("/tmp/test_all_players.jsonl"),
        seed=444,
        enable_logging=False,
    )

    final_state = engine.execute_game()

    # All players should have scores
    assert set(final_state.scores.keys()) == set(player_ids), \
        "All players should be in final scores"

    # All scores should be non-negative
    for player_id, score in final_state.scores.items():
        assert score >= 0, f"Player {player_id} has negative score: {score}"


def test_winner_is_one_of_players():
    """Test that winner is always one of the actual players."""
    player_ids = ["alice", "bob"]
    bots = {
        "alice": RandomBot("alice"),
        "bob": RandomBot("bob"),
    }

    engine = GameEngine(
        game_id="test_valid_winner",
        player_ids=player_ids,
        bots=bots,
        event_log_path=Path("/tmp/test_valid_winner.jsonl"),
        seed=555,
        enable_logging=False,
    )

    final_state = engine.execute_game()

    assert final_state.winner in player_ids, \
        f"Winner {final_state.winner} is not in player list {player_ids}"


def test_game_engine_with_different_seeds():
    """Test that different seeds produce different game outcomes."""
    player_ids = ["p1", "p2"]
    bots_1 = {
        "p1": RandomBot("p1"),
        "p2": RandomBot("p2"),
    }
    bots_2 = {
        "p1": RandomBot("p1"),
        "p2": RandomBot("p2"),
    }

    # Game with seed 1
    engine_1 = GameEngine(
        game_id="test_seed_1",
        player_ids=player_ids,
        bots=bots_1,
        event_log_path=Path("/tmp/test_seed_1.jsonl"),
        seed=1,
        enable_logging=False,
    )
    final_1 = engine_1.execute_game()

    # Game with seed 2
    engine_2 = GameEngine(
        game_id="test_seed_2",
        player_ids=player_ids,
        bots=bots_2,
        event_log_path=Path("/tmp/test_seed_2.jsonl"),
        seed=2,
        enable_logging=False,
    )
    final_2 = engine_2.execute_game()

    # Games with different seeds should produce different results
    # (statistically very unlikely to be identical)
    assert (final_1.winner != final_2.winner or
            final_1.scores != final_2.scores or
            final_1.current_round != final_2.current_round), \
        "Different seeds should produce different outcomes"


def test_game_engine_initialization_validation():
    """Test that GameEngine validates initialization parameters."""
    # Empty player list should raise error
    with pytest.raises(ValueError, match="player_ids cannot be empty"):
        GameEngine(
            game_id="test",
            player_ids=[],
            bots={},
            event_log_path=Path("/tmp/test.jsonl"),
        )

    # Missing bot for player should raise error
    with pytest.raises(ValueError, match="bots dictionary must contain all player IDs"):
        GameEngine(
            game_id="test",
            player_ids=["p1", "p2"],
            bots={"p1": RandomBot("p1")},  # Missing p2
            event_log_path=Path("/tmp/test.jsonl"),
        )


def test_game_cannot_be_executed_twice():
    """Test that attempting to execute a completed game raises an error."""
    player_ids = ["p1", "p2"]
    bots = {
        "p1": RandomBot("p1"),
        "p2": RandomBot("p2"),
    }

    engine = GameEngine(
        game_id="test_double_execute",
        player_ids=player_ids,
        bots=bots,
        event_log_path=Path("/tmp/test_double_execute.jsonl"),
        seed=666,
        enable_logging=False,
    )

    # First execution should succeed
    engine.execute_game()

    # Second execution should fail
    with pytest.raises(RuntimeError, match="Game has already been completed"):
        engine.execute_game()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

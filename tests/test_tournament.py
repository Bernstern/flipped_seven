"""
Tests for tournament system.
"""

from pathlib import Path
import tempfile
import shutil

from flip7.bots import ScaredyBot, RandomBot
from flip7.tournament import (
    TournamentConfig,
    TournamentOrchestrator,
    generate_round_robin_matchups,
    count_matchups,
)


def test_round_robin_matchups():
    """Test round-robin matchup generation."""
    bot_classes = [RandomBot, ScaredyBot]
    matchups = generate_round_robin_matchups(bot_classes, 2)

    # Should have 1 matchup for 2 bots with 2 players per game
    assert len(matchups) == 1
    assert matchups[0] == ("RandomBot", "ScaredyBot")


def test_count_matchups():
    """Test matchup counting."""
    # 2 bots, 2 players per game: C(2,2) = 1
    assert count_matchups(2, 2) == 1

    # 3 bots, 2 players per game: C(3,2) = 3
    assert count_matchups(3, 2) == 3

    # 4 bots, 2 players per game: C(4,2) = 6
    assert count_matchups(4, 2) == 6

    # 4 bots, 3 players per game: C(4,3) = 4
    assert count_matchups(4, 3) == 4


def test_tournament_config_validation():
    """Test tournament configuration validation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)

        # Valid config
        config = TournamentConfig(
            tournament_name="test",
            players_per_game=2,
            best_of_n=3,
            bot_classes=[RandomBot, ScaredyBot],
            bot_timeout_seconds=1.0,
            output_dir=output_dir,
            save_replays=False,
        )
        assert config is not None

        # Invalid players_per_game
        try:
            TournamentConfig(
                tournament_name="test",
                players_per_game=5,  # Invalid
                best_of_n=3,
                bot_classes=[RandomBot, ScaredyBot],
                bot_timeout_seconds=1.0,
                output_dir=output_dir,
                save_replays=False,
            )
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

        # Invalid best_of_n (even number)
        try:
            TournamentConfig(
                tournament_name="test",
                players_per_game=2,
                best_of_n=4,  # Invalid (even)
                bot_classes=[RandomBot, ScaredyBot],
                bot_timeout_seconds=1.0,
                output_dir=output_dir,
                save_replays=False,
            )
            assert False, "Should have raised ValueError"
        except ValueError:
            pass


def test_tournament_execution():
    """Test full tournament execution."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)

        config = TournamentConfig(
            tournament_name="test_tournament",
            players_per_game=2,
            best_of_n=1,  # Quick test
            bot_classes=[RandomBot, ScaredyBot],
            bot_timeout_seconds=5.0,
            output_dir=output_dir,
            save_replays=False,
            max_workers=1,
            tournament_seed=42,
        )

        orchestrator = TournamentOrchestrator(config)
        results = orchestrator.run_tournament()

        # Verify results
        assert results.total_matches == 1
        assert len(results.bot_statistics) == 2
        assert "RandomBot" in results.bot_statistics
        assert "ScaredyBot" in results.bot_statistics

        # Verify one bot won
        leaderboard = results.get_leaderboard()
        assert len(leaderboard) == 2
        winner_name, winner_stats = leaderboard[0]
        assert winner_stats.matches_won == 1

        # Verify results file was created
        results_file = output_dir / "tournament_results.json"
        assert results_file.exists()


if __name__ == "__main__":
    print("Running tournament tests...")

    print("Test: round_robin_matchups")
    test_round_robin_matchups()
    print("  PASSED")

    print("Test: count_matchups")
    test_count_matchups()
    print("  PASSED")

    print("Test: tournament_config_validation")
    test_tournament_config_validation()
    print("  PASSED")

    print("Test: tournament_execution")
    test_tournament_execution()
    print("  PASSED")

    print("\nAll tests passed!")

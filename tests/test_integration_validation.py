"""Integration tests for configuration validation in the CLI."""

import tempfile
from pathlib import Path

import pytest

from flip7.utils.config_validator import ConfigurationError, validate_tournament_config


class TestIntegrationValidation:
    """Integration tests to verify validation catches common configuration errors."""

    def test_typical_valid_configuration(self, tmp_path: Path) -> None:
        """Test a typical valid configuration that would be used in production."""
        validate_tournament_config(
            games_per_matchup_h2h=100_000,
            games_per_matchup_all=1_000_000,
            bot_timeout_seconds=1.0,
            output_dir_h2h=tmp_path / "tournament_results_head_to_head",
            output_dir_all=tmp_path / "tournament_results_all_vs_all",
        )

    def test_user_forgot_to_change_zero_games(self, tmp_path: Path) -> None:
        """Test catching when user forgets to set games > 0."""
        with pytest.raises(ConfigurationError) as exc_info:
            validate_tournament_config(
                games_per_matchup_h2h=0,  # User forgot to change this
                games_per_matchup_all=1_000_000,
                bot_timeout_seconds=1.0,
                output_dir_h2h=tmp_path / "h2h",
                output_dir_all=tmp_path / "all",
            )
        error_msg = str(exc_info.value)
        assert "GAMES_PER_MATCHUP_HEAD_TO_HEAD must be > 0" in error_msg
        assert "Suggestion:" in error_msg

    def test_user_sets_unrealistic_timeout(self, tmp_path: Path) -> None:
        """Test catching when user sets an unrealistic timeout."""
        with pytest.raises(ConfigurationError) as exc_info:
            validate_tournament_config(
                games_per_matchup_h2h=1000,
                games_per_matchup_all=1000,
                bot_timeout_seconds=500.0,  # 500 seconds is way too long
                output_dir_h2h=tmp_path / "h2h",
                output_dir_all=tmp_path / "all",
            )
        error_msg = str(exc_info.value)
        assert "very large" in error_msg.lower()
        assert "unreasonable" in error_msg.lower()

    def test_user_uses_string_instead_of_path(self, tmp_path: Path) -> None:
        """Test catching when user uses string instead of Path object."""
        with pytest.raises(ConfigurationError) as exc_info:
            validate_tournament_config(
                games_per_matchup_h2h=1000,
                games_per_matchup_all=1000,
                bot_timeout_seconds=1.0,
                output_dir_h2h="./results",  # type: ignore
                output_dir_all=tmp_path / "all",
            )
        error_msg = str(exc_info.value)
        assert "must be a Path object" in error_msg
        assert "Path(" in error_msg  # Should suggest using Path()

    def test_validation_provides_actionable_feedback(self, tmp_path: Path) -> None:
        """Test that validation errors provide actionable feedback."""
        with pytest.raises(ConfigurationError) as exc_info:
            validate_tournament_config(
                games_per_matchup_h2h=-1,
                games_per_matchup_all=0,
                bot_timeout_seconds=0.001,
                output_dir_h2h=tmp_path / "h2h",
                output_dir_all=tmp_path / "all",
            )
        error_msg = str(exc_info.value)
        # Should mention all three problems
        assert "GAMES_PER_MATCHUP_HEAD_TO_HEAD" in error_msg
        assert "GAMES_PER_MATCHUP_ALL_VS_ALL" in error_msg
        assert "BOT_TIMEOUT_SECONDS" in error_msg
        # Should provide suggestions
        assert "Suggestion:" in error_msg or "at least" in error_msg.lower()

    def test_edge_case_minimum_valid_values(self, tmp_path: Path) -> None:
        """Test that minimum valid values pass validation."""
        validate_tournament_config(
            games_per_matchup_h2h=1,  # Minimum valid
            games_per_matchup_all=1,  # Minimum valid
            bot_timeout_seconds=0.01,  # Minimum recommended
            output_dir_h2h=tmp_path / "h2h",
            output_dir_all=tmp_path / "all",
        )

    def test_edge_case_maximum_valid_values(self, tmp_path: Path) -> None:
        """Test that maximum reasonable values pass validation."""
        validate_tournament_config(
            games_per_matchup_h2h=100_000_000,  # At the threshold
            games_per_matchup_all=100_000_000,  # At the threshold
            bot_timeout_seconds=300.0,  # Maximum reasonable
            output_dir_h2h=tmp_path / "h2h",
            output_dir_all=tmp_path / "all",
        )

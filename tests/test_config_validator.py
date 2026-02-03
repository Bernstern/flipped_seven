"""Tests for configuration validation."""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from flip7.utils.config_validator import (
    ConfigurationError,
    check_platform_compatibility,
    validate_tournament_config,
)


class TestValidateTournamentConfig:
    """Tests for tournament configuration validation."""

    def test_valid_config(self, tmp_path: Path) -> None:
        """Test that valid configuration passes validation."""
        output_h2h = tmp_path / "h2h"
        output_all = tmp_path / "all"

        # Should not raise
        validate_tournament_config(
            games_per_matchup_h2h=1000,
            games_per_matchup_all=1000,
            bot_timeout_seconds=1.0,
            output_dir_h2h=output_h2h,
            output_dir_all=output_all,
        )

    def test_games_h2h_zero(self, tmp_path: Path) -> None:
        """Test that GAMES_PER_MATCHUP_HEAD_TO_HEAD = 0 fails."""
        with pytest.raises(ConfigurationError) as exc_info:
            validate_tournament_config(
                games_per_matchup_h2h=0,
                games_per_matchup_all=1000,
                bot_timeout_seconds=1.0,
                output_dir_h2h=tmp_path / "h2h",
                output_dir_all=tmp_path / "all",
            )
        assert "GAMES_PER_MATCHUP_HEAD_TO_HEAD must be > 0" in str(exc_info.value)
        assert "got 0" in str(exc_info.value)

    def test_games_h2h_negative(self, tmp_path: Path) -> None:
        """Test that negative GAMES_PER_MATCHUP_HEAD_TO_HEAD fails."""
        with pytest.raises(ConfigurationError) as exc_info:
            validate_tournament_config(
                games_per_matchup_h2h=-100,
                games_per_matchup_all=1000,
                bot_timeout_seconds=1.0,
                output_dir_h2h=tmp_path / "h2h",
                output_dir_all=tmp_path / "all",
            )
        assert "GAMES_PER_MATCHUP_HEAD_TO_HEAD must be > 0" in str(exc_info.value)

    def test_games_h2h_not_integer(self, tmp_path: Path) -> None:
        """Test that non-integer GAMES_PER_MATCHUP_HEAD_TO_HEAD fails."""
        with pytest.raises(ConfigurationError) as exc_info:
            validate_tournament_config(
                games_per_matchup_h2h=1000.5,  # type: ignore
                games_per_matchup_all=1000,
                bot_timeout_seconds=1.0,
                output_dir_h2h=tmp_path / "h2h",
                output_dir_all=tmp_path / "all",
            )
        assert "GAMES_PER_MATCHUP_HEAD_TO_HEAD must be an integer" in str(exc_info.value)

    def test_games_h2h_very_large(self, tmp_path: Path) -> None:
        """Test warning for very large GAMES_PER_MATCHUP_HEAD_TO_HEAD."""
        with pytest.raises(ConfigurationError) as exc_info:
            validate_tournament_config(
                games_per_matchup_h2h=200_000_000,
                games_per_matchup_all=1000,
                bot_timeout_seconds=1.0,
                output_dir_h2h=tmp_path / "h2h",
                output_dir_all=tmp_path / "all",
            )
        assert "very large" in str(exc_info.value).lower()
        assert "200,000,000" in str(exc_info.value)

    def test_games_all_zero(self, tmp_path: Path) -> None:
        """Test that GAMES_PER_MATCHUP_ALL_VS_ALL = 0 fails."""
        with pytest.raises(ConfigurationError) as exc_info:
            validate_tournament_config(
                games_per_matchup_h2h=1000,
                games_per_matchup_all=0,
                bot_timeout_seconds=1.0,
                output_dir_h2h=tmp_path / "h2h",
                output_dir_all=tmp_path / "all",
            )
        assert "GAMES_PER_MATCHUP_ALL_VS_ALL must be > 0" in str(exc_info.value)

    def test_timeout_zero(self, tmp_path: Path) -> None:
        """Test that BOT_TIMEOUT_SECONDS = 0 fails."""
        with pytest.raises(ConfigurationError) as exc_info:
            validate_tournament_config(
                games_per_matchup_h2h=1000,
                games_per_matchup_all=1000,
                bot_timeout_seconds=0.0,
                output_dir_h2h=tmp_path / "h2h",
                output_dir_all=tmp_path / "all",
            )
        assert "BOT_TIMEOUT_SECONDS must be > 0" in str(exc_info.value)

    def test_timeout_negative(self, tmp_path: Path) -> None:
        """Test that negative BOT_TIMEOUT_SECONDS fails."""
        with pytest.raises(ConfigurationError) as exc_info:
            validate_tournament_config(
                games_per_matchup_h2h=1000,
                games_per_matchup_all=1000,
                bot_timeout_seconds=-1.0,
                output_dir_h2h=tmp_path / "h2h",
                output_dir_all=tmp_path / "all",
            )
        assert "BOT_TIMEOUT_SECONDS must be > 0" in str(exc_info.value)

    def test_timeout_too_large(self, tmp_path: Path) -> None:
        """Test that BOT_TIMEOUT_SECONDS > 300 fails."""
        with pytest.raises(ConfigurationError) as exc_info:
            validate_tournament_config(
                games_per_matchup_h2h=1000,
                games_per_matchup_all=1000,
                bot_timeout_seconds=400.0,
                output_dir_h2h=tmp_path / "h2h",
                output_dir_all=tmp_path / "all",
            )
        assert "very large" in str(exc_info.value).lower()
        assert "400" in str(exc_info.value)
        assert "unreasonable" in str(exc_info.value).lower()

    def test_timeout_too_small(self, tmp_path: Path) -> None:
        """Test warning for very small BOT_TIMEOUT_SECONDS."""
        with pytest.raises(ConfigurationError) as exc_info:
            validate_tournament_config(
                games_per_matchup_h2h=1000,
                games_per_matchup_all=1000,
                bot_timeout_seconds=0.005,
                output_dir_h2h=tmp_path / "h2h",
                output_dir_all=tmp_path / "all",
            )
        assert "very small" in str(exc_info.value).lower()
        assert "0.005" in str(exc_info.value)

    def test_timeout_not_number(self, tmp_path: Path) -> None:
        """Test that non-numeric BOT_TIMEOUT_SECONDS fails."""
        with pytest.raises(ConfigurationError) as exc_info:
            validate_tournament_config(
                games_per_matchup_h2h=1000,
                games_per_matchup_all=1000,
                bot_timeout_seconds="1.0",  # type: ignore
                output_dir_h2h=tmp_path / "h2h",
                output_dir_all=tmp_path / "all",
            )
        assert "BOT_TIMEOUT_SECONDS must be a number" in str(exc_info.value)

    def test_output_dir_not_path(self, tmp_path: Path) -> None:
        """Test that non-Path output directory fails."""
        with pytest.raises(ConfigurationError) as exc_info:
            validate_tournament_config(
                games_per_matchup_h2h=1000,
                games_per_matchup_all=1000,
                bot_timeout_seconds=1.0,
                output_dir_h2h="./h2h",  # type: ignore
                output_dir_all=tmp_path / "all",
            )
        assert "OUTPUT_DIR_HEAD_TO_HEAD must be a Path object" in str(exc_info.value)

    def test_output_dir_not_writable(self, tmp_path: Path) -> None:
        """Test that non-writable output directory fails."""
        # Create a directory with no write permissions
        readonly_dir = tmp_path / "readonly"
        readonly_dir.mkdir()
        output_dir = readonly_dir / "subdir" / "h2h"

        # Remove write permissions from readonly_dir
        os.chmod(readonly_dir, 0o444)

        try:
            with pytest.raises(ConfigurationError) as exc_info:
                validate_tournament_config(
                    games_per_matchup_h2h=1000,
                    games_per_matchup_all=1000,
                    bot_timeout_seconds=1.0,
                    output_dir_h2h=output_dir,
                    output_dir_all=tmp_path / "all",
                )
            error_msg = str(exc_info.value)
            # Should mention either "not writable" or "cannot be created"
            assert ("not writable" in error_msg.lower() or
                    "cannot be created" in error_msg.lower())
        finally:
            # Restore permissions for cleanup
            os.chmod(readonly_dir, 0o755)

    def test_multiple_errors_reported_together(self, tmp_path: Path) -> None:
        """Test that multiple configuration errors are reported together."""
        with pytest.raises(ConfigurationError) as exc_info:
            validate_tournament_config(
                games_per_matchup_h2h=0,
                games_per_matchup_all=-1,
                bot_timeout_seconds=0.0,
                output_dir_h2h=tmp_path / "h2h",
                output_dir_all=tmp_path / "all",
            )
        error_msg = str(exc_info.value)
        # Should contain multiple errors
        assert "GAMES_PER_MATCHUP_HEAD_TO_HEAD" in error_msg
        assert "GAMES_PER_MATCHUP_ALL_VS_ALL" in error_msg
        assert "BOT_TIMEOUT_SECONDS" in error_msg

    def test_valid_timeout_ranges(self, tmp_path: Path) -> None:
        """Test that reasonable timeout values pass validation."""
        for timeout in [0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 60.0, 300.0]:
            validate_tournament_config(
                games_per_matchup_h2h=1000,
                games_per_matchup_all=1000,
                bot_timeout_seconds=timeout,
                output_dir_h2h=tmp_path / "h2h",
                output_dir_all=tmp_path / "all",
            )


class TestCheckPlatformCompatibility:
    """Tests for platform compatibility checking."""

    def test_linux_platform_passes(self) -> None:
        """Test that Linux platform passes compatibility check."""
        with patch.object(sys, 'platform', 'linux'):
            check_platform_compatibility()  # Should not raise

    def test_darwin_platform_passes(self) -> None:
        """Test that macOS (darwin) platform passes compatibility check."""
        with patch.object(sys, 'platform', 'darwin'):
            check_platform_compatibility()  # Should not raise

    def test_windows_platform_fails(self) -> None:
        """Test that Windows platform fails compatibility check."""
        with patch.object(sys, 'platform', 'win32'):
            with pytest.raises(ConfigurationError) as exc_info:
                check_platform_compatibility()
            error_msg = str(exc_info.value)
            assert "Windows is not supported" in error_msg
            assert "WSL" in error_msg
            assert "signal.SIGALRM" in error_msg

    def test_windows_platform_suggests_solutions(self) -> None:
        """Test that Windows error message suggests helpful solutions."""
        with patch.object(sys, 'platform', 'win32'):
            with pytest.raises(ConfigurationError) as exc_info:
                check_platform_compatibility()
            error_msg = str(exc_info.value)
            assert "Solutions:" in error_msg
            assert "WSL" in error_msg
            assert "Linux" in error_msg

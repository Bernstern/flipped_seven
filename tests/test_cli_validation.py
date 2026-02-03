"""Tests for CLI integration with configuration validation."""

import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from flip7.cli.main import cli


class TestCLIValidation:
    """Tests for CLI configuration validation integration."""

    def test_cli_checks_platform_on_windows(self, tmp_path: Path) -> None:
        """Test that CLI checks platform compatibility before loading config."""
        # Create a valid tournament_config.py
        config_file = tmp_path / "tournament_config.py"
        config_file.write_text("""
from pathlib import Path

TOURNAMENT_NAME = "Test"
GAMES_PER_MATCHUP_HEAD_TO_HEAD = 100
GAMES_PER_MATCHUP_ALL_VS_ALL = 100
BOT_TIMEOUT_SECONDS = 1.0
OUTPUT_DIR_HEAD_TO_HEAD = Path("./h2h")
OUTPUT_DIR_ALL_VS_ALL = Path("./all")
SAVE_REPLAYS = False
TOURNAMENT_SEED = 42
""")

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            # Write config to current directory
            (Path.cwd() / "tournament_config.py").write_text(config_file.read_text())

            # Mock Windows platform
            with patch.object(sys, 'platform', 'win32'):
                result = runner.invoke(cli, [])

                # Should fail with platform error
                assert result.exit_code != 0
                assert "Windows is not supported" in result.output
                assert "WSL" in result.output

    def test_cli_validates_config_before_running(self, tmp_path: Path) -> None:
        """Test that CLI validates configuration before starting tournament."""
        # Create an INVALID tournament_config.py (zero games)
        config_file = tmp_path / "tournament_config.py"
        config_file.write_text("""
from pathlib import Path

TOURNAMENT_NAME = "Test"
GAMES_PER_MATCHUP_HEAD_TO_HEAD = 0  # INVALID!
GAMES_PER_MATCHUP_ALL_VS_ALL = 1000
BOT_TIMEOUT_SECONDS = 1.0
OUTPUT_DIR_HEAD_TO_HEAD = Path("./h2h")
OUTPUT_DIR_ALL_VS_ALL = Path("./all")
SAVE_REPLAYS = False
TOURNAMENT_SEED = 42
""")

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            # Write config to current directory
            (Path.cwd() / "tournament_config.py").write_text(config_file.read_text())

            # Run CLI (should fail validation before starting tournament)
            result = runner.invoke(cli, [])

            # Should fail with validation error
            assert result.exit_code != 0
            assert "GAMES_PER_MATCHUP_HEAD_TO_HEAD must be > 0" in result.output
            assert "Configuration validation failed" in result.output

    def test_cli_validates_timeout_range(self, tmp_path: Path) -> None:
        """Test that CLI validates timeout is in reasonable range."""
        # Create an INVALID tournament_config.py (unreasonable timeout)
        config_file = tmp_path / "tournament_config.py"
        config_file.write_text("""
from pathlib import Path

TOURNAMENT_NAME = "Test"
GAMES_PER_MATCHUP_HEAD_TO_HEAD = 1000
GAMES_PER_MATCHUP_ALL_VS_ALL = 1000
BOT_TIMEOUT_SECONDS = 500.0  # INVALID! Too large
OUTPUT_DIR_HEAD_TO_HEAD = Path("./h2h")
OUTPUT_DIR_ALL_VS_ALL = Path("./all")
SAVE_REPLAYS = False
TOURNAMENT_SEED = 42
""")

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            # Write config to current directory
            (Path.cwd() / "tournament_config.py").write_text(config_file.read_text())

            # Run CLI (should fail validation)
            result = runner.invoke(cli, [])

            # Should fail with validation error
            assert result.exit_code != 0
            assert "BOT_TIMEOUT_SECONDS" in result.output
            assert "very large" in result.output.lower()
            assert "unreasonable" in result.output.lower()

    def test_cli_validates_output_directories(self, tmp_path: Path) -> None:
        """Test that CLI validates output directories are Path objects."""
        # Create an INVALID tournament_config.py (string instead of Path)
        config_file = tmp_path / "tournament_config.py"
        config_file.write_text("""
from pathlib import Path

TOURNAMENT_NAME = "Test"
GAMES_PER_MATCHUP_HEAD_TO_HEAD = 1000
GAMES_PER_MATCHUP_ALL_VS_ALL = 1000
BOT_TIMEOUT_SECONDS = 1.0
OUTPUT_DIR_HEAD_TO_HEAD = "./h2h"  # INVALID! Should be Path
OUTPUT_DIR_ALL_VS_ALL = Path("./all")
SAVE_REPLAYS = False
TOURNAMENT_SEED = 42
""")

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            # Write config to current directory
            (Path.cwd() / "tournament_config.py").write_text(config_file.read_text())

            # Run CLI (should fail validation)
            result = runner.invoke(cli, [])

            # Should fail with validation error
            assert result.exit_code != 0
            assert "OUTPUT_DIR_HEAD_TO_HEAD must be a Path object" in result.output
